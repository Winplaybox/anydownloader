import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Download, 
  Clipboard, 
  X, 
  Loader2, 
  AlertCircle,
  RefreshCw,
  Sparkles
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

const PLATFORM_ROUTES = {
  all: '/',
  twitter: '/twitter-video-downloader',
  youtube: '/youtube-video-downloader',
  facebook: '/facebook-video-downloader',
  instagram: '/instagram-video-downloader',
  tiktok: '/tiktok-video-downloader',
  pinterest: '/pinterest-video-downloader',
  reddit: '/reddit-video-downloader',
  generic: '/any-website-downloader'
};

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

  const [pasteNotice, setPasteNotice] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState(null);
  const [wakeNotice, setWakeNotice] = useState('');

  // Desktop autofocus only
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth >= 768 && inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Display helpful engine spin-up notification during cold starts
  useEffect(() => {
    let timer;
    if (loading) {
      timer = setTimeout(() => {
        setWakeNotice('Extractor engine is waking up (Render initial cold-start)... Resolving media stream...');
      }, 2500);
    } else {
      setWakeNotice('');
    }
    return () => clearTimeout(timer);
  }, [loading]);

  // Detect platform on input change
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
      } else {
        setDetectedPlatform(null);
      }
    } else {
      setDetectedPlatform(null);
      setPasteNotice('');
    }
  }, [url]);

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        const clean = text.trim();
        setUrl(clean);
        const norm = normalizeUrl(clean);
        if (norm.ok) {
          setDetectedPlatform(norm.platform);
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

  const platforms = [
    { id: 'all', label: 'Auto-Detect', icon: null },
    { id: 'twitter', label: 'X (Twitter)', icon: TwitterXIcon },
    { id: 'youtube', label: 'YouTube', icon: YoutubeIcon },
    { id: 'facebook', label: 'Facebook', icon: FacebookIcon },
    { id: 'instagram', label: 'Instagram', icon: InstagramIcon },
    { id: 'tiktok', label: 'TikTok', icon: TiktokIcon },
    { id: 'pinterest', label: 'Pinterest', icon: PinterestIcon },
    { id: 'reddit', label: 'Reddit', icon: RedditIcon },
    { id: 'threads', label: 'Threads', icon: ThreadsIcon },
    { id: 'generic', label: 'Any Website', icon: GlobeIcon },
  ];

  // Resolve current active tab based on route or detected platform
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

  const currentActivePlatform = detectedPlatform || routePlatform || activeCategory || 'all';

  function handlePlatformClick(platformId) {
    setActiveCategory(platformId);
    const targetRoute = PLATFORM_ROUTES[platformId] || '/';
    if (location.pathname !== targetRoute) {
      navigate(targetRoute);
    }
  }

  return (
    <section className="w-full max-w-4xl mx-auto px-4 pt-8 pb-12 sm:pt-12 sm:pb-16 text-center">
      
      {/* Platform Chips / Segmented Control with Real Navigation */}
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 mb-8" role="tablist">
        {platforms.map(p => {
          const Icon = p.icon;
          const isSelected = currentActivePlatform === p.id;
          return (
            <button
              key={p.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              onClick={() => handlePlatformClick(p.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-150 border cursor-pointer ${
                isSelected
                  ? 'bg-[var(--primary)] text-[var(--on-primary)] border-[var(--border-strong)] shadow-sm'
                  : 'bg-[var(--surface)] text-[var(--text-muted)] border-[var(--border)] hover:border-[var(--text)] hover:text-[var(--text)]'
              }`}
            >
              {Icon && <Icon className="w-3.5 h-3.5 shrink-0" />}
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Headline (H1) & Description */}
      <div className="space-y-3 mb-8">
        <h1 className="base-display text-[var(--text)] text-3xl sm:text-4xl lg:text-5xl tracking-tight font-extrabold">
          {pageH1 || 'Social Video & Image Downloader'}
        </h1>
        <p className="base-paragraph text-[var(--text-muted)] max-w-2xl mx-auto text-sm sm:text-base">
          {pageDesc || 'Download videos and original-resolution photos from Twitter/X, YouTube, Facebook, Instagram, TikTok, Pinterest, Reddit, and any website. 100% free with no sign-up.'}
        </p>
      </div>

      {/* URL Input Form Group */}
      <div className="w-full max-w-3xl mx-auto">
        <div className="relative flex flex-col sm:flex-row items-stretch gap-2 p-1.5 sm:p-2 bg-[var(--surface)] border-2 border-[var(--border-strong)] rounded-xl sm:rounded-2xl shadow-[var(--shadow-2)] transition-all ovd-input-wrapper">
          
          {/* Main Input */}
          <div className="relative flex-1 flex items-center min-w-0">
            <input
              ref={inputRef}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste any social media, video, or website link to download..."
              className="w-full bg-transparent text-[var(--text)] text-sm sm:text-base font-medium px-4 py-3 placeholder-[var(--text-muted)] outline-none border-none"
              aria-label="Social media post or media link"
              autoComplete="off"
              spellCheck="false"
            />

            {/* Clear Button (shown when text present) */}
            {url && (
              <button
                type="button"
                onClick={() => {
                  setUrl('');
                  if (onClear) onClear();
                  if (inputRef.current) inputRef.current.focus();
                }}
                className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text)] rounded-full hover:bg-[var(--bg-alt)] transition-colors mr-1 cursor-pointer"
                aria-label="Clear input"
                title="Clear"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Paste Button */}
            <button
              type="button"
              onClick={handlePaste}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-[var(--text)] bg-[var(--bg-alt)] hover:bg-[var(--border)] transition-colors mr-1 cursor-pointer"
              title="Paste from clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Paste</span>
            </button>
          </div>

          {/* Fetch Media Button */}
          <button
            type="button"
            onClick={() => onFetch()}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg sm:rounded-xl font-bold text-sm sm:text-base bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 active:scale-[0.99] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shrink-0 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 sm:w-5 sm:h-5" />
                <span>Fetch Media</span>
              </>
            )}
          </button>
        </div>

        {/* Cold-Start / Waking Notice */}
        {wakeNotice && loading && (
          <div className="mt-3 flex items-center justify-center gap-2 text-xs font-medium text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-lg p-2.5">
            <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
            <span>{wakeNotice}</span>
          </div>
        )}

        {/* Paste notice (multiple links, etc.) */}
        {pasteNotice && !error && (
          <p className="mt-2 text-xs text-[var(--text-muted)] text-left px-2">
            {pasteNotice}
          </p>
        )}

        {/* Error Announcement */}
        {error && (
          <div 
            role="alert" 
            className="mt-4 p-3.5 rounded-xl border border-[var(--negative)] bg-[var(--negative-bg)] text-[var(--negative)] flex items-start justify-between gap-3 text-left transition-all"
          >
            <div className="flex items-start gap-2.5 min-w-0">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="text-sm font-medium leading-relaxed">
                {error}
              </div>
            </div>

            {/* Retry button if retryable */}
            <button
              type="button"
              onClick={() => onFetch()}
              className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:border-[var(--text)] transition-colors shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
