/**
 * Build YouTube "subscribe confirmation" links (?sub_confirmation=1).
 * Opening the link shows YouTube's own Subscribe popup; the viewer still confirms.
 */

const HANDLE_RE = /^@?([A-Za-z0-9._-]{3,30})$/;
const CHANNEL_ID_RE = /^(UC[A-Za-z0-9_-]{22})$/;

/**
 * @param {string} input channel URL, @handle or channel ID
 * @returns {{ ok: true, kind: string, id: string, channelUrl: string, subscribeUrl: string } | { ok: false, error: string }}
 */
export function buildSubscribeLink(input) {
  const raw = String(input || '').trim();
  if (!raw) return { ok: false, error: 'Paste your YouTube channel link, @handle or channel ID.' };

  let kind = null;
  let id = null;

  const idMatch = raw.match(CHANNEL_ID_RE);
  if (idMatch) {
    kind = 'channel';
    id = idMatch[1];
  } else if (/^@/.test(raw) || (HANDLE_RE.test(raw) && !raw.includes('.'))) {
    const m = raw.match(HANDLE_RE);
    if (m) { kind = 'handle'; id = m[1]; }
  } else {
    let url;
    try {
      url = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`);
    } catch {
      return { ok: false, error: "That doesn't look like a YouTube channel link." };
    }
    const host = url.hostname.replace(/^(www\.|m\.)/, '');
    if (host !== 'youtube.com') {
      return { ok: false, error: 'Please use a youtube.com channel link (video links do not work).' };
    }
    const parts = url.pathname.split('/').filter(Boolean);
    if (parts[0] && parts[0].startsWith('@')) {
      kind = 'handle'; id = decodeURIComponent(parts[0].slice(1));
    } else if (parts[0] === 'channel' && parts[1] && CHANNEL_ID_RE.test(parts[1])) {
      kind = 'channel'; id = parts[1];
    } else if ((parts[0] === 'c' || parts[0] === 'user') && parts[1]) {
      kind = parts[0]; id = decodeURIComponent(parts[1]);
    } else if (parts[0] === 'watch' || parts[0] === 'shorts' || url.searchParams.get('v')) {
      return { ok: false, error: 'This is a video link. Open the video, tap the channel name and copy the channel link instead.' };
    }
  }

  if (!kind || !id) return { ok: false, error: "We couldn't find a channel in that link. Try your @handle." };

  const base = {
    handle: `https://www.youtube.com/@${encodeURIComponent(id)}`,
    channel: `https://www.youtube.com/channel/${id}`,
    c: `https://www.youtube.com/c/${encodeURIComponent(id)}`,
    user: `https://www.youtube.com/user/${encodeURIComponent(id)}`,
  }[kind];

  return { ok: true, kind, id, channelUrl: base, subscribeUrl: `${base}?sub_confirmation=1` };
}

export function subscribeButtonHtml(subscribeUrl, label = 'Subscribe on YouTube') {
  const safe = String(subscribeUrl).replace(/"/g, '&quot;');
  return `<a href="${safe}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#FF0000;color:#fff;font:600 15px/1 system-ui,sans-serif;padding:12px 18px;border-radius:8px;text-decoration:none">&#9654; ${label}</a>`;
}
