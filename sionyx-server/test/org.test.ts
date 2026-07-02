/**
 * Registration abuse-control tests (H-6): per-IP rate limit, Turnstile
 * enforcement, atomic org-id claim (TOCTOU), and rollback of the Auth user +
 * org claim when a later step fails.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createExecutionContext } from 'cloudflare:test';
import worker from '../src/index';
import type { Env } from '../src/firebase';
import { testEnv, jsonRes, MockFetch, DB } from './helpers';

const METADATA = `${DB}/organizations/testorg/metadata.json`;
const ORG_ROOT = `${DB}/organizations/testorg.json`;
const ADMIN_USER = `${DB}/organizations/testorg/users/admin-uid.json`;
const IDTK = 'https://identitytoolkit.googleapis.com';
const SITEVERIFY = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';

const fields = {
  organizationName: 'Test Org',
  nedarimMosadId: '123',
  nedarimApiValid: 'api-key',
  adminPhone: '050-1234567',
  adminPassword: 'pass123456',
  adminFirstName: 'A',
  adminLastName: 'B',
};

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

// Unique IP per request: wrangler.toml's REGISTER_RATE_LIMITER binding is
// simulated for real in these tests (5/min per key), so a shared IP would
// throttle later tests.
let ipCounter = 0;
const nextIp = () => `203.0.113.${++ipCounter}`;

async function register(
  body: Record<string, string>,
  envOverrides: Partial<Env> = {},
  ip = nextIp(),
): Promise<Response> {
  const req = new Request('https://sionyx-server.example/org/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'CF-Connecting-IP': ip },
    body: JSON.stringify(body),
  });
  return worker.fetch(req, await testEnv(envOverrides), createExecutionContext());
}

/** Mocks for a registration that reaches the very end successfully. */
function mockHappyPath(): void {
  mock.on('GET', METADATA, () => jsonRes(null, { ETag: 'e0' })); // claim CAS read
  mock.on('PUT', METADATA, () => jsonRes({})); // claim write
  mock.on('POST', `${IDTK}/v1/accounts:signUp`, () => jsonRes({ localId: 'admin-uid' }));
  mock.on('POST', `${IDTK}/v1/projects/test-project/accounts:update`, () => jsonRes({})); // displayName
  mock.on('PATCH', METADATA, () => jsonRes({})); // fill metadata
  mock.on('PUT', ADMIN_USER, () => jsonRes({})); // admin user record
}

describe('registerOrganization', () => {
  it('registers happy-path: claims the org id, creates the admin, fills metadata', async () => {
    mockHappyPath();
    const res = await register(fields);
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, orgId: 'testorg', adminUid: 'admin-uid' });
  });

  it('rejects a duplicate org without creating anything', async () => {
    mock.on('GET', METADATA, () => jsonRes({ name: 'Test Org' }, { ETag: 'e1' }));
    const res = await register(fields);
    expect(res.status).toBe(409);
    expect(await res.json()).toMatchObject({ success: false, error: 'org_already_exists' });
  });

  it('loses the claim race cleanly (TOCTOU: 412 → re-read shows the org exists)', async () => {
    mock.on('GET', METADATA, () => jsonRes(null, { ETag: 'e0' }));
    mock.on('PUT', METADATA, () => jsonRes({}, {}, 412));
    mock.on('GET', METADATA, () => jsonRes({ name: 'Test Org' }, { ETag: 'e2' }));
    const res = await register(fields);
    expect(res.status).toBe(409);
    expect(await res.json()).toMatchObject({ success: false, error: 'org_already_exists' });
  });

  it('releases the org claim when the phone is already registered', async () => {
    mock.on('GET', METADATA, () => jsonRes(null, { ETag: 'e0' }));
    mock.on('PUT', METADATA, () => jsonRes({}));
    mock.on('POST', `${IDTK}/v1/accounts:signUp`, () =>
      jsonRes({ error: { message: 'EMAIL_EXISTS' } }, {}, 400));
    let released = '';
    mock.on('PUT', ORG_ROOT, (_req, body) => {
      released = body;
      return jsonRes(null);
    });

    const res = await register(fields);
    expect(res.status).toBe(409);
    expect(await res.json()).toMatchObject({ success: false, error: 'phone_already_registered' });
    expect(released).toBe('null');
  });

  it('rolls back the Auth user AND the org claim when a later step fails', async () => {
    mock.on('GET', METADATA, () => jsonRes(null, { ETag: 'e0' }));
    mock.on('PUT', METADATA, () => jsonRes({}));
    mock.on('POST', `${IDTK}/v1/accounts:signUp`, () => jsonRes({ localId: 'admin-uid' }));
    mock.on('POST', `${IDTK}/v1/projects/test-project/accounts:update`, () => jsonRes({}));
    mock.on('PATCH', METADATA, () => jsonRes('boom', {}, 500)); // metadata fill fails
    let deletedUid = '';
    mock.on('POST', `${IDTK}/v1/projects/test-project/accounts:delete`, (_req, body) => {
      deletedUid = (JSON.parse(body) as { localId: string }).localId;
      return jsonRes({});
    });
    let released = '';
    mock.on('PUT', ORG_ROOT, (_req, body) => {
      released = body;
      return jsonRes(null);
    });

    const res = await register(fields);
    expect(res.status).toBe(500);
    expect(deletedUid).toBe('admin-uid');
    expect(released).toBe('null');
  });

  it('throttles by IP via the rate-limit binding', async () => {
    const res = await register(fields, {
      REGISTER_RATE_LIMITER: { limit: async () => ({ success: false }) },
    });
    expect(res.status).toBe(429);
    expect(await res.json()).toMatchObject({ success: false, error: 'rate_limited' });
  });

  it('requires a Turnstile token once TURNSTILE_SECRET is configured', async () => {
    const res = await register(fields, { TURNSTILE_SECRET: 'ts-secret' });
    expect(res.status).toBe(403);
    expect(await res.json()).toMatchObject({ success: false, error: 'turnstile_required' });
  });

  it('rejects a Turnstile token that fails siteverify', async () => {
    mock.on('POST', SITEVERIFY, () => jsonRes({ success: false }));
    const res = await register({ ...fields, turnstileToken: 'bad-token' }, { TURNSTILE_SECRET: 'ts-secret' });
    expect(res.status).toBe(403);
    expect(await res.json()).toMatchObject({ success: false, error: 'turnstile_failed' });
  });

  it('proceeds when siteverify passes', async () => {
    let verifyBody = '';
    mock.on('POST', SITEVERIFY, (_req, body) => {
      verifyBody = body;
      return jsonRes({ success: true });
    });
    mockHappyPath();
    const res = await register(
      { ...fields, turnstileToken: 'good-token' },
      { TURNSTILE_SECRET: 'ts-secret' },
      '198.51.100.42',
    );
    expect(res.status).toBe(200);
    const sent = JSON.parse(verifyBody);
    expect(sent.response).toBe('good-token');
    expect(sent.remoteip).toBe('198.51.100.42');
  });
});
