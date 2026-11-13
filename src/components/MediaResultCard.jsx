import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Check, 
  Copy, 
  ExternalLink, 
  CheckCircle2, 
  Image as ImageIcon, 
  Video, 
  Music,
  FileText,
  Layers, 
  Maximize2, 
  X,
  Play,
  Heart,
  MessageSquare,
  Share2,
  Bookmark,
  Repeat2,
  Eye,
  BadgeCheck,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Loader2,
  Sparkles,
  Archive,
  Mic,
  Volume2,
  Wand2
} from 'lucide-react';
import { 
  TwitterXIcon,
  YoutubeIcon, 
  FacebookIcon,
  InstagramIcon, 
  TiktokIcon,
  PinterestIcon,
  RedditIcon,
  ThreadsIcon,
  GlobeIcon
} from './BrandIcons.jsx';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

function formatMetricCount(val) {
  if (val === undefined || val === null || val === '') return null;
  if (typeof val === 'string' && (val.includes('K') || val.includes('M') || val.includes('B') || val.includes(','))) {
    return val;
  }
  const num = Number(val);
  if (isNaN(num) || num <= 0) return null;
  if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (num >= 1_000) return (num / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  return num.toLocaleString();
}

function formatDuration(sec) {
  if (!sec || isNaN(sec) || sec <= 0) return null;
  const s = Math.floor(sec);
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatBytes(bytes) {
  if (!bytes || isNaN(bytes) || bytes <= 0) return null;
  const mb = bytes / (1024 * 1024);
  if (mb >= 1000) {
    return (mb / 1024).toFixed(2) + ' GB';
  }
  return mb.toFixed(1) + ' MB';
}

function getPlatformIcon(platform) {
  const p = (platform || '').toLowerCase();
  if (p === 'twitter' || p === 'x') return TwitterXIcon;
  if (p === 'youtube') return YoutubeIcon;
  if (p === 'facebook') return FacebookIcon;
  if (p === 'instagram') return InstagramIcon;
  if (p === 'tiktok') return TiktokIcon;
  if (p === 'pinterest') return PinterestIcon;
  if (p === 'reddit') return RedditIcon;
  if (p === 'threads') return ThreadsIcon;
  return GlobeIcon;
}

function getValidImageUrl(val) {
  if (!val) return null;
  const str = typeof val === 'string' ? val : (val.url || val.streamUrl || val.thumbnail || '');
  if (!str || typeof str !== 'string') return null;
  // NEVER use download endpoints as inline image src
  if (str.includes('/download?') || str.includes('/api/download')) return null;
  if (str.startsWith('data:image/') || str.startsWith('http://') || str.startsWith('https://')) return str;
  if (str.startsWith('/api/proxy-image')) return `${BACKEND_BASE}${str}`;
  return str;
}

export default function MediaResultCard({ data, onReset }) {
  if (!data) return null;

  const platform = data.platform || 'social';
  const contentType = data.contentType || 'video';
  const title = data.title || 'Extracted Media';
  const caption = data.caption || data.description || title;
  const author = data.author || {};
  const authorName = author.displayName || author.name || 'Social Creator';
  const authorHandle = author.username || author.handle || authorName;
  const avatar = author.avatar || data.thumbnail;
  const publishedAt = data.publishedAt;
  const duration = data.duration;
  const stats = data.stats || data.metrics || {};
  const tags = data.tags || [];
  const hashtags = data.hashtags || [];
  const warnings = data.warnings || [];
  const isDegraded = data.status === 'degraded' || warnings.length > 0;

  const videos = Array.isArray(data.videos) && data.videos.length > 0 
    ? data.videos 
    : (Array.isArray(data.items) 
        ? data.items.flatMap(it => (it.variants || []).filter(v => v.kind === 'video')) 
        : []);

  const audios = Array.isArray(data.audios) && data.audios.length > 0 
    ? data.audios 
    : (Array.isArray(data.items) 
        ? data.items.flatMap(it => (it.variants || []).filter(v => v.kind === 'audio')) 
        : []);

  const rawImages = Array.isArray(data.images) && data.images.length > 0 
    ? data.images 
    : (Array.isArray(data.items) 
        ? data.items.flatMap(it => (it.variants || []).filter(v => v.kind === 'image')) 
        : []);

  const thumbnails = Array.isArray(data.thumbnails) ? data.thumbnails : [];
  const images = rawImages.length > 0 ? rawImages : thumbnails;
  const subtitles = Array.isArray(data.subtitles) ? data.subtitles : [];

  const hasVideos = videos.length > 0;
  const hasAudios = audios.length > 0;
  const hasImages = images.length > 0;
  const hasSubtitles = subtitles.length > 0;
  const isShortOrReel = contentType === 'short' || contentType === 'reel';
  const isImageOnly = !hasVideos && !hasAudios;

  const [activeTab, setActiveTab] = useState(() => {
    if (isImageOnly) return 'images';
    if (isShortOrReel && hasVideos) return 'shorts';
    if (hasVideos) return 'video';
    if (hasImages) return 'images';
    if (hasAudios) return 'audio';
    if (hasSubtitles) return 'subtitles';
    return hasVideos ? 'video' : 'images';
  });

  useEffect(() => {
    if (isImageOnly) {
      setActiveTab('images');
    } else if (isShortOrReel && hasVideos) {
      setActiveTab('shorts');
    } else if (hasVideos) {
      setActiveTab('video');
    } else if (hasImages) {
      setActiveTab('images');
    } else if (hasAudios) {
      setActiveTab('audio');
    }
  }, [data?.id, data?.url, hasVideos, hasAudios, isImageOnly]);

  const [previewMedia, setPreviewMedia] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [isCaptionExpanded, setIsCaptionExpanded] = useState(false);
  const [copiedCaption, setCopiedCaption] = useState(false);
  const [copiedTags, setCopiedTags] = useState(false);

  // AI Studio & Captions State
  const [aiData, setAiData] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [selectedVoice, setSelectedVoice] = useState('hi-IN-MadhurNeural');
  const [generatingVoice, setGeneratingVoice] = useState(false);
  const [voiceAudioUri, setVoiceAudioUri] = useState(null);
  const [copiedHookIdx, setCopiedHookIdx] = useState(null);
  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [copiedSocialSuite, setCopiedSocialSuite] = useState(false);

  const [activeJob, setActiveJob] = useState(null);
  const [jobError, setJobError] = useState(null);
  const [isZipping, setIsZipping] = useState(false);
  // Per-button download state: { key, progress (0-100 | null) }
  const [busyDownload, setBusyDownload] = useState(null);

  const viewsCount = formatMetricCount(stats.views);
  const likesCount = formatMetricCount(stats.likes);
  const commentsCount = formatMetricCount(stats.comments);
  const sharesCount = formatMetricCount(stats.shares);
  const savesCount = formatMetricCount(stats.saves);
  const repostsCount = formatMetricCount(stats.reposts || stats.retweets);
  const scoreCount = formatMetricCount(stats.score);
  const hasStats = Boolean(viewsCount || likesCount || commentsCount || sharesCount || savesCount || repostsCount || scoreCount);

  const PlatformIcon = getPlatformIcon(platform);

  const thumbToken = thumbnails[0]?.token || images[0]?.token;
  const directThumb = (thumbnails[0]?.url && thumbnails[0].url.startsWith('http') ? thumbnails[0].url : null)
    || (images[0]?.url && images[0].url.startsWith('http') ? images[0].url : null)
    || getValidImageUrl(data.thumbnail) 
    || getValidImageUrl(thumbnails[0]?.streamUrl)
    || getValidImageUrl(images[0]?.streamUrl)
    || getValidImageUrl(avatar);

  const mainThumbnail = directThumb || (thumbToken 
    ? `${BACKEND_BASE}/api/proxy-image?token=${encodeURIComponent(thumbToken)}`
    : null);

  async function fetchAiCaptions() {
    if (aiData || aiLoading) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const resp = await fetch(`${BACKEND_BASE}/api/ai/captions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: data.sourceUrl || data.url || '',
          title: title,
          caption: caption,
          platform: platform
        })
      });
      if (resp.ok) {
        const json = await resp.json();
        if (json.ok) {
          setAiData(json);
        } else {
          setAiError(json.error || 'Could not load AI subtitles.');
        }
      } else {
        setAiError('AI Subtitles service is busy.');
      }
    } catch (e) {
      setAiError('Failed to fetch AI captions.');
    } finally {
      setAiLoading(false);
    }
  }

  function downloadTextFile(content, filename, mimeType = 'text/plain') {
    if (!content) return;
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    setToastMessage(`Downloaded ${filename}!`);
    setTimeout(() => setToastMessage(''), 3000);
  }

  async function generateAiVoice() {
    const textToSpeak = aiData?.transcript || caption || title;
    if (!textToSpeak) return;
    setGeneratingVoice(true);
    try {
      const resp = await fetch(`${BACKEND_BASE}/api/ai/voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          voice: selectedVoice
        })
      });
      if (resp.ok) {
        const json = await resp.json();
        if (json.ok && json.data_uri) {
          setVoiceAudioUri(json.data_uri);
          setToastMessage('AI Voiceover generated successfully!');
          setTimeout(() => setToastMessage(''), 3000);
        } else {
          setToastMessage('Voice generation encountered an issue.');
          setTimeout(() => setToastMessage(''), 3000);
        }
      }
    } catch (e) {
      setToastMessage('Voice synthesis failed.');
      setTimeout(() => setToastMessage(''), 3000);
    } finally {
      setGeneratingVoice(false);
    }
  }


  useEffect(() => {
    if (!activeJob || activeJob.status === 'done' || activeJob.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`${BACKEND_BASE}/api/jobs/${activeJob.id}`);
        if (resp.ok) {
          const res = await resp.json();
          if (res.ok && res.job) {
            setActiveJob(prev => ({
              ...prev,
              status: res.job.status,
              progress: res.job.progress || 0
            }));

            if (res.job.status === 'done') {
              clearInterval(interval);
              setActiveJob(prev => ({ ...prev, status: 'done', progress: 100 }));
              window.location.href = `${BACKEND_BASE}/api/jobs/${activeJob.id}/file`;
              setToastMessage('Download started successfully!');
              setTimeout(() => setToastMessage(''), 4000);
              setTimeout(() => setActiveJob(null), 3000);
            } else if (res.job.status === 'failed') {
              clearInterval(interval);
              setJobError(res.job.error || 'Media processing encountered an issue.');
            }
          }
        }
      } catch (e) {
        // continue polling
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJob]);

  async function fetchWithProgress(fullUrl, key, fallbackName) {
    setJobError(null);
    setBusyDownload({ key, progress: null });
    try {
      const resp = await fetch(fullUrl);
      if (!resp.ok) {
        let message = 'We could not prepare this download. Please try again.';
        try {
          const j = await resp.json();
          message = (j.error && (j.error.message || j.error)) || message;
        } catch (_) { /* non-JSON error body */ }
        setJobError(typeof message === 'string' ? message : 'Download failed. Please try again.');
        return;
      }
      const total = Number(resp.headers.get('content-length')) || 0;
      const disposition = resp.headers.get('content-disposition') || '';
      const match = disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
      const filename = match ? decodeURIComponent(match[1]) : fallbackName;
      const reader = resp.body.getReader();
      const chunks = [];
      let received = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.length;
        if (total) setBusyDownload({ key, progress: Math.round((received / total) * 100) });
      }
      const blob = new Blob(chunks, { type: resp.headers.get('content-type') || 'application/octet-stream' });
      const href = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = href;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(href), 30000);
    } catch (e) {
      setJobError('Network problem while downloading. Please check your connection and try again.');
    } finally {
      setBusyDownload(null);
    }
  }

  function triggerDownload(item, key) {
    if (!item) return;
    const busyKey = key || item.downloadUrl || item.url || item.label;
    if (busyDownload) return;

    // Server-processed endpoints (video+audio / mp3): show spinner + progress, friendly errors
    if (item.downloadUrl && (item.downloadUrl.includes('/api/download_video') || item.downloadUrl.includes('/api/download_audio'))) {
      const fullUrl = item.downloadUrl.startsWith('http')
        ? item.downloadUrl
        : `${BACKEND_BASE}${item.downloadUrl.startsWith('/') ? '' : '/'}${item.downloadUrl}`;
      const isAudio = item.downloadUrl.includes('/api/download_audio');
      fetchWithProgress(fullUrl, busyKey, `${platform || 'ovd'}_${item.label || 'media'}.${isAudio ? 'mp3' : 'mp4'}`.replace(/[^a-zA-Z0-9._-]/g, '_'));
      return;
    }

    // Direct streams start immediately in the browser; brief spinner as click feedback
    setBusyDownload({ key: busyKey, progress: null });
    setTimeout(() => setBusyDownload(null), 2500);

    const rawUpstream = (typeof item.url === 'string' && item.url.startsWith('http')) 
      ? item.url 
      : ((typeof item.streamUrl === 'string' && item.streamUrl.startsWith('http')) ? item.streamUrl : null);

    const ext = item.ext || (item.kind === 'audio' ? 'mp3' : item.kind === 'image' ? 'jpg' : 'mp4');
    const cleanName = `${platform || 'ovd'}_${item.label || 'media'}.${ext}`.replace(/[^a-zA-Z0-9._-]/g, '_');

    if (item.token) {
      let downloadUrl = `${BACKEND_BASE}/api/download?token=${encodeURIComponent(item.token)}`;
      if (rawUpstream) {
        downloadUrl += `&url=${encodeURIComponent(rawUpstream)}`;
      }
      downloadUrl += `&filename=${encodeURIComponent(cleanName)}`;
      window.location.href = downloadUrl;
    } else if (item.downloadUrl) {
      const fullUrl = item.downloadUrl.startsWith('http')
        ? item.downloadUrl
        : `${BACKEND_BASE}${item.downloadUrl.startsWith('/') ? '' : '/'}${item.downloadUrl}`;
      window.location.href = fullUrl;
    } else if (rawUpstream) {
      window.location.href = `${BACKEND_BASE}/api/download?url=${encodeURIComponent(rawUpstream)}&filename=${encodeURIComponent(cleanName)}`;
    }
  }

  async function triggerMergeJob(videoItem) {
    setJobError(null);
    const videoToken = videoItem.token;
    const bestAudio = audios[0];
    const audioToken = bestAudio?.token;

    if (!videoToken) {
      triggerDownload(videoItem);
      return;
    }

    const tokens = [videoToken];
    if (audioToken) {
      tokens.push(audioToken);
    }

    try {
      setActiveJob({ id: 'pending', status: 'queued', progress: 10, action: 'merge' });
      const resp = await fetch(`${BACKEND_BASE}/api/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'merge', tokens })
      });

      if (resp.ok) {
        const json = await resp.json();
        if (json.ok && json.job_id) {
          setActiveJob({
            id: json.job_id,
            status: 'processing',
            progress: 25,
            action: 'merge'
          });
        } else {
          setJobError(json.error || 'Failed to start merge process.');
          setActiveJob(null);
        }
      } else {
        setJobError('Merge server busy. Initiating direct stream instead.');
        setActiveJob(null);
        triggerDownload(videoItem);
      }
    } catch (e) {
      setJobError('Could not start merge job. Downloading stream directly.');
      setActiveJob(null);
      triggerDownload(videoItem);
    }
  }

  async function triggerZipDownload() {
    setIsZipping(true);
    setJobError(null);
    const tokens = images.map(img => img.token).filter(Boolean);

    if (tokens.length === 0) {
      if (images[0]) triggerDownload(images[0]);
      setIsZipping(false);
      return;
    }

    try {
      const resp = await fetch(`${BACKEND_BASE}/api/zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tokens })
      });

      if (resp.ok) {
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${platform}_media_gallery.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setToastMessage('ZIP archive downloaded successfully!');
        setTimeout(() => setToastMessage(''), 4000);
      } else {
        setJobError('ZIP creation failed. Please download images individually.');
      }
    } catch (e) {
      setJobError('Error downloading ZIP archive.');
    } finally {
      setIsZipping(false);
    }
  }

  function handleCopyCaption() {
    if (!caption) return;
    navigator.clipboard.writeText(caption);
    setCopiedCaption(true);
    setTimeout(() => setCopiedCaption(false), 2000);
  }

  function handleCopyAllTags() {
    const allTags = [...tags, ...hashtags.map(h => (h.startsWith('#') ? h : `#${h}`))].join(' ');
    if (!allTags) return;
    navigator.clipboard.writeText(allTags);
    setCopiedTags(true);
    setTimeout(() => setCopiedTags(false), 2000);
  }

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8 animate-fadeIn">
      {/* Degraded Notice */}
      {isDegraded && (
        <div className="mb-4 p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-500" />
          <div className="text-xs">
            <p className="font-semibold">Platform Service Notice</p>
            <p className="opacity-90 mt-0.5">
              {warnings[0] || 'This platform is currently operating in fallback mode or experiencing rate restrictions. Downloads remain active.'}
            </p>
          </div>
        </div>
      )}

      {/* Main Container Card - Base Design System Surface Pattern */}
      <div className="bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] rounded-xl sm:rounded-2xl shadow-xs overflow-hidden transition-colors">
        
        {/* Header Summary Section */}
        <div className="p-5 sm:p-6 md:p-8 border-b border-[var(--border)]">
          <div className="flex flex-col md:flex-row gap-5 md:gap-6 items-start">
            
            {/* Visual Media Preview */}
            <div className="relative group w-full md:w-52 h-52 flex-shrink-0 rounded-xl overflow-hidden bg-[var(--bg-alt)] border border-[var(--border)]">
              {mainThumbnail ? (
                <img 
                  src={mainThumbnail} 
                  alt={title}
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  onError={(e) => {
                    const target = e.currentTarget;
                    if (target.dataset.hasFailed) {
                      target.style.display = 'none';
                      return;
                    }
                    target.dataset.hasFailed = 'true';

                    const currentSrc = target.src || '';
                    if (currentSrc.includes('maxresdefault.jpg')) {
                      target.src = currentSrc.replace('maxresdefault.jpg', 'hqdefault.jpg');
                      return;
                    }
                    if (currentSrc.includes('hqdefault.jpg')) {
                      target.src = currentSrc.replace('hqdefault.jpg', 'mqdefault.jpg');
                      return;
                    }

                    const safeAvatar = getValidImageUrl(avatar);
                    if (safeAvatar && target.src !== safeAvatar) {
                      target.src = safeAvatar;
                      return;
                    }

                    target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-[var(--text-muted)]">
                  <ImageIcon className="w-10 h-10 stroke-[1.5]" />
                  <span className="text-xs mt-1.5 font-medium">No Preview</span>
                </div>
              )}

              {/* Platform Chip Badge */}
              <div className="absolute top-2.5 left-2.5 bg-black/75 backdrop-blur-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 text-white text-xs font-semibold">
                <PlatformIcon className="w-3.5 h-3.5" />
                <span className="capitalize">{platform}</span>
              </div>

              {duration && (
                <div className="absolute bottom-2.5 right-2.5 bg-black/80 backdrop-blur-xs px-2 py-0.5 rounded text-white text-[11px] font-mono font-medium">
                  {formatDuration(duration)}
                </div>
              )}

              {mainThumbnail && (
                <button
                  type="button"
                  onClick={() => setPreviewMedia({ type: 'image', url: mainThumbnail, title })}
                  className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
                  aria-label="Enlarge image preview"
                >
                  <div className="p-2.5 bg-white/20 backdrop-blur-md rounded-full">
                    <Maximize2 className="w-4 h-4 text-white" />
                  </div>
                </button>
              )}
            </div>

            {/* Metadata & Author Details */}
            <div className="flex-1 min-w-0 flex flex-col justify-between self-stretch">
              <div>
                {/* Author Info & Reset */}
                <div className="flex items-center justify-between gap-3 mb-2.5">
                  <div className="flex items-center gap-2 min-w-0">
                    {avatar && (
                      <img 
                        src={avatar} 
                        alt={authorName} 
                        referrerPolicy="no-referrer"
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    )}
                    <div className="min-w-0 leading-tight">
                      <div className="flex items-center gap-1 font-semibold text-[var(--text)] text-sm truncate">
                        <span>{authorName}</span>
                        <BadgeCheck className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                      </div>
                      <p className="text-xs text-[var(--text-muted)] truncate">@{authorHandle}</p>
                    </div>
                  </div>

                  {onReset && (
                    <button
                      type="button"
                      onClick={onReset}
                      className="text-xs text-[var(--text-muted)] hover:text-[var(--text)] px-2.5 py-1 rounded-md border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--bg-alt)] transition-colors"
                    >
                      Search Again
                    </button>
                  )}
                </div>

                {/* Title */}
                <h2 className="text-base sm:text-lg font-bold text-[var(--text)] leading-snug line-clamp-2 mb-2">
                  {title}
                </h2>

                {/* Caption / Description Box */}
                {caption && (
                  <div className="mt-2 text-xs md:text-sm text-[var(--text)] bg-[var(--bg-alt)] p-3 rounded-lg border border-[var(--border)]">
                    <div className={`relative ${!isCaptionExpanded && caption.length > 200 ? 'line-clamp-2' : ''}`}>
                      <p className="whitespace-pre-line leading-relaxed">{caption}</p>
                    </div>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-[var(--border)]">
                      {caption.length > 200 ? (
                        <button
                          type="button"
                          onClick={() => setIsCaptionExpanded(!isCaptionExpanded)}
                          className="text-xs font-medium text-[var(--accent)] flex items-center gap-1"
                        >
                          {isCaptionExpanded ? <>Show less <ChevronUp className="w-3 h-3" /></> : <>Show full caption <ChevronDown className="w-3 h-3" /></>}
                        </button>
                      ) : <span />}
                      <button
                        type="button"
                        onClick={handleCopyCaption}
                        className="text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1 ml-auto"
                      >
                        {copiedCaption ? <><Check className="w-3 h-3 text-[var(--positive)]" /> Copied!</> : <><Copy className="w-3 h-3" /> Copy Caption</>}
                      </button>
                    </div>
                  </div>
                )}

                {/* Tags & Hashtags */}
                {(tags.length > 0 || hashtags.length > 0) && (
                  <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                    {hashtags.slice(0, 6).map((tag, i) => (
                      <span key={`ht_${i}`} className="text-xs px-2 py-0.5 rounded-md bg-[var(--accent-bg)] text-[var(--accent)] font-medium">
                        {tag.startsWith('#') ? tag : `#${tag}`}
                      </span>
                    ))}
                    {tags.slice(0, 4).map((tag, i) => (
                      <span key={`tg_${i}`} className="text-xs px-2 py-0.5 rounded-md bg-[var(--bg-alt)] border border-[var(--border)] text-[var(--text-muted)]">
                        {tag}
                      </span>
                    ))}
                    <button
                      type="button"
                      onClick={handleCopyAllTags}
                      className="text-xs text-[var(--text-muted)] hover:text-[var(--text)] ml-1 underline cursor-pointer"
                    >
                      {copiedTags ? 'Copied!' : 'Copy tags'}
                    </button>
                  </div>
                )}
              </div>

              {/* Stats Row (Honest metadata, omitting unavailable keys) */}
              {hasStats && (
                <div className="mt-3.5 pt-3 border-t border-[var(--border)] flex flex-wrap items-center gap-4 text-xs text-[var(--text-muted)] font-medium">
                  {viewsCount && (
                    <div className="flex items-center gap-1.5" title="Views">
                      <Eye className="w-3.5 h-3.5" />
                      <span>{viewsCount} views</span>
                    </div>
                  )}
                  {likesCount && (
                    <div className="flex items-center gap-1.5" title="Likes">
                      <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500/20" />
                      <span>{likesCount}</span>
                    </div>
                  )}
                  {commentsCount && (
                    <div className="flex items-center gap-1.5" title="Comments">
                      <MessageSquare className="w-3.5 h-3.5 text-blue-500" />
                      <span>{commentsCount}</span>
                    </div>
                  )}
                  {sharesCount && (
                    <div className="flex items-center gap-1.5" title="Shares">
                      <Share2 className="w-3.5 h-3.5 text-[var(--positive)]" />
                      <span>{sharesCount}</span>
                    </div>
                  )}
                  {savesCount && (
                    <div className="flex items-center gap-1.5" title="Saves">
                      <Bookmark className="w-3.5 h-3.5 text-amber-500" />
                      <span>{savesCount}</span>
                    </div>
                  )}
                  {repostsCount && (
                    <div className="flex items-center gap-1.5" title="Reposts">
                      <Repeat2 className="w-3.5 h-3.5 text-indigo-500" />
                      <span>{repostsCount}</span>
                    </div>
                  )}
                  {scoreCount && (
                    <div className="flex items-center gap-1.5" title="Score">
                      <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                      <span>{scoreCount} pts</span>
                    </div>
                  )}
                  {publishedAt && (
                    <span className="text-[11px] text-[var(--text-muted)] ml-auto">
                      {new Date(publishedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Elevated Segmented Tabs - Spectra UI / Radix Benchmark */}
        <div className="border-b border-[var(--border)] bg-[var(--bg-alt)]/40 px-4 sm:px-6 py-2.5">
          <div className="inline-flex items-center gap-1 bg-[var(--bg-alt)] p-1 rounded-xl border border-[var(--border)] max-w-full overflow-x-auto no-scrollbar">
            
            {hasVideos && !isShortOrReel && (
              <button
                type="button"
                onClick={() => setActiveTab('video')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'video'
                    ? 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <Video className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Video Formats</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[var(--bg)] border border-[var(--border)] text-[var(--text-muted)]">
                  {videos.length}
                </span>
              </button>
            )}

            {isShortOrReel && hasVideos && (
              <button
                type="button"
                onClick={() => setActiveTab('shorts')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'shorts'
                    ? 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                <span>Reel / Short Quality</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[var(--bg)] border border-[var(--border)] text-[var(--text-muted)]">
                  {videos.length}
                </span>
              </button>
            )}

            {hasImages && (
              <button
                type="button"
                onClick={() => setActiveTab('images')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'images'
                    ? 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <ImageIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>Thumbnails & Photos</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[var(--bg)] border border-[var(--border)] text-[var(--text-muted)]">
                  {images.length}
                </span>
              </button>
            )}

            {hasAudios && (
              <button
                type="button"
                onClick={() => setActiveTab('audio')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'audio'
                    ? 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <Music className="w-3.5 h-3.5 text-[var(--positive)]" />
                <span>Audio Only</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[var(--bg)] border border-[var(--border)] text-[var(--text-muted)]">
                  {audios.length}
                </span>
              </button>
            )}

            {hasSubtitles && (
              <button
                type="button"
                onClick={() => setActiveTab('subtitles')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'subtitles'
                    ? 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                <span>Subtitles</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-[var(--bg)] border border-[var(--border)] text-[var(--text-muted)]">
                  {subtitles.length}
                </span>
              </button>
            )}

            {/* AI Captions & Subtitles Tab - Only for video/audio content, not for image-only URLs */}
            {!isImageOnly && (hasVideos || hasAudios) && (
              <button
                type="button"
                onClick={() => {
                  setActiveTab('ai_captions');
                  fetchAiCaptions();
                }}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === 'ai_captions'
                    ? 'bg-purple-600 text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface)]/50'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
                <span>AI Captions & Subtitles</span>
                <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                  activeTab === 'ai_captions' ? 'bg-white/20 text-white' : 'bg-purple-500/10 border border-purple-500/30 text-purple-500'
                }`}>
                  AI Studio
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Processing Job Alert - Auto-dismisses and shows CheckCircle when done */}
        {activeJob && (
          <div className={`p-3.5 border-b text-[var(--text)] flex items-center justify-between gap-4 transition-all duration-300 ${
            activeJob.status === 'done' 
              ? 'bg-[var(--positive-bg)] border-[var(--positive)]/30' 
              : 'bg-[var(--accent-bg)] border-[var(--accent)]/20'
          }`}>
            <div className="flex items-center gap-2.5">
              {activeJob.status === 'done' ? (
                <CheckCircle2 className="w-4 h-4 text-[var(--positive)] shrink-0" />
              ) : (
                <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin shrink-0" />
              )}
              <div>
                <p className="text-xs sm:text-sm font-semibold">
                  {activeJob.status === 'done' 
                    ? 'Media Merged & Ready! Downloading to device...' 
                    : (activeJob.action === 'merge' ? 'Preparing your HD video...' : 'Preparing your download...')}
                </p>
                <p className="text-xs text-[var(--text-muted)]">
                  {activeJob.status === 'done' ? 'Completed 100%' : `Status: ${activeJob.status} (${activeJob.progress}%)`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-24 sm:w-28 bg-[var(--border)] h-1.5 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-300 ${
                    activeJob.status === 'done' ? 'bg-[var(--positive)]' : 'bg-[var(--accent)]'
                  }`}
                  style={{ width: `${activeJob.progress}%` }}
                />
              </div>
              <button
                type="button"
                onClick={() => setActiveJob(null)}
                className="text-[var(--text-muted)] hover:text-[var(--text)] p-1 rounded transition-colors cursor-pointer"
                aria-label="Dismiss alert"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Job Error Alert */}
        {jobError && (
          <div className="p-3 bg-[var(--negative-bg)] border-b border-[var(--negative)]/20 text-[var(--negative)] text-xs flex items-center justify-between">
            <span>{jobError}</span>
            <button 
              type="button" 
              onClick={() => setJobError(null)}
              className="text-xs font-semibold underline ml-2 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tab Content Panes */}
        <div className="p-4 sm:p-6 md:p-8">
          
          {/* 1. Video / Shorts Tab */}
          {(activeTab === 'video' || activeTab === 'shorts') && hasVideos && (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  Available Video Formats
                </h3>
                <span className="text-xs text-[var(--text-muted)]">
                  Direct High-Speed Stream
                </span>
              </div>

              <div className="overflow-hidden border border-[var(--border)] rounded-xl divide-y divide-[var(--border)]">
                {videos.map((vid, idx) => {
                  const isRecommended = idx === 0 || vid.label?.includes('1080');
                  const hasAudio = vid.hasAudio !== false;
                  const needsMerge = vid.needsMerge === true;
                  const ext = (vid.ext || 'mp4').toUpperCase();
                  const sizeFormatted = formatBytes(vid.filesize);

                  return (
                    <div 
                      key={`vid_${idx}`}
                      className="p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:bg-[var(--bg-alt)]/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-[var(--bg-alt)] border border-[var(--border)] text-[var(--text)]">
                          <Video className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[var(--text)] text-sm sm:text-base">
                              {vid.label || vid.quality || `${vid.height || 720}p`}
                            </span>
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--bg-alt)] border border-[var(--border)] text-[var(--text-muted)]">
                              {ext}
                            </span>
                            {isRecommended && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[var(--positive-bg)] text-[var(--positive)] border border-[var(--positive)]/30">
                                Recommended
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2 mt-0.5 text-xs text-[var(--text-muted)]">
                            {vid.fps && <span>{vid.fps} FPS</span>}
                            {vid.fps && sizeFormatted && <span>&bull;</span>}
                            {sizeFormatted && <span>{sizeFormatted}</span>}
                            <span>&bull;</span>
                            {needsMerge ? (
                              <span className="text-[var(--positive)] font-medium">HD with audio</span>
                            ) : hasAudio ? (
                              <span className="text-[var(--positive)] font-medium">Audio included</span>
                            ) : (
                              <span className="text-[var(--text-muted)]">Video only</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Download Buttons - Base Design System Actions */}
                      <div className="w-full sm:w-auto flex items-center gap-2">
                        {needsMerge ? (
                          <button
                            type="button"
                            onClick={() => triggerMergeJob(vid)}
                            disabled={!!activeJob}
                            aria-busy={!!activeJob}
                            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 disabled:opacity-60 font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-opacity"
                          >
                            {activeJob ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                            <span>{activeJob ? 'Preparing...' : `Download (${ext})`}</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => triggerDownload(vid, `vid_${idx}`)}
                            disabled={!!busyDownload}
                            aria-busy={busyDownload?.key === `vid_${idx}`}
                            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 disabled:opacity-60 font-semibold text-xs sm:text-sm flex items-center justify-center gap-1.5 shadow-xs transition-opacity"
                          >
                            {busyDownload?.key === `vid_${idx}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                            <span>
                              {busyDownload?.key === `vid_${idx}`
                                ? (busyDownload.progress != null ? `Downloading ${busyDownload.progress}%` : 'Preparing...')
                                : `Download (${ext})`}
                            </span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 2. Thumbnails & Photos Tab */}
          {activeTab === 'images' && hasImages && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-2">
                <div>
                  <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
                    Thumbnails & Original Photos
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">
                    Save individual stills or export all as a ZIP archive
                  </p>
                </div>
                
                {images.length > 1 && (
                  <button
                    type="button"
                    onClick={triggerZipDownload}
                    disabled={isZipping}
                    className="px-3.5 py-1.5 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 font-semibold text-xs flex items-center gap-1.5 transition-opacity disabled:opacity-50"
                  >
                    {isZipping ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Archive className="w-3.5 h-3.5" />}
                    <span>{isZipping ? 'Creating ZIP...' : 'Download All (ZIP)'}</span>
                  </button>
                )}
              </div>

              {/* Grid of Images */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
                {images.map((img, idx) => {
                  const directHttp = (typeof img.url === 'string' && img.url.startsWith('http')) 
                    ? img.url 
                    : ((typeof img.streamUrl === 'string' && img.streamUrl.startsWith('http')) ? img.streamUrl : null);
                  const proxyUrl = img.token 
                    ? `${BACKEND_BASE}/api/proxy-image?token=${encodeURIComponent(img.token)}`
                    : (directHttp ? `${BACKEND_BASE}/api/proxy-image?url=${encodeURIComponent(directHttp)}` : null);
                  const imgUrl = directHttp || proxyUrl;

                  return (
                    <div 
                      key={`img_${idx}`}
                      className="group bg-[var(--bg-alt)] border border-[var(--border)] rounded-xl overflow-hidden flex flex-col justify-between transition-colors"
                    >
                      <div className="relative aspect-video overflow-hidden bg-[var(--bg-alt)]">
                        {imgUrl ? (
                          <img 
                            src={imgUrl} 
                            alt={img.label || `Image ${idx + 1}`}
                            referrerPolicy="no-referrer"
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                            loading="lazy"
                            onError={(e) => {
                              const target = e.currentTarget;
                              if (!target.dataset.triedProxy && proxyUrl && target.src !== proxyUrl) {
                                target.dataset.triedProxy = 'true';
                                target.src = proxyUrl;
                                return;
                              }
                            }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-[var(--text-muted)] bg-[var(--bg-alt)]">
                            <ImageIcon className="w-8 h-8 opacity-40" />
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => setPreviewMedia({ type: 'image', url: imgUrl, title: img.label })}
                          className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
                          aria-label="Preview full size"
                        >
                          <Maximize2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="p-3 flex items-center justify-between gap-2 border-t border-[var(--border)]">
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-[var(--text)] truncate">
                            {img.label || `Photo ${idx + 1}`}
                          </p>
                          <p className="text-[10px] text-[var(--text-muted)] font-mono">
                            {img.width && img.height ? `${img.width}x${img.height}` : (img.ext || 'JPG').toUpperCase()}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => triggerDownload(img)}
                          className="p-1.5 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 transition-opacity shrink-0"
                          aria-label={`Download image ${idx + 1}`}
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 3. Audio Tab */}
          {activeTab === 'audio' && hasAudios && (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  Audio Tracks & Streams
                </h3>
                <span className="text-xs text-[var(--text-muted)]">
                  High-Bitrate Audio
                </span>
              </div>

              <div className="overflow-hidden border border-[var(--border)] rounded-xl divide-y divide-[var(--border)]">
                {audios.map((aud, idx) => {
                  const ext = (aud.ext || 'm4a').toUpperCase();
                  const sizeFormatted = formatBytes(aud.filesize);

                  return (
                    <div 
                      key={`aud_${idx}`}
                      className="p-3.5 sm:p-4 flex items-center justify-between gap-3 hover:bg-[var(--bg-alt)]/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-[var(--bg-alt)] border border-[var(--border)] text-[var(--text)]">
                          <Music className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[var(--text)] text-sm">
                              {aud.label || `Audio Track ${idx + 1}`}
                            </span>
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--bg-alt)] border border-[var(--border)] text-[var(--text-muted)]">
                              {ext}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-0.5 text-xs text-[var(--text-muted)]">
                            {aud.bitrate && <span>{aud.bitrate} kbps</span>}
                            {aud.bitrate && sizeFormatted && <span>&bull;</span>}
                            {sizeFormatted && <span>{sizeFormatted}</span>}
                          </div>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => triggerDownload(aud, `aud_${idx}`)}
                        disabled={!!busyDownload}
                        aria-busy={busyDownload?.key === `aud_${idx}`}
                        className="px-3.5 py-1.5 rounded-lg bg-[var(--positive)] text-white hover:opacity-90 disabled:opacity-60 font-semibold text-xs flex items-center gap-1.5 transition-opacity shadow-xs"
                      >
                        {busyDownload?.key === `aud_${idx}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                        <span>{busyDownload?.key === `aud_${idx}` ? (busyDownload.progress != null ? `${busyDownload.progress}%` : 'Preparing...') : 'Download Audio'}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 4. Subtitles Tab */}
          {activeTab === 'subtitles' && hasSubtitles && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">
                Closed Captions & Subtitles
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {subtitles.map((sub, idx) => (
                  <div 
                    key={`sub_${idx}`}
                    className="p-3 bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                      <div>
                        <p className="text-xs font-semibold text-[var(--text)]">{sub.lang || 'Subtitle'}</p>
                        <p className="text-[10px] text-[var(--text-muted)] font-mono">{(sub.ext || 'vtt').toUpperCase()}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => triggerDownload(sub)}
                      className="p-1.5 rounded-md bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 text-xs font-semibold"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. AI Captions, Subtitles & Voice Studio Tab (Only for Video/Audio media) */}
          {activeTab === 'ai_captions' && !isImageOnly && (
            <div className="space-y-6">
              {/* Header Banner */}
              <div className="p-4 sm:p-5 rounded-xl bg-gradient-to-r from-purple-500/10 via-indigo-500/10 to-transparent border border-purple-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-purple-500 text-white shrink-0 shadow-md">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm sm:text-base font-bold text-[var(--text)] flex items-center gap-2">
                      <span>AI Subtitles, Captions & Voice Studio</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                        aiData?.is_real_speech 
                          ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' 
                          : 'bg-purple-500/20 text-purple-600 dark:text-purple-300 border-purple-500/30'
                      }`}>
                        {aiData?.is_real_speech ? '⚡ Real Spoken Dialogue' : '🤖 AI Dialogue Breakdown'}
                      </span>
                    </h3>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      {aiData?.is_real_speech 
                        ? 'Verified spoken dialogue extracted directly from video speech audio.' 
                        : 'Export synced subtitles for Premiere/CapCut, read transcripts, copy viral social hooks, or generate AI voiceovers.'}
                    </p>
                  </div>
                </div>

                {!aiLoading && (
                  <button
                    type="button"
                    onClick={fetchAiCaptions}
                    className="px-3 py-1.5 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-xs font-semibold hover:bg-[var(--bg-alt)] transition-colors shrink-0 flex items-center gap-1.5"
                  >
                    <Wand2 className="w-3.5 h-3.5 text-purple-500" />
                    <span>Regenerate AI</span>
                  </button>
                )}
              </div>

              {/* Loading State */}
              {aiLoading && (
                <div className="p-8 text-center bg-[var(--bg-alt)]/50 border border-[var(--border)] rounded-xl space-y-3">
                  <Loader2 className="w-7 h-7 text-purple-500 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-[var(--text)]">
                    Analyzing speech & transcribing media...
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">
                    Extracting synchronized speech lines, timestamps, viral hooks, and subtitle tracks.
                  </p>
                </div>
              )}

              {/* Error State */}
              {aiError && !aiLoading && (
                <div className="p-4 bg-[var(--negative-bg)] border border-[var(--negative)]/30 rounded-xl text-xs text-[var(--negative)] flex items-center justify-between">
                  <span>{aiError}</span>
                  <button
                    type="button"
                    onClick={fetchAiCaptions}
                    className="font-bold underline ml-2 cursor-pointer"
                  >
                    Try Again
                  </button>
                </div>
              )}

              {/* Loaded Content */}
              {aiData && !aiLoading && (
                <div className="space-y-6">

                  {/* 5 Core Action Buttons Requested by User */}
                  <div>
                    <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5">
                      Instant Download & Export Actions
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">

                      {/* 1. Download .SRT */}
                      <button
                        type="button"
                        onClick={() => downloadTextFile(aiData.srt, `${(title || 'captions').slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_')}.srt`, 'text/plain')}
                        className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-purple-500/50 hover:bg-purple-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                            <Download className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm font-bold text-[var(--text)]">📥 Download .SRT Subtitles</p>
                            <p className="text-[10px] text-[var(--text-muted)]">SubRip format for Premiere & CapCut</p>
                          </div>
                        </div>
                      </button>

                      {/* 2. Download .VTT */}
                      <button
                        type="button"
                        onClick={() => downloadTextFile(aiData.vtt, `${(title || 'captions').slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_')}.vtt`, 'text/vtt')}
                        className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                            <Download className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm font-bold text-[var(--text)]">📥 Download .VTT Subtitles</p>
                            <p className="text-[10px] text-[var(--text-muted)]">WebVTT format for web & players</p>
                          </div>
                        </div>
                      </button>

                      {/* 3. Download Transcript (.TXT) */}
                      <button
                        type="button"
                        onClick={() => downloadTextFile(aiData.transcript, `${(title || 'transcript').slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_')}_transcript.txt`, 'text/plain')}
                        className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-blue-500/50 hover:bg-blue-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm font-bold text-[var(--text)]">📄 Download Transcript (.TXT)</p>
                            <p className="text-[10px] text-[var(--text-muted)]">Full readable text file</p>
                          </div>
                        </div>
                      </button>

                      {/* 4. Copy Viral Captions & Hashtags */}
                      <button
                        type="button"
                        onClick={() => {
                          const fullCopy = `${aiData.caption}\n\n${aiData.hashtags}`;
                          navigator.clipboard.writeText(fullCopy);
                          setCopiedSocialSuite(true);
                          setToastMessage('Copied Viral Caption & Hashtags!');
                          setTimeout(() => {
                            setCopiedSocialSuite(false);
                            setToastMessage('');
                          }, 3000);
                        }}
                        className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                            {copiedSocialSuite ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm font-bold text-[var(--text)]">📋 Copy Viral Captions & Tags</p>
                            <p className="text-[10px] text-[var(--text-muted)]">{copiedSocialSuite ? 'Copied to clipboard!' : 'Ready-to-paste social post'}</p>
                          </div>
                        </div>
                      </button>

                      {/* 5. Generate AI Voiceover (MP3) */}
                      <button
                        type="button"
                        onClick={generateAiVoice}
                        disabled={generatingVoice}
                        className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-amber-500/50 hover:bg-amber-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                            {generatingVoice ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
                          </div>
                          <div>
                            <p className="text-xs sm:text-sm font-bold text-[var(--text)]">🎙️ Generate AI Voiceover (MP3)</p>
                            <p className="text-[10px] text-[var(--text-muted)]">
                              {generatingVoice ? 'Synthesizing neural audio...' : 'Convert transcript into spoken MP3'}
                            </p>
                          </div>
                        </div>
                      </button>

                      {/* 6. Download Original Video Audio (MP3) */}
                      {hasAudios && audios[0] && (
                        <button
                          type="button"
                          onClick={() => triggerDownload(audios[0])}
                          className="p-3 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-left flex items-center justify-between group cursor-pointer"
                        >
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                              <Music className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="text-xs sm:text-sm font-bold text-[var(--text)]">🎵 Original Audio (MP3)</p>
                              <p className="text-[10px] text-[var(--text-muted)]">Download original video sound</p>
                            </div>
                          </div>
                        </button>
                      )}

                    </div>
                  </div>

                  {/* Audio Player if generated */}
                  {voiceAudioUri && (
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-fadeIn">
                      <div className="flex items-center gap-3">
                        <Volume2 className="w-5 h-5 text-amber-500 shrink-0" />
                        <div>
                          <p className="text-xs sm:text-sm font-bold text-[var(--text)]">AI Voiceover Track Ready</p>
                          <p className="text-[10px] text-[var(--text-muted)]">Preview audio or download directly as MP3</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 w-full sm:w-auto">
                        <audio controls src={voiceAudioUri} className="h-8 max-w-xs" />
                        <a
                          href={voiceAudioUri}
                          download={`${(title || 'voiceover').slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_')}_ai.mp3`}
                          className="px-3 py-1.5 rounded-lg bg-amber-500 text-white hover:opacity-90 text-xs font-bold flex items-center gap-1 shrink-0"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>MP3</span>
                        </a>
                      </div>
                    </div>
                  )}

                  {/* Section: Spoken Transcript View */}
                  <div className="bg-[var(--bg-alt)] border border-[var(--border)] rounded-xl p-4 sm:p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-[var(--text)] uppercase tracking-wider flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-purple-500" />
                        <span>Spoken Video Transcript</span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono font-normal">
                          ({aiData.transcript.split(/\s+/).length} words)
                        </span>
                      </h4>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(aiData.transcript);
                          setCopiedTranscript(true);
                          setToastMessage('Transcript copied to clipboard!');
                          setTimeout(() => setCopiedTranscript(false), 3000);
                        }}
                        className="px-2.5 py-1 rounded bg-[var(--surface)] border border-[var(--border)] text-[10px] font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1 cursor-pointer"
                      >
                        {copiedTranscript ? <Check className="w-3 h-3 text-[var(--positive)]" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedTranscript ? 'Copied' : 'Copy Text'}</span>
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-xs text-[var(--text)] leading-relaxed select-text font-sans">
                      {aiData.transcript}
                    </div>
                  </div>

                  {/* Section: 3 Viral Opening Hooks */}
                  {Array.isArray(aiData.hooks) && aiData.hooks.length > 0 && (
                    <div className="space-y-2.5">
                      <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
                        ⚡ 3 Viral Opening Hooks (For Reels & Shorts)
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                        {aiData.hooks.map((hook, hIdx) => (
                          <div 
                            key={`hook_${hIdx}`}
                            className="p-3.5 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] flex flex-col justify-between gap-3 hover:border-purple-500/40 transition-colors"
                          >
                            <p className="text-xs text-[var(--text)] font-medium leading-snug">
                              &ldquo;{hook}&rdquo;
                            </p>
                            <button
                              type="button"
                              onClick={() => {
                                navigator.clipboard.writeText(hook);
                                setCopiedHookIdx(hIdx);
                                setToastMessage(`Copied Hook #${hIdx + 1}!`);
                                setTimeout(() => setCopiedHookIdx(null), 3000);
                              }}
                              className="self-end px-2.5 py-1 rounded bg-[var(--surface)] border border-[var(--border)] text-[10px] font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1 cursor-pointer"
                            >
                              {copiedHookIdx === hIdx ? <Check className="w-3 h-3 text-[var(--positive)]" /> : <Copy className="w-3 h-3" />}
                              <span>{copiedHookIdx === hIdx ? 'Copied' : 'Copy Hook'}</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Section: Voiceover Voice Selector */}
                  <div className="p-4 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <h4 className="text-xs font-bold text-[var(--text)]">AI Voice Character</h4>
                      <p className="text-[10px] text-[var(--text-muted)]">Select neural narrator voice for audio dubbing</p>
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <select
                        value={selectedVoice}
                        onChange={(e) => setSelectedVoice(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-xs font-semibold text-[var(--text)] cursor-pointer focus:outline-hidden w-full sm:w-auto"
                      >
                        <option value="hi-IN-MadhurNeural">🇮🇳 Madhur (Hindi Male - Energetic)</option>
                        <option value="hi-IN-SwaraNeural">🇮🇳 Swara (Hindi Female - Smooth)</option>
                        <option value="en-IN-PrabhatNeural">🇮🇳 Prabhat (Indian English Male - Tech)</option>
                        <option value="en-IN-NeerjaNeural">🇮🇳 Neerja (Indian English Female - Pro)</option>
                        <option value="en-US-ChristopherNeural">🇺🇸 Christopher (US Male - Cinematic)</option>
                        <option value="en-US-JennyNeural">🇺🇸 Jenny (US Female - Friendly)</option>
                      </select>
                      <button
                        type="button"
                        onClick={generateAiVoice}
                        disabled={generatingVoice}
                        className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shrink-0 transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                      >
                        {generatingVoice ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Mic className="w-3.5 h-3.5" />}
                        <span>Synthesize</span>
                      </button>
                    </div>
                  </div>

                </div>
              )}

            </div>
          )}

        </div>

      </div>

      {/* Lightbox Modal */}
      {previewMedia && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setPreviewMedia(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh] flex flex-col items-center" onClick={e => e.stopPropagation()}>
            <button
              type="button"
              onClick={() => setPreviewMedia(null)}
              className="absolute -top-10 right-0 p-1.5 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors"
              aria-label="Close preview"
            >
              <X className="w-5 h-5" />
            </button>
            <img 
              src={previewMedia.url} 
              alt={previewMedia.title || 'Preview'} 
              className="max-h-[80vh] w-auto rounded-xl object-contain shadow-2xl"
            />
            {previewMedia.title && (
              <p className="text-white/90 text-xs mt-2.5 font-medium text-center">{previewMedia.title}</p>
            )}
          </div>
        </div>
      )}

      {/* Feedback Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-2.5 bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] text-xs font-semibold rounded-xl shadow-lg flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-[var(--positive)]" />
          <span>{toastMessage}</span>
        </div>
      )}

    </div>
  );
}
