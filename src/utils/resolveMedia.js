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

  const variants = [
    {
      id: 'maxres_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '1080p Full HD Maxres Thumbnail',
      width: 1920,
      height: 1080,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`
    },
    {
      id: 'hq_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '720p HD Thumbnail',
      width: 1280,
      height: 720,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`
    },
    {
      id: 'mq_jpg',
      kind: 'image',
      ext: 'jpg',
      quality: '480p Standard Thumbnail',
      width: 640,
      height: 480,
      downloadUrl: `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`
    }
  ];

  return {
    platform: 'youtube',
    sourceUrl: `https://www.youtube.com/watch?v=${videoId}`,
    title,
    author: { name: author, handle: author, avatar: thumb },
    items: [{
      index: 1,
      kind: 'image',
      thumbnail: thumb,
      variants
    }]
  };
}

/**
 * Main Resilient Resolve Function
 */
export async function resolveMedia(rawInput) {
  const norm = normalizeUrl(rawInput, true);
  if (!norm.ok) {
    return { ok: false, code: norm.code, error: getErrorMessage(norm.code, norm.error) };
  }

  const attributionHeaders = getAttributionHeaders();
  const attributionData = getAttribution();

  // 1. Primary Attempt: /api/resolve
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    const resp = await fetch(`${BACKEND_BASE}/api/resolve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: norm.url,
        allow_generic: true,
        attribution: attributionData
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (resp.ok) {
      const json = await resp.json();
      if (json.ok && json.data) {
        return { ok: true, data: json.data };
      }
      if (json.error) {
        return { ok: false, code: json.error.code, error: getErrorMessage(json.error.code, json.error.message) };
      }
    }

    // If 404 (endpoint not deployed on current backend instance), fall through to /api/extract
  } catch (e) {
    // Network error or abort, proceed to fallback attempt
  }

  // 2. Secondary Attempt: /api/extract (legacy gateway)
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    const resp = await fetch(`${BACKEND_BASE}/api/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: norm.url,
        attribution: attributionData
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (resp.ok) {
      const json = await resp.json();
      if (json.ok && json.data) {
        return { ok: true, data: json.data };
      }
      const legacyPayload = json.data || json;
      if ((json.success || json.ok) && legacyPayload) {
        const normalized = normalizeLegacyExtract(legacyPayload, norm.url, norm.platform);
        if (normalized && normalized.items && normalized.items.length > 0 && normalized.items[0].variants && normalized.items[0].variants.length > 0) {
          return { ok: true, data: normalized };
        }
      }
      if (json.error) {
        return { ok: false, code: ErrorCode.UPSTREAM_FAILED, error: json.error };
      }
    }
  } catch (e) {
    // Network error
  }

  // 3. YouTube specific client fallback (extract video ID)
  if (norm.platform === 'youtube') {
    const vidMatch = norm.url.match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})/);
    if (vidMatch) {
      try {
        const ytData = await resolveYouTubeClientFallback(norm.url, vidMatch[1]);
        return { ok: true, data: ytData };
      } catch (e) {}
    }
  }

  return {
    ok: false,
    code: ErrorCode.UPSTREAM_FAILED,
    error: 'The extraction engine could not resolve media from this link. Please check if the post is public and try again.'
  };
}
