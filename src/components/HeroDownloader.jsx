import React from 'react';
import { 
  Download, 
  Clipboard, 
  Sparkles, 
  Loader2, 
  AlertCircle,
  Video,
  Music,
  FileText,
  Subtitles,
  Image as ImageIcon,
  Trophy,
  Zap,
  ArrowRight
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';

export default function HeroDownloader({ 
  url, 
  setUrl, 
  onFetch, 
  loading, 
  error,
  onPaste,
  activeCategory = 'youtube',
  onSelectCategory,
  activeSubfeature = 'all',
  onSelectSubfeature
}) {
  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      onFetch();
    }
  }

  const platforms = [
    { id: 'youtube', name: 'YouTube', icon: YoutubeIcon, color: 'text-red-500', activeBg: 'bg-red-500/10 border-red-500/40 text-white' },
    { id: 'facebook', name: 'Facebook', icon: FacebookIcon, color: 'text-blue-500', activeBg: 'bg-blue-500/10 border-blue-500/40 text-white' },
    { id: 'instagram', name: 'Instagram', icon: InstagramIcon, color: 'text-pink-500', activeBg: 'bg-pink-500/10 border-pink-500/40 text-white' },
    { id: 'tiktok', name: 'TikTok', icon: TiktokIcon, color: 'text-cyan-400', activeBg: 'bg-cyan-500/10 border-cyan-500/40 text-white' },
  ];

  const ytSubfeatures = [
    { id: 'all', label: 'YouTube', icon: Video, hint: 'Download YouTube videos in any resolution' },
    { id: 'mp4', label: 'YouTube MP4', icon: Download, hint: 'Direct 1080p, 720p & 4K MP4 video formats' },
    { id: 'shorts', label: 'YouTube Shorts', icon: Sparkles, hint: 'Fast download for YouTube Shorts vertical videos' },
    { id: 'mp3', label: 'YouTube MP3', icon: Music, hint: 'Convert & download audio up to 320 kbps high bitrate' },
    { id: 'transcript', label: 'YouTube Transcript', icon: FileText, hint: 'Interactive timestamped transcript & text exporter' },
    { id: 'subtitles', label: 'YouTube Subtitles', icon: Subtitles, hint: 'Download multi-language subtitles in SRT & VTT' },
    { id: 'thumbnails', label: 'YouTube Thumbnails', icon: ImageIcon, hint: 'All quality thumbnail images (1080p, 720p, 480p, SD)' },
    { id: 'top100', label: 'Top 100 Channels', icon: Trophy, hint: 'Global ranking by current subscriber count' },
  ];

  function getTitleAndDesc() {
    if (activeCategory === 'youtube') {
      return {
        badge: 'YouTube All-in-One Pro Downloader & Explorer',
        title: 'YouTube Video Downloader',
        gradient: 'YouTube MP4, Shorts, MP3 & Transcripts',
        desc: 'Extract full HD 1080p & 4K videos, separate 320kbps MP3 tracks, interactive transcripts, multi-language subtitles, and full-resolution thumbnail images for any YouTube video.'
      };
    }
    if (activeCategory === 'facebook') {
      return {
        badge: 'Facebook Watch & Reels Saver',
        title: 'Facebook Video Downloader',
        gradient: 'Full HD 1080p & High Quality Audio',
        desc: 'Download Facebook public videos, reels, stories, and watch clips directly in ultra high quality MP4 format.'
      };
    }
    if (activeCategory === 'instagram') {
      return {
        badge: 'Instagram Reels, Stories & Posts',
        title: 'Instagram Downloader',
        gradient: 'Reels, Carousels & High-Res Photos',
        desc: 'Save Instagram reels without quality loss, download stories, videos, and HD photos directly to your device.'
      };
    }
    if (activeCategory === 'tiktok') {
      return {
        badge: 'TikTok Video Downloader Without Watermark',
        title: 'TikTok Video Downloader',
        gradient: 'Original Audio & HD No-Watermark MP4',
        desc: 'Download clean TikTok videos with no watermark, background sounds in MP3, and instant HD playback.'
      };
    }
    return {
      badge: 'Universal Fast Online Downloader',
      title: 'Download Any Media',
      gradient: 'In Seconds',
      desc: 'Free fast media downloader for YouTube, Facebook, Instagram, TikTok, Twitter and more.'
    };
  }

  function getPlaceholder() {
    if (activeCategory === 'youtube') {
      if (activeSubfeature === 'shorts') return 'Paste YouTube Shorts link (e.g. https://www.youtube.com/shorts/...)...';
      if (activeSubfeature === 'mp3') return 'Paste YouTube URL to convert & download high-bitrate MP3...';
      if (activeSubfeature === 'transcript') return 'Paste YouTube URL to extract interactive timestamped transcript...';
      if (activeSubfeature === 'subtitles') return 'Paste YouTube URL to extract multi-language SRT/VTT subtitles...';
      if (activeSubfeature === 'thumbnails') return 'Paste YouTube URL to view & download all thumbnail resolutions...';
      return 'Paste YouTube video or Shorts link here (e.g. https://www.youtube.com/watch?v=...)...';
    }
    if (activeCategory === 'facebook') return 'Paste Facebook video or reel link (e.g. https://www.facebook.com/watch/...)...';
    if (activeCategory === 'instagram') return 'Paste Instagram reel, story, or post link (e.g. https://www.instagram.com/reel/...)...';
    if (activeCategory === 'tiktok') return 'Paste TikTok video link (e.g. https://www.tiktok.com/@...)...';
    return 'Paste video, reel, or audio link here...';
  }

  function handleSubfeatureClick(subId) {
    if (subId === 'top100') {
      const el = document.getElementById('top-youtube-channels');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
      return;
    }
    if (onSelectSubfeature) {
      onSelectSubfeature(subId);
    }
  }

  const info = getTitleAndDesc();

  return (
    <section id="downloader-input" className="relative pt-8 pb-14 overflow-hidden">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[320px] bg-gradient-to-r from-rose-600/20 via-purple-600/20 to-cyan-500/20 blur-[130px] pointer-events-none rounded-full" />

      <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
        
        {/* Main Category Tabs (YouTube, Facebook, Instagram, TikTok) */}
        <div className="inline-flex p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur-md mb-8 max-w-full overflow-x-auto">
          {platforms.map((p) => {
            const Icon = p.icon;
            const isActive = activeCategory === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  if (onSelectCategory) onSelectCategory(p.id);
                }}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-slate-800 text-white shadow-md border border-slate-700'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${p.color}`} />
                <span>{p.name}</span>
              </button>
            );
          })}
        </div>

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-rose-400 font-semibold mb-5 shadow-inner">
          <Sparkles className="w-3.5 h-3.5 text-rose-400" />
          <span>{info.badge}</span>
        </div>

        {/* Main Title */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-[1.1] mb-4">
          {info.title}
        </h1>

        {/* Dynamic Gradient Subtitle */}
        <p className="text-base sm:text-xl font-bold bg-gradient-to-r from-rose-400 via-pink-400 to-amber-300 bg-clip-text text-transparent mb-4">
          {info.gradient}
        </p>

        {/* Description */}
        <p className="text-slate-400 text-xs sm:text-sm max-w-2xl mx-auto mb-8 leading-relaxed">
          {info.desc}
        </p>

        {/* YouTube Tool Suite Pills (When YouTube is active) */}
        {activeCategory === 'youtube' && (
          <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-3xl mx-auto">
            {ytSubfeatures.map((sub) => {
              const SubIcon = sub.icon;
              const isSelected = activeSubfeature === sub.id;
              return (
                <button
                  key={sub.id}
                  type="button"
                  onClick={() => handleSubfeatureClick(sub.id)}
                  title={sub.hint}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
                    isSelected
                      ? 'bg-rose-500/15 border-rose-500/50 text-rose-300 shadow-sm'
                      : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <SubIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-rose-400' : 'text-slate-400'}`} />
                  <span>{sub.label}</span>
                  {sub.id === 'top100' && (
                    <span className="text-[10px] bg-rose-500 text-white font-extrabold px-1.5 py-0.2 rounded-full ml-0.5">
                      12H
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Big Input Bar */}
        <div className="max-w-3xl mx-auto bg-slate-900/90 border border-slate-700/80 p-2 sm:p-2.5 rounded-2xl sm:rounded-3xl shadow-2xl backdrop-blur-md focus-within:border-rose-500/80 focus-within:ring-4 focus-within:ring-rose-500/10 transition duration-300">
          <div className="flex flex-col sm:flex-row items-center gap-2">
            {/* Input with icon */}
            <div className="flex items-center gap-3 px-3 py-2 flex-1 w-full">
              <span className="shrink-0">
                {activeCategory === 'youtube' ? (
                  <YoutubeIcon className="w-5 h-5 text-red-500" />
                ) : activeCategory === 'facebook' ? (
                  <FacebookIcon className="w-5 h-5 text-blue-500" />
                ) : activeCategory === 'instagram' ? (
                  <InstagramIcon className="w-5 h-5 text-pink-500" />
                ) : activeCategory === 'tiktok' ? (
                  <TiktokIcon className="w-5 h-5 text-cyan-400" />
                ) : (
                  <Download className="w-5 h-5 text-slate-400" />
                )}
              </span>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getPlaceholder()}
                className="w-full bg-transparent text-white placeholder-slate-500 text-xs sm:text-sm focus:outline-none"
              />
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
              <button
                type="button"
                onClick={onPaste}
                className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
                title="Paste from clipboard"
              >
                <Clipboard className="w-3.5 h-3.5" />
                <span>Paste</span>
              </button>

              <button
                type="button"
                onClick={onFetch}
                disabled={loading || !url.trim()}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-rose-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Fetch Media</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="mt-4 max-w-xl mx-auto flex items-center gap-2 px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs text-left animate-in fade-in duration-200">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Quick Example Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-6 text-xs text-slate-400">
          <span className="text-slate-500 font-medium">Quick samples:</span>
          {activeCategory === 'youtube' ? (
            <>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
              >
                Never Gonna Give You Up (HD)
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/shorts/aqz-KE-bpKQ')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
              >
                YouTube Shorts Sample
              </button>
              <a
                href="#top-youtube-channels"
                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition font-semibold"
              >
                View Top 100 YouTube Channels &darr;
              </a>
            </>
          ) : activeCategory === 'facebook' ? (
            <button
              type="button"
              onClick={() => setUrl('https://www.facebook.com/watch/')}
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
            >
              Facebook Video Clip
            </button>
          ) : activeCategory === 'instagram' ? (
            <button
              type="button"
              onClick={() => setUrl('https://www.instagram.com/reels/')}
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
            >
              Instagram Reel Sample
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setUrl('https://www.tiktok.com/')}
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
            >
              TikTok Video Sample
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
