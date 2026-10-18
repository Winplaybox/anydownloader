import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Download, 
  ChevronDown, 
  Menu, 
  X, 
  Sparkles, 
  TrendingUp, 
  Video, 
  Music, 
  FileText, 
  Image as ImageIcon, 
  Subtitles, 
  ExternalLink,
  Award,
  Newspaper,
  Zap,
  ArrowRight
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';

export default function Header() {
  const [openYoutubeMenu, setOpenYoutubeMenu] = useState(false);
  const [openFacebookMenu, setOpenFacebookMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const ytMenuRef = useRef(null);
  const fbMenuRef = useRef(null);
  const location = useLocation();

  // Close menus on route change
  useEffect(() => {
    setOpenYoutubeMenu(false);
    setOpenFacebookMenu(false);
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Lock body scroll when mobile menu is open to prevent background scrolling
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  // Click outside to close desktop dropdowns
  useEffect(() => {
    function handleClickOutside(e) {
      if (ytMenuRef.current && !ytMenuRef.current.contains(e.target)) {
        setOpenYoutubeMenu(false);
      }
      if (fbMenuRef.current && !fbMenuRef.current.contains(e.target)) {
        setOpenFacebookMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const ytTools = [
    { title: 'YouTube Video Downloader', desc: 'Universal video & audio converter', icon: Video, path: '/youtube/youtube-video-downloader' },
    { title: 'YouTube MP4', desc: 'Download Full HD 1080p, 720p & 4K MP4 Videos', icon: Download, path: '/youtube/youtube-mp4' },
    { title: 'YouTube Shorts', desc: 'Fast vertical video downloader', icon: Sparkles, path: '/youtube/youtube-shorts' },
    { title: 'YouTube MP3', desc: 'Extract audio up to 320 kbps high fidelity', icon: Music, path: '/youtube/youtube-mp3' },
    { title: 'YouTube Transcript', desc: 'Interactive timestamped transcript generator', icon: FileText, path: '/youtube/youtube-transcript' },
    { title: 'YouTube Subtitles', desc: 'Download subtitles in SRT & VTT formats', icon: Subtitles, path: '/youtube/youtube-subtitles' },
    { title: 'YouTube Thumbnails', desc: 'Maxres 1080p, HD, SD & HQ image downloads', icon: ImageIcon, path: '/youtube/youtube-thumbnails' },
  ];

  const fbTools = [
    { title: 'Facebook Video Downloader', desc: 'Download public videos in 1080p & 720p HD', icon: Download, path: '/facebook/facebook-video-downloader' },
    { title: 'Facebook Reels', desc: 'Save 9:16 vertical reels without watermarks', icon: Sparkles, path: '/facebook/facebook-reels' },
    { title: 'Facebook Posts', desc: 'Download photos, albums & status posts', icon: ImageIcon, path: '/facebook/facebook-posts' },
    { title: 'Facebook Watch', desc: 'Episodes, shows & recorded live streams', icon: Video, path: '/facebook/facebook-watch' },
    { title: 'Facebook Stories', desc: 'Save public stories before they expire', icon: FileText, path: '/facebook/facebook-stories' },
    { title: 'Facebook MP3', desc: 'Extract 320kbps & 192kbps MP3 audio tracks', icon: Music, path: '/facebook/facebook-mp3' },
    { title: 'Facebook Transcript', desc: 'Extract captions & speech text transcripts', icon: FileText, path: '/facebook/facebook-transcript' },
    { title: 'Facebook Thumbnails', desc: 'Full-resolution video cover & poster artwork', icon: ImageIcon, path: '/facebook/facebook-thumbnails' },
  ];

  const quickFbCountries = [
    { name: 'United States', flag: '🇺🇸' },
    { name: 'Portugal', flag: '🇵🇹' },
    { name: 'Spain', flag: '🇪🇸' },
    { name: 'South Korea', flag: '🇰🇷' },
    { name: 'China', flag: '🇨🇳' },
    { name: 'Brazil', flag: '🇧🇷' }
  ];

  const quickCountries = [
    { name: 'United States', flag: '🇺🇸' },
    { name: 'India', flag: '🇮🇳' },
    { name: 'Brazil', flag: '🇧🇷' },
    { name: 'Japan', flag: '🇯🇵' },
    { name: 'United Kingdom', flag: '🇬🇧' },
    { name: 'Germany', flag: '🇩🇪' }
  ];

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/95 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        
        {/* Brand Logo - Flat & Sleek */}
        <Link to="/" className="flex items-center gap-2.5 group shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-600 via-pink-600 to-amber-500 flex items-center justify-center text-white shadow-lg shadow-rose-600/25 group-hover:scale-105 transition transform">
            <Download className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg tracking-tight text-white">
                OVD <span className="bg-gradient-to-r from-rose-500 to-amber-400 bg-clip-text text-transparent">Downloader</span>
              </span>
              <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                PRO
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium hidden sm:block">ovd.winplaybox.in</p>
          </div>
        </Link>

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-1.5 xl:gap-2 text-xs font-semibold text-slate-300">
          
          {/* 1. YouTube Dropdown Toggle */}
          <div className="relative" ref={ytMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenYoutubeMenu(!openYoutubeMenu);
                setOpenFacebookMenu(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition cursor-pointer ${
                openYoutubeMenu || location.pathname.startsWith('/youtube')
                  ? 'bg-slate-900 text-white border border-slate-800'
                  : 'hover:bg-slate-900 hover:text-white'
              }`}
            >
              <YoutubeIcon className="w-4 h-4 text-red-500" />
              <span>YouTube</span>
              <ChevronDown className={`w-3.5 h-3.5 transition transform ${openYoutubeMenu ? 'rotate-180 text-rose-500' : 'text-slate-500'}`} />
            </button>
          </div>

          {/* 2. Facebook Dropdown Toggle */}
          <div className="relative" ref={fbMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenFacebookMenu(!openFacebookMenu);
                setOpenYoutubeMenu(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition cursor-pointer ${
                openFacebookMenu || location.pathname.startsWith('/facebook')
                  ? 'bg-slate-900 text-white border border-slate-800'
                  : 'hover:bg-slate-900 hover:text-white'
              }`}
            >
              <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />
              <span>Facebook</span>
              <ChevronDown className={`w-3.5 h-3.5 transition transform ${openFacebookMenu ? 'rotate-180 text-blue-500' : 'text-slate-500'}`} />
            </button>
          </div>

          {/* 3. Instagram */}
          <Link
            to="/instagram/instagram-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname.startsWith('/instagram')
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />
            <span>Instagram</span>
          </Link>

          {/* 4. TikTok */}
          <Link
            to="/tiktok/tiktok-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname.startsWith('/tiktok')
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <TiktokIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>TikTok</span>
          </Link>

          {/* 5. Blogs (Real-Time Social Media Updates) */}
          <Link
            to="/blogs"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname.startsWith('/blog')
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <Newspaper className="w-3.5 h-3.5 text-amber-400" />
            <span>Blogs</span>
          </Link>

          {/* 6. Updates (Product Releases & Changelog) */}
          <Link
            to="/updates"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname.startsWith('/updates')
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-rose-400" />
            <span>Updates</span>
          </Link>
        </nav>

        {/* Right Action / Mobile Toggle */}
        <div className="flex items-center gap-3">
          {/* LatestNewsNX quick link for desktop */}
          <a
            href="https://latestnewsnx.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 text-xs font-bold text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-800 transition"
          >
            <span>LatestNewsNX</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition cursor-pointer"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* SPACIOUS YOUTUBE MEGA MENU (DESKTOP) */}
      {openYoutubeMenu && (
        <div
          ref={ytMenuRef}
          className="fixed inset-x-0 top-16 flex justify-center z-50 px-4 pt-3 pointer-events-none"
        >
          <div className="pointer-events-auto w-full max-w-4xl bg-slate-950/98 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-2xl text-slate-200 animate-in fade-in slide-in-from-top-2 duration-200">
            
            {/* Header */}
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <YoutubeIcon className="w-5 h-5 text-red-500" />
                <span className="font-extrabold text-white text-sm">YouTube Complete Suite & Rankings</span>
              </div>
              <Link
                to="/youtube/top-100-youtube-channels"
                onClick={() => setOpenYoutubeMenu(false)}
                className="text-xs font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1 transition"
              >
                <span>View Full Top 100 Database &rarr;</span>
              </Link>
            </div>

            {/* Clean 2-Column Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-7 items-start">
              
              {/* Left Column: 7 Tools Suite */}
              <div className="space-y-1 md:border-r md:border-slate-800/80 md:pr-6">
                <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2.5">
                  YouTube Tools & Downloaders
                </div>
                {ytTools.map((feat, idx) => {
                  const Icon = feat.icon;
                  return (
                    <Link
                      key={idx}
                      to={feat.path}
                      onClick={() => setOpenYoutubeMenu(false)}
                      className="w-full text-left p-2 rounded-xl hover:bg-slate-900 flex items-start gap-3 transition group"
                    >
                      <div className="w-7 h-7 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-rose-500 group-hover:text-white transition">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-bold text-white text-xs group-hover:text-rose-400 transition">
                          {feat.title}
                        </div>
                        <div className="text-[10px] text-slate-400 leading-tight truncate">
                          {feat.desc}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Right Column: Top 100 YouTube Channels */}
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-rose-500" />
                      <h4 className="font-extrabold text-white text-sm">
                        Top 100 YouTube Channels
                      </h4>
                    </div>
                    <span className="text-[9px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded-full">
                      12H Auto-Sync
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed mb-4">
                    Global subscriber leaderboard recorded by OVD.winplaybox.in and refreshed every 12 hours.
                  </p>

                  {/* Quick Ranking Links */}
                  <div className="space-y-1.5 mb-4">
                    <Link
                      to="/youtube/top-100-youtube-channels?limit=50"
                      onClick={() => setOpenYoutubeMenu(false)}
                      className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white transition group"
                    >
                      <span className="font-medium">Top 50 Most Subscribed Channels</span>
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400 group-hover:translate-x-0.5 transition" />
                    </Link>

                    <Link
                      to="/youtube/top-100-youtube-channels?limit=100"
                      onClick={() => setOpenYoutubeMenu(false)}
                      className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white transition group"
                    >
                      <span className="font-medium">Top 100 Most Subscribed Channels</span>
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400 group-hover:translate-x-0.5 transition" />
                    </Link>
                  </div>

                  {/* Browse by Country */}
                  <div className="mb-4">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
                      Filter by Country
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {quickCountries.map((c) => (
                        <Link
                          key={c.name}
                          to={`/youtube/top-100-youtube-channels?country=${encodeURIComponent(c.name)}`}
                          onClick={() => setOpenYoutubeMenu(false)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs transition"
                        >
                          <span>{c.flag}</span>
                          <span>{c.name}</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Big Direct Button */}
                <Link
                  to="/youtube/top-100-youtube-channels"
                  onClick={() => setOpenYoutubeMenu(false)}
                  className="w-full mt-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white text-xs font-bold text-center shadow-lg shadow-rose-600/20 transition flex items-center justify-center gap-2"
                >
                  <span>Open Full Top 100 Ranking Database</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

            </div>
          </div>
        </div>
      )}

      {/* SPACIOUS FACEBOOK MEGA MENU (DESKTOP) */}
      {openFacebookMenu && (
        <div
          ref={fbMenuRef}
          className="fixed inset-x-0 top-16 flex justify-center z-50 px-4 pt-3 pointer-events-none"
        >
          <div className="pointer-events-auto w-full max-w-4xl bg-slate-950/98 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-2xl text-slate-200 animate-in fade-in slide-in-from-top-2 duration-200">
            
            {/* Header */}
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <FacebookIcon className="w-5 h-5 text-blue-500" />
                <span className="font-extrabold text-white text-sm">Facebook Complete Suite & Top Pages</span>
              </div>
              <Link
                to="/facebook/top-100-facebook-pages"
                onClick={() => setOpenFacebookMenu(false)}
                className="text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition"
              >
                <span>View Full Top 100 Database &rarr;</span>
              </Link>
            </div>

            {/* Clean 2-Column Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-7 items-start">
              
              {/* Left Column: Facebook Tools */}
              <div className="space-y-1 md:border-r md:border-slate-800/80 md:pr-6">
                <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2.5">
                  Facebook Tools & Downloaders
                </div>
                {fbTools.map((feat, idx) => {
                  const Icon = feat.icon;
                  return (
                    <Link
                      key={idx}
                      to={feat.path}
                      onClick={() => setOpenFacebookMenu(false)}
                      className="w-full text-left p-2 rounded-xl hover:bg-slate-900 flex items-start gap-3 transition group"
                    >
                      <div className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-blue-600 group-hover:text-white transition">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-bold text-white text-xs group-hover:text-blue-400 transition">
                          {feat.title}
                        </div>
                        <div className="text-[10px] text-slate-400 leading-tight truncate">
                          {feat.desc}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Right Column: Top 100 Facebook Pages */}
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-blue-400" />
                      <h4 className="font-extrabold text-white text-sm">
                        Top 100 Facebook Pages
                      </h4>
                    </div>
                    <span className="text-[9px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full">
                      12H Auto-Sync
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed mb-4">
                    Global follower rankings for verified pages, athletes, media organizations, and creators.
                  </p>

                  {/* Quick Ranking Links */}
                  <div className="space-y-1.5 mb-4">
                    <Link
                      to="/facebook/top-100-facebook-pages?limit=50"
                      onClick={() => setOpenFacebookMenu(false)}
                      className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white transition group"
                    >
                      <span className="font-medium">Top 50 Most Followed Pages</span>
                      <TrendingUp className="w-3.5 h-3.5 text-blue-400 group-hover:translate-x-0.5 transition" />
                    </Link>

                    <Link
                      to="/facebook/top-100-facebook-pages?limit=100"
                      onClick={() => setOpenFacebookMenu(false)}
                      className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white transition group"
                    >
                      <span className="font-medium">Top 100 Most Followed Pages</span>
                      <TrendingUp className="w-3.5 h-3.5 text-blue-400 group-hover:translate-x-0.5 transition" />
                    </Link>
                  </div>

                  {/* Browse by Country */}
                  <div className="mb-4">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
                      Filter by Country
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {quickFbCountries.map((c) => (
                        <Link
                          key={c.name}
                          to={`/facebook/top-100-facebook-pages?country=${encodeURIComponent(c.name)}`}
                          onClick={() => setOpenFacebookMenu(false)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950/70 hover:bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs transition"
                        >
                          <span>{c.flag}</span>
                          <span>{c.name}</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Big Direct Button */}
                <Link
                  to="/facebook/top-100-facebook-pages"
                  onClick={() => setOpenFacebookMenu(false)}
                  className="w-full mt-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold text-center shadow-lg shadow-blue-600/20 transition flex items-center justify-center gap-2"
                >
                  <span>Open Full Top 100 Pages Database</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

            </div>
          </div>
        </div>
      )}

      {/* FIXED SLIDE-OVER DRAWER FOR MOBILE & TABLET (WITH INDEPENDENT SCROLL) */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop Blur Overlay */}
          <div 
            className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />

          {/* Fixed Drawer Panel */}
          <div className="fixed top-0 right-0 bottom-0 w-[88vw] max-w-sm sm:max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col z-50 animate-in slide-in-from-right duration-200">
            
            {/* Sticky Drawer Top Bar */}
            <div className="h-16 px-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/95 sticky top-0 z-10 shrink-0">
              <Link 
                to="/" 
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5"
              >
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-rose-600 via-pink-600 to-amber-500 flex items-center justify-center text-white shadow-md">
                  <Download className="w-4 h-4 stroke-[2.5]" />
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-base tracking-tight text-white">
                    OVD <span className="bg-gradient-to-r from-rose-500 to-amber-400 bg-clip-text text-transparent">Downloader</span>
                  </span>
                  <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    PRO
                  </span>
                </div>
              </Link>

              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
                aria-label="Close navigation menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scrollable Drawer Body with Independent Smooth Scroll */}
            <div className="flex-1 overflow-y-auto px-4 py-5 space-y-6 overscroll-contain">
              
              {/* 1. YouTube Complete Suite */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-red-400 uppercase tracking-wider">
                    <YoutubeIcon className="w-3.5 h-3.5 text-red-500" />
                    <span>YouTube Suite</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-semibold">7 Tools</span>
                </div>

                {/* Top 100 YouTube Channels Banner */}
                <Link
                  to="/youtube/top-100-youtube-channels"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-rose-950/30 border border-rose-500/30 hover:border-rose-500/50 text-white font-bold text-xs transition group"
                >
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Top 100 YouTube Channels</span>
                  </div>
                  <span className="text-[9px] bg-rose-500 text-white px-2 py-0.5 rounded-full font-bold">12H Sync</span>
                </Link>

                {/* All 7 YouTube Tools */}
                <div className="space-y-1 pl-1">
                  {ytTools.map((t, idx) => {
                    const Icon = t.icon;
                    return (
                      <Link
                        key={idx}
                        to={t.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center justify-between p-2 rounded-xl text-xs transition ${
                          location.pathname === t.path
                            ? 'bg-rose-500/15 text-rose-300 font-semibold border border-rose-500/30'
                            : 'text-slate-300 hover:text-white hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className="w-3.5 h-3.5 text-rose-400" />
                          <span>{t.title}</span>
                        </div>
                        <ChevronDown className="w-3 h-3 text-slate-600 -rotate-90" />
                      </Link>
                    );
                  })}
                </div>
              </div>

              {/* 2. Facebook Complete Suite */}
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-blue-400 uppercase tracking-wider">
                    <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />
                    <span>Facebook Suite</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-semibold">8 Tools</span>
                </div>

                {/* Top 100 Facebook Pages Banner */}
                <Link
                  to="/facebook/top-100-facebook-pages"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-blue-950/30 border border-blue-500/30 hover:border-blue-500/50 text-white font-bold text-xs transition group"
                >
                  <div className="flex items-center gap-2">
                    <Award className="w-3.5 h-3.5 text-blue-400" />
                    <span>Top 100 Facebook Pages</span>
                  </div>
                  <span className="text-[9px] bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold">12H Sync</span>
                </Link>

                {/* All 8 Facebook Tools */}
                <div className="space-y-1 pl-1">
                  {fbTools.map((t, idx) => {
                    const Icon = t.icon;
                    return (
                      <Link
                        key={idx}
                        to={t.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center justify-between p-2 rounded-xl text-xs transition ${
                          location.pathname === t.path
                            ? 'bg-blue-500/15 text-blue-300 font-semibold border border-blue-500/30'
                            : 'text-slate-300 hover:text-white hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className="w-3.5 h-3.5 text-blue-400" />
                          <span>{t.title}</span>
                        </div>
                        <ChevronDown className="w-3 h-3 text-slate-600 -rotate-90" />
                      </Link>
                    );
                  })}
                </div>
              </div>

              {/* 3. Other Platforms */}
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
                  Other Platforms
                </div>
                <div className="space-y-1 pl-1">
                  <Link
                    to="/instagram/instagram-downloader"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-between p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />
                      <span>Instagram Downloader</span>
                    </div>
                    <ChevronDown className="w-3 h-3 text-slate-600 -rotate-90" />
                  </Link>

                  <Link
                    to="/tiktok/tiktok-downloader"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-between p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <TiktokIcon className="w-3.5 h-3.5 text-cyan-400" />
                      <span>TikTok Video Downloader</span>
                    </div>
                    <ChevronDown className="w-3 h-3 text-slate-600 -rotate-90" />
                  </Link>
                </div>
              </div>

              {/* 4. News & Releases */}
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
                  News & Releases
                </div>
                <div className="space-y-1 pl-1">
                  <Link
                    to="/blogs"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-between p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <Newspaper className="w-3.5 h-3.5 text-amber-400" />
                      <span>Social Media Updates Blog</span>
                    </div>
                    <span className="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.2 rounded-full font-bold">Daily</span>
                  </Link>
                  <Link
                    to="/updates"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-between p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <Zap className="w-3.5 h-3.5 text-rose-400" />
                      <span>Product Release Changelog</span>
                    </div>
                    <span className="text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-1.5 py-0.2 rounded-full font-bold">v2.6</span>
                  </Link>
                </div>
              </div>

              {/* 5. Legal & Policies (Google AdSense Compliance) */}
              <div className="pt-3 border-t border-slate-800/80 flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-slate-400 px-1">
                <Link to="/privacy-policy" onClick={() => setMobileMenuOpen(false)} className="hover:text-white transition">Privacy Policy</Link>
                <Link to="/terms-of-service" onClick={() => setMobileMenuOpen(false)} className="hover:text-white transition">Terms of Service</Link>
                <Link to="/contact" onClick={() => setMobileMenuOpen(false)} className="hover:text-white transition">Contact Us</Link>
              </div>

            </div>
          </div>
        </div>
      )}
    </header>
  );
}
