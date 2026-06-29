/**
 * SIONYX backend — single Cloudflare Worker replacing all Firebase Cloud
 * Functions so the project runs on the Firebase Spark (free) plan.
 *
 * Routing is intentionally tiny (no framework) to stay within Workers limits.
 * This Worker is the ONLY holder of the Firebase service account, so it is the
 * only writer of balances/purchases/passwords — money is server-authoritative.
 */
import {
  Env,
  dbGet,
  dbUpdate,
  dbCompareAndSet,
  verifyIdToken,
} from './firebase';
import { nedarimCallback } from './payments';
import { adminResetPassword } from './auth';
import { deleteUser } from './users';
import { registerOrganization } from './org';
import { runCleanup, cleanupTestOrganization } from './cleanup';
import { deductPrint, deductTime } from './usage';
import { adjustBalance } from './admin';

type Handler = (req: Request, env: Env, ctx: ExecutionContext) => Promise<Response>;

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

const notImplemented = (name: string): Response =>
  json({ error: 'not_implemented', endpoint: name }, 501);

// ---- auth helpers ----------------------------------------------------------

async function requireUser(req: Request, env: Env): Promise<{ user_id: string; email?: string }> {
  const auth = req.headers.get('Authorization') || '';
  const m = auth.match(/^Bearer (.+)$/);
  if (!m) throw new HttpError(401, 'missing_bearer_token');
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) throw new HttpError(401, 'invalid_id_token');
  return claims;
}

function requireAdminSecret(req: Request, env: Env): void {
  const secret = req.headers.get('x-sionyx-secret');
  if (!secret || secret !== env.ADMIN_SECRET) throw new HttpError(401, 'unauthorized');
}

class HttpError extends Error {
  constructor(public status: number, public code: string) {
    super(code);
  }
}

// ---- handlers --------------------------------------------------------------

const health: Handler = async () => json({ ok: true, service: 'sionyx-server' });

/** Read the latest published release (clients may also read RTDB directly). */
const latestVersion: Handler = async (_req, env) => {
  const data = await dbGet<{ version?: string; downloadUrl?: string }>(env, 'public/latestRelease');
  return json({ version: data?.version ?? null, downloadUrl: data?.downloadUrl ?? null });
};

/**
 * Server-authoritative credit (admin-only). Proves the money-write path that
 * RTDB rules now forbid clients from doing. Body: { orgId, userId, addSeconds?, addPrintBalance? }
 */
const adminCredit: Handler = async (req, env) => {
  requireAdminSecret(req, env);
  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; userId?: string; addSeconds?: number; addPrintBalance?: number }
    | null;
  if (!body?.orgId || !body?.userId) throw new HttpError(400, 'missing_fields');
  const base = `organizations/${body.orgId}/users/${body.userId}`;
  const ok = await dbCompareAndSet(env, base, (cur: any) => {
    const u = cur || {};
    return {
      ...u,
      remainingTime: Math.max(0, (Number(u.remainingTime) || 0) + (Number(body.addSeconds) || 0)),
      printBalance: (Number(u.printBalance) || 0) + (Number(body.addPrintBalance) || 0),
      updatedAt: new Date().toISOString(),
    };
  });
  return ok ? json({ ok: true }) : json({ error: 'conflict' }, 409);
};

// Stubs — implemented in subsequent increments (each replaces a Cloud Function).
const chargeSavedCard: Handler = async () => notImplemented('payments/charge-saved-card');
const yemotWebhook: Handler = async () => notImplemented('auth/yemot');

// ---- router ----------------------------------------------------------------

const routes: Record<string, Record<string, Handler>> = {
  GET: {
    '/health': health,
    '/version/latest': latestVersion,
  },
  POST: {
    '/admin/credit': adminCredit,
    '/payments/nedarim-callback': nedarimCallback,
    '/payments/charge-saved-card': chargeSavedCard,
    '/auth/reset-password': adminResetPassword,
    '/auth/yemot': yemotWebhook,
    '/org/register': registerOrganization,
    '/admin/delete-user': deleteUser,
    '/admin/cleanup-test-org': cleanupTestOrganization,
    '/usage/deduct-print': deductPrint,
    '/usage/deduct-time': deductTime,
    '/admin/adjust-balance': adjustBalance,
  },
};

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const handler = routes[req.method]?.[url.pathname];
    if (!handler) return json({ error: 'not_found' }, 404);
    try {
      return await handler(req, env, ctx);
    } catch (e) {
      if (e instanceof HttpError) return json({ error: e.code }, e.status);
      console.error('[sionyx-server] error', (e as Error).message);
      return json({ error: 'internal_error' }, 500);
    }
  },

  /** Cron Trigger — replaces the scheduled cleanupInactiveUsers function. */
  async scheduled(_event: ScheduledController, env: Env, _ctx: ExecutionContext): Promise<void> {
    const summary = await runCleanup(env);
    console.log('[sionyx-server] scheduled cleanup done', summary);
  },
};
