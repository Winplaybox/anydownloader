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
  Award
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';
import TopChannelsMegaMenu from './TopChannelsMegaMenu.jsx';

export default function Header() {
  const [openMegaMenu, setOpenMegaMenu] = useState(false);
  const [openYoutubeMenu, setOpenYoutubeMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const megaMenuRef = useRef(null);
  const ytMenuRef = useRef(null);
  const location = useLocation();

  // Close menus on route change or click outside
  useEffect(() => {
    setOpenMegaMenu(false);
    setOpenYoutubeMenu(false);
    setMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (megaMenuRef.current && !megaMenuRef.current.contains(e.target)) {
        setOpenMegaMenu(false);
      }
      if (ytMenuRef.current && !ytMenuRef.current.contains(e.target)) {
        setOpenYoutubeMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const ytFeatures = [
    { title: 'YouTube Video Downloader', desc: 'Download Full HD & 4K Videos', icon: Video, path: '/youtube-video-downloader' },
    { title: 'YouTube MP4', desc: 'Direct MP4 formats in all qualities', icon: Download, path: '/youtube-mp4' },
    { title: 'YouTube Shorts', desc: 'Fast vertical video downloader', icon: Sparkles, path: '/youtube-shorts' },
    { title: 'YouTube MP3', desc: 'Extract audio up to 320 kbps high fidelity', icon: Music, path: '/youtube-mp3' },
    { title: 'YouTube Transcript', desc: 'Interactive timestamped transcript generator', icon: FileText, path: '/youtube-transcript' },
    { title: 'YouTube Subtitles', desc: 'Download subtitles in SRT & VTT formats', icon: Subtitles, path: '/youtube-subtitles' },
    { title: 'YouTube Thumbnails (All Quality)', desc: 'Maxres, HD, SD & HQ image downloads', icon: ImageIcon, path: '/youtube-thumbnail' }
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

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-1.5 xl:gap-2 text-xs font-semibold text-slate-300">
          
          {/* YouTube Category Dropdown */}
          <div className="relative" ref={ytMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenYoutubeMenu(!openYoutubeMenu);
                setOpenMegaMenu(false);
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

            {/* YouTube Dropdown Menu */}
            {openYoutubeMenu && (
              <div className="absolute left-0 mt-2 w-72 bg-slate-950 border border-slate-800 rounded-2xl p-2 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="px-3 py-1.5 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  YouTube Tool Suite
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
                      <div>
                        <div className="font-bold text-white text-xs group-hover:text-rose-400 transition">{feat.title}</div>
                        <div className="text-[10px] text-slate-400 leading-tight">{feat.desc}</div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Top YouTube Channels Mega Menu Trigger */}
          <div className="relative" ref={megaMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenMegaMenu(!openMegaMenu);
                setOpenYoutubeMenu(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition cursor-pointer ${
                openMegaMenu || location.pathname === '/top-100-youtube-channels'
                  ? 'bg-slate-900 text-white border border-slate-700 shadow-md' 
                  : 'hover:bg-slate-900 hover:text-white'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span>Top YouTube Channels</span>
              <ChevronDown className={`w-3.5 h-3.5 transition transform ${openMegaMenu ? 'rotate-180 text-rose-500' : 'text-slate-500'}`} />
            </button>
          </div>

          {/* Facebook */}
          <Link
            to="/facebook-video-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname === '/facebook-video-downloader'
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />
            <span>Facebook</span>
          </Link>

          {/* Instagram */}
          <Link
            to="/instagram-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname === '/instagram-downloader'
                ? 'bg-slate-900 text-white border border-slate-800'
                : 'hover:bg-slate-900 hover:text-white'
            }`}
          >
            <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />
            <span>Instagram</span>
          </Link>

          {/* TikTok */}
          <Link
            to="/tiktok-downloader"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
              location.pathname === '/tiktok-downloader'
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
            to="/top-100-youtube-channels"
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

      {/* FIXED CENTRED MEGA MENU (Never squished!) */}
      {openMegaMenu && (
        <div
          ref={megaMenuRef}
          className="fixed inset-x-0 top-16 flex justify-center z-50 px-4 pt-3 pointer-events-none"
        >
          <div className="pointer-events-auto w-full max-w-4xl shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
            <TopChannelsMegaMenu
              onClose={() => setOpenMegaMenu(false)}
            />
          </div>
        </div>
      )}

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-800 bg-slate-950/98 px-4 py-6 space-y-4 max-h-[85vh] overflow-y-auto">
          {/* Top 100 YouTube Channels Prominent Link */}
          <Link
            to="/top-100-youtube-channels"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center justify-between p-3 rounded-2xl bg-gradient-to-r from-rose-950/40 to-slate-900 border border-rose-500/30 text-white font-bold text-xs"
          >
            <div className="flex items-center gap-2.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Top 100 Most Subscribed Channels</span>
            </div>
            <span className="text-[10px] bg-rose-500 text-white px-2 py-0.5 rounded-full font-bold">12H Ranks</span>
          </Link>

          {/* YouTube Tools */}
          <div className="pt-2">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 px-1">
              YouTube Tools
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {ytFeatures.map((feat, idx) => {
                const Icon = feat.icon;
                return (
                  <Link
                    key={idx}
                    to={feat.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-900/60 border border-slate-800/80 text-slate-300 text-xs font-semibold hover:text-white"
                  >
                    <Icon className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>{feat.title}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Social Platforms */}
          <div className="pt-2">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 px-1">
              Other Supported Platforms
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <Link
                to="/facebook-video-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold"
              >
                <FacebookIcon className="w-4 h-4 text-blue-500" />
                <span>Facebook</span>
              </Link>
              <Link
                to="/instagram-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold"
              >
                <InstagramIcon className="w-4 h-4 text-pink-500" />
                <span>Instagram</span>
              </Link>
              <Link
                to="/tiktok-downloader"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-semibold"
              >
                <TiktokIcon className="w-4 h-4 text-cyan-400" />
                <span>TikTok</span>
              </Link>
            </div>
          </div>

          {/* Legal Pages for AdSense Compliance */}
          <div className="pt-4 border-t border-slate-800/80 flex flex-wrap gap-4 text-[11px] text-slate-500">
            <Link to="/privacy-policy" onClick={() => setMobileMenuOpen(false)} className="hover:text-slate-300">Privacy Policy</Link>
            <Link to="/terms-of-service" onClick={() => setMobileMenuOpen(false)} className="hover:text-slate-300">Terms of Service</Link>
            <Link to="/contact" onClick={() => setMobileMenuOpen(false)} className="hover:text-slate-300">Contact Us</Link>
          </div>
        </div>
      )}
    </header>
  );
}
