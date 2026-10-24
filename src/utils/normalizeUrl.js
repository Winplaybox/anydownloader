import { ErrorCode } from './errors.js';

const SHORT_DOMAINS = new Set([
  't.co',
  'youtu.be',
  'fb.watch',
  'vm.tiktok.com',
  'vt.tiktok.com',
  'instagr.am',
  'pin.it',
  'redd.it'
]);

const STRIP_PARAMS = new Set([
  's', 't', 'igsh', 'igshid', 'fbclid', 'si', 'feature',
  'ref', 'source', 'ref_src', 'context', 'vertical'
]);

export function extractFirstUrl(text) {
  if (!text) return null;
  const match = text.match(/(https?:\/\/[^\s<>"']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s<>"']*)?)/);
  return match ? match[0].replace(/[.,;!?:)]+$/, '') : null;
}

export function normalizeUrl(rawInput, allowGeneric = true) {
  if (!rawInput || !rawInput.trim()) {
    return { ok: false, code: ErrorCode.URL_MISSING, error: 'Paste a link to get started.' };
  }

  const cleanedText = rawInput.trim();
  const allUrls = cleanedText.match(/https?:\/\/[^\s<>"']+/g) || [];
  const multipleFound = allUrls.length > 1;

  const extracted = extractFirstUrl(cleanedText);
  if (!extracted) {
    return { ok: false, code: ErrorCode.URL_INVALID, error: "That doesn't look like a valid link." };
  }

  let target = extracted;
  if (!target.startsWith('http://') && !target.startsWith('https://')) {
    target = 'https://' + target;
  }

  let parsed;
  try {
    parsed = new URL(target);
  } catch (e) {
    return { ok: false, code: ErrorCode.URL_INVALID, error: "That doesn't look like a valid link." };
  }

  let host = (parsed.hostname || '').toLowerCase();
  let path = parsed.pathname || '/';

  if (!host || !host.includes('.')) {
    return { ok: false, code: ErrorCode.URL_INVALID, error: "That doesn't look like a valid link." };
  }

  let platform = 'generic';

  // Twitter / X
  if (['twitter.com', 'mobile.twitter.com', 'www.twitter.com', 'fxtwitter.com', 'vxtwitter.com', 'fixupx.com', 'x.com'].includes(host)) {
    platform = 'twitter';
    host = 'x.com';
    const statusMatch = path.match(/\/(?:i\/web\/status|i\/status|[\w-]+\/status)\/(\d+)/);
    if (statusMatch) {
      path = `/i/status/${statusMatch[1]}`;
    }
  }
  // YouTube
  else if (['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'].includes(host)) {
    platform = 'youtube';
    host = 'www.youtube.com';
    if (parsed.hostname === 'youtu.be') {
      const vidId = path.replace(/^\//, '').split('/')[0];
      path = '/watch';
      parsed.searchParams.set('v', vidId);
    }
  }
  // Facebook
  else if (['facebook.com', 'www.facebook.com', 'm.facebook.com', 'fb.watch', 'web.facebook.com'].includes(host)) {
    platform = 'facebook';
    host = 'www.facebook.com';
  }
  // Instagram
  else if (['instagram.com', 'www.instagram.com', 'instagr.am'].includes(host)) {
    platform = 'instagram';
    host = 'www.instagram.com';
  }
  // TikTok
  else if (['tiktok.com', 'www.tiktok.com', 'm.tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'].includes(host)) {
    platform = 'tiktok';
    host = 'www.tiktok.com';
  }
  // Pinterest
  else if (['pinterest.com', 'www.pinterest.com', 'pin.it'].some(d => host.includes(d))) {
    platform = 'pinterest';
  }
  // Reddit
  else if (['reddit.com', 'www.reddit.com', 'redd.it'].some(d => host.includes(d))) {
    platform = 'reddit';
  }
  // Threads
  else if (['threads.net', 'www.threads.net'].some(d => host.includes(d))) {
    platform = 'threads';
  }
  // Vimeo
  else if (['vimeo.com', 'www.vimeo.com'].some(d => host.includes(d))) {
    platform = 'vimeo';
  }
  else if (!allowGeneric) {
    return {
      ok: false,
      code: ErrorCode.PLATFORM_UNSUPPORTED,
      error: "This site isn't supported yet. Supported: X, YouTube, Facebook, Instagram, TikTok, Pinterest, Reddit, Vimeo."
    };
  }

  // Strip tracking query params
  const cleanParams = new URLSearchParams();
  for (const [key, value] of parsed.searchParams.entries()) {
    const kLower = key.toLowerCase();
    if (STRIP_PARAMS.has(kLower) || kLower.startsWith('utm_')) {
      continue;
    }
    cleanParams.append(key, value);
  }

  const queryStr = cleanParams.toString();
  const cleanPath = (path.endsWith('/') && path.length > 1) ? path.slice(0, -1) : path;
  const canonicalUrl = `https://${host}${cleanPath}${queryStr ? '?' + queryStr : ''}`;

  return {
    ok: true,
    url: canonicalUrl,
    platform,
    raw: rawInput,
    multipleFound
  };
}
