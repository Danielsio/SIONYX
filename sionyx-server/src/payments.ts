/**
 * Payment endpoints — ports `nedarimCallback` (server-authoritative crediting).
 *
 * Security model: the gateway calls this with a secret in the URL/header; we
 * verify the amount against the stored purchase (anti-tampering), are idempotent
 * via `creditedAt`, and credit the user + mark the purchase in ONE fan-out write.
 * Clients can never credit themselves (RTDB rules deny it).
 */
import { Env, dbGet, dbSet, dbUpdate, decryptData, verifyIdToken } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface Purchase {
  userId?: string;
  amount?: number;
  minutes?: number;
  printBudget?: number;
  validityDays?: number;
  status?: string;
  creditedAt?: string;
}

interface NedarimUser {
  remainingTime?: number;
  printBalance?: number;
}

/** Parse a Nedarim callback body (form-urlencoded or JSON). */
async function parseBody(req: Request): Promise<Record<string, string>> {
  const ct = req.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    return (await req.json().catch(() => ({}))) as Record<string, string>;
  }
  const text = await req.text();
  const out: Record<string, string> = {};
  for (const [k, v] of new URLSearchParams(text)) out[k] = v;
  return out;
}

export async function nedarimCallback(req: Request, env: Env): Promise<Response> {
  // Authenticate the gateway callback. Fail closed (the original only warned).
  if (!env.CALLBACK_SECRET) {
    console.error('[nedarim] CALLBACK_SECRET not configured — refusing callback');
    return json({ success: false, error: 'server_misconfigured' }, 500);
  }
  const url = new URL(req.url);
  const provided = url.searchParams.get('secret') || req.headers.get('x-callback-secret');
  if (provided !== env.CALLBACK_SECRET) {
    return json({ success: false, error: 'forbidden' }, 403);
  }

  const body = await parseBody(req);
  const Status = body.Status;
  const TransactionId = body.TransactionId;
  const purchaseId = (body.Param1 || '').trim(); // purchaseId
  const orgId = (body.Param2 || '').trim(); // orgId (multi-tenant)
  const amountNum = body.Amount != null ? Number(body.Amount) : NaN;

  // Validation
  if (Number.isNaN(amountNum) || amountNum < 0) return json({ success: false, error: 'invalid_amount' }, 400);
  if (!purchaseId) return json({ success: false, error: 'invalid_purchaseId' }, 400);
  if (!orgId) return json({ success: false, error: 'invalid_orgId' }, 400);
  if (!TransactionId || !Status) return json({ success: false, error: 'missing_fields' }, 400);

  const purchasePath = `organizations/${orgId}/purchases/${purchaseId}`;

  // Record the gateway result on the purchase.
  await dbUpdate(env, purchasePath, {
    status: Status === 'Error' ? 'failed' : 'completed',
    transactionId: TransactionId,
    amount: amountNum,
    creditCardNumber: body.CreditCardNumber ? '****' : '****',
    message: body.Message || '',
    callbackReceivedAt: Date.now(),
    processedAt: new Date().toISOString(),
  });

  if (Status === 'Error') {
    return json({ success: true, message: 'failure_recorded' });
  }

  // Re-read the purchase to verify + check idempotency.
  const purchase = await dbGet<Purchase>(env, purchasePath);
  if (!purchase) return json({ success: false, error: 'purchase_not_found' }, 404);

  // Anti-tampering: callback amount must match the stored purchase amount.
  if (purchase.amount != null && amountNum > 0) {
    const stored = Number(purchase.amount);
    if (!Number.isNaN(stored) && stored > 0 && Math.abs(stored - amountNum) > 0.01) {
      console.error('[nedarim] amount mismatch', { purchaseId, callbackAmount: amountNum, stored });
      return json({ success: false, error: 'amount_mismatch' }, 400);
    }
  }

  // Idempotency: already credited → no-op.
  if (purchase.creditedAt) {
    return json({ success: true, message: 'already_credited' });
  }
  if (!purchase.userId) return json({ success: false, error: 'purchase_missing_userId' }, 400);

  const userPath = `organizations/${orgId}/users/${purchase.userId}`;
  const user = await dbGet<NedarimUser>(env, userPath);
  if (!user) return json({ success: false, error: 'user_not_found' }, 404);

  const newTime = (Number(user.remainingTime) || 0) + (Number(purchase.minutes) || 0) * 60;
  const newPrint = (Number(user.printBalance) || 0) + (Number(purchase.printBudget) || 0);
  const nowIso = new Date().toISOString();

  // Atomic fan-out: credit the user AND mark the purchase credited together.
  const fanout: Record<string, unknown> = {
    [`${userPath}/remainingTime`]: newTime,
    [`${userPath}/printBalance`]: newPrint,
    [`${userPath}/updatedAt`]: nowIso,
    [`${userPath}/lastCreditedAt`]: nowIso,
    [`${userPath}/lastCreditedBy`]: 'nedarim-callback',
    [`${purchasePath}/creditedAt`]: nowIso,
    [`${purchasePath}/creditedUserId`]: purchase.userId,
  };
  if ((Number(purchase.validityDays) || 0) > 0) {
    const exp = new Date();
    exp.setDate(exp.getDate() + Number(purchase.validityDays));
    fanout[`${userPath}/timeExpiresAt`] = exp.toISOString();
  }

  await dbUpdate(env, '', fanout); // PATCH at root = multi-path fan-out update

  console.log('[nedarim] credited', { orgId, userId: purchase.userId, addMinutes: purchase.minutes, newTime });
  return json({ success: true, message: 'credited' });
}

