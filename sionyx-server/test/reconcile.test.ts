/**
 * Read-only purchase reconcile: lets the kiosk confirm the authoritative credit
 * state after its own poll window closes (a late callback lands after the kiosk
 * gave up). It must NEVER credit — crediting stays the callback's job — and must
 * only report the Worker-written `creditedAt`, never act on client-settable
 * fields.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createExecutionContext } from 'cloudflare:test';
import worker from '../src/index';
import { testEnv, jsonRes, MockFetch, DB, makeIdToken } from './helpers';

const BASE = 'https://sionyx-server.example';
const USER = (uid: string) => `${DB}/organizations/org1/users/${uid}.json`;
const PURCHASE = (pid: string) => `${DB}/organizations/org1/purchases/${pid}.json`;

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

async function call(
  { uid, body, method = 'POST' }: { uid: string | null; body?: unknown; method?: string },
): Promise<Response> {
  const req = new Request(`${BASE}/payments/reconcile`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(uid ? { Authorization: `Bearer ${await makeIdToken(uid)}` } : {}),
    },
    ...(method === 'POST' ? { body: JSON.stringify(body ?? {}) } : {}),
  });
  return worker.fetch(req, await testEnv(), createExecutionContext());
}

describe('reconcile — reporting credit state', () => {
  it('reports credited=true once the Worker has set creditedAt (the late-callback case)', async () => {
    mock.on('GET', USER('u1'), () => jsonRes({ role: 'user' }));
    mock.on('GET', PURCHASE('p1'), () =>
      jsonRes({ userId: 'u1', amount: 50, status: 'completed', creditedAt: '2026-07-16T00:00:00Z' }),
    );

    const res = await call({ uid: 'u1', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, found: true, credited: true, status: 'completed' });
  });

  it('reports credited=false while the purchase is still pending', async () => {
    mock.on('GET', USER('u1'), () => jsonRes({ role: 'user' }));
    mock.on('GET', PURCHASE('p1'), () => jsonRes({ userId: 'u1', amount: 50, status: 'pending' }));

    const res = await call({ uid: 'u1', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(await res.json()).toMatchObject({ success: true, found: true, credited: false, status: 'pending' });
  });

  it('does NOT trust a client-forged status: a fake status=completed is still credited=false without creditedAt', async () => {
    mock.on('GET', USER('u1'), () => jsonRes({ role: 'user' }));
    // A malicious client created the purchase claiming completed + a huge amount,
    // but never got a real callback (no creditedAt). Reconcile must report the
    // truth: not credited.
    mock.on('GET', PURCHASE('p1'), () => jsonRes({ userId: 'u1', amount: 999999, status: 'completed' }));

    const res = await call({ uid: 'u1', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(await res.json()).toMatchObject({ found: true, credited: false });
  });

  it('reports found=false for an unknown purchase', async () => {
    mock.on('GET', USER('u1'), () => jsonRes({ role: 'user' }));
    mock.on('GET', PURCHASE('ghost'), () => jsonRes(null));

    const res = await call({ uid: 'u1', body: { orgId: 'org1', purchaseId: 'ghost' } });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, found: false, credited: false });
  });
});

describe('reconcile — access control', () => {
  it('lets an admin inspect any purchase in the org', async () => {
    mock.on('GET', USER('boss'), () => jsonRes({ role: 'admin' }));
    mock.on('GET', PURCHASE('p1'), () =>
      jsonRes({ userId: 'someoneElse', status: 'completed', creditedAt: '2026-07-16T00:00:00Z' }),
    );

    const res = await call({ uid: 'boss', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ credited: true });
  });

  it("forbids a member from inspecting another user's purchase", async () => {
    mock.on('GET', USER('u1'), () => jsonRes({ role: 'user' }));
    mock.on('GET', PURCHASE('p1'), () => jsonRes({ userId: 'u2', status: 'completed' }));

    const res = await call({ uid: 'u1', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(res.status).toBe(403);
  });

  it('refuses a caller who is not a member of the org', async () => {
    mock.on('GET', USER('outsider'), () => jsonRes(null));
    const res = await call({ uid: 'outsider', body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(res.status).toBe(403);
  });

  it('refuses an unauthenticated caller', async () => {
    const res = await call({ uid: null, body: { orgId: 'org1', purchaseId: 'p1' } });
    expect(res.status).toBe(401);
  });

  it('rejects a request missing fields', async () => {
    const res = await call({ uid: 'u1', body: { orgId: 'org1' } });
    expect(res.status).toBe(400);
  });
});
