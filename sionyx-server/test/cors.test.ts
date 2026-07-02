/**
 * CORS regression tests (C-1): the web admin on Firebase Hosting must be able
 * to preflight and call this Worker cross-origin, and only allowed origins
 * may be echoed in Access-Control-Allow-Origin.
 */
import { describe, it, expect } from 'vitest';
import { env, createExecutionContext, waitOnExecutionContext } from 'cloudflare:test';
import type { Env } from '../src/firebase';
import worker from '../src/index';

const WEB_ORIGIN = 'https://sionyx-19636.web.app';

async function run(req: Request, e: Env = env): Promise<Response> {
  const ctx = createExecutionContext();
  const res = await worker.fetch(req, e, ctx);
  await waitOnExecutionContext(ctx);
  return res;
}

function preflightRequest(origin: string, path = '/admin/adjust-balance'): Request {
  return new Request(`https://sionyx-server.example${path}`, {
    method: 'OPTIONS',
    headers: {
      Origin: origin,
      'Access-Control-Request-Method': 'POST',
      'Access-Control-Request-Headers': 'authorization,content-type',
    },
  });
}

describe('OPTIONS preflight', () => {
  it('answers with ACAO + allowed methods/headers for the web origin', async () => {
    const res = await run(preflightRequest(WEB_ORIGIN));
    expect(res.status).toBe(204);
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe(WEB_ORIGIN);
    expect(res.headers.get('Access-Control-Allow-Methods')).toContain('POST');
    const allowHeaders = res.headers.get('Access-Control-Allow-Headers') ?? '';
    expect(allowHeaders).toContain('authorization');
    expect(allowHeaders).toContain('content-type');
    expect(res.headers.get('Access-Control-Max-Age')).toBeTruthy();
    expect(res.headers.get('Vary')).toBe('Origin');
  });

  it('allows localhost dev origins on any port', async () => {
    for (const origin of ['http://localhost:5173', 'http://127.0.0.1:8080']) {
      const res = await run(preflightRequest(origin));
      expect(res.status).toBe(204);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe(origin);
    }
  });

  it('does not echo ACAO for an unknown origin', async () => {
    const res = await run(preflightRequest('https://evil.example.com'));
    expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
  });

  it('falls back to the live web origins when WEB_ORIGIN is unset', async () => {
    const res = await run(preflightRequest(WEB_ORIGIN), {} as Env);
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe(WEB_ORIGIN);
  });
});

describe('CORS on regular responses', () => {
  it('adds ACAO to a handled route (GET /health)', async () => {
    const res = await run(
      new Request('https://sionyx-server.example/health', { headers: { Origin: WEB_ORIGIN } })
    );
    expect(res.status).toBe(200);
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe(WEB_ORIGIN);
  });

  it('adds ACAO to error responses too (404)', async () => {
    const res = await run(
      new Request('https://sionyx-server.example/nope', { headers: { Origin: WEB_ORIGIN } })
    );
    expect(res.status).toBe(404);
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe(WEB_ORIGIN);
  });

  it('leaves server-to-server requests (no Origin header) working unchanged', async () => {
    const res = await run(new Request('https://sionyx-server.example/health'));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, service: 'sionyx-server' });
    expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
  });
});

describe('request IDs', () => {
  it('tags every response with a UUID x-request-id, including 404s', async () => {
    const ok = await run(new Request('https://sionyx-server.example/health'));
    const missing = await run(new Request('https://sionyx-server.example/nope'));
    const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
    expect(ok.headers.get('x-request-id')).toMatch(uuid);
    expect(missing.headers.get('x-request-id')).toMatch(uuid);
    expect(ok.headers.get('x-request-id')).not.toBe(missing.headers.get('x-request-id'));
  });
});
