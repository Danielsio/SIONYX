/**
 * Crediting regression tests (C-2 double-credit, H-1 amount bypass).
 *
 * The fetch mock throws on any un-mocked call, so a path that must not credit
 * is asserted simply by not mocking any PUT/PATCH — an attempted write turns
 * into a failed test.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { createExecutionContext } from 'cloudflare:test';
import worker from '../src/index';
import { testEnv, jsonRes, MockFetch, DB } from './helpers';

const CALLBACK_URL =
  'https://sionyx-server.example/payments/nedarim-callback?secret=test-callback-secret';
const PURCHASE = `${DB}/organizations/org1/purchases/p1.json`;
const CLAIM = `${DB}/organizations/org1/purchases/p1/creditedAt.json`;
const USER = `${DB}/organizations/org1/users/u1.json`;
const FANOUT = `${DB}/.json`;

const okFields = { Status: 'OK', TransactionId: 'tx-1', Param1: 'p1', Param2: 'org1', Amount: '100' };

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

function callback(fields: Record<string, string>, url = CALLBACK_URL): Request {
  return new Request(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(fields).toString(),
  });
}

async function run(req: Request): Promise<Response> {
  return worker.fetch(req, await testEnv(), createExecutionContext());
}

describe('nedarimCallback crediting', () => {
  it('credits a valid callback: claims creditedAt, fans out user credit + bookkeeping', async () => {
    mock.on('GET', PURCHASE, () =>
      jsonRes({ userId: 'u1', amount: 100, minutes: 60, printBudget: 10, status: 'pending' }));
    mock.on('GET', CLAIM, () => jsonRes(null, { ETag: 'etag-0' }));
    let claimBody = '';
    mock.on('PUT', CLAIM, (_req, body) => {
      claimBody = body;
      return jsonRes({});
    });
    mock.on('GET', USER, () => jsonRes({ remainingTime: 300, printBalance: 2 }));
    let fanoutBody = '';
    mock.on('PATCH', FANOUT, (_req, body) => {
      fanoutBody = body;
      return jsonRes({});
    });

    const res = await run(callback(okFields));
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, message: 'credited' });

    expect(JSON.parse(claimBody)).toMatch(/^\d{4}-\d{2}-\d{2}T/); // ISO timestamp claim
    const fanout = JSON.parse(fanoutBody);
    expect(fanout['organizations/org1/users/u1/remainingTime']).toBe(300 + 60 * 60);
    expect(fanout['organizations/org1/users/u1/printBalance']).toBe(12);
    expect(fanout['organizations/org1/purchases/p1/creditedUserId']).toBe('u1');
    expect(fanout['organizations/org1/purchases/p1/status']).toBe('completed');
    expect(fanout['organizations/org1/purchases/p1/callbackAmount']).toBe(100);
    // The fan-out must NOT overwrite the anti-tamper reference amount.
    expect(fanout['organizations/org1/purchases/p1/amount']).toBeUndefined();
  });

  it('no-ops a retried callback once the purchase is credited (gateway retries)', async () => {
    mock.on('GET', PURCHASE, () =>
      jsonRes({ userId: 'u1', amount: 100, creditedAt: '2026-07-02T00:00:00.000Z' }));
    const res = await run(callback(okFields));
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ success: true, message: 'already_credited' });
  });

  it('does not credit when a concurrent callback claimed between read and CAS', async () => {
    mock.on('GET', PURCHASE, () => jsonRes({ userId: 'u1', amount: 100, minutes: 60 }));
    mock.on('GET', CLAIM, () => jsonRes('2026-07-02T00:00:00.000Z', { ETag: 'etag-1' }));
    const res = await run(callback(okFields));
    expect(await res.json()).toMatchObject({ success: true, message: 'already_credited' });
  });

  it('does not credit when losing the CAS write race (412 → re-read shows credited)', async () => {
    mock.on('GET', PURCHASE, () => jsonRes({ userId: 'u1', amount: 100, minutes: 60 }));
    mock.on('GET', CLAIM, () => jsonRes(null, { ETag: 'etag-0' }));
    mock.on('PUT', CLAIM, () => jsonRes({}, {}, 412));
    mock.on('GET', CLAIM, () => jsonRes('2026-07-02T00:00:00.000Z', { ETag: 'etag-2' }));
    const res = await run(callback(okFields));
    expect(await res.json()).toMatchObject({ success: true, message: 'already_credited' });
  });

  it('rejects a callback amount that differs from the stored purchase amount', async () => {
    mock.on('GET', PURCHASE, () => jsonRes({ userId: 'u1', amount: 100 }));
    const res = await run(callback({ ...okFields, Amount: '50' }));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ success: false, error: 'amount_mismatch' });
  });

  it('rejects a zero or absent callback amount on success status (H-1)', async () => {
    for (const fields of [{ ...okFields, Amount: '0' }, (({ Amount, ...rest }) => rest)(okFields)]) {
      const res = await run(callback(fields as Record<string, string>));
      expect(res.status).toBe(400);
      expect(await res.json()).toMatchObject({ success: false, error: 'invalid_amount' });
    }
  });

  it('rejects when the stored purchase has no positive amount (H-1)', async () => {
    mock.on('GET', PURCHASE, () => jsonRes({ userId: 'u1' }));
    const res = await run(callback(okFields));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ success: false, error: 'amount_mismatch' });
  });

  it('records a failed payment without crediting and without touching amount', async () => {
    let recorded = '';
    mock.on('PATCH', PURCHASE, (_req, body) => {
      recorded = body;
      return jsonRes({});
    });
    const res = await run(callback({ ...okFields, Status: 'Error', Amount: '' }));
    expect(await res.json()).toMatchObject({ success: true, message: 'failure_recorded' });
    const body = JSON.parse(recorded);
    expect(body.status).toBe('failed');
    expect(body).not.toHaveProperty('amount');
    expect(body).not.toHaveProperty('callbackAmount');
  });

  it('releases the claim when the fan-out fails so a retry can credit', async () => {
    mock.on('GET', PURCHASE, () => jsonRes({ userId: 'u1', amount: 100, minutes: 60 }));
    mock.on('GET', CLAIM, () => jsonRes(null, { ETag: 'etag-0' }));
    mock.on('PUT', CLAIM, () => jsonRes({}));
    mock.on('GET', USER, () => jsonRes({ remainingTime: 0 }));
    mock.on('PATCH', FANOUT, () => jsonRes('boom', {}, 500));
    let released = '';
    mock.on('PUT', CLAIM, (_req, body) => {
      released = body;
      return jsonRes(null);
    });

    const res = await run(callback(okFields));
    expect(res.status).toBe(500);
    expect(released).toBe('null'); // creditedAt reset → a gateway retry credits
  });

  it('refuses a callback with a wrong secret', async () => {
    const res = await run(
      callback(okFields, 'https://sionyx-server.example/payments/nedarim-callback?secret=wrong'),
    );
    expect(res.status).toBe(403);
  });
});
