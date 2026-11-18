import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { BellPlus, ChevronDown, Menu, Moon, Newspaper, Sun, Wand2, X, Crown, Sparkles, User, LogIn, LogOut, Loader2 } from 'lucide-react';
import {
  TwitterXIcon, YoutubeIcon, FacebookIcon, InstagramIcon, TiktokIcon, PinterestIcon, RedditIcon, ThreadsIcon, GlobeIcon, ChromeIcon,
} from './BrandIcons.jsx';
import PricingModal from './PricingModal.jsx';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

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

function GoogleGIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

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
        className={`h-10 px-3 rounded-xl text-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${active ? 'bg-[var(--text)] text-[var(--bg)]' : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'}`}>
        {label}<ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <ul className="animate-in absolute left-0 top-full mt-2 w-64 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-1.5 shadow-[var(--shadow-2)] z-50">
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
  const [pricingOpen, setPricingOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);
  const profileRef = useRef(null);
  const { pathname } = useLocation();

  const [session, setSession] = useState(() => {
    try {
      const cached = localStorage.getItem('wpb_session_data');
      return cached ? JSON.parse(cached) : { authenticated: false, is_guest: true, credits: 2, max_resolution: 480, plan: 'free' };
    } catch {
      return { authenticated: false, is_guest: true, credits: 2, max_resolution: 480, plan: 'free' };
    }
  });

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

  // Click outside profile dropdown
  useEffect(() => {
    if (!profileOpen) return undefined;
    const onDoc = (e) => { if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setProfileOpen(false); };
    document.addEventListener('pointerdown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDoc); document.removeEventListener('keydown', onKey); };
  }, [profileOpen]);

  // Listen for global open-pricing-modal event
  useEffect(() => {
    const onOpen = () => setPricingOpen(true);
    window.addEventListener('open-pricing-modal', onOpen);
    return () => window.removeEventListener('open-pricing-modal', onOpen);
  }, []);

  // Fetch session on mount
  useEffect(() => {
    async function loadSession() {
      try {
        const token = localStorage.getItem('wpb_token');
        const guestId = localStorage.getItem('wpb_guest_id');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (guestId) headers['x-guest-id'] = guestId;

        const res = await fetch(`${BACKEND_BASE}/api/auth/session`, {
          credentials: 'include',
          headers
        });
        const data = await res.json();
        if (data.ok && data.identity) {
          setSession(data.identity);
          if (data.identity.guest_id) {
            localStorage.setItem('wpb_guest_id', data.identity.guest_id);
          }
          localStorage.setItem('wpb_session_data', JSON.stringify(data.identity));
        }
      } catch (e) {
        console.warn('Session load failed:', e);
      }
    }
    loadSession();
  }, []);

  async function handleGoogleLogin() {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
      return;
    }
    const email = prompt('Enter your Google email to sign in:');
    if (!email) return;
    setLoggingIn(true);
    try {
      const guestId = localStorage.getItem('wpb_guest_id');
      const res = await fetch(`${BACKEND_BASE}/api/auth/google`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential: btoa(JSON.stringify({ email, name: email.split('@')[0], sub: `g_${Date.now()}` })),
          guest_id: guestId
        })
      });
      const data = await res.json();
      if (data.ok && data.user) {
        if (data.token) localStorage.setItem('wpb_token', data.token);
        setSession(data.user);
        localStorage.setItem('wpb_session_data', JSON.stringify(data.user));
        setProfileOpen(false);
      }
    } catch (err) {
      console.error('Google login error:', err);
    } finally {
      setLoggingIn(false);
    }
  }

  async function handleLogout() {
    try {
      await fetch(`${BACKEND_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch {}
    localStorage.removeItem('wpb_token');
    const freshGuest = { authenticated: false, is_guest: true, credits: 2, max_resolution: 480, plan: 'free' };
    setSession(freshGuest);
    localStorage.setItem('wpb_session_data', JSON.stringify(freshGuest));
    setProfileOpen(false);
  }

  const onPlatform = PLATFORMS.some((p) => p.to === pathname);
  const onTool = TOOLS.some((p) => p.to === pathname);
  const isAuthenticated = session?.authenticated && !session?.is_guest;
  const credits = session?.credits ?? 2;
  const plan = session?.plan || 'free';
  const isPaid = plan !== 'free';

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg)]/90 backdrop-blur-md" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 select-none" aria-label="OVD home">
          <span className="w-9 h-9 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center font-extrabold text-lg" style={{ fontFamily: 'var(--font-display)' }}>o</span>
          <span className="font-extrabold text-xl tracking-tight text-[var(--text)]" style={{ fontFamily: 'var(--font-display)' }}>ovd</span>
        </Link>

        {/* Desktop Main Nav */}
        <nav aria-label="Main" className="hidden lg:flex items-center gap-1">
          <Menu_ label="Downloaders" items={PLATFORMS} active={onPlatform} />
          <Menu_ label="Tools" items={TOOLS} active={onTool} />
          <button
            type="button"
            onClick={() => setPricingOpen(true)}
            className="h-10 px-3 rounded-xl text-sm font-semibold flex items-center gap-1.5 text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors cursor-pointer"
          >
            <Crown className="w-4 h-4 text-amber-500" />
            <span>Plans</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-black uppercase bg-amber-500/15 text-amber-500 border border-amber-500/30">7 Tiers</span>
          </button>
          <NavLink to="/blog" className={linkCls}><Newspaper className="w-4 h-4" />Blog</NavLink>
        </nav>

        {/* Right Nav: Plans Pill + User/Guest Avatar + Theme Toggle */}
        <div className="flex items-center gap-2">
          {/* Quick Plans Upgrade Button */}
          <button
            type="button"
            onClick={() => setPricingOpen(true)}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/15 via-orange-500/15 to-amber-500/15 hover:from-amber-500/25 hover:to-orange-500/25 border border-amber-500/35 text-amber-400 text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            <Crown className="w-3.5 h-3.5 text-amber-400" />
            <span>Plans</span>
            <span className="px-1.5 py-0.5 rounded bg-amber-500 text-black text-[9px] font-black uppercase">7 Tiers</span>
          </button>

          {/* User / Guest Avatar Pill & Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => setProfileOpen((v) => !v)}
              aria-label="User account and credits"
              className="flex items-center gap-2 p-1 sm:px-2.5 sm:py-1.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--bg-alt)] transition-colors cursor-pointer"
            >
              {/* Avatar circle */}
              <div className="w-7 h-7 sm:w-7 sm:h-7 rounded-lg bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-[1.5px] shadow-sm shrink-0">
                <div className="w-full h-full bg-[#14161f] rounded-[6px] flex items-center justify-center overflow-hidden">
                  {session?.avatar ? (
                    <img src={session.avatar} alt="Avatar" className="w-full h-full object-cover" />
                  ) : isAuthenticated ? (
                    <span className="text-white font-bold text-xs uppercase">{(session?.name || session?.email || 'U')[0]}</span>
                  ) : (
                    <span className="text-xs" role="img" aria-label="Guest">🤖</span>
                  )}
                </div>
              </div>

              {/* Text label */}
              <div className="hidden sm:flex flex-col text-left leading-none">
                <span className="text-xs font-bold text-[var(--text)]">
                  {isAuthenticated ? (session.name?.split(' ')[0] || 'User') : 'Guest'}
                </span>
                <span className="text-[10px] text-amber-400 font-semibold mt-0.5">
                  {credits} credit{credits === 1 ? '' : 's'}
                </span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-muted)] transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Account Popover */}
            {profileOpen && (
              <div className="animate-in absolute right-0 top-full mt-2 w-72 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-3 shadow-2xl z-50 text-[var(--text)]">
                <div className="flex items-center gap-3 p-2 rounded-xl bg-[var(--bg-alt)] mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-[2px] shrink-0">
                    <div className="w-full h-full bg-[#14161f] rounded-[8px] flex items-center justify-center overflow-hidden">
                      {session?.avatar ? (
                        <img src={session.avatar} alt="Avatar" className="w-full h-full object-cover" />
                      ) : isAuthenticated ? (
                        <span className="text-white font-bold text-sm uppercase">{(session?.name || session?.email || 'U')[0]}</span>
                      ) : (
                        <span className="text-base">🤖</span>
                      )}
                    </div>
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[var(--text)] truncate">
                      {isAuthenticated ? (session.name || session.email) : 'Guest Visitor'}
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)] flex items-center gap-1">
                      <span className="text-amber-400 font-bold">{credits} credits</span>
                      <span>•</span>
                      <span>{session?.max_resolution || 480}p max</span>
                    </p>
                  </div>
                </div>

                <div className="space-y-1.5 mb-3">
                  <div className="flex items-center justify-between text-xs px-2 py-1 text-[var(--text-muted)]">
                    <span>Plan:</span>
                    <strong className="text-[var(--text)] uppercase font-bold">{plan} ({session?.max_resolution || 480}p)</strong>
                  </div>
                  <div className="flex items-center justify-between text-xs px-2 py-1 text-[var(--text-muted)]">
                    <span>Daily free renewal:</span>
                    <strong className="text-emerald-400 font-bold">2 credits / day</strong>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => { setProfileOpen(false); setPricingOpen(true); }}
                  className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:opacity-95 text-black text-xs font-black flex items-center justify-center gap-2 shadow-md mb-2 cursor-pointer"
                >
                  <Crown className="w-4 h-4 text-black" />
                  <span>View 7-Tier Plans (480p to 8K)</span>
                </button>

                {!isAuthenticated ? (
                  <button
                    type="button"
                    onClick={handleGoogleLogin}
                    disabled={loggingIn}
                    className="w-full py-2 px-3 rounded-xl bg-white hover:bg-zinc-100 text-zinc-900 text-xs font-bold flex items-center justify-center gap-2 border border-zinc-200 shadow-sm transition-colors cursor-pointer"
                  >
                    {loggingIn ? <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-900" /> : <GoogleGIcon />}
                    <span>Sign in with Google</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full py-2 px-3 rounded-xl hover:bg-[var(--bg-alt)] text-[var(--text-muted)] hover:text-[var(--text)] text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign out</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Theme toggle */}
          <button type="button" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="w-10 h-10 rounded-xl border border-[var(--border)] bg-[var(--surface)] grid place-items-center text-[var(--text)] hover:border-[var(--accent)] transition-colors cursor-pointer">
            {theme === 'dark' ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
          </button>

          {/* Mobile menu button */}
          <button type="button" onClick={() => setDrawer((v) => !v)} aria-expanded={drawer} aria-controls="mobile-menu" aria-label={drawer ? 'Close menu' : 'Open menu'}
            className="lg:hidden w-10 h-10 rounded-xl border border-[var(--border)] bg-[var(--surface)] grid place-items-center text-[var(--text)] cursor-pointer">
            {drawer ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {drawer && (
        <div id="mobile-menu" className="lg:hidden fixed inset-x-0 bottom-0 bg-[var(--bg)] overflow-y-auto overscroll-contain animate-fadeIn"
          style={{ top: 'calc(4rem + env(safe-area-inset-top))' }}>
          <nav aria-label="Mobile" className="px-4 py-4 pb-10 space-y-6">
            {/* Account Card */}
            <div className="p-3.5 rounded-2xl border border-[var(--border)] bg-[var(--surface)]">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-[2px] shrink-0">
                  <div className="w-full h-full bg-[#14161f] rounded-[8px] flex items-center justify-center overflow-hidden">
                    {session?.avatar ? (
                      <img src={session.avatar} alt="Avatar" className="w-full h-full object-cover" />
                    ) : isAuthenticated ? (
                      <span className="text-white font-bold text-sm uppercase">{(session?.name || session?.email || 'U')[0]}</span>
                    ) : (
                      <span className="text-base">🤖</span>
                    )}
                  </div>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-[var(--text)] truncate">
                    {isAuthenticated ? (session.name || session.email) : 'Guest Visitor'}
                  </p>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    <strong className="text-amber-400">{credits} credits</strong> • {session?.max_resolution || 480}p SD limit
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => { setDrawer(false); setPricingOpen(true); }}
                  className="py-2 px-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-black text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm"
                >
                  <Crown className="w-3.5 h-3.5" />
                  <span>7 Plans</span>
                </button>
                {!isAuthenticated ? (
                  <button
                    type="button"
                    onClick={() => { setDrawer(false); handleGoogleLogin(); }}
                    className="py-2 px-3 rounded-xl bg-white text-zinc-900 text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm border border-zinc-200"
                  >
                    <GoogleGIcon className="w-3.5 h-3.5" />
                    <span>Sign in</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="py-2 px-3 rounded-xl bg-[var(--bg-alt)] text-[var(--text)] text-xs font-semibold flex items-center justify-center gap-1.5 border border-[var(--border)]"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Logout</span>
                  </button>
                )}
              </div>
            </div>

            {/* Downloaders */}
            <div>
              <p className="px-1 mb-2 text-sm font-semibold text-[var(--text-muted)]">Downloaders</p>
              <ul className="grid grid-cols-2 gap-2">
                {PLATFORMS.map(({ label, to, icon: Icon }) => (
                  <li key={to}><NavLink to={to} className={({ isActive }) => `flex items-center gap-2.5 h-12 px-3 rounded-2xl border text-sm font-semibold ${isActive ? 'border-[var(--accent)] bg-[var(--accent-bg)] text-[var(--accent)]' : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'}`}><Icon className="w-4 h-4" />{label}</NavLink></li>
                ))}
              </ul>
            </div>

            {/* Tools */}
            <div>
              <p className="px-1 mb-2 text-sm font-semibold text-[var(--text-muted)]">Tools & Plans</p>
              <ul className="space-y-2">
                <li>
                  <button
                    type="button"
                    onClick={() => { setDrawer(false); setPricingOpen(true); }}
                    className="w-full flex items-center justify-between h-12 px-3 rounded-2xl border border-amber-500/40 bg-amber-500/10 text-amber-400 text-sm font-bold"
                  >
                    <span className="flex items-center gap-3"><Crown className="w-4 h-4 text-amber-400" /> 7-Tier Plans & Pricing</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500 text-black text-[10px] font-black uppercase">Explore</span>
                  </button>
                </li>
                {[...TOOLS, { label: 'Blog and guides', to: '/blog', icon: Newspaper }, { label: 'Updates', to: '/updates', icon: Newspaper }].map(({ label, to, icon: Icon }) => (
                  <li key={to}><NavLink to={to} className={({ isActive }) => `flex items-center gap-3 h-12 px-3 rounded-2xl border text-sm font-semibold ${isActive ? 'border-[var(--accent)] bg-[var(--accent-bg)] text-[var(--accent)]' : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text)]'}`}><Icon className="w-4 h-4" />{label}</NavLink></li>
                ))}
              </ul>
            </div>
          </nav>
        </div>
      )}

      {/* Global 7-Tier Dodo Payments Modal */}
      <PricingModal
        isOpen={pricingOpen}
        onClose={() => setPricingOpen(false)}
        userPlan={session?.plan || 'free'}
        onPlanUpgraded={(np) => {
          setSession((p) => ({ ...p, plan: np }));
          setPricingOpen(false);
        }}
      />
    </header>
  );
}
