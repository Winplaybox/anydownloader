import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, Check, Clipboard, Link2, Loader2, RotateCw, TriangleAlert, X } from 'lucide-react';
import {
  TwitterXIcon, YoutubeIcon, FacebookIcon, InstagramIcon, TiktokIcon,
  PinterestIcon, RedditIcon, ThreadsIcon, GlobeIcon,
} from './BrandIcons.jsx';
import { normalizeUrl } from '../utils/normalizeUrl.js';
import { PLATFORM_LABEL } from '../data/toolRoutes.js';

const ICONS = {
  twitter: TwitterXIcon, youtube: YoutubeIcon, facebook: FacebookIcon, instagram: InstagramIcon,
  tiktok: TiktokIcon, pinterest: PinterestIcon, reddit: RedditIcon, threads: ThreadsIcon, generic: GlobeIcon,
};

const CHIPS = [
  { id: 'youtube', to: '/youtube-video-downloader' },
  { id: 'instagram', to: '/instagram-video-downloader' },
  { id: 'tiktok', to: '/tiktok-video-downloader' },
  { id: 'facebook', to: '/facebook-video-downloader' },
  { id: 'twitter', to: '/twitter-video-downloader' },
  { id: 'pinterest', to: '/pinterest-video-downloader' },
  { id: 'reddit', to: '/reddit-video-downloader' },
  { id: 'threads', to: '/threads-video-downloader' },
  { id: 'generic', to: '/any-website-downloader' },
];

const WAIT_MESSAGES = [
  [0, 'Finding your media...'],
  [6000, 'Still working. Large videos take a few more seconds...'],
  [15000, 'Waking up the download server. The first request can take up to a minute.'],
];

function useWaitMessage(loading) {
  const [msg, setMsg] = useState('');
  useEffect(() => {
    if (!loading) { setMsg(''); return undefined; }
    const timers = WAIT_MESSAGES.map(([ms, text]) => setTimeout(() => setMsg(text), ms));
    return () => timers.forEach(clearTimeout);
  }, [loading]);
  return msg;
}