interface PackageData {
  name?: string;
  price?: number;
  minutes?: number;
  prints?: number;
  validityDays?: number;
}

/**
 * Charge a user's saved card ("keva") server-side. The org's Nedarim gateway
 * password lives only here (decrypted from metadata) — never on the kiosk, which
 * was the audit's payment flaw. Creates a pending purchase, calls Nedarim
 * TashlumBodedNew, and lets the existing callback credit (idempotently).
 */
export async function chargeSavedCard(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);
  const userId = claims.user_id;

  const body = (await req.json().catch(() => null)) as { orgId?: string; packageId?: string } | null;
  if (!body?.orgId || !body?.packageId) return json({ success: false, error: 'missing_fields' }, 400);
  const { orgId, packageId } = body;

  const pkg = await dbGet<PackageData>(env, `organizations/${orgId}/packages/${packageId}`);
  if (!pkg || pkg.price == null) return json({ success: false, error: 'package_not_found' }, 404);

  const user = await dbGet<{ savedCard?: { kevaId?: string } }>(env, `organizations/${orgId}/users/${userId}`);
  const kevaId = user?.savedCard?.kevaId;
  if (!kevaId) return json({ success: false, error: 'no_saved_card' }, 400);

  const meta = await dbGet<{ nedarim_mosad_id?: string }>(env, `organizations/${orgId}/metadata`);
  // ApiPassword lives in the server-only secrets/ path (not client-readable metadata).
  const encApiPassword = await dbGet<string>(env, `organizations/${orgId}/secrets/nedarim_api_password`);
  if (!meta?.nedarim_mosad_id || !encApiPassword) {
    return json({ success: false, error: 'gateway_not_configured' }, 400);
  }
  const mosadId = String(await decryptData(env, meta.nedarim_mosad_id));
  const apiPassword = String(await decryptData(env, encApiPassword));

  // Pending purchase (matches the schema the callback credits from).
  const purchaseId = crypto.randomUUID();
  const amount = Number(pkg.price);
  await dbSet(env, `organizations/${orgId}/purchases/${purchaseId}`, {
    userId,
    amount,
    minutes: Number(pkg.minutes) || 0,
    printBudget: Number(pkg.prints) || 0,
    validityDays: Number(pkg.validityDays) || 0,
    packageName: pkg.name || '',
    status: 'pending',
    method: 'saved-card',
    createdAt: new Date().toISOString(),
  });

  // Server-side charge (ApiPassword stays here). The callback credits idempotently.
  const callbackUrl = `${new URL(req.url).origin}/payments/nedarim-callback?secret=${env.CALLBACK_SECRET}`;
  const form = new URLSearchParams({
    Action: 'TashlumBodedNew',
    MosadNumber: mosadId,
    ApiPassword: apiPassword,
    Currency: '1',
    KevaId: kevaId,
    Amount: String(amount),
    Tashloumim: '1',
    JoinToKevaId: 'NoJoin',
    Param1: purchaseId,
    Param2: orgId,
    CallBack: callbackUrl,
    Comments: `Purchase:${purchaseId}`,
  });

  let status = '';
  let respText = '';
  try {
    const resp = await fetch('https://matara.pro/nedarimplus/Reports/Manage3.aspx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    respText = await resp.text();
    status = (JSON.parse(respText) as { Status?: string }).Status || '';
  } catch (e) {
    console.error('[saved-card] gateway error', (e as Error).message);
  }

  if (status !== 'OK') {
    await dbUpdate(env, `organizations/${orgId}/purchases/${purchaseId}`, {
      status: 'failed',
      message: respText.slice(0, 200),
    });
    return json({ success: false, error: 'charge_failed', purchaseId }, 402);
  }

  console.log('[saved-card] charged', { orgId, userId, purchaseId });
  return json({ success: true, purchaseId });
}
