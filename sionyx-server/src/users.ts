/**
 * User-management endpoints (org-admin initiated, ID-token authenticated).
 *
 * `deleteUser` ports the Cloud Function: an org admin deletes a member, with
 * the same guards (can't delete yourself or another admin) and the same cascade
 * (remove their messages, clear computer association, delete the user record,
 * delete the Firebase Auth account).
 */
import { Env, dbGet, dbSet, dbUpdate, deleteAuthUser, verifyIdToken } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface OrgUser {
  isAdmin?: boolean;
  role?: string;
  currentComputerId?: string;
}

const isAdmin = (u: OrgUser | null): boolean => !!u && (u.isAdmin === true || u.role === 'admin');

export async function deleteUser(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);
  const callerUid = claims.user_id;

  const body = (await req.json().catch(() => null)) as { orgId?: string; userId?: string } | null;
  if (!body?.orgId || !body?.userId) return json({ success: false, error: 'missing_fields' }, 400);
  const { orgId, userId } = body;

  const caller = await dbGet<OrgUser>(env, `organizations/${orgId}/users/${callerUid}`);
  if (!isAdmin(caller)) return json({ success: false, error: 'not_admin' }, 403);
  if (userId === callerUid) return json({ success: false, error: 'cannot_delete_self' }, 400);

  const userPath = `organizations/${orgId}/users/${userId}`;
  const target = await dbGet<OrgUser>(env, userPath);
  if (!target) return json({ success: false, error: 'user_not_found' }, 404);
  if (isAdmin(target)) return json({ success: false, error: 'cannot_delete_admin' }, 400);

  // 1. Remove this user's messages (fan-out delete).
  const messages = await dbGet<Record<string, { toUserId?: string }>>(env, `organizations/${orgId}/messages`);
  if (messages) {
    const batch: Record<string, null> = {};
    for (const [msgId, msg] of Object.entries(messages)) {
      if (msg?.toUserId === userId) batch[`organizations/${orgId}/messages/${msgId}`] = null;
    }
    if (Object.keys(batch).length) await dbUpdate(env, '', batch);
  }

  // 2. Clear computer association if this user holds one.
  if (target.currentComputerId) {
    const compPath = `organizations/${orgId}/computers/${target.currentComputerId}`;
    const comp = await dbGet<{ currentUserId?: string }>(env, compPath);
    if (comp && comp.currentUserId === userId) {
      await dbUpdate(env, compPath, { currentUserId: null, isActive: false });
    }
  }

  // 3. Delete the user record.
  await dbSet(env, userPath, null);

  // 4. Delete the Firebase Auth account (ignore "not found").
  try {
    await deleteAuthUser(env, userId);
  } catch (e) {
    console.warn('[users] auth delete failed (non-fatal)', (e as Error).message);
  }

  console.log('[users] deleted', { orgId, userId, by: callerUid });
  return json({ success: true, message: 'user_deleted' });
}
