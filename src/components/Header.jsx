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
  ShieldCheck,
  Award,
  Globe,
  Tag
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';
import TopChannelsMegaMenu from './TopChannelsMegaMenu.jsx';

export default function Header() {
  const [openYoutubeMenu, setOpenYoutubeMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const ytMenuRef = useRef(null);
  const location = useLocation();

  // Close menu on route change
  useEffect(() => {
    setOpenYoutubeMenu(false);
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(e) {
      if (ytMenuRef.current && !ytMenuRef.current.contains(e.target)) {
        setOpenYoutubeMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const ytFeatures = [
    { title: 'YouTube Video Downloader', desc: 'Download Full HD & 4K Videos', icon: Video, path: '/youtube/youtube-video-downloader' },
    { title: 'YouTube MP4', desc: 'Direct MP4 formats in all qualities', icon: Download, path: '/youtube/youtube-mp4' },
    { title: 'YouTube Shorts', desc: 'Fast vertical video downloader', icon: Sparkles, path: '/youtube/youtube-shorts' },
    { title: 'YouTube MP3', desc: 'Extract audio up to 320 kbps high fidelity', icon: Music, path: '/youtube/youtube-mp3' },
    { title: 'YouTube Transcript', desc: 'Interactive timestamped transcript generator', icon: FileText, path: '/youtube/youtube-transcript' },
    { title: 'YouTube Subtitles', desc: 'Download subtitles in SRT & VTT formats', icon: Subtitles, path: '/youtube/youtube-subtitles' },
    { title: 'YouTube Thumbnails', desc: 'Maxres 1080p, HD, SD & HQ image downloads', icon: ImageIcon, path: '/youtube/youtube-thumbnails' },
    { title: 'Top 100 Channels (12H)', desc: 'Live global subscriber ranking database', icon: Award, path: '/youtube/top-100-youtube-channels', badge: '12H' }
  ];

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/95 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        
        {/* Brand Logo */}
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

        {/* Desktop Nav Items (Clean 4 Categories) */}
        <nav className="hidden lg:flex items-center gap-1.5 xl:gap-2 text-xs font-semibold text-slate-300">
          
          {/* 1. YouTube Category with Unified Mega Menu */}
          <div className="relative" ref={ytMenuRef}>
            <button
              type="button"
              onClick={() => setOpenYoutubeMenu(!openYoutubeMenu)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition cursor-pointer ${
                openYoutubeMenu || location.pathname.startsWith('/youtube')
                  ? 'bg-slate-900 text-white border border-slate-700 shadow-md shadow-rose-500/10'
                  : 'hover:bg-slate-900 hover:text-white'
              }`}
            >
              <YoutubeIcon className="w-4 h-4 text-red-500" />
              <span>YouTube</span>
              <span className="text-[9px] bg-rose-500/20 text-rose-400 border border-rose-500/30 px-1.5 py-0.2 rounded-full font-bold ml-0.5">
                Suite & 100 Ranks
              </span>
              <ChevronDown className={`w-3.5 h-3.5 transition transform ${openYoutubeMenu ? 'rotate-180 text-rose-500' : 'text-slate-500'}`} />
            </button>
          </div>

          {/* 2. Facebook */}
          <Link
            to="/facebook/facebook-video-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname.startsWith('/facebook')
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />
            <span>Facebook</span>
          </Link>

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
        </nav>

        {/* Right CTA Button & Mobile Toggle */}
        <div className="flex items-center gap-2.5">
          <Link
            to="/youtube/top-100-youtube-channels"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-bold text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-600 px-3.5 py-2 rounded-xl border border-rose-500/20 hover:border-transparent transition"
          >
            <Award className="w-3.5 h-3.5" />
            <span>Top 100 Channels</span>
          </Link>

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

      {/* FIXED CENTRED UNIFIED YOUTUBE MEGA MENU */}
      {openYoutubeMenu && (
        <div
          ref={ytMenuRef}
          className="fixed inset-x-0 top-16 flex justify-center z-50 px-4 pt-3 pointer-events-none"
        >
          <div className="pointer-events-auto w-full max-w-5xl bg-slate-950/98 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-2xl text-slate-200 animate-in fade-in slide-in-from-top-2 duration-200">
            {/* Header info */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-slate-800 gap-2">
              <div className="flex items-center gap-2.5">
                <YoutubeIcon className="w-5 h-5 text-red-500" />
                <span className="font-extrabold text-white text-sm">YouTube Complete Suite & Rankings</span>
                <span className="text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold px-2 py-0.5 rounded-full">
                  Updated Every 12 Hours
                </span>
              </div>
              <Link
                to="/youtube/top-100-youtube-channels"
                onClick={() => setOpenYoutubeMenu(false)}
                className="text-xs font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1 transition self-end sm:self-auto"
              >
                <span>View Full Top 100 Database &rarr;</span>
              </Link>
            </div>

            {/* Split Grid: Left = 8 Tools Suite, Right = Top Channels Mega Explorer */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: 8 Tools */}
              <div className="lg:col-span-5 space-y-1 lg:border-r lg:border-slate-800/80 lg:pr-5">
                <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
                  YouTube Tools & Downloaders
                </div>
                {ytFeatures.map((feat, idx) => {
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
                        <div className="font-bold text-white text-xs group-hover:text-rose-400 transition flex items-center gap-1.5">
                          <span>{feat.title}</span>
                          {feat.badge && (
                            <span className="text-[9px] bg-rose-500 text-white px-1.5 py-0.2 rounded font-extrabold">
                              {feat.badge}
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-400 leading-tight truncate">{feat.desc}</div>
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Right Column: Top Channels Explorer (Top 50, 100, Countries, Categories) */}
              <div className="lg:col-span-7">
                <TopChannelsMegaMenu
                  onClose={() => setOpenYoutubeMenu(false)}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-800 bg-slate-950/98 px-4 py-6 space-y-4 max-h-[85vh] overflow-y-auto">
          {/* Top 100 YouTube Channels Prominent Link */}
          <Link
            to="/youtube/top-100-youtube-channels"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center justify-between p-3 rounded-2xl bg-gradient-to-r from-rose-950/40 to-slate-900 border border-rose-500/30 text-white font-bold text-xs"
          >
            <div className="flex items-center gap-2.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Top 100 Most Subscribed Channels</span>
            </div>
            <span className="text-[10px] bg-rose-500 text-white px-2 py-0.5 rounded-full font-bold">12H Ranks</span>
          </Link>

          {/* YouTube Suite in Mobile */}
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 px-1">
              YouTube Suite
            </div>
            <div className="space-y-1">
              {ytFeatures.map((feat, idx) => (
                <Link
                  key={idx}
                  to={feat.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-2 p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
                >
                  <feat.icon className="w-3.5 h-3.5 text-rose-400" />
                  <span>{feat.title}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* Other Platforms in Mobile */}
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 px-1">
              Other Platforms
            </div>
            <div className="space-y-1">
              <Link
                to="/facebook/facebook-video-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
              >
                <FacebookIcon className="w-4 h-4 text-blue-500" />
                <span>Facebook Video Downloader</span>
              </Link>
              <Link
                to="/instagram/instagram-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
              >
                <InstagramIcon className="w-4 h-4 text-pink-500" />
                <span>Instagram Downloader</span>
              </Link>
              <Link
                to="/tiktok/tiktok-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 p-2 rounded-xl text-xs text-slate-300 hover:text-white hover:bg-slate-900 transition"
              >
                <TiktokIcon className="w-4 h-4 text-cyan-400" />
                <span>TikTok Video Downloader</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
