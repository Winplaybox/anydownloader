import React, { useState, useEffect, useRef } from 'react';
import { 
  Download, 
  Clipboard, 
  X, 
  Loader2, 
  AlertCircle,
  RefreshCw,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { 
  TwitterXIcon,
  YoutubeIcon, 
  FacebookIcon,
  InstagramIcon, 
  TiktokIcon 
} from './BrandIcons.jsx';
import { normalizeUrl } from '../utils/normalizeUrl.js';
import { getErrorMessage, ErrorCode } from '../utils/errors.js';

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
  const [pasteNotice, setPasteNotice] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState(null);

  // Desktop autofocus only
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth >= 768 && inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

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
        // Automatically validate & attempt resolve if valid
        const norm = normalizeUrl(clean);
        if (norm.ok) {
          setDetectedPlatform(norm.platform);
        }
      }
    } catch (e) {
      // Graceful fallback for permission refusal
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
  ];

  const currentActivePlatform = detectedPlatform || activeCategory || 'all';

  return (
    <section className="w-full max-w-4xl mx-auto px-4 pt-8 pb-12 sm:pt-12 sm:pb-16 text-center">
      
      {/* Platform Chips / Segmented Control */}
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 mb-8">
        {platforms.map(p => {
          const Icon = p.icon;
          const isSelected = currentActivePlatform === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                setActiveCategory(p.id);
              }}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-150 border ${
                isSelected
                  ? 'bg-[var(--primary)] text-[var(--on-primary)] border-[var(--border-strong)] shadow-sm'
                  : 'bg-[var(--surface)] text-[var(--text-muted)] border-[var(--border)] hover:border-[var(--text)] hover:text-[var(--text)]'
              }`}
            >
              {Icon && <Icon className="w-3.5 h-3.5" />}
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Headline (H1) & Description */}
      <div className="space-y-3 mb-8">
        <h1 className="base-display text-[var(--text)] text-3xl sm:text-4xl lg:text-5xl tracking-tight">
          {pageH1 || 'Social Video & Image Downloader'}
        </h1>
        <p className="base-paragraph text-[var(--text-muted)] max-w-2xl mx-auto text-sm sm:text-base">
          {pageDesc || 'Download videos and original-resolution photos from Twitter/X, YouTube, Facebook, Instagram, and TikTok in seconds. 100% free with no sign-up.'}
        </p>
      </div>

      {/* URL Input Form Group */}
      <div className="w-full max-w-3xl mx-auto">
        <div className="relative flex flex-col sm:flex-row items-stretch gap-2 p-1.5 sm:p-2 bg-[var(--surface)] border-2 border-[var(--border-strong)] rounded-xl sm:rounded-2xl shadow-[var(--shadow-2)] transition-all focus-within:ring-2 focus-within:ring-[var(--accent)]">
          
          {/* Main Input */}
          <div className="relative flex-1 flex items-center min-w-0">
            <input
              ref={inputRef}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste X/Twitter, YouTube, Facebook, Instagram, or TikTok link..."
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
                className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text)] rounded-full hover:bg-[var(--bg-alt)] transition-colors mr-1"
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
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[var(--text)] bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg hover:border-[var(--border-strong)] transition-all mr-1"
              title="Paste from clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span>Paste</span>
            </button>
          </div>

          {/* Primary Action Button */}
          <button
            type="button"
            onClick={() => onFetch()}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg sm:rounded-xl font-bold text-sm sm:text-base bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 active:scale-[0.99] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Resolving...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Fetch Media</span>
              </>
            )}
          </button>
        </div>

        {/* Notice for multiple URLs extracted */}
        {pasteNotice && (
          <div className="mt-2 text-xs font-medium text-[var(--text-muted)] text-left px-2">
            💡 {pasteNotice}
          </div>
        )}

        {/* Inline Error Notification Banner */}
        {error && (
          <div 
            role="alert"
            className="mt-4 p-4 rounded-xl border border-[var(--negative)] bg-[var(--negative-bg)] text-left flex items-start justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-150"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-[var(--negative)] shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-[var(--text)]">
                  {errorCode ? getErrorMessage(errorCode, error) : error}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Check that the post is public, contains media, and the link was copied correctly.
                </p>
              </div>
            </div>
            
            <button
              type="button"
              onClick={() => onFetch()}
              className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:border-[var(--text)] transition-colors shrink-0"
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
