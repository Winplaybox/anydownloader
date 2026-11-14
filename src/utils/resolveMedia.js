import { normalizeUrl } from './normalizeUrl.js';
import { ErrorCode, getErrorMessage } from './errors.js';
import { getAttributionHeaders, getAttribution } from './attribution.js';

export const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

/**
 * Normalizes legacy /api/extract response into standard ResolveResult contract
 */
function normalizeLegacyExtract(raw, sourceUrl, platform) {
  const title = raw.title || 'Extracted Media';
  const caption = raw.caption || raw.description || title;
  const authorName = raw.uploader || raw.author || 'Social Creator';
  const authorHandle = raw.uploader_id || raw.handle || raw.username || authorName;
  const thumb = raw.thumbnail;
  const metrics = raw.metrics || {
    likes: raw.likes || raw.like_count,
    comments: raw.comments || raw.comment_count,
    shares: raw.shares || raw.share_count || raw.reposts,
    views: raw.views || raw.view_count || raw.plays
  };

  const variants = [];

  // Videos
  if (Array.isArray(raw.video_formats)) {
    raw.video_formats.forEach((vf, idx) => {
      const q = vf.quality || (vf.height ? `${vf.height}p` : `Option ${idx + 1}`);
      variants.push({
        id: vf.id || `video_${idx}`,
        kind: 'video',
        ext: vf.ext || 'mp4',
        quality: q,
        width: vf.width,
        height: vf.height,
        hasAudio: vf.has_audio !== false,
        downloadUrl: vf.stream_url || vf.url
      });
    });
  }

  // Thumbnails / Photos
  if (Array.isArray(raw.thumbnails)) {
    raw.thumbnails.forEach((th, idx) => {
      variants.push({
        id: `thumb_${idx}`,
        kind: 'image',
        ext: 'jpg',
        quality: th.quality || th.label || `Photo ${idx + 1}`,
        downloadUrl: th.stream_url || th.url
      });
    });
  }

  // Fallback single thumbnail if no formats found
  if (variants.length === 0 && thumb) {
    variants.push({
      id: 'thumb_main',
      kind: 'image',
      ext: 'jpg',
      quality: 'High Resolution Photo',
      downloadUrl: thumb
    });
  }

  // Carousel Slides
  if (Array.isArray(raw.carousel_media) && raw.carousel_media.length > 0) {
    const items = raw.carousel_media.map((cm, idx) => ({
      index: idx + 1,
      kind: cm.type === 'video' ? 'video' : 'image',
      thumbnail: cm.url,
      variants: [{
        id: `slide_${idx + 1}`,
        kind: cm.type === 'video' ? 'video' : 'image',
        ext: cm.type === 'video' ? 'mp4' : 'jpg',
        quality: cm.quality || `Slide ${idx + 1}`,
        downloadUrl: cm.stream_url || cm.url
      }]
    }));

    return {
      platform: platform || raw.platform || 'social',
      sourceUrl,
      title,
      caption,
      author: { name: authorName, handle: authorHandle, avatar: thumb },
      metrics,
      items
    };
  }

  // Single Item
  const kind = variants.some(v => v.kind === 'video') ? 'video' : 'image';
  const item = {
    index: 1,
    kind,
    thumbnail: thumb,
    durationSec: raw.duration,
    variants
  };

  return {
    platform: platform || raw.platform || 'social',
    sourceUrl,
    title,
    caption,
    author: { name: authorName, handle: authorHandle, avatar: thumb },
    metrics,
    items: [item]
  };
}

/**
 * Direct client-side YouTube fallback when cloud hosting IPs are bot-blocked
 */
