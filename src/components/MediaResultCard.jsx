import React, { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Archive, BadgeCheck, Check, ChevronDown, ChevronUp, CircleAlert, Copy, Download, Eye, FileText, Heart,
  Image as ImageIcon, Loader2, Maximize2, MessageSquare, Music, RotateCw, Share2, Sparkles, Video, X,
} from 'lucide-react';
import {
  TwitterXIcon, YoutubeIcon, FacebookIcon, InstagramIcon, TiktokIcon,
  PinterestIcon, RedditIcon, ThreadsIcon, GlobeIcon,
} from './BrandIcons.jsx';
import { BACKEND_BASE } from '../utils/resolveMedia.js';

const AiStudio = lazy(() => import('./AiStudio.jsx'));

const PLATFORM_ICON = {
  twitter: TwitterXIcon, x: TwitterXIcon, youtube: YoutubeIcon, facebook: FacebookIcon, instagram: InstagramIcon,
  tiktok: TiktokIcon, pinterest: PinterestIcon, reddit: RedditIcon, threads: ThreadsIcon,
};

/* ---------- helpers ---------- */
function compact(val) {
  if (val === undefined || val === null || val === '') return null;
  if (typeof val === 'string' && /[KMB,]/.test(val)) return val;
  const n = Number(val);
  if (!Number.isFinite(n) || n <= 0) return null;
  if (n >= 1e9) return `${(n / 1e9).toFixed(1).replace(/\.0$/, '')}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1).replace(/\.0$/, '')}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1).replace(/\.0$/, '')}K`;
  return n.toLocaleString();
}

