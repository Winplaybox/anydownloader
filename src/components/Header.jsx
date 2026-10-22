import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sun, Moon, Newspaper, Sparkles } from 'lucide-react';
import {
  TwitterXIcon,
  YoutubeIcon,
  FacebookIcon,
  InstagramIcon,
  TiktokIcon
} from './BrandIcons.jsx';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('ovd_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    }
    return 'light';
  });

  const location = useLocation();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('ovd_theme', theme);
  }, [theme]);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  function toggleTheme() {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }

  const navLinks = [
    { label: 'X (Twitter)', path: '/twitter-video-downloader', icon: TwitterXIcon },
    { label: 'YouTube', path: '/youtube-video-downloader', icon: YoutubeIcon },
    { label: 'Facebook', path: '/facebook-video-downloader', icon: FacebookIcon },
    { label: 'Instagram', path: '/instagram-video-downloader', icon: InstagramIcon },
    { label: 'TikTok', path: '/tiktok-video-downloader', icon: TiktokIcon },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg)]/95 backdrop-blur-md border-b border-[var(--border)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group rounded-lg p-1 focus:outline-none">
          <div className="w-8 h-8 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] flex items-center justify-center font-black text-sm tracking-wider">
            OVD
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-base tracking-tight text-[var(--text)]">
              OVD Downloader
            </span>
            <span className="text-[10px] uppercase font-semibold tracking-wider text-[var(--text-muted)] -mt-1">
              Social Media Downloader
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-sm'
                    : 'text-[var(--text)] hover:bg-[var(--bg-alt)] border border-transparent hover:border-[var(--border)]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--on-primary)]' : 'text-[var(--text-muted)]'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
          {/* Blog & Updates */}
          <Link
            to="/blog"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 ${
              location.pathname === '/blog'
                ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-sm'
                : 'text-[var(--text)] hover:bg-[var(--bg-alt)] border border-transparent hover:border-[var(--border)]'
            }`}
          >
            <Newspaper className="w-4 h-4 text-[var(--text-muted)]" />
            <span>Blog</span>
          </Link>
        </nav>

        {/* Right: Theme Toggle + Mobile Menu */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className="p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-700" />
            )}
          </button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle mobile menu"
            className="md:hidden p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[var(--border)] bg-[var(--bg)] px-4 pt-2 pb-6 space-y-1">
          <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] px-3 py-2">
            Platforms
          </div>
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-[var(--primary)] text-[var(--on-primary)]'
                    : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                <span className="text-xs opacity-60">Video & Photos</span>
              </Link>
            );
          })}
          <div className="pt-2 border-t border-[var(--border)] mt-2 space-y-1">
            <Link to="/blog" className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors">
              <Newspaper className="w-4 h-4" />
              <span>Blog & Guides</span>
            </Link>
            <Link to="/updates" className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors">
              <Sparkles className="w-4 h-4" />
              <span>Updates & Changelog</span>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
