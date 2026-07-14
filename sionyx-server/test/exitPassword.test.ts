/**
 * Kiosk exit password: stored server-side only (encrypted), never returned,
 * admin-gated to set, rate-limited to verify.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createExecutionContext } from 'cloudflare:test';
import worker from '../src/index';
import { encryptData } from '../src/firebase';
import type { Env } from '../src/firebase';
import { testEnv, jsonRes, MockFetch, DB, makeIdToken } from './helpers';

const BASE = 'https://sionyx-server.example';
const SECRET = `${DB}/organizations/org1/secrets/admin_exit_password.json`;

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

// Unique IP per call: the vitest pool simulates the rate-limit binding for real.
let ip = 0;
const nextIp = () => `198.51.100.${++ip}`;

async function call(
  path: string,
  { uid, body, method = 'POST' }: { uid: string | null; body?: unknown; method?: string }
): Promise<Response> {
  const req = new Request(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'CF-Connecting-IP': nextIp(),
      ...(uid ? { Authorization: `Bearer ${await makeIdToken(uid)}` } : {}),
    },
    ...(method === 'POST' ? { body: JSON.stringify(body ?? {}) } : {}),
  });
  return worker.fetch(req, await testEnv(), createExecutionContext());
}

const asAdmin = () =>
  mock.on('GET', `${DB}/organizations/org1/users/boss.json`, () => jsonRes({ role: 'admin' }));
const asUser = () =>
  mock.on('GET', `${DB}/organizations/org1/users/u1.json`, () => jsonRes({ role: 'user' }));

describe('setting the exit password', () => {
  it('stores it ENCRYPTED — never as readable plaintext (the fork bug)', async () => {
    asAdmin();
    let written = '';
    mock.on('PUT', SECRET, (_req, b) => {
      written = b;
      return jsonRes({});
    });

    const res = await call('/admin/set-exit-password', {
      uid: 'boss',
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(res.status).toBe(200);

    // The stored value must be v2: AES-GCM, and must not contain the password.
    expect(written).toContain('v2:');
    expect(written).not.toContain('letmeout42');
  });

  it('refuses a non-admin caller', async () => {
    asUser();
    const res = await call('/admin/set-exit-password', {
      uid: 'u1',
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(res.status).toBe(403);
  });

  it('refuses an unauthenticated caller', async () => {
    const res = await call('/admin/set-exit-password', {
      uid: null,
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(res.status).toBe(401);
  });

  it('rejects a too-short password', async () => {
    asAdmin();
    const res = await call('/admin/set-exit-password', {
      uid: 'boss',
      body: { orgId: 'org1', password: '12' },
    });
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ error: 'password_too_short' });
  });

  it('an empty password clears the remote override', async () => {
    asAdmin();
    let written = 'unset';
    mock.on('PUT', SECRET, (_req, b) => {
      written = b;
      return jsonRes({});
    });

    const res = await call('/admin/set-exit-password', {
      uid: 'boss',
      body: { orgId: 'org1', password: '' },
    });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ cleared: true });
    expect(written).toBe('null');
  });
});

describe('verifying the exit password', () => {
  const storeEncrypted = async (password: string) => {
    const enc = await encryptData((await testEnv()) as Env, password);
    mock.on('GET', SECRET, () => jsonRes(enc));
  };

  it('accepts the correct password', async () => {
    asUser();
    await storeEncrypted('letmeout42');
    const res = await call('/auth/verify-exit-password', {
      uid: 'u1',
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(await res.json()).toMatchObject({ success: true, valid: true, configured: true });
  });

  it('rejects a wrong password without leaking the real one', async () => {
    asUser();
    await storeEncrypted('letmeout42');
    const res = await call('/auth/verify-exit-password', {
      uid: 'u1',
      body: { orgId: 'org1', password: 'wrong' },
    });
    const payload = await res.json();
    expect(payload).toMatchObject({ success: true, valid: false });
    expect(JSON.stringify(payload)).not.toContain('letmeout42');
  });

  it('reports not-configured when no remote password is set (kiosk falls back locally)', async () => {
    asUser();
    mock.on('GET', SECRET, () => jsonRes(null));
    const res = await call('/auth/verify-exit-password', {
      uid: 'u1',
      body: { orgId: 'org1', password: 'anything' },
    });
    expect(await res.json()).toMatchObject({ valid: false, configured: false });
  });

  it('refuses a caller who is not a member of that org', async () => {
    mock.on('GET', `${DB}/organizations/org1/users/outsider.json`, () => jsonRes(null));
    const res = await call('/auth/verify-exit-password', {
      uid: 'outsider',
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(res.status).toBe(403);
  });

  it('refuses an unauthenticated caller', async () => {
    const res = await call('/auth/verify-exit-password', {
      uid: null,
      body: { orgId: 'org1', password: 'letmeout42' },
    });
    expect(res.status).toBe(401);
  });
});

describe('exit-password status', () => {
  it('tells an admin whether one is configured, without revealing it', async () => {
    asAdmin();
    const enc = await encryptData((await testEnv()) as Env, 'letmeout42');
    mock.on('GET', SECRET, () => jsonRes(enc));

    const req = new Request(`${BASE}/admin/exit-password-status?orgId=org1`, {
      headers: { Authorization: `Bearer ${await makeIdToken('boss')}` },
    });
    const res = await worker.fetch(req, await testEnv(), createExecutionContext());
    const payload = await res.json();
    expect(payload).toMatchObject({ success: true, configured: true });
    expect(JSON.stringify(payload)).not.toContain('letmeout42');
  });

  it('refuses a non-admin', async () => {
    asUser();
    const req = new Request(`${BASE}/admin/exit-password-status?orgId=org1`, {
      headers: { Authorization: `Bearer ${await makeIdToken('u1')}` },
    });
    const res = await worker.fetch(req, await testEnv(), createExecutionContext());
    expect(res.status).toBe(403);
  });
});
