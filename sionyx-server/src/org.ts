/**
 * Organization registration — ports `registerOrganization`.
 *
 * Public endpoint, hardened against abuse (H-6):
 *  - per-IP rate limit (Workers Rate Limiting binding, wrangler.toml);
 *  - Cloudflare Turnstile, ENFORCED once TURNSTILE_SECRET is configured
 *    (rollout toggle: the web widget must ship before the secret is set);
 *  - the org id is CLAIMED atomically (compare-and-set on the metadata node),
 *    closing the dup-check TOCTOU race;
 *  - every step after the claim rolls back on failure — no half-provisioned
 *    org, no orphaned Auth user.
 */
import {
  Env,
  dbSet,
  dbUpdate,
  dbCompareAndSet,
  encodeClientReadable,
  encryptData,
  createAuthUser,
  deleteAuthUser,
  phoneToEmail,
  EmailExistsError,
} from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

/** Server-side Turnstile check (siteverify is never called from the browser). */
async function verifyTurnstile(env: Env, token: string, ip: string): Promise<boolean> {
  const resp = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip }),
  });
  if (!resp.ok) return false;
  const data = (await resp.json()) as { success?: boolean };
  return data.success === true;
}

export async function registerOrganization(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => null)) as Record<string, string> | null;
  if (!body) return json({ success: false, error: 'invalid_body' }, 400);

  const ip = req.headers.get('CF-Connecting-IP') || 'unknown';

  // Abuse throttle: this endpoint creates Auth users + DB records for anyone.
  if (env.REGISTER_RATE_LIMITER) {
    const { success } = await env.REGISTER_RATE_LIMITER.limit({ key: ip });
    if (!success) return json({ success: false, error: 'rate_limited' }, 429);
  }

  if (env.TURNSTILE_SECRET) {
    if (!body.turnstileToken) return json({ success: false, error: 'turnstile_required' }, 403);
    if (!(await verifyTurnstile(env, body.turnstileToken, ip))) {
      return json({ success: false, error: 'turnstile_failed' }, 403);
    }
  } else {
    console.warn('[org] TURNSTILE_SECRET not set — registration is NOT bot-protected');
  }

  const {
    organizationName,
    nedarimMosadId,
    nedarimApiValid,
    nedarimApiPassword,
    adminPhone,
    adminPassword,
    adminFirstName,
    adminLastName,
    adminEmail,
  } = body;

  if (!organizationName || !nedarimMosadId || !nedarimApiValid || !adminPhone || !adminPassword || !adminFirstName || !adminLastName) {
    return json({ success: false, error: 'missing_fields' }, 400);
  }

  const cleanOrgName = organizationName.trim();
  const cleanMosadId = nedarimMosadId.trim();
  const cleanApiValid = nedarimApiValid.trim();
  const cleanAdminPhone = adminPhone.replace(/\D/g, '');

  // Org ID derived from the name (letters, numbers, Hebrew; no spaces).
  const orgId = cleanOrgName
    .toLowerCase()
    .replace(/[^a-z0-9֐-׿\s]/g, '')
    .replace(/\s+/g, '');
  if (!orgId || orgId.length < 2) {
    return json({ success: false, error: 'invalid_org_name' }, 400);
  }

  const metadataPath = `organizations/${orgId}/metadata`;

  // Atomically claim the org id: only the caller that creates the metadata
  // node proceeds. Two concurrent registrations can no longer both pass a
  // read-then-write duplicate check.
  let orgExists = false;
  const claimed = await dbCompareAndSet(env, metadataPath, (cur: unknown) => {
    if (cur) {
      orgExists = true;
      return undefined; // abort — no write
    }
    orgExists = false;
    return {
      name: cleanOrgName,
      status: 'provisioning',
      created_at: new Date().toISOString(),
      created_by: 'public-registration',
    };
  });
  if (orgExists) return json({ success: false, error: 'org_already_exists' }, 409);
  if (!claimed) return json({ success: false, error: 'conflict' }, 409);

  const releaseOrg = async () => {
    try {
      await dbSet(env, `organizations/${orgId}`, null);
    } catch (e) {
      console.error('[org] CRITICAL: failed to remove claimed org after error', {
        orgId,
        error: (e as Error).message,
      });
    }
  };

  // 1. Create the admin Auth user (rolled back below if a later step fails).
  const adminFirebaseEmail = phoneToEmail(cleanAdminPhone);
  let adminUid: string;
  try {
    adminUid = await createAuthUser(env, adminFirebaseEmail, adminPassword, `${adminFirstName} ${adminLastName}`);
  } catch (e) {
    await releaseOrg();
    if (e instanceof EmailExistsError) return json({ success: false, error: 'phone_already_registered' }, 409);
    throw e;
  }

  try {
    // 2. Fill the org metadata. mosad_id/api_valid are base64-encoded, NOT
    // encrypted — the web admin and kiosk decode them locally (no key) and
    // they end up in the payment iframe anyway. The real secret (ApiPassword)
    // is GCM-encrypted below, in the server-only secrets/ path.
    await dbUpdate(env, metadataPath, {
      nedarim_mosad_id: encodeClientReadable(cleanMosadId),
      nedarim_api_valid: encodeClientReadable(cleanApiValid),
      status: 'active',
      admin_uid: adminUid,
      admin_phone: cleanAdminPhone,
      admin_email: adminEmail ? adminEmail.trim() : '',
    });

    // Server-side charge credential (saved-card). Stored OUTSIDE the
    // client-readable metadata, under a secrets/ path only the Worker (admin)
    // can access. Optional — only orgs that provide it can charge saved cards.
    if (nedarimApiPassword && nedarimApiPassword.trim()) {
      await dbSet(env, `organizations/${orgId}/secrets/nedarim_api_password`, await encryptData(env, nedarimApiPassword.trim()));
    }

    // 3. Admin user record.
    await dbSet(env, `organizations/${orgId}/users/${adminUid}`, {
      firstName: adminFirstName.trim(),
      lastName: adminLastName.trim(),
      phoneNumber: cleanAdminPhone,
      email: adminEmail ? adminEmail.trim() : '',
      remainingTime: 0,
      printBalance: 0,
      isSessionActive: false,
      isAdmin: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      createdBy: 'organization-registration',
    });
  } catch (e) {
    // No half-provisioned org, no orphaned Auth user.
    try {
      await deleteAuthUser(env, adminUid);
    } catch (e2) {
      console.error('[org] CRITICAL: rollback of auth user failed', {
        orgId,
        adminUid,
        error: (e2 as Error).message,
      });
    }
    await releaseOrg();
    throw e;
  }

  console.log('[org] registered', { orgId, adminUid });
  return json({ success: true, orgId, adminUid, message: 'organization_registered' });
}
