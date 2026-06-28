/**
 * Privileged Firebase access for Cloudflare Workers (no firebase-admin SDK).
 *
 * We mint a Google OAuth2 access token from the Firebase service account
 * (RS256 JWT signed with WebCrypto), then call the Realtime Database REST API
 * and the Identity Toolkit Admin REST API with that token. The token grants
 * admin access, so these helpers bypass Security Rules — they are the ONLY
 * place balances/purchases/passwords are mutated (server-authoritative).
 */

export interface ServiceAccount {
  client_email: string;
  private_key: string;
  project_id: string;
}

export interface Env {
  // JSON string of the Firebase service account (set via `wrangler secret put`)
  FIREBASE_SERVICE_ACCOUNT: string;
  // e.g. https://<project>-default-rtdb.firebaseio.com  (no trailing slash)
  FIREBASE_DATABASE_URL: string;
  // Public web API key (used for some Identity Toolkit calls)
  FIREBASE_API_KEY: string;
  // Shared secret guarding admin-only endpoints (set via secret)
  ADMIN_SECRET: string;
  // Secret embedded in the Nedarim callback URL (?secret=...) — authenticates the gateway callback
  CALLBACK_SECRET?: string;
  // Nedarim Plus gateway server credentials (set via secret)
  NEDARIM_MOSAD_ID?: string;
  NEDARIM_API_PASSWORD?: string;
  // Optional AES key for org credential encryption (>=32 chars). Must match the
  // value the kiosk/legacy functions used, or stored creds won't decode.
  ENCRYPTION_KEY?: string;
}

/** Raised when an Auth user already exists (so callers can map it to a 409). */
export class EmailExistsError extends Error {}

// Cached access token per isolate (tokens last ~1h; refresh a little early).
let cachedToken: { token: string; expMs: number } | null = null;

function b64urlFromString(s: string): string {
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlFromBytes(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function pemToArrayBuffer(pem: string): ArrayBuffer {
  const body = pem
    .replace(/-----BEGIN PRIVATE KEY-----/, '')
    .replace(/-----END PRIVATE KEY-----/, '')
    .replace(/\s+/g, '');
  const bin = atob(body);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

function parseServiceAccount(env: Env): ServiceAccount {
  const sa = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT) as ServiceAccount;
  // Private keys stored in env vars usually have literal "\n"; normalize.
  sa.private_key = sa.private_key.replace(/\\n/g, '\n');
  return sa;
}

const SCOPES = [
  'https://www.googleapis.com/auth/firebase.database',
  'https://www.googleapis.com/auth/identitytoolkit',
  'https://www.googleapis.com/auth/userinfo.email',
].join(' ');

/** Mint (and cache) a Google OAuth2 access token for the service account. */
export async function getAccessToken(env: Env): Promise<string> {
  if (cachedToken && cachedToken.expMs - Date.now() > 60_000) {
    return cachedToken.token;
  }
  const sa = parseServiceAccount(env);
  const now = Math.floor(Date.now() / 1000);
  const header = b64urlFromString(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = b64urlFromString(
    JSON.stringify({
      iss: sa.client_email,
      scope: SCOPES,
      aud: 'https://oauth2.googleapis.com/token',
      iat: now,
      exp: now + 3600,
    }),
  );
  const signingInput = `${header}.${claim}`;

  const key = await crypto.subtle.importKey(
    'pkcs8',
    pemToArrayBuffer(sa.private_key),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sig = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    key,
    new TextEncoder().encode(signingInput),
  );
  const jwt = `${signingInput}.${b64urlFromBytes(sig)}`;

  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }),
  });
  if (!res.ok) {
    throw new Error(`OAuth token exchange failed: ${res.status} ${await res.text()}`);
  }
  const json = (await res.json()) as { access_token: string; expires_in: number };
  cachedToken = { token: json.access_token, expMs: Date.now() + json.expires_in * 1000 };
  return json.access_token;
}

// ---------- Realtime Database REST (admin, bypasses rules) ----------

async function dbFetch(env: Env, path: string, init?: RequestInit): Promise<Response> {
  const token = await getAccessToken(env);
  const url = `${env.FIREBASE_DATABASE_URL}/${path}.json`;
  return fetch(url, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
}

export async function dbGet<T = unknown>(env: Env, path: string): Promise<T | null> {
  const res = await dbFetch(env, path);
  if (!res.ok) throw new Error(`dbGet ${path}: ${res.status}`);
  return (await res.json()) as T | null;
}

export async function dbSet(env: Env, path: string, data: unknown): Promise<void> {
  const res = await dbFetch(env, path, { method: 'PUT', body: JSON.stringify(data) });
  if (!res.ok) throw new Error(`dbSet ${path}: ${res.status} ${await res.text()}`);
}

export async function dbUpdate(env: Env, path: string, data: Record<string, unknown>): Promise<void> {
  const res = await dbFetch(env, path, { method: 'PATCH', body: JSON.stringify(data) });
  if (!res.ok) throw new Error(`dbUpdate ${path}: ${res.status} ${await res.text()}`);
}

/** Atomic-ish transactional update via ETag (compare-and-set). Returns true on success. */
export async function dbCompareAndSet(
  env: Env,
  path: string,
  mutate: (current: any) => any,
  retries = 3,
): Promise<boolean> {
  const token = await getAccessToken(env);
  const url = `${env.FIREBASE_DATABASE_URL}/${path}.json`;
  for (let attempt = 0; attempt < retries; attempt++) {
    const getRes = await fetch(url, {
      headers: { Authorization: `Bearer ${token}`, 'X-Firebase-ETag': 'true' },
    });
    const etag = getRes.headers.get('ETag') || 'null_etag';
    const current = await getRes.json();
    const next = mutate(current);
    const putRes = await fetch(url, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'if-match': etag,
      },
      body: JSON.stringify(next),
    });
    if (putRes.ok) return true;
    if (putRes.status !== 412) throw new Error(`dbCompareAndSet ${path}: ${putRes.status}`);
    // 412 = ETag mismatch -> retry
  }
  return false;
}

