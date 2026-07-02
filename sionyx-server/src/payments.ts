/**
 * Payment endpoints — ports `nedarimCallback` (server-authoritative crediting).
 *
 * Security model: the gateway calls this with a secret in the URL/header; we
 * verify the amount against the stored purchase (anti-tampering), and crediting
 * is idempotent via an atomic compare-and-set claim on `creditedAt` — only the
 * caller that flips it null → timestamp proceeds, so concurrent or retried
 * callbacks (Nedarim retries normally) can never double-credit.
 * Clients can never credit themselves (RTDB rules deny it).
 */
import { Env, dbCompareAndSet, dbGet, dbSet, dbUpdate, decryptData, verifyIdToken } from './firebase';

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

export type CreditOutcome =
  | 'credited'
  | 'already_credited'
  | 'purchase_not_found'
  | 'purchase_missing_userId'
  | 'amount_mismatch'
  | 'user_not_found'
  | 'conflict';

export interface CreditExtras {
  transactionId?: string;
  message?: string;
  /** Reusable gateway token to persist for one-click charges (with card last4). */
  savedCard?: { kevaId: string; last4: string | null };
}

/**
 * Idempotently credit a completed purchase to its user (the ONLY money-credit
 * path). Steps:
 *   1. verify the callback amount against the stored purchase amount — both
 *      must be > 0 and equal (±0.01); a 0/absent stored amount is rejected, it
 *      can't silently skip verification (H-1);
 *   2. CLAIM the credit by compare-and-setting `creditedAt` null → now. Only
 *      the claimer proceeds, so a concurrent/retried callback can't double-
 *      credit (C-2) — it sees the claim and reports `already_credited`;
 *   3. fan-out the user credit + purchase bookkeeping in one multi-path write.
 * If a step after the claim fails, the claim is released so a gateway retry
 * can credit again (an unreleasable claim under-credits, never double-credits).
 */
export async function creditPurchase(
  env: Env,
  orgId: string,
  purchaseId: string,
  callbackAmount: number,
  source: string,
  extras: CreditExtras = {},
): Promise<CreditOutcome> {
  const purchasePath = `organizations/${orgId}/purchases/${purchaseId}`;
  const purchase = await dbGet<Purchase>(env, purchasePath);
  if (!purchase) return 'purchase_not_found';
  if (purchase.creditedAt) return 'already_credited';
  if (!purchase.userId) return 'purchase_missing_userId';

  // Anti-tampering: the stored amount is what the client committed to pay and
  // the callback amount is what the gateway says was paid. Never credit unless
  // both are positive and equal.
  const stored = Number(purchase.amount);
  if (
    !Number.isFinite(stored) || stored <= 0 ||
    !Number.isFinite(callbackAmount) || callbackAmount <= 0 ||
    Math.abs(stored - callbackAmount) > 0.01
  ) {
    console.error('[credit] amount mismatch', { orgId, purchaseId, callbackAmount, stored });
    return 'amount_mismatch';
  }

  // Claim: atomically flip creditedAt null → now. Losing the race (or finding
  // it already set on retry) means someone else credited — do nothing.
  const nowIso = new Date().toISOString();
  const claimPath = `${purchasePath}/creditedAt`;
  let alreadyCredited = false;
  const claimed = await dbCompareAndSet(env, claimPath, (cur: unknown) => {
    if (cur != null) {
      alreadyCredited = true;
      return undefined; // abort — no write
    }
    alreadyCredited = false;
    return nowIso;
  });
  if (alreadyCredited) return 'already_credited';
  if (!claimed) return 'conflict';

  const releaseClaim = async () => {
    try {
      await dbSet(env, claimPath, null);
    } catch (e) {
      // The purchase looks credited but the user was not — needs manual replay.
      console.error('[credit] CRITICAL: claim release failed; purchase marked credited without crediting user', {
        orgId, purchaseId, error: (e as Error).message,
      });
    }
  };

  const userPath = `organizations/${orgId}/users/${purchase.userId}`;
  let user: NedarimUser | null;
  try {
    user = await dbGet<NedarimUser>(env, userPath);
  } catch (e) {
    await releaseClaim();
    throw e;
  }
  if (!user) {
    await releaseClaim();
    return 'user_not_found';
  }

  const newTime = (Number(user.remainingTime) || 0) + (Number(purchase.minutes) || 0) * 60;
  const newPrint = (Number(user.printBalance) || 0) + (Number(purchase.printBudget) || 0);

  // Atomic fan-out: credit the user AND finish the purchase bookkeeping together.
  const fanout: Record<string, unknown> = {
    [`${userPath}/remainingTime`]: newTime,
    [`${userPath}/printBalance`]: newPrint,
    [`${userPath}/updatedAt`]: nowIso,
    [`${userPath}/lastCreditedAt`]: nowIso,
    [`${userPath}/lastCreditedBy`]: source,
    [`${purchasePath}/creditedUserId`]: purchase.userId,
    [`${purchasePath}/status`]: 'completed',
    [`${purchasePath}/callbackAmount`]: callbackAmount,
    [`${purchasePath}/processedAt`]: nowIso,
    [`${purchasePath}/callbackReceivedAt`]: Date.now(),
  };
  if (extras.transactionId) fanout[`${purchasePath}/transactionId`] = extras.transactionId;
  if (extras.message) fanout[`${purchasePath}/message`] = extras.message;
  if ((Number(purchase.validityDays) || 0) > 0) {
    const exp = new Date();
    exp.setDate(exp.getDate() + Number(purchase.validityDays));
    fanout[`${userPath}/timeExpiresAt`] = exp.toISOString();
  }
  // Saved card: a tokenizing transaction (kiosk PaymentType=CreateToken) makes the
  // gateway return a reusable token. Persist it server-side so the user can later pay
  // one-click via /payments/charge-saved-card. The token alone cannot charge — that
  // needs the org's ApiPassword, which never leaves the Worker.
  if (extras.savedCard) {
    fanout[`${userPath}/savedCard`] = { ...extras.savedCard, savedAt: nowIso };
    console.log('[credit] saved card token stored', { orgId, userId: purchase.userId });
  }

  try {
    await dbUpdate(env, '', fanout); // PATCH at root = multi-path fan-out update
  } catch (e) {
    await releaseClaim();
    throw e;
  }

  console.log('[credit] credited', { orgId, userId: purchase.userId, addMinutes: purchase.minutes, newTime, source });
  return 'credited';
}

