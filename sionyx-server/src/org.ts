/**
 * Organization registration — ports `registerOrganization`.
 *
 * Public endpoint (matches the original "public-registration" flow): creates the
 * org metadata (with Nedarim creds encrypted the same way the kiosk decodes),
 * provisions the first admin Firebase Auth user, and writes the admin user record.
 *
 * NOTE: like the original this is unauthenticated; add a captcha / rate-limit
 * before exposing it widely (tracked as a follow-up).
 */
import {
  Env,
  dbGet,
  dbSet,
  encodeClientReadable,
  encryptData,
  createAuthUser,
  phoneToEmail,
  EmailExistsError,
} from './firebase';

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });

export async function registerOrganization(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => null)) as Record<string, string> | null;
  if (!body) return json({ success: false, error: 'invalid_body' }, 400);

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

  // Duplicate check.
  const existing = await dbGet(env, `organizations/${orgId}/metadata`);
  if (existing) return json({ success: false, error: 'org_already_exists' }, 409);

  // 1. Create the admin Auth user.
  const adminFirebaseEmail = phoneToEmail(cleanAdminPhone);
  let adminUid: string;
  try {
    adminUid = await createAuthUser(env, adminFirebaseEmail, adminPassword, `${adminFirstName} ${adminLastName}`);
  } catch (e) {
    if (e instanceof EmailExistsError) return json({ success: false, error: 'phone_already_registered' }, 409);
    throw e;
  }

  // 2. Org metadata. mosad_id/api_valid are base64-encoded, NOT encrypted —
  // the web admin and kiosk decode them locally (no key) and they end up in
  // the payment iframe anyway. The real secret (ApiPassword) is GCM-encrypted
  // below, in the server-only secrets/ path.
  const metadata: Record<string, unknown> = {
    name: cleanOrgName,
    nedarim_mosad_id: encodeClientReadable(cleanMosadId),
    nedarim_api_valid: encodeClientReadable(cleanApiValid),
    created_at: new Date().toISOString(),
    status: 'active',
    created_by: 'public-registration',
    admin_uid: adminUid,
    admin_phone: cleanAdminPhone,
    admin_email: adminEmail ? adminEmail.trim() : '',
  };
  await dbSet(env, `organizations/${orgId}/metadata`, metadata);

  // Server-side charge credential (saved-card). Stored OUTSIDE the client-readable
  // metadata, under a secrets/ path only the Worker (admin) can access. Optional —
  // only orgs that provide it can charge saved cards.
  if (nedarimApiPassword && nedarimApiPassword.trim()) {
    await dbSet(
      env,
      `organizations/${orgId}/secrets/nedarim_api_password`,
      await encryptData(env, nedarimApiPassword.trim()),
    );
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

  console.log('[org] registered', { orgId, adminUid });
  return json({ success: true, orgId, adminUid, message: 'organization_registered' });
}
