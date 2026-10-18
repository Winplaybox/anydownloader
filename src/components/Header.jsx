import React, { useState, useRef, useEffect } from 'react';
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
  ExternalLink 
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';
import TopChannelsMegaMenu from './TopChannelsMegaMenu.jsx';

export default function Header({ onSelectCategory, onSelectTopChannelsFilter }) {
  const [openMegaMenu, setOpenMegaMenu] = useState(false);
  const [openYoutubeMenu, setOpenYoutubeMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const megaMenuRef = useRef(null);
  const ytMenuRef = useRef(null);

  // Close dropdowns on outside click
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
    { title: 'YouTube Video Downloader', desc: 'Download Full HD & 4K Videos', icon: Video, mode: 'video' },
    { title: 'YouTube MP4', desc: 'Direct MP4 formats in all qualities', icon: Download, mode: 'mp4' },
    { title: 'YouTube Shorts', desc: 'Fast vertical video downloader', icon: Sparkles, mode: 'shorts' },
    { title: 'YouTube MP3', desc: 'Extract audio up to 320 kbps high fidelity', icon: Music, mode: 'mp3' },
    { title: 'YouTube Transcript', desc: 'Interactive timestamped transcript generator', icon: FileText, mode: 'transcript' },
    { title: 'YouTube Subtitles', desc: 'Download subtitles in SRT & VTT formats', icon: Subtitles, mode: 'subtitles' },
    { title: 'YouTube Thumbnails (All Quality)', desc: 'Maxres, HD, SD & HQ image downloads', icon: ImageIcon, mode: 'thumbnails' }
  ];

  function handleSelectYtFeature(mode) {
    if (onSelectCategory) {
      onSelectCategory('youtube', mode);
    }
    setOpenYoutubeMenu(false);
    setMobileMenuOpen(false);
    // Scroll to downloader input smoothly
    const el = document.getElementById('downloader-input');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  function handleSelectPlatform(platform) {
    if (onSelectCategory) {
      onSelectCategory(platform);
    }
    setMobileMenuOpen(false);
    const el = document.getElementById('downloader-input');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  function handleMegaMenuFilter(filter) {
    if (onSelectTopChannelsFilter) {
      onSelectTopChannelsFilter(filter);
    }
    setOpenMegaMenu(false);
    setMobileMenuOpen(false);
    const el = document.getElementById('top-youtube-channels');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <a href="/" className="flex items-center gap-2.5 group shrink-0">
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
        </a>

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-2 xl:gap-3 text-xs font-semibold text-slate-300">
          {/* YouTube Category Dropdown */}
          <div className="relative" ref={ytMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenYoutubeMenu(!openYoutubeMenu);
                setOpenMegaMenu(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
                openYoutubeMenu ? 'bg-slate-900 text-white' : 'hover:bg-slate-900 hover:text-white'
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
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectYtFeature(feat.mode)}
                      className="w-full text-left p-2.5 rounded-xl hover:bg-slate-900 flex items-start gap-3 transition group"
                    >
                      <div className="w-7 h-7 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-rose-500 group-hover:text-white transition">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="font-bold text-white text-xs group-hover:text-rose-400 transition">{feat.title}</div>
                        <div className="text-[10px] text-slate-400 leading-tight">{feat.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Top YouTube Channels Mega Menu Toggle (Exactly as in User Reference Image) */}
          <div className="relative" ref={megaMenuRef}>
            <button
              type="button"
              onClick={() => {
                setOpenMegaMenu(!openMegaMenu);
                setOpenYoutubeMenu(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition ${
                openMegaMenu 
                  ? 'bg-slate-900 text-white border border-slate-700 shadow-md' 
                  : 'hover:bg-slate-900 hover:text-white'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span>Top YouTube Channels</span>
              <ChevronDown className={`w-3.5 h-3.5 transition transform ${openMegaMenu ? 'rotate-180 text-rose-500' : 'text-slate-500'}`} />
            </button>

            {/* Mega Menu Dropdown */}
            {openMegaMenu && (
              <div className="absolute left-1/2 -translate-x-1/2 mt-3 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <TopChannelsMegaMenu
                  onSelectFilter={handleMegaMenuFilter}
                  onClose={() => setOpenMegaMenu(false)}
                />
              </div>
            )}
          </div>

          {/* Facebook */}
          <button
            type="button"
            onClick={() => handleSelectPlatform('facebook')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl hover:bg-slate-900 hover:text-white transition cursor-pointer"
          >
            <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />
            <span>Facebook</span>
          </button>

          {/* Instagram */}
          <button
            type="button"
            onClick={() => handleSelectPlatform('instagram')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl hover:bg-slate-900 hover:text-white transition cursor-pointer"
          >
            <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />
            <span>Instagram</span>
          </button>

          {/* TikTok */}
          <button
            type="button"
            onClick={() => handleSelectPlatform('tiktok')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl hover:bg-slate-900 hover:text-white transition cursor-pointer"
          >
            <TiktokIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>TikTok</span>
          </button>
        </nav>

        {/* Action Button & Mobile Toggle */}
        <div className="flex items-center gap-2.5">
          <a
            href="#top-youtube-channels"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-bold text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-600 px-3.5 py-2 rounded-xl border border-rose-500/20 hover:border-transparent transition"
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Rankings 100</span>
          </a>

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-slate-950 border-b border-slate-800 p-4 space-y-3 animate-in fade-in duration-200">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Categories</div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleSelectPlatform('youtube')}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-white text-left"
            >
              <YoutubeIcon className="w-4 h-4 text-red-500" />
              <span>YouTube</span>
            </button>
            <button
              onClick={() => handleSelectPlatform('instagram')}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-white text-left"
            >
              <InstagramIcon className="w-4 h-4 text-pink-500" />
              <span>Instagram</span>
            </button>
            <button
              onClick={() => handleSelectPlatform('tiktok')}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-white text-left"
            >
              <TiktokIcon className="w-4 h-4 text-cyan-400" />
              <span>TikTok</span>
            </button>
            <button
              onClick={() => handleSelectPlatform('facebook')}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-white text-left"
            >
              <FacebookIcon className="w-4 h-4 text-blue-500" />
              <span>Facebook</span>
            </button>
          </div>

          <div className="pt-2">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">YouTube Tools</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {ytFeatures.map((f, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectYtFeature(f.mode)}
                  className="p-2 text-left text-xs text-slate-300 hover:text-white hover:bg-slate-900 rounded-lg transition"
                >
                  • {f.title}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                const el = document.getElementById('top-youtube-channels');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-amber-500 text-white font-bold text-xs shadow-lg"
            >
              <TrendingUp className="w-4 h-4" />
              <span>View Top 100 YouTube Channels</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
