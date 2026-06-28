/**
 * Payment endpoints — ports `nedarimCallback` (server-authoritative crediting).
 *
 * Security model: the gateway calls this with a secret in the URL/header; we
 * verify the amount against the stored purchase (anti-tampering), are idempotent
 * via `creditedAt`, and credit the user + mark the purchase in ONE fan-out write.
 * Clients can never credit themselves (RTDB rules deny it).
 */
import { Env, dbGet, dbUpdate } from './firebase';

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
