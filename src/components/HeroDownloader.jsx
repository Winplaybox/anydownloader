import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Download, 
  Clipboard, 
  X, 
  Loader2, 
  AlertCircle,
  RefreshCw,
  Sparkles,
  AlertTriangle,
  Check
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
import { normalizeUrl } from '../utils/normalizeUrl.js';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

const DEFAULT_PLATFORMS = [
  { id: 'all', name: 'Auto-Detect', icon: null, status: 'ok', tier: 'A', seo: { slug: '' } },
  { id: 'twitter', name: 'X (Twitter)', icon: TwitterXIcon, status: 'ok', tier: 'A', seo: { slug: 'twitter-video-downloader' } },
  { id: 'youtube', name: 'YouTube', icon: YoutubeIcon, status: 'ok', tier: 'A', seo: { slug: 'youtube-video-downloader' } },
  { id: 'facebook', name: 'Facebook', icon: FacebookIcon, status: 'ok', tier: 'A', seo: { slug: 'facebook-video-downloader' } },
  { id: 'instagram', name: 'Instagram', icon: InstagramIcon, status: 'ok', tier: 'A', seo: { slug: 'instagram-video-downloader' } },
  { id: 'tiktok', name: 'TikTok', icon: TiktokIcon, status: 'ok', tier: 'A', seo: { slug: 'tiktok-video-downloader' } },
  { id: 'pinterest', name: 'Pinterest', icon: PinterestIcon, status: 'ok', tier: 'A', seo: { slug: 'pinterest-video-downloader' } },
  { id: 'reddit', name: 'Reddit', icon: RedditIcon, status: 'ok', tier: 'A', seo: { slug: 'reddit-video-downloader' } },
  { id: 'threads', name: 'Threads', icon: ThreadsIcon, status: 'ok', tier: 'A', seo: { slug: 'threads-video-downloader' } },
  { id: 'generic', name: 'Any Website', icon: GlobeIcon, status: 'beta', tier: 'B', seo: { slug: 'any-website-downloader' } }
];

