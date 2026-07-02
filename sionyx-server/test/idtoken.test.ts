/**
 * Local ID-token verification tests (M-1): RS256 against the (mocked) Google
 * securetoken JWKS, with strict iss/aud/exp checks — replacing the old
 * per-request Identity Toolkit lookup.
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { verifyIdToken } from '../src/firebase';
import { testEnv, makeIdToken, MockFetch } from './helpers';

const mock = new MockFetch();
beforeAll(() => mock.install());
afterAll(() => mock.uninstall());
beforeEach(() => mock.reset());
afterEach(() => mock.assertDone());

describe('verifyIdToken (local RS256)', () => {
  it('accepts a valid token and returns its claims', async () => {
    const token = await makeIdToken('user-1', { email: 'a@b.c' });
    const claims = await verifyIdToken(await testEnv(), token);
    expect(claims).toEqual({ user_id: 'user-1', email: 'a@b.c' });
  });

  it('rejects an expired token', async () => {
    const token = await makeIdToken('user-1', { exp: Math.floor(Date.now() / 1000) - 60 });
    expect(await verifyIdToken(await testEnv(), token)).toBeNull();
  });

  it('rejects a token for another Firebase project (aud)', async () => {
    const token = await makeIdToken('user-1', { aud: 'other-project' });
    expect(await verifyIdToken(await testEnv(), token)).toBeNull();
  });

  it('rejects a token from another issuer', async () => {
    const token = await makeIdToken('user-1', { iss: 'https://securetoken.google.com/other-project' });
    expect(await verifyIdToken(await testEnv(), token)).toBeNull();
  });

  it('rejects a tampered signature', async () => {
    const token = await makeIdToken('user-1');
    const [h, p, sig] = token.split('.');
    const flipped = (sig[0] === 'A' ? 'B' : 'A') + sig.slice(1);
    expect(await verifyIdToken(await testEnv(), `${h}.${p}.${flipped}`)).toBeNull();
  });

  it('rejects a token whose payload was swapped (signature no longer matches)', async () => {
    const token = await makeIdToken('user-1');
    const other = await makeIdToken('attacker');
    const [h] = token.split('.');
    const [, otherPayload] = other.split('.');
    const [, , sig] = token.split('.');
    expect(await verifyIdToken(await testEnv(), `${h}.${otherPayload}.${sig}`)).toBeNull();
  });

  it('rejects garbage tokens without throwing', async () => {
    expect(await verifyIdToken(await testEnv(), 'not-a-jwt')).toBeNull();
    expect(await verifyIdToken(await testEnv(), 'a.b.c')).toBeNull();
    expect(await verifyIdToken(await testEnv(), '')).toBeNull();
  });
});