export async function nedarimCallback(req: Request, env: Env): Promise<Response> {
  // Authenticate the gateway callback. Fail closed (the original only warned).
  if (!env.CALLBACK_SECRET) {
    console.error('[nedarim] CALLBACK_SECRET not configured — refusing callback');
    return json({ success: false, error: 'server_misconfigured' }, 500);
  }
  const url = new URL(req.url);
  const provided = req.headers.get('x-callback-secret') || url.searchParams.get('secret');
  if (provided !== env.CALLBACK_SECRET) {
    return json({ success: false, error: 'forbidden' }, 403);
  }

  const body = await parseBody(req);
  const Status = body.Status;
  const TransactionId = body.TransactionId;
  const purchaseId = (body.Param1 || '').trim(); // purchaseId
  const orgId = (body.Param2 || '').trim(); // orgId (multi-tenant)
  const amountNum = body.Amount != null && body.Amount !== '' ? Number(body.Amount) : NaN;

  // Validation
  if (!purchaseId) return json({ success: false, error: 'invalid_purchaseId' }, 400);
  if (!orgId) return json({ success: false, error: 'invalid_orgId' }, 400);
  if (!TransactionId || !Status) return json({ success: false, error: 'missing_fields' }, 400);

  const purchasePath = `organizations/${orgId}/purchases/${purchaseId}`;

  // Failed payment: record the gateway result, never credit. The stored
  // `amount` is intentionally left untouched (it is the anti-tamper reference).
  if (Status === 'Error') {
    await dbUpdate(env, purchasePath, {
      status: 'failed',
      transactionId: TransactionId,
      message: body.Message || '',
      ...(Number.isFinite(amountNum) ? { callbackAmount: amountNum } : {}),
      callbackReceivedAt: Date.now(),
      processedAt: new Date().toISOString(),
    });
    return json({ success: true, message: 'failure_recorded' });
  }

  // A successful payment must state a positive amount — a 0/absent amount can
  // no longer bypass the anti-tampering check (H-1).
  if (!Number.isFinite(amountNum) || amountNum <= 0) {
    return json({ success: false, error: 'invalid_amount' }, 400);
  }

  const savedToken = body.KevaId || body.Tokef || body.Token || body.TransactionToken || '';
  const outcome = await creditPurchase(env, orgId, purchaseId, amountNum, 'nedarim-callback', {
    transactionId: TransactionId,
    message: body.Message || '',
    ...(savedToken
      ? {
          savedCard: {
            kevaId: savedToken,
            last4: (body.CreditCardNumber || '').replace(/\D/g, '').slice(-4) || null,
          },
        }
      : {}),
  });

  switch (outcome) {
    case 'credited':
      return json({ success: true, message: 'credited' });
    case 'already_credited':
      return json({ success: true, message: 'already_credited' });
    case 'purchase_not_found':
      return json({ success: false, error: 'purchase_not_found' }, 404);
    case 'purchase_missing_userId':
      return json({ success: false, error: 'purchase_missing_userId' }, 400);
    case 'amount_mismatch':
      return json({ success: false, error: 'amount_mismatch' }, 400);
    case 'user_not_found':
      return json({ success: false, error: 'user_not_found' }, 404);
    case 'conflict':
      return json({ success: false, error: 'conflict' }, 409);
  }
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