export default function HeroDownloader({
  url, setUrl, onSubmit, loading, error, errorCode, retryable = true, onClear,
  title, subtitle, platform = 'all',
}) {
  const inputRef = useRef(null);
  const [pasted, setPasted] = useState(false);
  const waitMsg = useWaitMessage(loading);

  const detected = useMemo(() => {
    if (!url || url.trim().length < 6) return null;
    const n = normalizeUrl(url);
    return n.ok ? n.platform : null;
  }, [url]);

  const GlyphIcon = (detected && ICONS[detected]) || (platform !== 'all' && ICONS[platform]) || Link2;
  const hintLabel = detected ? `${PLATFORM_LABEL[detected] || 'Link'} link detected` : null;

  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches) inputRef.current?.focus();
  }, []);

  async function handlePaste() {
    try {
      const text = (await navigator.clipboard.readText()).trim();
      if (!text) { inputRef.current?.focus(); return; }
      setUrl(text);
      setPasted(true);
      setTimeout(() => setPasted(false), 1600);
      onSubmit(text);
    } catch {
      inputRef.current?.focus(); // clipboard permission denied: let the user paste manually
    }
  }

  function submit(e) {
    e.preventDefault();
    if (loading) return;
    onSubmit(url);
  }

  return (
    <section className="w-full max-w-3xl mx-auto px-4 pt-8 sm:pt-14 pb-4">
      <div className="text-center mb-7 sm:mb-9">
        <h1 className="font-extrabold text-[2rem] leading-[1.08] sm:text-5xl md:text-[3.4rem] text-[var(--text)] text-balance">
          {title}
        </h1>
        <p className="mt-4 text-base sm:text-lg text-[var(--text-muted)] max-w-xl mx-auto text-pretty">{subtitle}</p>
      </div>

      <form onSubmit={submit} noValidate>
        <div className="ovd-paste relative" data-busy={loading}>
          <div className="flex items-center gap-2 p-2 sm:p-2.5">
            <span
              className="hidden sm:flex shrink-0 w-11 h-11 rounded-2xl bg-[var(--bg-alt)] items-center justify-center text-[var(--text)]"
              aria-hidden="true"
            >
              <GlyphIcon className="w-5 h-5" />
            </span>
            <label htmlFor="ovd-url" className="sr-only">Link to the video or photo</label>
            <input
              id="ovd-url"
              ref={inputRef}
              type="text"
              inputMode="url"
              enterKeyHint="go"
              autoComplete="off"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste link here"
              className="min-w-0 flex-1 bg-transparent text-[var(--text)] placeholder:text-[var(--text-muted)] text-base sm:text-lg px-2 py-3 outline-none"
            />
            {url ? (
              <button type="button" onClick={onClear} aria-label="Clear link"
                className="shrink-0 w-10 h-10 grid place-items-center rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors">
                <X className="w-5 h-5" />
              </button>
            ) : (
              <button type="button" onClick={handlePaste}
                aria-label="Paste link from clipboard" className="shrink-0 h-11 px-3 min-[420px]:px-3.5 rounded-xl border border-[var(--border)] bg-[var(--bg-alt)] text-sm font-semibold text-[var(--text)] flex items-center gap-1.5 hover:border-[var(--accent)] transition-colors">
                {pasted ? <Check className="w-4 h-4 text-[var(--positive)]" /> : <Clipboard className="w-4 h-4" />}
                <span className="hidden min-[420px]:inline">{pasted ? 'Pasted' : 'Paste'}</span>
              </button>
            )}
            <button type="submit" disabled={loading}
              className="shrink-0 h-11 sm:h-12 px-4 sm:px-6 rounded-2xl bg-[var(--primary)] text-[var(--on-primary)] font-bold text-base flex items-center gap-2 hover:brightness-110 active:scale-[.98] transition disabled:opacity-70">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowDown className="w-5 h-5" />}
              <span className="hidden sm:inline">{loading ? 'Working' : 'Download'}</span>
              <span className="sm:hidden">{loading ? '' : 'Go'}</span>
            </button>
          </div>
          <div className="ovd-progress" aria-hidden="true" />
        </div>

        <div className="min-h-[1.75rem] mt-3 text-sm text-center" aria-live="polite">
          {loading && <p className="text-[var(--text-muted)]">{waitMsg}</p>}
          {!loading && hintLabel && !error && <p className="text-[var(--positive)] font-medium">{hintLabel}</p>}
        </div>
      </form>

      {error && (
        <div role="alert" className="mt-2 rounded-2xl border border-[var(--negative)]/30 bg-[var(--negative-bg)] p-4 flex items-start gap-3 animate-fadeIn">
          <TriangleAlert className="w-5 h-5 shrink-0 mt-0.5 text-[var(--negative)]" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-[var(--text)]">{error}</p>
            {errorCode === 'SOURCE_BLOCKED' && (
              <p className="text-sm text-[var(--text-muted)] mt-1">This is temporary. Retrying in a minute usually works.</p>
            )}
          </div>
          {retryable && url && (
            <button type="button" onClick={() => onSubmit(url)}
              className="shrink-0 h-9 px-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-sm font-semibold flex items-center gap-1.5 hover:border-[var(--accent)]">
              <RotateCw className="w-4 h-4" /> Retry
            </button>
          )}
        </div>
      )}

      <nav aria-label="Supported platforms" className="mt-5">
        <ul className="snap-row no-scrollbar gap-2 sm:justify-center py-1 -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap">
          {CHIPS.map(({ id, to }) => {
            const Icon = ICONS[id];
            const active = (detected || platform) === id;
            return (
              <li key={id}>
                <Link to={to}
                  aria-current={active ? 'page' : undefined}
                  className={`h-10 px-3.5 rounded-full text-sm font-semibold whitespace-nowrap flex items-center gap-2 border transition-colors ${
                    active
                      ? 'bg-[var(--text)] text-[var(--bg)] border-[var(--text)]'
                      : 'bg-[var(--surface)] text-[var(--text)] border-[var(--border)] hover:border-[var(--accent)]'
                  }`}>
                  <Icon className="w-4 h-4" />
                  {PLATFORM_LABEL[id]}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </section>
  );
}
