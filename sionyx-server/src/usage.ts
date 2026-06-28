/**
 * Usage endpoints — server-authoritative balance deduction for the kiosk.
 *
 * Once RTDB rules deny clients from writing remainingTime/printBalance, the kiosk
 * deducts through here. Deduction-only + caller must be the user themselves, so
 * the worst a caller can do is reduce their OWN balance (no revenue impact). The
 * Worker writes via the service account (atomic compare-and-set on the field).
 */
import { Env, dbCompareAndSet, verifyIdToken } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

async function isSelf(req: Request, env: Env, userId: string): Promise<boolean> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return false;
  const claims = await verifyIdToken(env, m[1]);
  return !!claims && claims.user_id === userId;
}

export async function deductPrint(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; userId?: string; amount?: number; allowNegative?: boolean }
    | null;
  if (!body?.orgId || !body?.userId || typeof body.amount !== 'number') {
    return json({ success: false, error: 'missing_fields' }, 400);
  }
  if (!(await isSelf(req, env, body.userId))) return json({ success: false, error: 'unauthorized' }, 401);

  const amount = body.amount;
  const allowNegative = body.allowNegative === true;
  let newBalance = 0;
  const ok = await dbCompareAndSet(
    env,
    `organizations/${body.orgId}/users/${body.userId}/printBalance`,
    (cur: any) => {
      const current = Number(cur) || 0;
      newBalance = allowNegative ? current - amount : Math.max(0, current - amount);
      return newBalance;
    },
  );
  return ok ? json({ success: true, printBalance: newBalance }) : json({ success: false, error: 'conflict' }, 409);
}

export async function deductTime(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; userId?: string; seconds?: number }
    | null;
  if (!body?.orgId || !body?.userId || typeof body.seconds !== 'number') {
    return json({ success: false, error: 'missing_fields' }, 400);
  }
  if (!(await isSelf(req, env, body.userId))) return json({ success: false, error: 'unauthorized' }, 401);

  const seconds = body.seconds;
  let remaining = 0;
  const ok = await dbCompareAndSet(
    env,
    `organizations/${body.orgId}/users/${body.userId}/remainingTime`,
    (cur: any) => {
      const current = Number(cur) || 0;
      remaining = Math.max(0, current - seconds);
      return remaining;
    },
  );
  return ok ? json({ success: true, remainingTime: remaining }) : json({ success: false, error: 'conflict' }, 409);
}
