// Wakes the Render free-tier backend only while a real user is on the site.
// - One ping on page load, so the ~30-60s cold start overlaps with the user browsing.
// - Re-ping every 10 min, but only if the tab is visible AND the user interacted
//   in the last 15 min. When nobody is active, pings stop and Render sleeps normally.
import { BACKEND_BASE } from './resolveMedia.js';

const PING_INTERVAL_MS = 10 * 60 * 1000;
const ACTIVE_WINDOW_MS = 15 * 60 * 1000;

let started = false;
let lastActivity = Date.now();
let lastPing = 0;

function ping() {
  lastPing = Date.now();
  fetch(`${BACKEND_BASE}/health`, { method: 'GET', cache: 'no-store', keepalive: true }).catch(() => {});
}

function maybePing() {
  if (document.visibilityState !== 'visible') return;
  if (Date.now() - lastActivity > ACTIVE_WINDOW_MS) return;
  if (Date.now() - lastPing < PING_INTERVAL_MS) return;
  ping();
}

export function startBackendWarmup() {
  if (started || typeof window === 'undefined') return;
  started = true;

  ping();

  const markActive = () => {
    lastActivity = Date.now();
  };
  ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach((evt) =>
    window.addEventListener(evt, markActive, { passive: true })
  );

  // Returning to the tab after a while: wake the backend immediately.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      markActive();
      maybePing();
    }
  });

  setInterval(maybePing, 60 * 1000);
}
