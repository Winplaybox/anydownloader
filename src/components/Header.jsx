import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sun, Moon, Newspaper, ChevronDown, Wand2 } from 'lucide-react';
import {
  TwitterXIcon,
  YoutubeIcon,
  FacebookIcon,
  InstagramIcon,
  TiktokIcon,
  PinterestIcon,
  RedditIcon,
  ThreadsIcon,
  GlobeIcon,
  ChromeIcon
} from './BrandIcons.jsx';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [moreDropdownOpen, setMoreDropdownOpen] = useState(false);
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
    setMoreDropdownOpen(false);
  }, [location.pathname]);

  function toggleTheme() {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }

  const primaryNavLinks = [
    { label: 'X (Twitter)', path: '/twitter-video-downloader', icon: TwitterXIcon },
    { label: 'YouTube', path: '/youtube-video-downloader', icon: YoutubeIcon },
    { label: 'Facebook', path: '/facebook-video-downloader', icon: FacebookIcon },
    { label: 'Instagram', path: '/instagram-video-downloader', icon: InstagramIcon },
    { label: 'TikTok', path: '/tiktok-video-downloader', icon: TiktokIcon },
  ];

  const secondaryNavLinks = [
    { label: 'Pinterest', path: '/pinterest-video-downloader', icon: PinterestIcon },
    { label: 'Reddit', path: '/reddit-video-downloader', icon: RedditIcon },
    { label: 'Threads', path: '/threads-video-downloader', icon: ThreadsIcon },
    { label: 'Any Website', path: '/any-website-downloader', icon: GlobeIcon },
  ];

  const isSecondaryActive = secondaryNavLinks.some(item => location.pathname === item.path);

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg)]/95 backdrop-blur-md border-b border-[var(--border)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

        {/* Brand Logo - PURE TEXT OVD in White/Black Theme */}
        <Link 
          to="/" 
          className="flex items-center gap-2 group p-1 focus:outline-none select-none"
          title="OVD Downloader"
        >
          <span className="font-black text-2xl tracking-tighter text-[var(--text)] group-hover:opacity-80 transition-opacity">
            OVD
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {primaryNavLinks.map((item) => {
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

          {/* More Platforms Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setMoreDropdownOpen(!moreDropdownOpen)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 cursor-pointer ${
                isSecondaryActive
                  ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-sm'
                  : 'text-[var(--text)] hover:bg-[var(--bg-alt)] border border-transparent hover:border-[var(--border)]'
              }`}
            >
              <span>More</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {moreDropdownOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setMoreDropdownOpen(false)} 
                />
              <div className="absolute top-full right-0 mt-1.5 w-48 rounded-xl bg-[var(--surface)] border border-[var(--border)] shadow-xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
                {secondaryNavLinks.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMoreDropdownOpen(false)}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                        isActive
                          ? 'bg-[var(--primary)] text-[var(--on-primary)]'
                          : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--on-primary)]' : 'text-[var(--text-muted)]'}`} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
              </>
            )}
          </div>

          {/* AI Video Editor */}
          <Link
            to="/ai-video-editor"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 ${
              location.pathname === '/ai-video-editor'
                ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-sm'
                : 'text-[var(--text)] hover:bg-[var(--bg-alt)] border border-transparent hover:border-[var(--border)]'
            }`}
          >
            <Wand2 className="w-4 h-4 text-[var(--accent)]" />
            <span>AI Editor</span>
          </Link>

          {/* Extension */}
          <Link
            to="/extension"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-150 ${
              location.pathname === '/extension'
                ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-sm'
                : 'text-[var(--text)] hover:bg-[var(--bg-alt)] border border-transparent hover:border-[var(--border)]'
            }`}
          >
            <ChromeIcon className="w-4 h-4 text-[var(--text-muted)]" />
            <span>Extension</span>
          </Link>

          {/* Blog */}
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
            className="p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors cursor-pointer"
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
            className="lg:hidden p-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors cursor-pointer"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-[var(--border)] bg-[var(--bg)] px-4 pt-2 pb-6 space-y-1">
          <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] px-3 py-2">
            Social Media Downloaders
          </div>
          {[...primaryNavLinks, ...secondaryNavLinks].map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-[var(--primary)] text-[var(--on-primary)]'
                    : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--on-primary)]' : 'text-[var(--text-muted)]'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
          
          <div className="border-t border-[var(--border)] my-2 pt-2">
            <Link
              to="/ai-video-editor"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                location.pathname === '/ai-video-editor'
                  ? 'bg-[var(--primary)] text-[var(--on-primary)]'
                  : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
              }`}
            >
              <Wand2 className="w-4 h-4 text-[var(--accent)]" />
              <span>AI Video Editor</span>
            </Link>
            <Link
              to="/blog"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                location.pathname === '/blog'
                  ? 'bg-[var(--primary)] text-[var(--on-primary)]'
                  : 'text-[var(--text)] hover:bg-[var(--bg-alt)]'
              }`}
            >
              <Newspaper className="w-4 h-4 text-[var(--text-muted)]" />
              <span>Blog & Articles</span>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
