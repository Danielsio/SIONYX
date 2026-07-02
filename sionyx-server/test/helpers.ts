/**
 * Shared test scaffolding.
 *
 * Outbound HTTP (Google OAuth, RTDB REST, Identity Toolkit) is stubbed via a
 * tiny FIFO fetch mock (`MockFetch`) — `@cloudflare/vitest-pool-workers` 0.17
 * dropped the `fetchMock` export, and since tests import the worker module
 * directly, stubbing the isolate's global `fetch` intercepts every outbound
 * call. Any un-mocked call throws, so "this path must not write" is asserted
 * simply by not mocking a write.
 *
 * The service account carries a real throwaway RSA key because
 * `getAccessToken` signs a JWT with WebCrypto before hitting the (mocked)
 * token endpoint.
 */
import { vi } from 'vitest';
import { env } from 'cloudflare:test';
import type { Env } from '../src/firebase';

/** Mock RTDB origin — keeps tests off the real database no matter what. */
export const DB = 'https://test-rtdb.example';

export const jsonRes = (body: unknown, headers: Record<string, string> = {}, status = 200): Response =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...headers } });

type Reply = (req: Request, body: string) => Response | Promise<Response>;

interface Route {
  method: string;
  origin: string;
  pathname: string;
  reply: Reply;
  persist: boolean;
  used: boolean;
}

export class MockFetch {
  private routes: Route[] = [];
  private unmatched: string[] = [];

  install(): void {
    vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const req = new Request(input, init);
      const url = new URL(req.url);
      const body = req.body ? await req.text() : '';
      // FIFO: first unused route matching method + origin + pathname (query ignored).
      const route = this.routes.find(
        (r) => !r.used && r.method === req.method && r.origin === url.origin && r.pathname === url.pathname,
      );
      if (!route) {
        this.unmatched.push(`${req.method} ${req.url}`);
        throw new Error(`Unmocked fetch: ${req.method} ${req.url}`);
      }
      if (!route.persist) route.used = true;
      return route.reply(req, body);
    });
  }

  uninstall(): void {
    vi.unstubAllGlobals();
  }

  /** Register a mock. Same-URL mocks are consumed in registration order. */
  on(method: string, urlStr: string, reply: Reply, opts: { persist?: boolean } = {}): void {
    const url = new URL(urlStr);
    this.routes.push({
      method,
      origin: url.origin,
      pathname: url.pathname,
      reply,
      persist: opts.persist ?? false,
      used: false,
    });
  }

  reset(): void {
    this.routes = [];
    this.unmatched = [];
    // OAuth token mint — the token is cached per isolate, so keep this
    // persistently available in every test.
    this.on('POST', 'https://oauth2.googleapis.com/token', () => jsonRes({ access_token: 'test-token', expires_in: 3600 }), {
      persist: true,
    });
  }

  /** Fail if any expected mock went unused or any un-mocked call happened. */
  assertDone(): void {
    if (this.unmatched.length) {
      throw new Error(`Un-mocked fetch calls:\n  ${this.unmatched.join('\n  ')}`);
    }
    const pending = this.routes.filter((r) => !r.persist && !r.used);
    if (pending.length) {
      throw new Error(
        `Expected fetches never happened:\n  ${pending.map((r) => `${r.method} ${r.origin}${r.pathname}`).join('\n  ')}`,
      );
    }
  }
}

let saJson: string | null = null;

export async function testEnv(overrides: Partial<Env> = {}): Promise<Env> {
  if (!saJson) {
    const kp = await crypto.subtle.generateKey(
      { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
      true,
      ['sign', 'verify'],
    );
    const pkcs8 = new Uint8Array(await crypto.subtle.exportKey('pkcs8', kp.privateKey));
    let bin = '';
    for (let i = 0; i < pkcs8.length; i++) bin += String.fromCharCode(pkcs8[i]);
    const pem = `-----BEGIN PRIVATE KEY-----\n${btoa(bin).match(/.{1,64}/g)!.join('\n')}\n-----END PRIVATE KEY-----\n`;
    saJson = JSON.stringify({
      client_email: 'test@test-project.iam.gserviceaccount.com',
      private_key: pem,
      project_id: 'test-project',
    });
  }
  return {
    ...env,
    FIREBASE_SERVICE_ACCOUNT: saJson,
    FIREBASE_DATABASE_URL: DB,
    CALLBACK_SECRET: 'test-callback-secret',
    ADMIN_SECRET: 'test-admin-secret',
    ...overrides,
  } as Env;
}
