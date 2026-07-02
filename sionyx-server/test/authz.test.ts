/**
 * Authorization tests: usage deductions are self-only (a user can only reduce
 * their OWN balance) and /admin/adjust-balance requires an org-admin caller.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createExecutionContext } from 'cloudflare:test';
import worker from '../src/index';
import { testEnv, jsonRes, MockFetch, DB } from './helpers';

const BASE = 'https://sionyx-server.example';

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

async function post(path: string, body: unknown, withToken = true): Promise<Response> {
  const req = new Request(`${BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(withToken ? { Authorization: 'Bearer test-id-token' } : {}),
    },
    body: JSON.stringify(body),
  });
  return worker.fetch(req, await testEnv(), createExecutionContext());
}

/** Mock verifyIdToken: the Identity Toolkit lookup resolves the token to `uid`. */
function tokenResolvesTo(uid: string): void {
  mock.on('POST', 'https://identitytoolkit.googleapis.com/v1/accounts:lookup', () =>
    jsonRes({ users: [{ localId: uid }] }));
}

describe('usage deductions are self-only', () => {
  it('deducts time for the token owner', async () => {
    tokenResolvesTo('u1');
    mock.on('GET', `${DB}/organizations/org1/users/u1/remainingTime.json`, () => jsonRes(120, { ETag: 'e1' }));
    mock.on('PUT', `${DB}/organizations/org1/users/u1/remainingTime.json`, () => jsonRes(60));

    const res = await post('/usage/deduct-time', { orgId: 'org1', userId: 'u1', seconds: 60 });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, remainingTime: 60 });
  });

  it("rejects deducting another user's time", async () => {
    tokenResolvesTo('attacker');
    const res = await post('/usage/deduct-time', { orgId: 'org1', userId: 'u1', seconds: 60 });
    expect(res.status).toBe(401);
    expect(await res.json()).toMatchObject({ success: false, error: 'unauthorized' });
  });

  it("rejects deducting another user's print balance", async () => {
    tokenResolvesTo('attacker');
    const res = await post('/usage/deduct-print', { orgId: 'org1', userId: 'u1', amount: 1 });
    expect(res.status).toBe(401);
  });

  it('rejects a deduction without a bearer token', async () => {
    const res = await post('/usage/deduct-time', { orgId: 'org1', userId: 'u1', seconds: 60 }, false);
    expect(res.status).toBe(401);
  });
});

describe('/admin/adjust-balance requires an org admin', () => {
  it('rejects a non-admin caller', async () => {
    tokenResolvesTo('u2');
    mock.on('GET', `${DB}/organizations/org1/users/u2.json`, () => jsonRes({ role: 'user' }));

    const res = await post('/admin/adjust-balance', { orgId: 'org1', userId: 'u1', addSeconds: 9999 });
    expect(res.status).toBe(403);
    expect(await res.json()).toMatchObject({ success: false, error: 'not_admin' });
  });

  it('adjusts balances for an admin caller', async () => {
    tokenResolvesTo('boss');
    mock.on('GET', `${DB}/organizations/org1/users/boss.json`, () => jsonRes({ role: 'admin' }));
    mock.on('GET', `${DB}/organizations/org1/users/u1.json`, () => jsonRes({ role: 'user' }));
    mock.on('GET', `${DB}/organizations/org1/users/u1/remainingTime.json`, () => jsonRes(100, { ETag: 'e1' }));
    mock.on('PUT', `${DB}/organizations/org1/users/u1/remainingTime.json`, () => jsonRes(160));

    const res = await post('/admin/adjust-balance', { orgId: 'org1', userId: 'u1', addSeconds: 60 });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, remainingTime: 160 });
  });
});