function getIconForPlatform(id) {
  const p = (id || '').toLowerCase();
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

export default function HeroDownloader({ 
  url = '', 
  setUrl = () => {}, 
  onFetch = () => {}, 
  loading = false, 
  error = '',
  errorCode = null,
  onClear = () => {},
  activeCategory = 'all',
  setActiveCategory = () => {},
  pageH1 = null,
  pageDesc = null
}) {
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  const [platformList, setPlatformList] = useState(DEFAULT_PLATFORMS);
  const [pasteNotice, setPasteNotice] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState(null);
  const [wakeNotice, setWakeNotice] = useState('');
  const [clipboardPasted, setClipboardPasted] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth >= 768 && inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Fetch dynamic registry & health from /api/platforms
  useEffect(() => {
    let isMounted = true;
    async function loadPlatforms() {
      try {
        const resp = await fetch(`${BACKEND_BASE}/api/platforms`);
        if (resp.ok) {
          const data = await resp.json();
          if (data && Array.isArray(data.platforms) && isMounted) {
            const dynamicList = [
              { id: 'all', name: 'Auto-Detect', icon: null, status: 'ok', tier: 'A' },
              ...data.platforms.map(p => ({
                id: p.id,
                name: p.name || p.id,
                tier: p.tier || 'A',
                status: p.status || (p.tier === 'B' ? 'beta' : 'ok'),
                icon: getIconForPlatform(p.id),
                seo: p.seo || { slug: `${p.id}-video-downloader` }
              }))
            ];
            setPlatformList(dynamicList);
          }
        }
      } catch (e) {
        // Fallback to default platforms
      }
    }
    loadPlatforms();
    return () => { isMounted = false; };
  }, []);

  // Cold start feedback
  useEffect(() => {
    let timer;
    if (loading) {
      timer = setTimeout(() => {
        setWakeNotice('Extractor engine is resolving streams and metadata...');
      }, 2500);
    } else {
      setWakeNotice('');
    }
    return () => clearTimeout(timer);
  }, [loading]);

  // URL auto-detect & platform switch
  useEffect(() => {
    if (url && typeof url === 'string' && url.trim().length > 4) {
      const norm = normalizeUrl(url);
      if (norm.ok && norm.platform) {
        setDetectedPlatform(norm.platform);
        if (norm.multipleFound) {
          setPasteNotice('Multiple links found. Using the first URL.');
        } else {
          setPasteNotice('');
        }

        if (activeCategory && activeCategory !== 'all' && norm.platform !== 'generic' && norm.platform !== activeCategory) {
          if (typeof setActiveCategory === 'function') {
            setActiveCategory(norm.platform);
          }
        }
      } else {
        setDetectedPlatform(null);
      }
    } else {
      setDetectedPlatform(null);
      setPasteNotice('');
    }
  }, [url, activeCategory, setActiveCategory]);

  // Handle Paste
  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        const clean = text.trim();
        setUrl(clean);
        setClipboardPasted(true);
        setTimeout(() => setClipboardPasted(false), 2000);

        const norm = normalizeUrl(clean);
        if (norm.ok) {
          setDetectedPlatform(norm.platform);
          if (activeCategory && activeCategory !== 'all' && norm.platform !== 'generic' && norm.platform !== activeCategory) {
            if (typeof setActiveCategory === 'function') {
              setActiveCategory(norm.platform);
            }
          }
        }

        // Auto-extract immediately on paste passing the clean URL
        if (typeof onFetch === 'function') {
          onFetch(clean);
        }
      }
    } catch (e) {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (typeof onFetch === 'function') {
        onFetch(url);
      }
    }
  }

  function handleChipClick(platformItem) {
    const pId = platformItem.id;
    if (typeof setActiveCategory === 'function') {
      setActiveCategory(pId);
    }

    if (location.pathname === '/') {
      return;
    }

    if (pId === 'all') {
      navigate('/');
    } else if (platformItem.seo?.slug) {
      navigate(`/${platformItem.seo.slug}`);
    } else {
      navigate(`/${pId}-video-downloader`);
    }
  }

  const path = location.pathname.toLowerCase();
  let routePlatform = 'all';
  if (path.includes('twitter') || path.includes('/x')) routePlatform = 'twitter';
  else if (path.includes('youtube')) routePlatform = 'youtube';
  else if (path.includes('facebook')) routePlatform = 'facebook';
  else if (path.includes('instagram')) routePlatform = 'instagram';
  else if (path.includes('tiktok')) routePlatform = 'tiktok';
  else if (path.includes('pinterest')) routePlatform = 'pinterest';
  else if (path.includes('reddit')) routePlatform = 'reddit';
  else if (path.includes('threads')) routePlatform = 'threads';
  else if (path.includes('any-website') || path.includes('website')) routePlatform = 'generic';

  const currentActivePlatform = detectedPlatform || (activeCategory !== 'all' ? activeCategory : routePlatform) || 'all';
  const activePlatformData = platformList.find(p => p.id === currentActivePlatform);
  const isPlatformDegraded = activePlatformData?.status === 'degraded';

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pt-10 pb-6">
      
      {/* Title & Description */}
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-[var(--text)] tracking-tight leading-tight">
          {pageH1 || 'Download Social Videos & Photos'}
        </h1>
        <p className="mt-3 text-sm sm:text-base md:text-lg text-[var(--text-muted)] max-w-2xl mx-auto">
          {pageDesc || 'Fast, 100% free extractor for Twitter, YouTube, Instagram, TikTok, Facebook, Reddit, Pinterest, and any website.'}
        </p>
      </div>

      {/* Main Search / URL Box - Base Design System Input Pattern */}
      <div className="relative bg-[var(--surface)] border border-[var(--border)] focus-within:border-[var(--border-strong)] rounded-xl shadow-xs transition-colors">
        <div className="flex items-center p-1.5 sm:p-2">
          <input
            ref={inputRef}
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste media link here (YouTube, Twitter, TikTok, Instagram...)"
            className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-transparent text-[var(--text)] placeholder-[var(--text-muted)] text-sm sm:text-base outline-none"
            aria-label="Social media post or video URL"
          />

          {/* Action buttons */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {url ? (
              <button
                type="button"
                onClick={onClear}
                className="p-2 text-[var(--text-muted)] hover:text-[var(--text)] rounded-lg transition-colors"
                aria-label="Clear input"
              >
                <X className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePaste}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-[var(--text)] bg-[var(--bg-alt)] hover:bg-[var(--border)] rounded-lg border border-[var(--border)] transition-colors"
              >
                {clipboardPasted ? <Check className="w-3.5 h-3.5 text-[var(--positive)]" /> : <Clipboard className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{clipboardPasted ? 'Pasted!' : 'Paste'}</span>
              </button>
            )}

            {/* Submit / Extract Button - Base Design System Primary */}
            <button
              type="button"
              onClick={() => onFetch(url)}
              disabled={loading}
              className="flex items-center gap-2 px-5 sm:px-6 py-2.5 sm:py-3 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 font-semibold text-sm sm:text-base shadow-xs transition-opacity disabled:opacity-50 disabled:pointer-events-none"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="hidden sm:inline">Extracting...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Notices */}
        {pasteNotice && (
          <div className="px-4 py-1.5 text-xs text-amber-600 dark:text-amber-400 border-t border-[var(--border)] flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{pasteNotice}</span>
          </div>
        )}
      </div>

      {/* Engine Wake Notice */}
      {wakeNotice && (
        <div className="mt-3 px-4 py-2 text-xs text-[var(--accent)] bg-[var(--accent-bg)] rounded-lg border border-[var(--accent)]/20 flex items-center justify-center gap-2 animate-pulse">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>{wakeNotice}</span>
        </div>
      )}

      {/* Error Message Box - Base Design System Negative Token */}
      {error && (
        <div className="mt-4 p-3.5 rounded-lg bg-[var(--negative-bg)] border border-[var(--negative)]/20 text-[var(--negative)] text-sm flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">{error}</p>
            {errorCode && (
              <p className="text-xs opacity-80 mt-0.5 font-mono">Error Code: {errorCode}</p>
            )}
          </div>
        </div>
      )}

      {/* Degraded Platform Warning */}
      {isPlatformDegraded && (
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-500" />
          <span>
            <strong>{activePlatformData.name}</strong> is currently experiencing elevated upstream delays. Our fallback engines are engaged.
          </span>
        </div>
      )}

      {/* Dynamic Platform Chips - Base Design System Chips Pattern */}
      <div className="mt-6 flex items-center justify-start sm:justify-center gap-1.5 overflow-x-auto no-scrollbar py-2">
        {platformList.map((p) => {
          const isActive = currentActivePlatform === p.id;
          const Icon = p.icon;
          const isBeta = p.status === 'beta' || p.tier === 'B';
          const isDegraded = p.status === 'degraded';

          return (
            <button
              key={p.id}
              type="button"
              onClick={() => handleChipClick(p)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-xs'
                  : 'bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--border)] hover:bg-[var(--bg-alt)]'
              }`}
            >
              {Icon && <Icon className="w-3.5 h-3.5" />}
              <span>{p.name}</span>

              {isBeta && (
                <span className={`text-[9px] font-mono font-bold px-1 py-0.2 rounded border ${
                  isActive ? 'border-[var(--on-primary)]/40 text-[var(--on-primary)]' : 'border-[var(--border)] text-[var(--text-muted)] bg-[var(--bg-alt)]'
                }`}>
                  BETA
                </span>
              )}
              {isDegraded && (
                <span className="text-[9px] font-mono font-bold px-1 py-0.2 rounded bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                  DEGRADED
                </span>
              )}
            </button>
          );
        })}
      </div>

    </div>
  );
}
