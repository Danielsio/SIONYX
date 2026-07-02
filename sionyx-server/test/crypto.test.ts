/**
 * Credential encryption tests (H-2): AES-GCM, fail-closed without a key,
 * tamper detection, and read-only fallbacks for values stored in the legacy
 * CBC / base64 formats.
 */
import { describe, it, expect } from 'vitest';
import { encryptData, decryptData, encodeClientReadable } from '../src/firebase';
import type { Env } from '../src/firebase';

const KEY = 'test-encryption-key-0123456789abcdef'; // 36 chars
const keyed = { ENCRYPTION_KEY: KEY } as Env;
const keyless = {} as Env;

describe('encryptData / decryptData (AES-GCM)', () => {
  it('round-trips a secret', async () => {
    const enc = await encryptData(keyed, 'nedarim-api-password-123');
    expect(enc.startsWith('v2:')).toBe(true);
    expect(enc).not.toContain('nedarim');
    expect(await decryptData(keyed, enc)).toBe('nedarim-api-password-123');
  });

  it('produces a different ciphertext per call (random IV)', async () => {
    const a = await encryptData(keyed, 'same');
    const b = await encryptData(keyed, 'same');
    expect(a).not.toBe(b);
  });

  it('fails closed when ENCRYPTION_KEY is missing', async () => {
    await expect(encryptData(keyless, 'secret')).rejects.toThrow(/ENCRYPTION_KEY/);
  });

  it('fails closed when ENCRYPTION_KEY is shorter than 32 chars', async () => {
    await expect(encryptData({ ENCRYPTION_KEY: 'short' } as Env, 'secret')).rejects.toThrow(/ENCRYPTION_KEY/);
  });

  it('rejects tampered ciphertext (authenticated encryption)', async () => {
    const enc = await encryptData(keyed, 'secret');
    const [prefix, iv, ct] = enc.split(':');
    const bytes = Uint8Array.from(atob(ct), (c) => c.charCodeAt(0));
    bytes[0] ^= 0xff;
    let bin = '';
    for (const b of bytes) bin += String.fromCharCode(b);
    const tampered = `${prefix}:${iv}:${btoa(bin)}`;
    await expect(decryptData(keyed, tampered)).rejects.toThrow();
  });

  it('rejects a v2 value when the key is wrong (no silent fallback)', async () => {
    const enc = await encryptData(keyed, 'secret');
    const otherKey = { ENCRYPTION_KEY: 'another-encryption-key-fedcba98765432' } as Env;
    await expect(decryptData(otherKey, enc)).rejects.toThrow();
  });
});

describe('legacy read fallbacks', () => {
  it('reads legacy base64(JSON) values (production data predates the key)', async () => {
    const legacy = btoa(JSON.stringify('12345'));
    expect(await decryptData(keyed, legacy)).toBe('12345');
    expect(await decryptData(keyless, legacy)).toBe('12345'); // even keyless
  });

  it('reads legacy AES-CBC values written by the old code', async () => {
    // Reproduce the old writer: iv(16) + AES-CBC with key = first 32 chars raw.
    const plaintext = new TextEncoder().encode(JSON.stringify('legacy-password'));
    const keyBytes = new TextEncoder().encode(KEY.slice(0, 32));
    const iv = crypto.getRandomValues(new Uint8Array(16));
    const key = await crypto.subtle.importKey('raw', keyBytes, { name: 'AES-CBC' }, false, ['encrypt']);
    const ct = await crypto.subtle.encrypt({ name: 'AES-CBC', iv }, key, plaintext);
    const b64 = (buf: ArrayBuffer | Uint8Array) => {
      const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
      let bin = '';
      for (const b of bytes) bin += String.fromCharCode(b);
      return btoa(bin);
    };
    const legacyCbc = `${b64(iv)}:${b64(ct)}`;

    expect(await decryptData(keyed, legacyCbc)).toBe('legacy-password');
  });
});

describe('encodeClientReadable', () => {
  it('matches the web/kiosk decoder: JSON.parse(atob(value))', () => {
    const encoded = encodeClientReadable('mosad-4567');
    expect(JSON.parse(atob(encoded))).toBe('mosad-4567');
  });
});
