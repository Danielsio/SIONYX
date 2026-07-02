/**
 * CORS layer for the Worker.
 *
 * The web admin is served from Firebase Hosting (*.web.app) while this Worker
 * lives on *.workers.dev, so every browser call is cross-origin — and because
 * requests carry `Content-Type: application/json` (+ `Authorization`), the
 * browser sends an OPTIONS preflight first. Without an OPTIONS route and
 * `Access-Control-Allow-Origin` on responses, all browser-originated calls
 * fail before reaching a handler.
 *
 * Allowed origins come from the comma-separated `WEB_ORIGIN` var (see
 * wrangler.toml), falling back to the live web app origins. Localhost dev
 * servers are always allowed. Server-to-server callers (payment gateway,
 * kiosk, CI) send no Origin header and are unaffected.
 */
import { Env } from './firebase';

// Fallback when WEB_ORIGIN is not configured: the live web app. Firebase
// Hosting serves the same site on both domains.
const DEFAULT_ALLOWED_ORIGINS = [
  'https://sionyx-19636.web.app',
  'https://sionyx-19636.firebaseapp.com',
];

// Local dev servers (vite etc.) — any localhost port, http only.
const LOCALHOST_ORIGIN = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function isAllowed(env: Env, origin: string): boolean {
  const allowed = env.WEB_ORIGIN
    ? env.WEB_ORIGIN.split(',').map((s) => s.trim()).filter(Boolean)
    : DEFAULT_ALLOWED_ORIGINS;
  return allowed.includes(origin) || LOCALHOST_ORIGIN.test(origin);
}

/**
 * CORS headers for this request. `Access-Control-Allow-Origin` echoes the
 * request origin only when it is allowed; `Vary: Origin` is always set so
 * caches never serve one origin's ACAO to another.
 */
export function corsHeaders(env: Env, req: Request): Record<string, string> {
  const origin = req.headers.get('Origin');
  const headers: Record<string, string> = { Vary: 'Origin' };
  if (origin && isAllowed(env, origin)) headers['Access-Control-Allow-Origin'] = origin;
  return headers;
}

/** Short-circuit response for an OPTIONS preflight. */
export function preflight(env: Env, req: Request): Response {
  return new Response(null, {
    status: 204,
    headers: {
      ...corsHeaders(env, req),
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'authorization,content-type',
      'Access-Control-Max-Age': '86400',
    },
  });
}

/** Return a copy of `res` with the CORS headers merged in (handler response headers are immutable). */
export function withCors(res: Response, cors: Record<string, string>): Response {
  const out = new Response(res.body, res);
  for (const [k, v] of Object.entries(cors)) out.headers.set(k, v);
  return out;
}