async function resolveYouTubeClientFallback(url, videoId) {
  let title = 'YouTube Video';
  let author = 'YouTube Creator';
  let thumb = `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`;

  try {
    const oembedUrl = `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`;
    const resp = await fetch(oembedUrl);
    if (resp.ok) {
      const odata = await resp.json();
      title = odata.title || title;
      author = odata.author_name || author;
      thumb = odata.thumbnail_url || thumb;
    }
  } catch (e) {
    // Ignore oembed failure
  }

  const cleanTitle = title.replace(/[\\/*?:"<>|]/g, '').trim();

  const reliableThumb = thumb || `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;

  const variants = [
    {
      id: 'maxres_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '1080p Full HD Maxres Thumbnail',
      width: 1920,
      height: 1080,
      url: `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`
    },
    {
      id: 'hq_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '720p HD Thumbnail',
      width: 1280,
      height: 720,
      url: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`
    },
    {
      id: 'mq_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '480p Standard Thumbnail',
      width: 640,
      height: 480,
      url: `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`
    }
  ];

  return {
    platform: 'youtube',
    sourceUrl: `https://www.youtube.com/watch?v=${videoId}`,
    title,
    thumbnail: reliableThumb,
    author: { name: author, handle: author, avatar: reliableThumb },
    items: [{
      index: 1,
      kind: 'image',
      thumbnail: reliableThumb,
      variants
    }]
  };
}

/**
 * Main resolve function.
 * One backend call (the server already walks every engine + fallback and answers within its own budget).
 * The 75 s ceiling covers a Render cold start (~50 s). We only retry on a network failure, never after a
 * definitive answer, so the user is never made to wait twice.
 */
export async function resolveMedia(rawInput, { signal } = {}) {
  const norm = normalizeUrl(rawInput, true);
  if (!norm.ok) {
    return { ok: false, code: norm.code, error: getErrorMessage(norm.code, norm.error) };
  }
  const attributionData = getAttribution();

  const callOnce = async (path) => {
    const controller = new AbortController();
    const onAbort = () => controller.abort();
    if (signal) signal.addEventListener('abort', onAbort, { once: true });
    const timeoutId = setTimeout(() => controller.abort(), 75000);
    try {
      const resp = await fetch(`${BACKEND_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: norm.url, allow_generic: true, attribution: attributionData }),
        signal: controller.signal,
      });
      let json = null;
      try { json = await resp.json(); } catch (_) { json = null; }
      return { resp, json };
    } finally {
      clearTimeout(timeoutId);
      if (signal) signal.removeEventListener('abort', onAbort);
    }
  };

  let networkFailed = false;
  for (const path of ['/api/resolve', '/api/extract']) {
    const startedAt = Date.now();
    try {
      const { resp, json } = await callOnce(path);
      if (resp.ok && json && json.ok && json.data) {
        return { ok: true, data: json.data };
      }
      if (resp.ok && json && (json.success || json.ok) && (json.data || json)) {
        const normalized = normalizeLegacyExtract(json.data || json, norm.url, norm.platform);
        if (normalized.items?.[0]?.variants?.length) return { ok: true, data: normalized };
      }
      if (json && json.error && resp.status !== 404 && resp.status !== 405) {
        const code = json.error.code || ErrorCode.UPSTREAM_FAILED;
        return { ok: false, code, retryable: !!json.error.retryable, error: getErrorMessage(code, json.error.message) };
      }
      break; // definitive non-error answer we could not use: do not repeat the same work
    } catch (e) {
      if (signal && signal.aborted) return { ok: false, aborted: true, code: 'ABORTED', error: '' };
      networkFailed = true;
      if (Date.now() - startedAt > 10000) break; // a long timeout means the server is overloaded: do not wait twice
    }
  }

  // Last resort for YouTube only when the backend is unreachable: show details + thumbnails honestly.
  if (networkFailed && norm.platform === 'youtube') {
    const vidMatch = norm.url.match(/(?:v=|youtu\.be\/|shorts\/|live\/)([a-zA-Z0-9_-]{11})/);
    if (vidMatch) {
      try {
        const ytData = await resolveYouTubeClientFallback(norm.url, vidMatch[1]);
        ytData.status = 'degraded';
        ytData.notice = {
          code: 'SERVER_UNREACHABLE',
          message: 'Our download server is waking up. Video downloads will appear when you retry in a few seconds.',
          retryable: true,
          downloads_available: false,
        };
        return { ok: true, data: ytData };
      } catch (e) { /* fall through */ }
    }
  }

  return {
    ok: false,
    code: networkFailed ? 'NETWORK' : ErrorCode.UPSTREAM_FAILED,
    retryable: true,
    error: networkFailed
      ? 'We could not reach the download server. Check your connection and try again.'
      : 'We could not find downloadable media at this link. Make sure the post is public and try again.',
  };
}
