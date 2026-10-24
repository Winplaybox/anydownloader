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

// Built-in initial platforms registry cache (ensures instant rendering before /api/platforms loads)
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
  if (p === 'generic') return GlobeIcon;
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

  // Desktop autofocus
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

  // Helpful status message during server cold starts
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

  // Auto-Detect platform & URL change handling
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

        // Automatic platform switch if user picked a chip and URL belongs to a different platform
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

  // Paste & Auto-Extract
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

        // Auto-extract immediately on paste as per Section 5 spec
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
      onFetch();
    }
  }

  // Handle platform chip navigation or selection
  function handleChipClick(platformItem) {
    const pId = platformItem.id;
    if (typeof setActiveCategory === 'function') {
      setActiveCategory(pId);
    }

    if (location.pathname === '/') {
      return;
    }

    // On tool pages, navigate to corresponding route
    if (pId === 'all') {
      navigate('/');
    } else if (platformItem.seo?.slug) {
      navigate(`/${platformItem.seo.slug}`);
    } else {
      navigate(`/${pId}-video-downloader`);
    }
  }

  // Active platform indicator
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

  // Check if active platform is degraded
  const activePlatformData = platformList.find(p => p.id === currentActivePlatform);
  const isPlatformDegraded = activePlatformData?.status === 'degraded';

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pt-10 pb-6">
      
      {/* Title & Tagline */}
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
          {pageH1 || 'Download Social Videos & Photos'}
        </h1>
        <p className="mt-3 text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          {pageDesc || 'Fast, 100% free extractor for Twitter, YouTube, Instagram, TikTok, Facebook, Reddit, Pinterest, and any website.'}
        </p>
      </div>

      {/* Main Input Box */}
      <div className="relative bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-800 focus-within:border-blue-600 dark:focus-within:border-blue-500 rounded-3xl shadow-xl transition-all duration-300">
        <div className="flex items-center p-2 sm:p-2.5">
          <input
            ref={inputRef}
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste media link here (YouTube, Twitter, TikTok, Instagram...)"
            className="w-full px-4 py-3 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm sm:text-base outline-none"
            aria-label="Social media post or video URL"
          />

          {/* Action buttons (Clear / Paste) */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {url ? (
              <button
                type="button"
                onClick={onClear}
                className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl transition-colors"
                aria-label="Clear input"
              >
                <X className="w-5 h-5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handlePaste}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 rounded-xl transition-all hover:bg-slate-200 dark:hover:bg-slate-700"
              >
                {clipboardPasted ? <Check className="w-4 h-4 text-emerald-500" /> : <Clipboard className="w-4 h-4" />}
                <span className="hidden sm:inline">{clipboardPasted ? 'Pasted!' : 'Paste'}</span>
              </button>
            )}

            {/* Fetch / Download Button */}
            <button
              type="button"
              onClick={() => onFetch()}
              disabled={loading}
              className="flex items-center gap-2 px-5 sm:px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm sm:text-base shadow-lg shadow-blue-500/25 transition-all transform active:scale-95 disabled:opacity-75 disabled:pointer-events-none"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="hidden sm:inline">Extracting...</span>
                </>
              ) : (
                <>
                  <Download className="w-5 h-5" />
                  <span>Download</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Notices & Multiple Links Warning */}
        {pasteNotice && (
          <div className="px-5 py-2 text-xs text-amber-600 dark:text-amber-400 border-t border-slate-100 dark:border-slate-800 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{pasteNotice}</span>
          </div>
        )}
      </div>

      {/* Engine Wake Notice (during Render cold starts) */}
      {wakeNotice && (
        <div className="mt-3 px-4 py-2 text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800/40 flex items-center justify-center gap-2 animate-pulse">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>{wakeNotice}</span>
        </div>
      )}

      {/* Error Message Box */}
      {error && (
        <div className="mt-4 p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 flex items-start gap-3 animate-shake">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
          <div className="text-sm">
            <p className="font-semibold">{error}</p>
            {errorCode && (
              <p className="text-xs opacity-75 mt-0.5 font-mono">Error Code: {errorCode}</p>
            )}
          </div>
        </div>
      )}

      {/* Platform Degraded Warning Banner */}
      {isPlatformDegraded && (
        <div className="mt-4 p-3 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
          <span>
            <strong>{activePlatformData.name}</strong> is currently experiencing elevated upstream delays. Our fallback engines are engaged.
          </span>
        </div>
      )}

      {/* Dynamic Platform Chips (Fetched from /api/platforms with status badges) */}
      <div className="mt-6 flex items-center justify-start sm:justify-center gap-2 overflow-x-auto no-scrollbar py-2">
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
              className={`relative flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60'
              }`}
            >
              {Icon && <Icon className="w-3.5 h-3.5" />}
              <span>{p.name}</span>

              {/* Status Badges */}
              {isBeta && (
                <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                  isActive ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                }`}>
                  BETA
                </span>
              )}
              {isDegraded && (
                <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                  isActive ? 'bg-amber-400 text-black' : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                }`}>
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
