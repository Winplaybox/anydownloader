import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { BellPlus, ChevronDown, Menu, Moon, Newspaper, Sun, Wand2, X } from 'lucide-react';
import {
  TwitterXIcon, YoutubeIcon, FacebookIcon, InstagramIcon, TiktokIcon, PinterestIcon, RedditIcon, ThreadsIcon, GlobeIcon, ChromeIcon,
} from './BrandIcons.jsx';

const PLATFORMS = [
  { label: 'YouTube', to: '/youtube-video-downloader', icon: YoutubeIcon },
  { label: 'Instagram', to: '/instagram-video-downloader', icon: InstagramIcon },
  { label: 'TikTok', to: '/tiktok-video-downloader', icon: TiktokIcon },
  { label: 'Facebook', to: '/facebook-video-downloader', icon: FacebookIcon },
  { label: 'X (Twitter)', to: '/twitter-video-downloader', icon: TwitterXIcon },
  { label: 'Pinterest', to: '/pinterest-video-downloader', icon: PinterestIcon },
  { label: 'Reddit', to: '/reddit-video-downloader', icon: RedditIcon },
  { label: 'Threads', to: '/threads-video-downloader', icon: ThreadsIcon },
  { label: 'Any website', to: '/any-website-downloader', icon: GlobeIcon },
];
const TOOLS = [
  { label: 'YouTube Subscribe Link', to: '/youtube-subscribe-link-generator', icon: BellPlus },
  { label: 'AI Video Editor', to: '/ai-video-editor', icon: Wand2 },
  { label: 'Chrome Extension', to: '/extension', icon: ChromeIcon },
];

const linkCls = ({ isActive }) =>
  `h-10 px-3 rounded-xl text-sm font-semibold flex items-center gap-2 transition-colors ${
    isActive ? 'bg-[var(--text)] text-[var(--bg)]' : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
  }`;

function Menu_({ label, items, active }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('pointerdown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDoc); document.removeEventListener('keydown', onKey); };
  }, [open]);
  return (
    <div className="relative" ref={ref}>
      <button type="button" aria-expanded={open} aria-haspopup="true" onClick={() => setOpen((v) => !v)}
        className={`h-10 px-3 rounded-xl text-sm font-semibold flex items-center gap-1.5 transition-colors ${active ? 'bg-[var(--text)] text-[var(--bg)]' : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'}`}>
        {label}<ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <ul className="animate-in absolute left-0 top-full mt-2 w-64 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-1.5 shadow-[var(--shadow-2)]">
          {items.map(({ label: l, to, icon: Icon }) => (
            <li key={to}>
              <NavLink to={to} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex items-center gap-3 px-3 h-11 rounded-xl text-sm font-semibold ${isActive ? 'bg-[var(--accent-bg)] text-[var(--accent)]' : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'}`}>
                <Icon className="w-4 h-4 text-[var(--text-muted)]" />{l}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Header() {
  const [drawer, setDrawer] = useState(false);
  const { pathname } = useLocation();
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('ovd_theme') || 'light'; }
    catch { return 'light'; }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('ovd_theme', theme); } catch { /* private mode */ }
  }, [theme]);

  useEffect(() => { setDrawer(false); }, [pathname]);

  useEffect(() => {
    if (!drawer) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e) => { if (e.key === 'Escape') setDrawer(false); };
    document.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = prev; document.removeEventListener('keydown', onKey); };
  }, [drawer]);

  const onPlatform = PLATFORMS.some((p) => p.to === pathname);
  const onTool = TOOLS.some((p) => p.to === pathname);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg)]/90 backdrop-blur-md" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2 select-none" aria-label="OVD home">
          <span className="w-9 h-9 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center font-extrabold text-lg" style={{ fontFamily: 'var(--font-display)' }}>o</span>
          <span className="font-extrabold text-xl tracking-tight text-[var(--text)]" style={{ fontFamily: 'var(--font-display)' }}>ovd</span>
        </Link>

        <nav aria-label="Main" className="hidden lg:flex items-center gap-1">
          <Menu_ label="Downloaders" items={PLATFORMS} active={onPlatform} />
          <Menu_ label="Tools" items={TOOLS} active={onTool} />
          <NavLink to="/blog" className={linkCls}><Newspaper className="w-4 h-4" />Blog</NavLink>
        </nav>

        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="w-10 h-10 rounded-xl border border-[var(--border)] bg-[var(--surface)] grid place-items-center text-[var(--text)] hover:border-[var(--accent)] transition-colors">
            {theme === 'dark' ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
          </button>
          <button type="button" onClick={() => setDrawer((v) => !v)} aria-expanded={drawer} aria-controls="mobile-menu" aria-label={drawer ? 'Close menu' : 'Open menu'}
            className="lg:hidden w-10 h-10 rounded-xl border border-[var(--border)] bg-[var(--surface)] grid place-items-center text-[var(--text)]">
            {drawer ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {drawer && (
        <div id="mobile-menu" className="lg:hidden fixed inset-x-0 bottom-0 bg-[var(--bg)] overflow-y-auto overscroll-contain animate-fadeIn"
          style={{ top: 'calc(4rem + env(safe-area-inset-top))' }}>
          <nav aria-label="Mobile" className="px-4 py-4 pb-10 space-y-6">
            <div>
              <p className="px-1 mb-2 text-sm font-semibold text-[var(--text-muted)]">Downloaders</p>
              <ul className="grid grid-cols-2 gap-2">
                {PLATFORMS.map(({ label, to, icon: Icon }) => (
                  <li key={to}><NavLink to={to} className={({ isActive }) => `flex items-center gap-2.5 h-12 px-3 rounded-2xl border text-sm font-semibold ${isActive ? 'border-[var(--accent)] bg-[var(--accent-bg)] text-[var(--accent)]' : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'}`}><Icon className="w-4 h-4" />{label}</NavLink></li>
                ))}
              </ul>
            </div>
            <div>
              <p className="px-1 mb-2 text-sm font-semibold text-[var(--text-muted)]">Tools</p>
              <ul className="space-y-2">
                {[...TOOLS, { label: 'Blog and guides', to: '/blog', icon: Newspaper }, { label: 'Updates', to: '/updates', icon: Newspaper }].map(({ label, to, icon: Icon }) => (
                  <li key={to}><NavLink to={to} className={({ isActive }) => `flex items-center gap-3 h-12 px-3 rounded-2xl border text-sm font-semibold ${isActive ? 'border-[var(--accent)] bg-[var(--accent-bg)] text-[var(--accent)]' : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'}`}><Icon className="w-4 h-4" />{label}</NavLink></li>
                ))}
              </ul>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
