/**
 * Auth endpoints.
 *
 * `adminResetPassword` ports `resetUserPassword`: an org admin resets a member's
 * password. The caller proves identity with a Firebase ID token; we verify they
 * are an admin of the org before changing the target user's password via the
 * Identity Toolkit admin API.
 */
import { Env, dbGet, dbUpdate, verifyIdToken, setUserPasswordByUid } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface OrgUser {
  isAdmin?: boolean;
  role?: string;
}

const isAdmin = (u: OrgUser | null): boolean => !!u && (u.isAdmin === true || u.role === 'admin');

export async function adminResetPassword(req: Request, env: Env): Promise<Response> {
  // Caller identity from Firebase ID token.
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);
  const callerUid = claims.user_id;

  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; userId?: string; newPassword?: string }
    | null;
  if (!body?.orgId || !body?.userId || !body?.newPassword) {
    return json({ success: false, error: 'missing_fields' }, 400);
  }
  if (body.newPassword.length < 6) {
    return json({ success: false, error: 'password_too_short' }, 400);
  }

  // Caller must be an admin of the org.
  const caller = await dbGet<OrgUser>(env, `organizations/${body.orgId}/users/${callerUid}`);
  if (!caller) return json({ success: false, error: 'not_org_member' }, 403);
  if (!isAdmin(caller)) return json({ success: false, error: 'not_admin' }, 403);

  // Target user must exist in the org.
  const targetPath = `organizations/${body.orgId}/users/${body.userId}`;
  const target = await dbGet<OrgUser>(env, targetPath);
  if (!target) return json({ success: false, error: 'user_not_found' }, 404);

  await setUserPasswordByUid(env, body.userId, body.newPassword);
  await dbUpdate(env, targetPath, {
    passwordResetAt: new Date().toISOString(),
    passwordResetBy: callerUid,
    updatedAt: new Date().toISOString(),
  });

  console.log('[auth] admin reset password', { orgId: body.orgId, target: body.userId, by: callerUid });
  return json({ success: true, message: 'password_reset' });
}