function formatDuration(sec) {
  const n = Number(sec);
  if (!Number.isFinite(n) || n <= 0) return null;
  const s = Math.floor(n);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}` : `${m}:${String(r).padStart(2, '0')}`;
}

function formatBytes(bytes) {
  const n = Number(bytes);
  if (!Number.isFinite(n) || n <= 0) return null;
  const mb = n / 1048576;
  return mb >= 1000 ? `${(mb / 1024).toFixed(2)} GB` : `${mb.toFixed(1)} MB`;
}

/** "1080p (Full HD) • With Sound" -> "1080p (Full HD)" */
function cleanLabel(label, fallback) {
  const t = String(label || '').replace(/\s*[•·|].*$/, '').trim();
  return t || fallback;
}

function heightOf(v) {
  if (Number(v.height) > 0) return Number(v.height);
  const m = String(v.label || '').match(/(\d{3,4})\s*p/i);
  return m ? Number(m[1]) : 0;
}

function decodeTokenTarget(token) {
  try {
    const part = String(token || '').split('.')[0].replace(/-/g, '+').replace(/_/g, '/');
    const json = JSON.parse(atob(part + '='.repeat((4 - (part.length % 4)) % 4)));
    return json.u || null;
  } catch { return null; }
}

function isHttp(v) { return typeof v === 'string' && /^https?:\/\//i.test(v); }

function imageSrc(img) {
  if (isHttp(img.url)) return img.url;
  if (isHttp(img.streamUrl)) return img.streamUrl;
  if (img.token) return `${BACKEND_BASE}/api/proxy-image?token=${encodeURIComponent(img.token)}`;
  return null;
}

function absolute(path) {
  return isHttp(path) ? path : `${BACKEND_BASE}${path.startsWith('/') ? '' : '/'}${path}`;
}

/** Server-processed downloads (yt-dlp + ffmpeg): we show progress and friendly errors for these. */
function processedTarget(item) {
  const own = item.downloadUrl || '';
  if (/\/api\/download_(video|audio)\?/.test(own)) return own;
  const t = decodeTokenTarget(item.token);
  return t && /^\/api\/download_(video|audio)\?/.test(t) ? t : null;
}

function safeName(s) { return String(s || 'ovd').replace(/[^a-zA-Z0-9._-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 80) || 'ovd'; }

/* ---------- component ---------- */
export default function MediaResultCard({ data, onReset, onRetry, innerRef }) {
  const platform = data?.platform || 'social';
  const title = data?.title || 'Your download';
  const caption = data?.caption && data.caption !== title ? data.caption : '';
  const author = data?.author || {};
  const authorName = author.displayName || author.name || '';
  const authorHandle = author.username || author.handle || '';
  const stats = data?.stats || data?.metrics || {};
  const tags = data?.tags || [];
  const hashtags = data?.hashtags || [];
  const notice = data?.notice || null;
  const warnings = data?.warnings || [];

  const items = Array.isArray(data?.items) ? data.items : [];
  const fromItems = (kind) => items.flatMap((it) => (it.variants || []).filter((v) => v.kind === kind));

  const videos = useMemo(() => {
    const list = (Array.isArray(data?.videos) && data.videos.length ? data.videos : fromItems('video'));
    return [...list].sort((a, b) => heightOf(b) - heightOf(a));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);
  const audios = useMemo(() => (Array.isArray(data?.audios) && data.audios.length ? data.audios : fromItems('audio')),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data]);
  const images = useMemo(() => {
    const raw = Array.isArray(data?.images) && data.images.length ? data.images : fromItems('image');
    return raw.length ? raw : (Array.isArray(data?.thumbnails) ? data.thumbnails : []);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);
  const subtitles = Array.isArray(data?.subtitles) ? data.subtitles : [];

  const tabs = useMemo(() => {
    const t = [];
    if (videos.length) t.push({ id: 'video', label: 'Video', icon: Video, count: videos.length });
    if (audios.length) t.push({ id: 'audio', label: 'Audio', icon: Music, count: audios.length });
    if (images.length) t.push({ id: 'images', label: videos.length ? 'Thumbnails' : 'Photos', icon: ImageIcon, count: images.length });
    if (subtitles.length) t.push({ id: 'subtitles', label: 'Subtitles', icon: FileText, count: subtitles.length });
    if (videos.length || audios.length) t.push({ id: 'ai', label: 'Captions', icon: Sparkles });
    return t;
  }, [videos, audios, images, subtitles]);

  const [activeTab, setActiveTab] = useState(tabs[0]?.id || 'images');
  useEffect(() => { setActiveTab(tabs[0]?.id || 'images'); }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  const [busy, setBusy] = useState(null); // { key, progress }
  const [dlError, setDlError] = useState(null); // { message, retry }
  const [toast, setToast] = useState('');
  const [preview, setPreview] = useState(null);
  const [captionOpen, setCaptionOpen] = useState(false);
  const [copied, setCopied] = useState('');
  const [zipping, setZipping] = useState(false);
  const [job, setJob] = useState(null);
  const abortRef = useRef(null);
  const toastTimer = useRef(null);

  const showToast = useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(''), 3200);
  }, []);

  useEffect(() => () => { abortRef.current?.abort(); clearTimeout(toastTimer.current); }, []);

  // Esc closes the full-size preview
  useEffect(() => {
    if (!preview) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') setPreview(null); };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', onKey); document.body.style.overflow = prev; };
  }, [preview]);

  const PlatformIcon = PLATFORM_ICON[platform] || GlobeIcon;
  const thumb = useMemo(() => {
    const cand = [data?.thumbnail, data?.thumbnails?.[0]?.url, images[0] && imageSrc(images[0]), author.avatar];
    return cand.find(isHttp) || (images[0]?.token ? `${BACKEND_BASE}/api/proxy-image?token=${encodeURIComponent(images[0].token)}` : null);
  }, [data, images, author.avatar]);
  const duration = formatDuration(data?.duration);
  const statList = [
    { key: 'views', v: compact(stats.views), Icon: Eye, suffix: ' views' },
    { key: 'likes', v: compact(stats.likes), Icon: Heart },
    { key: 'comments', v: compact(stats.comments), Icon: MessageSquare },
    { key: 'shares', v: compact(stats.shares || stats.reposts || stats.retweets), Icon: Share2 },
  ].filter((s) => s.v);

  /* ----- downloads ----- */
  const runProcessed = useCallback(async (item, key, fallbackName, target) => {
    setDlError(null);
    setBusy({ key, progress: null });
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const resp = await fetch(absolute(target), { signal: controller.signal });
      if (!resp.ok) {
        let message = 'We could not prepare this download. Please try another quality.';
        try {
          const j = await resp.json();
          message = (j.error && (j.error.message || j.error)) || message;
        } catch { /* body was not JSON */ }
        setDlError({ message: typeof message === 'string' ? message : 'Download failed. Please try again.', retry: () => runProcessed(item, key, fallbackName, target) });
        return;
      }
      const total = Number(resp.headers.get('content-length')) || 0;
      const disp = resp.headers.get('content-disposition') || '';
      const m = disp.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
      const filename = m ? decodeURIComponent(m[1]) : fallbackName;
      const reader = resp.body.getReader();
      const chunks = [];
      let got = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        got += value.length;
        if (total) setBusy({ key, progress: Math.min(99, Math.round((got / total) * 100)) });
      }
      const href = URL.createObjectURL(new Blob(chunks, { type: resp.headers.get('content-type') || 'application/octet-stream' }));
      const a = Object.assign(document.createElement('a'), { href, download: filename });
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(href), 60000);
      showToast('Saved. Check your Downloads.');
    } catch (e) {
      if (e.name !== 'AbortError') {
        setDlError({ message: 'The connection dropped while downloading. Check your internet and try again.', retry: () => runProcessed(item, key, fallbackName, target) });
      }
    } finally {
      setBusy(null);
    }
  }, [showToast]);

  const startDownload = useCallback((item, key) => {
    if (!item || busy) return;
    const ext = item.ext || (item.kind === 'audio' ? 'mp3' : item.kind === 'image' ? 'jpg' : 'mp4');
    const name = `${safeName(platform)}_${safeName(item.label || 'media')}.${ext}`;
    const target = processedTarget(item);
    if (target) { runProcessed(item, key, name, target); return; }

    // Direct CDN stream: the browser saves it natively (no memory use). Brief spinner as feedback.
    setBusy({ key, progress: null });
    setTimeout(() => setBusy(null), 2200);
    const upstream = isHttp(item.url) ? item.url : (isHttp(item.streamUrl) ? item.streamUrl : null);
    let href = null;
    if (item.token) {
      href = `${BACKEND_BASE}/api/download?token=${encodeURIComponent(item.token)}`;
      if (upstream) href += `&url=${encodeURIComponent(upstream)}`;
      href += `&filename=${encodeURIComponent(name)}`;
    } else if (item.downloadUrl) {
      href = absolute(item.downloadUrl);
    } else if (upstream) {
      href = `${BACKEND_BASE}/api/download?url=${encodeURIComponent(upstream)}&filename=${encodeURIComponent(name)}`;
    }
    if (href) {
      const a = document.createElement('a');
      a.href = href;
      if (name) a.download = name;
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => a.remove(), 200);
    }
  }, [busy, platform, runProcessed]);

  // merge jobs (separate video + audio streams)
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed' || job.id === 'pending') return undefined;
    let failCount = 0;
    const t = setInterval(async () => {
      try {
        const r = await fetch(`${BACKEND_BASE}/api/jobs/${job.id}`);
        if (!r.ok) {
          failCount++;
          if (failCount >= 4) {
            clearInterval(t);
            setJob(null);
            setDlError({ message: 'Download server timed out or restarted. Please retry.' });
          }
          return;
        }
        const j = await r.json();
        if (!j.ok || !j.job) {
          failCount++;
          if (failCount >= 4) {
            clearInterval(t);
            setJob(null);
            setDlError({ message: j.error || 'Job not found. Please try downloading again.' });
          }
          return;
        }
        failCount = 0;
        if (j.job.status === 'done') {
          clearInterval(t);
          setJob((p) => (p ? { ...p, status: 'done', progress: 100 } : null));
          const dlTarget = j.job.download_url || `${BACKEND_BASE}/api/jobs/${job.id}/file`;
          const a = document.createElement('a');
          a.href = absolute(dlTarget);
          a.download = j.job.filename || 'video.mp4';
          a.rel = 'noopener noreferrer';
          document.body.appendChild(a);
          a.click();
          setTimeout(() => a.remove(), 200);
          showToast('Your video is ready.');
          setTimeout(() => setJob(null), 2500);
        } else if (j.job.status === 'failed') {
          clearInterval(t);
          setJob(null);
          setDlError({ message: j.job.error || 'We could not prepare this video. Please try another quality.' });
        } else {
          setJob((p) => (p ? { ...p, status: j.job.status, progress: j.job.progress || p.progress } : p));
        }
      } catch {
        failCount++;
        if (failCount >= 4) {
          clearInterval(t);
          setJob(null);
          setDlError({ message: 'Network interrupted. Please try again.' });
        }
      }
    }, 1200);
    return () => clearInterval(t);
  }, [job, showToast]);

  async function startMerge(video, key) {
    setDlError(null);
    const targetKey = key || 'merge';
    if (!video.token && !video.url) { startDownload(video, targetKey); return; }
    const tokens = [video.token, audios[0]?.token].filter(Boolean);
    try {
      setJob({ id: 'pending', status: 'queued', progress: 15, targetKey });
      const r = await fetch(`${BACKEND_BASE}/api/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'merge',
          tokens,
          url: data?.url || data?.webpage_url,
          title: data?.title || 'video',
          height: heightOf(video) || 1080,
        }),
      });
      const j = await r.json();
      if (r.ok && j.ok && j.job_id) {
        setJob({ id: j.job_id, status: 'processing', progress: 30, targetKey });
      } else {
        setJob(null);
        startDownload(video, targetKey);
      }
    } catch {
      setJob(null);
      startDownload(video, targetKey);
    }
  }

  async function downloadZip() {
    const tokens = images.map((i) => i.token).filter(Boolean);
    if (!tokens.length) { startDownload(images[0], 'img_0'); return; }
    setZipping(true);
    setDlError(null);
    try {
      const r = await fetch(`${BACKEND_BASE}/api/zip`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tokens }),
      });
      if (!r.ok) throw new Error('zip');
      const href = URL.createObjectURL(await r.blob());
      const a = Object.assign(document.createElement('a'), { href, download: `${safeName(platform)}_photos.zip` });
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(href), 60000);
      showToast('ZIP saved.');
    } catch {
      setDlError({ message: 'Could not create the ZIP. Download the photos one by one instead.' });
    } finally { setZipping(false); }
  }

  function copy(text, id) {
    if (!text) return;
    navigator.clipboard?.writeText(text).then(() => { setCopied(id); setTimeout(() => setCopied(''), 1800); }).catch(() => {});
  }

  const allTags = [...hashtags.map((h) => (String(h).startsWith('#') ? h : `#${h}`)), ...tags].slice(0, 12);

  const btnBase = 'shrink-0 min-h-11 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition active:scale-[.98] disabled:opacity-60';

  const renderDownloadButton = ({ item, id, label = 'Download', primary = true, merge = false }) => {
    const mine = busy?.key === id;
    const isThisJob = merge && job?.targetKey === id;
    return (
      <button
        key={id}
        type="button"
        onClick={() => (merge ? startMerge(item, id) : startDownload(item, id))}
        disabled={!!busy || !!job}
        aria-busy={mine || isThisJob}
        className={`${btnBase} ${primary ? 'bg-[var(--primary)] text-[var(--on-primary)] hover:brightness-110' : 'bg-[var(--bg-alt)] text-[var(--text)] border border-[var(--border)] hover:border-[var(--accent)]'} min-w-[8.5rem]`}
      >
        {mine || isThisJob ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
        <span>
          {mine
            ? (busy.progress != null ? `${busy.progress}%` : 'Preparing...')
            : isThisJob
            ? (job.progress ? `${job.progress}%` : 'Preparing...')
            : label}
        </span>
      </button>
    );
  };

  /* ---------- render ---------- */
  if (!data) return null;
  const canNotice = notice || (warnings.length > 0 && data.status === 'degraded');

  return (
    <section ref={innerRef} aria-label="Download options" className="ovd-sheet w-full max-w-4xl mx-auto px-4 pb-10">
      {canNotice && (
        <div role="status" className="mb-3 rounded-2xl border border-[var(--warning)]/40 bg-[var(--warning-bg)] p-4 flex items-start gap-3">
          <CircleAlert className="w-5 h-5 shrink-0 mt-0.5 text-[var(--warning)]" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-[var(--text)]">{notice?.downloads_available === false ? 'Video downloads are paused for this link' : 'Heads up'}</p>
            <p className="text-[var(--text-muted)] mt-0.5">{notice?.message || warnings[0]}</p>
          </div>
          {(notice?.retryable ?? true) && onRetry && (
            <button type="button" onClick={onRetry} className="shrink-0 h-9 px-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-sm font-semibold flex items-center gap-1.5 hover:border-[var(--accent)]">
              <RotateCw className="w-4 h-4" /> Retry
            </button>
          )}
        </div>
      )}

      <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-2)] overflow-hidden">
        {/* summary */}
        <div className="p-4 sm:p-6 grid gap-4 sm:gap-6 md:grid-cols-[280px_1fr]">
          <div className="relative aspect-video md:aspect-[4/3] rounded-2xl overflow-hidden bg-[var(--bg-alt)] group">
            {thumb ? (
              <img
                src={thumb} alt="" referrerPolicy="no-referrer" decoding="async"
                className="absolute inset-0 w-full h-full object-cover"
                onError={(e) => {
                  const el = e.currentTarget;
                  if (el.src.includes('maxresdefault')) el.src = el.src.replace('maxresdefault', 'hqdefault');
                  else el.style.visibility = 'hidden';
                }}
              />
            ) : (
              <div className="absolute inset-0 grid place-items-center text-[var(--text-muted)]"><ImageIcon className="w-10 h-10" /></div>
            )}
            <span className="absolute top-2.5 left-2.5 flex items-center gap-1.5 bg-black/70 text-white text-xs font-semibold px-2.5 py-1 rounded-full backdrop-blur-sm">
              <PlatformIcon className="w-3.5 h-3.5" /><span className="capitalize">{platform}</span>
            </span>
            {duration && <span className="absolute bottom-2.5 right-2.5 bg-black/80 text-white text-xs font-mono px-2 py-0.5 rounded-md">{duration}</span>}
            {thumb && (
              <button type="button" onClick={() => setPreview({ url: thumb, title })} aria-label="View full size"
                className="absolute inset-0 grid place-items-center bg-black/0 hover:bg-black/30 text-white opacity-0 hover:opacity-100 focus-visible:opacity-100 transition">
                <span className="p-3 rounded-full bg-white/20 backdrop-blur-md"><Maximize2 className="w-5 h-5" /></span>
              </button>
            )}
          </div>

          <div className="min-w-0 flex flex-col">
            <div className="flex items-start justify-between gap-3">
              {authorName ? (
                <div className="flex items-center gap-1.5 min-w-0 text-sm font-semibold text-[var(--text)]">
                  <span className="truncate">{authorName}</span>
                  <BadgeCheck className="w-4 h-4 shrink-0 text-[var(--accent)]" />
                  {authorHandle && authorHandle !== authorName && <span className="truncate font-normal text-[var(--text-muted)]">@{String(authorHandle).replace(/^@/, '')}</span>}
                </div>
              ) : <span />}
              {onReset && (
                <button type="button" onClick={onReset} className="shrink-0 text-sm font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1">
                  <X className="w-4 h-4" /> New link
                </button>
              )}
            </div>
            <h2 className="mt-2 text-xl sm:text-2xl font-bold leading-snug text-[var(--text)] line-clamp-3 wrap-any">{title}</h2>

            {statList.length > 0 && (
              <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-[var(--text-muted)]">
                {statList.map(({ key, v, Icon, suffix }) => (
                  <li key={key} className="flex items-center gap-1.5"><Icon className="w-4 h-4" />{v}{suffix || ''}</li>
                ))}
              </ul>
            )}

            {caption && (
              <div className="mt-3 text-sm text-[var(--text)] rounded-xl bg-[var(--bg-alt)] p-3">
                <p className={`whitespace-pre-line wrap-any ${captionOpen ? '' : 'line-clamp-3'}`}>{caption}</p>
                <div className="mt-2 flex items-center justify-between gap-3">
                  {caption.length > 160 ? (
                    <button type="button" onClick={() => setCaptionOpen((v) => !v)} className="text-xs font-semibold text-[var(--accent)] flex items-center gap-1">
                      {captionOpen ? <>Show less <ChevronUp className="w-3.5 h-3.5" /></> : <>Show more <ChevronDown className="w-3.5 h-3.5" /></>}
                    </button>
                  ) : <span />}
                  <button type="button" onClick={() => copy(caption, 'caption')} className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1">
                    {copied === 'caption' ? <><Check className="w-3.5 h-3.5 text-[var(--positive)]" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy caption</>}
                  </button>
                </div>
              </div>
            )}

            {allTags.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5">
                {allTags.slice(0, 6).map((t, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-lg bg-[var(--accent-bg)] text-[var(--accent)] font-medium">{t}</span>
                ))}
                <button type="button" onClick={() => copy(allTags.join(' '), 'tags')} className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] underline underline-offset-2">
                  {copied === 'tags' ? 'Copied' : 'Copy tags'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* tabs */}
        {tabs.length > 1 && (
          <div role="tablist" aria-label="Download type" className="snap-row no-scrollbar gap-1.5 px-4 sm:px-6 py-2 border-y border-[var(--border)] bg-[var(--bg-alt)]/60">
            {tabs.map(({ id, label, icon: Icon, count }) => (
              <button
                key={id} type="button" role="tab" aria-selected={activeTab === id}
                onClick={() => setActiveTab(id)}
                className={`h-10 px-3.5 rounded-full text-sm font-semibold whitespace-nowrap flex items-center gap-2 transition-colors ${
                  activeTab === id ? 'bg-[var(--text)] text-[var(--bg)]' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
                }`}
              >
                <Icon className="w-4 h-4" />{label}
                {count != null && <span className={`text-xs ${activeTab === id ? 'opacity-70' : 'opacity-60'}`}>{count}</span>}
              </button>
            ))}
          </div>
        )}

        {/* status strips */}
        {job && (
          <div className="px-4 sm:px-6 py-3 bg-[var(--accent-bg)] border-b border-[var(--border)] flex items-center gap-3 text-sm" role="status">
            <Loader2 className="w-4 h-4 animate-spin text-[var(--accent)]" />
            <span className="font-semibold text-[var(--text)]">{job.status === 'done' ? 'Ready. Saving to your device...' : 'Downloading & processing HD video in background...'}</span>
            <span className="ml-auto text-[var(--text-muted)]">{job.progress}%</span>
          </div>
        )}
        {dlError && (
          <div className="px-4 sm:px-6 py-3 bg-[var(--negative-bg)] border-b border-[var(--border)] flex items-center gap-3 text-sm" role="alert">
            <CircleAlert className="w-4 h-4 shrink-0 text-[var(--negative)]" />
            <span className="flex-1 text-[var(--text)]">{dlError.message}</span>
            {dlError.retry && <button type="button" onClick={dlError.retry} className="font-semibold underline">Try again</button>}
            <button type="button" onClick={() => setDlError(null)} aria-label="Dismiss" className="p-1"><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* panels */}
        <div className="p-4 sm:p-6" role="tabpanel">
          {activeTab === 'video' && videos.length > 0 && (
            <ul className="space-y-2.5">
              {videos.map((v, i) => {
                const best = i === 0;
                const ext = String(v.ext || 'mp4').toUpperCase();
                const size = formatBytes(v.filesize);
                const sound = v.needsMerge ? 'With sound' : (v.hasAudio === false ? 'No sound' : 'With sound');
                return (
                  <li key={`v${i}`} className={`flex items-center gap-3 rounded-2xl border p-3 sm:p-4 ${best ? 'border-[var(--accent)] bg-[var(--accent-bg)]/50' : 'border-[var(--border)]'}`}>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-lg font-bold text-[var(--text)]">{cleanLabel(v.label || v.quality, `${heightOf(v) || 720}p`)}</span>
                        {best && <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-[var(--primary)] text-[var(--on-primary)]">Best quality</span>}
                      </div>
                      <p className="text-sm text-[var(--text-muted)]">
                        {ext}{v.fps ? ` · ${v.fps} fps` : ''}{size ? ` · ${size}` : ''} ·{' '}
                        <span className={sound === 'No sound' ? '' : 'text-[var(--positive)] font-medium'}>{sound}</span>
                      </p>
                    </div>
                    {renderDownloadButton({ item: v, id: `v${i}`, primary: best, merge: v.needsMerge === true })}
                  </li>
                );
              })}
            </ul>
          )}

          {activeTab === 'audio' && audios.length > 0 && (
            <ul className="space-y-2.5">
              {audios.map((a, i) => (
                <li key={`a${i}`} className="flex items-center gap-3 rounded-2xl border border-[var(--border)] p-3 sm:p-4">
                  <span className="w-11 h-11 rounded-xl bg-[var(--bg-alt)] grid place-items-center shrink-0"><Music className="w-5 h-5" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="font-bold text-[var(--text)] truncate">{cleanLabel(a.label, `Audio ${i + 1}`)}</p>
                    <p className="text-sm text-[var(--text-muted)]">{String(a.ext || 'mp3').toUpperCase()}{a.bitrate ? ` · ${a.bitrate} kbps` : ''}{formatBytes(a.filesize) ? ` · ${formatBytes(a.filesize)}` : ''}</p>
                  </div>
                  {renderDownloadButton({ item: { ...a, kind: 'audio' }, id: `a${i}`, label: 'Save MP3', primary: i === 0 })}
                </li>
              ))}
            </ul>
          )}

          {activeTab === 'images' && images.length > 0 && (
            <div>
              {images.length > 1 && (
                <div className="flex items-center justify-between gap-3 mb-3">
                  <p className="text-sm text-[var(--text-muted)]">{images.length} images</p>
                  <button type="button" onClick={downloadZip} disabled={zipping} className={`${btnBase} bg-[var(--primary)] text-[var(--on-primary)]`}>
                    {zipping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Archive className="w-4 h-4" />}
                    {zipping ? 'Creating ZIP...' : 'Download all (ZIP)'}
                  </button>
                </div>
              )}
              <ul className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {images.map((img, i) => {
                  const src = imageSrc(img);
                  return (
                    <li key={`i${i}`} className="rounded-2xl border border-[var(--border)] overflow-hidden bg-[var(--bg-alt)] flex flex-col">
                      <button type="button" onClick={() => src && setPreview({ url: src, title: img.label })} className="relative aspect-video block" aria-label={`Preview ${img.label || `image ${i + 1}`}`}>
                        {src ? <img src={src} alt="" loading="lazy" decoding="async" referrerPolicy="no-referrer" className="absolute inset-0 w-full h-full object-cover" /> : <ImageIcon className="absolute inset-0 m-auto w-8 h-8 opacity-40" />}
                      </button>
                      <div className="p-2.5 flex items-center justify-between gap-2 bg-[var(--surface)]">
                        <span className="text-sm font-semibold truncate">{cleanLabel(img.label, `Photo ${i + 1}`)}</span>
                        <button type="button" onClick={() => startDownload({ ...img, kind: 'image' }, `i${i}`)} disabled={!!busy} aria-label={`Download ${img.label || `image ${i + 1}`}`}
                          className="shrink-0 w-10 h-10 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center disabled:opacity-60">
                          {busy?.key === `i${i}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {activeTab === 'subtitles' && subtitles.length > 0 && (
            <ul className="grid sm:grid-cols-2 gap-2.5">
              {subtitles.map((s, i) => (
                <li key={`s${i}`} className="flex items-center gap-3 rounded-2xl border border-[var(--border)] p-3">
                  <FileText className="w-5 h-5 shrink-0 text-[var(--text-muted)]" />
                  <div className="flex-1 min-w-0"><p className="font-semibold truncate">{s.lang || s.language || 'Subtitle'}</p><p className="text-xs text-[var(--text-muted)]">{String(s.ext || 'vtt').toUpperCase()}</p></div>
                  <button type="button" onClick={() => startDownload({ ...s, kind: 'subtitle' }, `s${i}`)} aria-label="Download subtitle" className="w-10 h-10 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center"><Download className="w-4 h-4" /></button>
                </li>
              ))}
            </ul>
          )}

          {activeTab === 'ai' && (
            <Suspense fallback={<div className="ovd-skeleton h-40 rounded-2xl" />}>
              <AiStudio data={data} title={title} caption={caption} platform={platform} audios={audios}
                onDownload={startDownload} onToast={showToast} />
            </Suspense>
          )}

          {!tabs.length && (
            <p className="text-center text-[var(--text-muted)] py-6">No downloadable files were found for this link.</p>
          )}
        </div>
      </div>

      {preview && (
        <div className="fixed inset-0 z-[60] bg-black/90 grid place-items-center p-4 animate-fadeIn" role="dialog" aria-modal="true" aria-label="Image preview" onClick={() => setPreview(null)}>
          <button type="button" onClick={() => setPreview(null)} aria-label="Close preview" className="absolute top-4 right-4 w-11 h-11 rounded-full bg-white/15 text-white grid place-items-center hover:bg-white/25"><X className="w-6 h-6" /></button>
          <img src={preview.url} alt={preview.title || 'Preview'} className="max-h-[85dvh] max-w-full rounded-2xl object-contain" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-[max(1rem,env(safe-area-inset-bottom))] z-50 flex justify-center px-4">
        {toast && (
          <div className="animate-fadeIn pointer-events-auto flex items-center gap-2 rounded-full bg-[var(--text)] text-[var(--bg)] px-4 py-2.5 text-sm font-semibold shadow-[var(--shadow-2)]">
            <Check className="w-4 h-4" />{toast}
          </div>
        )}
      </div>
    </section>
  );
}
