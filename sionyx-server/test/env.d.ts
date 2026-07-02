import { Env } from '../src/firebase';

declare module 'cloudflare:test' {
  // The `env` provided to tests carries the vars from wrangler.toml.
  interface ProvidedEnv extends Env {}
}
