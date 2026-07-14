/**
 * Kiosk admin-exit password — set from the web console, verified by the kiosk.
 *
 * Why this is server-side: the password unlocks a kiosk's lockdown. The fork
 * stores it at `metadata/settings/adminExitPassword` in PLAINTEXT, and metadata
 * is readable by every user in the org — so any kiosk user can read it and walk
 * out. Here it lives at `organizations/$orgId/secrets/admin_exit_password`
 * (RTDB rules deny clients that path entirely), AES-GCM encrypted, and the
 * plaintext is NEVER returned: the kiosk submits a candidate and gets a boolean.
 *
 * Brute force: verification is rate-limited per org+IP (a 4-digit password is
 * otherwise guessable), and a wrong answer is indistinguishable from "not set".
 */
import { Env, dbGet, dbSet, decryptData, encryptData, verifyIdToken } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface OrgUser {
  isAdmin?: boolean;
  role?: string;
}
const isOrgAdmin = (u: OrgUser | null): boolean =>
  !!u && (u.isAdmin === true || u.role === 'admin');

const secretPath = (orgId: string) => `organizations/${orgId}/secrets/admin_exit_password`;

/** Constant-time compare so a wrong answer leaks no timing signal. */
function timingSafeEqual(a: string, b: string): boolean {
  const ab = new TextEncoder().encode(a);
  const bb = new TextEncoder().encode(b);
  // Length differences are inherently visible; compare content in fixed time.
  let diff = ab.length ^ bb.length;
  const len = Math.max(ab.length, bb.length);
  for (let i = 0; i < len; i++) {
    diff |= (ab[i] ?? 0) ^ (bb[i] ?? 0);
  }
  return diff === 0;
}

/**
 * Set (or clear) the org's kiosk exit password. Admin-only.
 * Body: { orgId, password }  — an empty password removes the remote override,
 * so kiosks fall back to the one provisioned by the installer.
 */
export async function setExitPassword(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);

  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; password?: string }
    | null;
  if (!body?.orgId) return json({ success: false, error: 'missing_fields' }, 400);

  const caller = await dbGet<OrgUser>(env, `organizations/${body.orgId}/users/${claims.user_id}`);
  if (!isOrgAdmin(caller)) return json({ success: false, error: 'not_admin' }, 403);

  const password = (body.password ?? '').trim();

  if (!password) {
    await dbSet(env, secretPath(body.orgId), null);
    console.log(JSON.stringify({ event: 'exit_password_cleared', orgId: body.orgId }));
    return json({ success: true, cleared: true });
  }

  if (password.length < 4) {
    return json({ success: false, error: 'password_too_short' }, 400);
  }

  // encryptData fails closed when ENCRYPTION_KEY is missing — we never store a
  // readable password.
  await dbSet(env, secretPath(body.orgId), await encryptData(env, password));
  console.log(JSON.stringify({ event: 'exit_password_set', orgId: body.orgId }));
  return json({ success: true });
}

/** Whether a remote password is configured (never reveals it). Admin-only. */
export async function getExitPasswordStatus(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);

  const url = new URL(req.url);
  const orgId = url.searchParams.get('orgId') || '';
  if (!orgId) return json({ success: false, error: 'missing_fields' }, 400);

  const caller = await dbGet<OrgUser>(env, `organizations/${orgId}/users/${claims.user_id}`);
  if (!isOrgAdmin(caller)) return json({ success: false, error: 'not_admin' }, 403);

  const stored = await dbGet<string>(env, secretPath(orgId));
  return json({ success: true, configured: !!stored });
}

/**
 * Verify a candidate exit password (called by the kiosk). Returns only a
 * boolean. Any authenticated member of the org may ask — the kiosk runs as the
 * logged-in user — so this is rate-limited to stop guessing.
 */
export async function verifyExitPassword(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);

  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; password?: string }
    | null;
  if (!body?.orgId || !body?.password) {
    return json({ success: false, error: 'missing_fields' }, 400);
  }

  // The caller must belong to the org whose kiosk they are trying to unlock.
  const caller = await dbGet<OrgUser>(env, `organizations/${body.orgId}/users/${claims.user_id}`);
  if (!caller) return json({ success: false, error: 'not_in_org' }, 403);

  // Throttle guessing (a short numeric password is otherwise brute-forceable).
  if (env.EXIT_PASSWORD_LIMITER) {
    const ip = req.headers.get('CF-Connecting-IP') || 'unknown';
    const { success } = await env.EXIT_PASSWORD_LIMITER.limit({ key: `${body.orgId}:${ip}` });
    if (!success) return json({ success: false, error: 'rate_limited' }, 429);
  }

  const stored = await dbGet<string>(env, secretPath(body.orgId));
  if (!stored) {
    // No remote password configured — the kiosk falls back to its local one.
    return json({ success: true, valid: false, configured: false });
  }

  let valid = false;
  try {
    const plain = String(await decryptData(env, stored));
    valid = timingSafeEqual(plain, body.password);
  } catch (e) {
    console.error(
      JSON.stringify({ event: 'exit_password_decrypt_failed', orgId: body.orgId, error: (e as Error).message })
    );
    return json({ success: false, error: 'internal_error' }, 500);
  }

  if (!valid) {
    console.warn(JSON.stringify({ event: 'exit_password_rejected', orgId: body.orgId }));
  }
  return json({ success: true, valid, configured: true });
}
