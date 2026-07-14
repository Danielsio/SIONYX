/**
 * SIONYX backend — single Cloudflare Worker replacing all Firebase Cloud
 * Functions so the project runs on the Firebase Spark (free) plan.
 *
 * Routing is intentionally tiny (no framework) to stay within Workers limits.
 * This Worker is the ONLY holder of the Firebase service account, so it is the
 * only writer of balances/purchases/passwords — money is server-authoritative.
 */
import { Env, dbGet } from './firebase';
import { corsHeaders, preflight, withCors } from './cors';
import { nedarimCallback, chargeSavedCard } from './payments';
import { adminResetPassword } from './auth';
import { deleteUser } from './users';
import { registerOrganization } from './org';
import { runCleanup, cleanupTestOrganization } from './cleanup';
import { deductPrint, deductTime } from './usage';
import { adjustBalance, setLatestRelease } from './admin';
import { setExitPassword, getExitPasswordStatus, verifyExitPassword } from './exitPassword';

type Handler = (req: Request, env: Env, ctx: ExecutionContext) => Promise<Response>;

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

const notImplemented = (name: string): Response =>
  json({ error: 'not_implemented', endpoint: name }, 501);

// ---- handlers --------------------------------------------------------------

const health: Handler = async () => json({ ok: true, service: 'sionyx-server' });

/** Read the latest published release (clients may also read RTDB directly). */
const latestVersion: Handler = async (_req, env) => {
  const data = await dbGet<{ version?: string; downloadUrl?: string }>(env, 'public/latestRelease');
  return json({ version: data?.version ?? null, downloadUrl: data?.downloadUrl ?? null });
};

// Stubs — implemented in subsequent increments (each replaces a Cloud Function).
const yemotWebhook: Handler = async () => notImplemented('auth/yemot');

// ---- router ----------------------------------------------------------------

const routes: Record<string, Record<string, Handler>> = {
  GET: {
    '/health': health,
    '/version/latest': latestVersion,
    '/admin/exit-password-status': getExitPasswordStatus,
  },
  POST: {
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
    '/admin/set-latest-release': setLatestRelease,
    '/admin/set-exit-password': setExitPassword,
    '/auth/verify-exit-password': verifyExitPassword,
  },
};

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    if (req.method === 'OPTIONS') return preflight(env, req);
    const requestId = crypto.randomUUID();
    const startedMs = Date.now();
    const cors = corsHeaders(env, req);
    const url = new URL(req.url);
    const handler = routes[req.method]?.[url.pathname];

    let res: Response;
    if (!handler) {
      res = json({ error: 'not_found' }, 404);
    } else {
      try {
        res = await handler(req, env, ctx);
      } catch (e) {
        console.error(
          JSON.stringify({
            event: 'unhandled_error',
            requestId,
            method: req.method,
            path: url.pathname,
            error: (e as Error).message,
          }),
        );
        res = json({ error: 'internal_error' }, 500);
      }
    }

    res = withCors(res, cors);
    res.headers.set('x-request-id', requestId);
    // One structured access-log line per request (Workers Logs indexes JSON).
    // pathname only — query strings can carry the nedarim callback secret.
    console.log(
      JSON.stringify({
        event: 'request',
        requestId,
        method: req.method,
        path: url.pathname,
        status: res.status,
        ms: Date.now() - startedMs,
      }),
    );
    return res;
  },

  /** Cron Trigger — replaces the scheduled cleanupInactiveUsers function. */
  async scheduled(_event: ScheduledController, env: Env, _ctx: ExecutionContext): Promise<void> {
    const summary = await runCleanup(env);
    console.log('[sionyx-server] scheduled cleanup done', summary);
  },
};
