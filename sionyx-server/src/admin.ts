/**
 * Admin balance adjustment — replaces the web admin's direct RTDB write
 * (userService.adjustUserBalance). Server-authoritative so that, once RTDB rules
 * deny client balance writes, admins still adjust balances through here.
 *
 * Auth: caller proves identity with a Firebase ID token and must be an org admin.
 * Adjustments are additive (addSeconds/addPrints may be negative); clamped to >= 0.
 */
import { Env, dbGet, dbSet, dbCompareAndSet, verifyIdToken } from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

interface OrgUser {
  isAdmin?: boolean;
  role?: string;
}
const isAdmin = (u: OrgUser | null): boolean => !!u && (u.isAdmin === true || u.role === 'admin');

export async function adjustBalance(req: Request, env: Env): Promise<Response> {
  const m = (req.headers.get('Authorization') || '').match(/^Bearer (.+)$/);
  if (!m) return json({ success: false, error: 'missing_bearer_token' }, 401);
  const claims = await verifyIdToken(env, m[1]);
  if (!claims) return json({ success: false, error: 'invalid_id_token' }, 401);
  const callerUid = claims.user_id;

  const body = (await req.json().catch(() => null)) as
    | { orgId?: string; userId?: string; addSeconds?: number; addPrints?: number }
    | null;
  if (!body?.orgId || !body?.userId) return json({ success: false, error: 'missing_fields' }, 400);

  const caller = await dbGet<OrgUser>(env, `organizations/${body.orgId}/users/${callerUid}`);
  if (!isAdmin(caller)) return json({ success: false, error: 'not_admin' }, 403);

  const base = `organizations/${body.orgId}/users/${body.userId}`;
  const target = await dbGet<OrgUser>(env, base);
  if (!target) return json({ success: false, error: 'user_not_found' }, 404);

  let remainingTime: number | undefined;
  let printBalance: number | undefined;

  if (typeof body.addSeconds === 'number' && body.addSeconds !== 0) {
    const add = body.addSeconds;
    await dbCompareAndSet(env, `${base}/remainingTime`, (cur: any) => {
      remainingTime = Math.max(0, (Number(cur) || 0) + add);
      return remainingTime;
    });
  }
  if (typeof body.addPrints === 'number' && body.addPrints !== 0) {
    const add = body.addPrints;
    await dbCompareAndSet(env, `${base}/printBalance`, (cur: any) => {
      printBalance = Math.max(0, (Number(cur) || 0) + add);
      return printBalance;
    });
  }

  return json({ success: true, remainingTime, printBalance });
}

/**
 * Publish the latest release metadata to RTDB `public/latestRelease` (read by the
 * web download page and the kiosk auto-updater). Called by the release workflow
 * after it uploads the installer to GitHub Releases. Admin-secret gated; the
 * Worker's admin token writes the `.write:false` public node.
 */
export async function setLatestRelease(req: Request, env: Env): Promise<Response> {
  if ((req.headers.get('x-sionyx-secret') || '') !== env.ADMIN_SECRET) {
    return json({ success: false, error: 'unauthorized' }, 401);
  }
  const body = (await req.json().catch(() => null)) as
    | { version?: string; downloadUrl?: string; sha256?: string; buildNumber?: number; releasedAt?: string }
    | null;
  if (!body?.version || !body?.downloadUrl) return json({ success: false, error: 'missing_fields' }, 400);

  await dbSet(env, 'public/latestRelease', {
    version: body.version,
    downloadUrl: body.downloadUrl,
    sha256: body.sha256 || null,
    buildNumber: body.buildNumber ?? null,
    releasedAt: body.releasedAt || new Date().toISOString(),
  });
  console.log('[release] published', { version: body.version });
  return json({ success: true });
}
