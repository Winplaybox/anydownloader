/**
 * WinPlayBox Zero-Trust gateway client (browser, zero deps).
 * Every call: fetch a fresh single-use token bound to (scope, endpoint, exact body), then call once.
 *
 *   import { gateway } from './wpb-gateway-client.js';
 *   const res = await gateway.post('/api/v2/gravityclaw/generate', { requirement, target: 'auto' });
 *
 * Admin pages: gateway.setAdminKey(key)  (kept in sessionStorage only, never localStorage)
 */
const BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

const SCOPE_BY_PREFIX = [
  ['/api/v2/gravityclaw/', 'gravityclaw:generate'],
];

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}

export class GatewayError extends Error {
  constructor(status, code, message, requestId) {
    super(message); this.status = status; this.code = code; this.requestId = requestId;
  }
}

function adminHeaders() {
  try { const k = sessionStorage.getItem('wpb_admin_key'); return k ? { 'X-Admin-Key': k } : {}; }
  catch { return {}; }
}

async function parse(res) {
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON */ }
  if (!res.ok || (data && data.ok === false)) {
    const e = (data && data.error) || {};
    throw new GatewayError(res.status, e.code || 'HTTP' + res.status, e.message || res.statusText, data && data.request_id);
  }
  return data;
}

export const gateway = {
  base: BASE,
  setAdminKey(k) { try { k ? sessionStorage.setItem('wpb_admin_key', k) : sessionStorage.removeItem('wpb_admin_key'); } catch {} },

  async token(scope, aud, bodyText) {
    const body = { scope, aud };
    if (bodyText !== undefined) body.body_sha256 = await sha256Hex(bodyText);
    const res = await fetch(`${BASE}/api/v2/auth/token`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', ...adminHeaders() }, body: JSON.stringify(body),
    });
    return (await parse(res)).token;
  },

  async get(path) {
    return parse(await fetch(`${BASE}${path}`));
  },

  /** POST with a fresh single-use token. Retries once on 429 after the server hint. */
  async post(path, payload, { scope, signal } = {}) {
    const sc = scope || (SCOPE_BY_PREFIX.find(([p]) => path.startsWith(p)) || [])[1];
    if (!sc) throw new Error('No scope mapped for ' + path);
    const text = JSON.stringify(payload ?? {});
    const tok = await this.token(sc, path, text);
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
      body: text,                       // exact bytes that were hashed into the token
    });
    return parse(res);
  },
};
