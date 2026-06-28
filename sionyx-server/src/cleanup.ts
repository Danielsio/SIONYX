/**
 * Cleanup jobs.
 *
 * `runCleanup` ports `cleanupInactiveUsers` (called from the daily cron): delete
 * non-admin users who never purchased and registered more than N days ago, with
 * the same cascade as deleteUser. `cleanupTestOrganization` wipes a test/ci
 * org (admin-secret gated; CI use).
 */
import { Env, dbGet, dbSet, dbUpdate, deleteAuthUser } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface CleanupSummary {
  orgs: number;
  deleted: number;
  skipped: number;
  errors: number;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export async function runCleanup(env: Env, singleOrgId?: string): Promise<CleanupSummary> {
  const days = Number(env.INACTIVE_DAYS_NEVER_PURCHASED) || 7;
  const cutoff = Date.now() - days * 86_400_000;
  const summary: CleanupSummary = { orgs: 0, deleted: 0, skipped: 0, errors: 0 };

  let organizations: Record<string, any> = {};
  if (singleOrgId) {
    const org = await dbGet<any>(env, `organizations/${singleOrgId}`);
    if (!org) return summary;
    organizations = { [singleOrgId]: org };
  } else {
    organizations = (await dbGet<Record<string, any>>(env, 'organizations')) || {};
  }

  for (const [orgId, orgData] of Object.entries(organizations)) {
    if (!orgData || !orgData.users) continue;
    summary.orgs++;
    const users: Record<string, any> = orgData.users || {};
    const purchases: Record<string, any> = orgData.purchases || {};
    const withPurchases = new Set(
      Object.values(purchases).map((p: any) => p?.userId).filter(Boolean),
    );

    for (const [userId, u] of Object.entries(users) as [string, any][]) {
      if (u.isAdmin) { summary.skipped++; continue; }
      if (withPurchases.has(userId)) { summary.skipped++; continue; }
      const createdAt = u.createdAt ? new Date(u.createdAt).getTime() : 0;
      if (createdAt > cutoff) { summary.skipped++; continue; }

      try {
        // 1. Remove the user's messages.
        if (orgData.messages) {
          const batch: Record<string, null> = {};
          for (const [mid, m] of Object.entries(orgData.messages) as [string, any][]) {
            if (m?.toUserId === userId) batch[`organizations/${orgId}/messages/${mid}`] = null;
          }
          if (Object.keys(batch).length) await dbUpdate(env, '', batch);
        }
        // 2. Clear computer association.
        const compId = u.currentComputerId;
        if (compId && orgData.computers?.[compId]?.currentUserId === userId) {
          await dbUpdate(env, `organizations/${orgId}/computers/${compId}`, {
            currentUserId: null,
            isActive: false,
          });
        }
        // 3. Delete the user record + Auth account.
        await dbSet(env, `organizations/${orgId}/users/${userId}`, null);
        try { await deleteAuthUser(env, userId); } catch { /* ignore not-found */ }
        summary.deleted++;
      } catch (e) {
        console.warn('[cleanup] error deleting user', { orgId, userId, err: (e as Error).message });
        summary.errors++;
      }
    }
  }
  return summary;
}

export async function cleanupTestOrganization(req: Request, env: Env): Promise<Response> {
  if ((req.headers.get('x-sionyx-secret') || '') !== env.ADMIN_SECRET) {
    return json({ success: false, error: 'unauthorized' }, 401);
  }
  const body = (await req.json().catch(() => null)) as { orgId?: string } | null;
  const orgId = body?.orgId;
  if (!orgId) return json({ success: false, error: 'missing_orgId' }, 400);

  const lower = orgId.toLowerCase();
  if (!lower.startsWith('ci') && !lower.startsWith('test')) {
    return json({ success: false, error: 'only_test_orgs' }, 403);
  }

  const org = await dbGet<any>(env, `organizations/${orgId}`);
  if (!org) return json({ success: true, message: 'nothing_to_clean' });

  const adminUid = org.metadata?.admin_uid;
  if (adminUid) {
    try { await deleteAuthUser(env, adminUid); } catch { /* ignore */ }
  }
  if (org.users) {
    for (const uid of Object.keys(org.users)) {
      if (uid === adminUid) continue;
      try { await deleteAuthUser(env, uid); } catch { /* ignore */ }
    }
  }
  await dbSet(env, `organizations/${orgId}`, null);
  console.log('[cleanup] test org wiped', { orgId });
  return json({ success: true, message: 'cleaned' });
}