// ---------- Identity Toolkit Admin REST (manage Auth users) ----------

export async function setUserPasswordByEmail(env: Env, email: string, password: string): Promise<void> {
  const sa = parseServiceAccount(env);
  const token = await getAccessToken(env);
  // Look up the user to get localId.
  const lookup = await fetch(
    `https://identitytoolkit.googleapis.com/v1/projects/${sa.project_id}/accounts:lookup`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: [email] }),
    },
  );
  const data = (await lookup.json()) as { users?: Array<{ localId: string }> };
  const localId = data.users?.[0]?.localId;
  if (!localId) throw new Error(`No auth user for ${email}`);
  const upd = await fetch(
    `https://identitytoolkit.googleapis.com/v1/projects/${sa.project_id}/accounts:update`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ localId, password }),
    },
  );
  if (!upd.ok) throw new Error(`setUserPassword: ${upd.status} ${await upd.text()}`);
}

export async function setUserPasswordByUid(env: Env, localId: string, password: string): Promise<void> {
  const sa = parseServiceAccount(env);
  const token = await getAccessToken(env);
  const upd = await fetch(
    `https://identitytoolkit.googleapis.com/v1/projects/${sa.project_id}/accounts:update`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ localId, password }),
    },
  );
  if (!upd.ok) throw new Error(`setUserPasswordByUid: ${upd.status} ${await upd.text()}`);
}

export async function deleteAuthUser(env: Env, localId: string): Promise<void> {
  const sa = parseServiceAccount(env);
  const token = await getAccessToken(env);
  const res = await fetch(
    `https://identitytoolkit.googleapis.com/v1/projects/${sa.project_id}/accounts:delete`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ localId }),
    },
  );
  if (!res.ok) throw new Error(`deleteAuthUser: ${res.status} ${await res.text()}`);
}

/** Verify a Firebase ID token (from a client) and return its claims. */
export async function verifyIdToken(env: Env, idToken: string): Promise<{ user_id: string; email?: string } | null> {
  const res = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${env.FIREBASE_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken }),
    },
  );
  if (!res.ok) return null;
  const data = (await res.json()) as { users?: Array<{ localId: string; email?: string }> };
  const u = data.users?.[0];
  return u ? { user_id: u.localId, email: u.email } : null;
}

// ---------- Org-registration helpers ----------

function b64Std(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

export const phoneToEmail = (phone: string): string => `${phone.replace(/\D/g, '')}@sionyx.app`;

/** Mirror of the Cloud Functions encryptData: AES-256-CBC ("iv:ct" base64) or base64 fallback. */
export async function encryptData(env: Env, data: unknown): Promise<string> {
  const plaintext = new TextEncoder().encode(JSON.stringify(data));
  const k = env.ENCRYPTION_KEY;
  if (k && k.length >= 32) {
    const keyBytes = new TextEncoder().encode(k.slice(0, 32));
    const iv = crypto.getRandomValues(new Uint8Array(16));
    const key = await crypto.subtle.importKey('raw', keyBytes, { name: 'AES-CBC' }, false, ['encrypt']);
    const ct = await crypto.subtle.encrypt({ name: 'AES-CBC', iv }, key, plaintext);
    return `${b64Std(iv)}:${b64Std(ct)}`;
  }
  return b64Std(plaintext);
}

/** Create a Firebase Auth user (email/password). Returns the new uid. Throws EmailExistsError if taken. */
export async function createAuthUser(env: Env, email: string, password: string, displayName?: string): Promise<string> {
  const res = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${env.FIREBASE_API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, returnSecureToken: false }),
  });
  const data = (await res.json()) as { localId?: string; error?: { message?: string } };
  if (!res.ok) {
    if ((data.error?.message || '').includes('EMAIL_EXISTS')) throw new EmailExistsError('email_exists');
    throw new Error(`createAuthUser: ${data.error?.message || res.status}`);
  }
  const localId = data.localId!;
  if (displayName) {
    const sa = parseServiceAccount(env);
    const token = await getAccessToken(env);
    await fetch(`https://identitytoolkit.googleapis.com/v1/projects/${sa.project_id}/accounts:update`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ localId, displayName }),
    }).catch(() => {});
  }
  return localId;
}
