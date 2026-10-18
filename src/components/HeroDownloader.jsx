import React from 'react';
import { 
  Download, 
  Clipboard, 
  Sparkles, 
  Loader2, 
  AlertCircle 
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon, 
  TwitterXIcon 
} from './BrandIcons.jsx';

export default function HeroDownloader({ 
  url, 
  setUrl, 
  onFetch, 
  loading, 
  error,
  onPaste
}) {
  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      onFetch();
    }
  }

  function getPlatformIcon() {
    const l = url.toLowerCase();
    if (l.includes('youtube.com') || l.includes('youtu.be')) return <YoutubeIcon className="w-5 h-5 text-red-500" />;
    if (l.includes('instagram.com')) return <InstagramIcon className="w-5 h-5 text-pink-500" />;
    if (l.includes('tiktok.com')) return <TiktokIcon className="w-5 h-5 text-cyan-400" />;
    if (l.includes('facebook.com') || l.includes('fb.watch')) return <FacebookIcon className="w-5 h-5 text-blue-500" />;
    if (l.includes('twitter.com') || l.includes('x.com')) return <TwitterXIcon className="w-5 h-5 text-slate-100" />;
    return <Download className="w-5 h-5 text-slate-400" />;
  }

  return (
    <section className="relative pt-12 pb-16 overflow-hidden">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-r from-rose-600/20 via-purple-600/20 to-cyan-500/20 blur-[120px] pointer-events-none rounded-full" />

      <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-rose-400 font-semibold mb-6 shadow-inner">
          <Sparkles className="w-3.5 h-3.5 text-rose-400" />
          <span>YouTube 1080p, TikTok No Watermark & Instagram Reels</span>
        </div>

        {/* Big Headline */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-[1.1] mb-5">
          Download Any Video or Audio{' '}
          <span className="bg-gradient-to-r from-rose-500 via-pink-500 to-amber-400 bg-clip-text text-transparent">
            In Seconds.
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto mb-10 leading-relaxed">
          The ultimate fast media downloader. Paste any link from YouTube, Instagram, TikTok, Facebook, Twitter, or Pinterest to download Full HD MP4 or high-fidelity MP3 audio for free.
        </p>

        {/* Big Input Bar */}
        <div className="max-w-3xl mx-auto bg-slate-900/90 border border-slate-700/80 p-2 sm:p-2.5 rounded-2xl sm:rounded-3xl shadow-2xl backdrop-blur-md focus-within:border-rose-500/80 focus-within:ring-4 focus-within:ring-rose-500/10 transition duration-300">
          <div className="flex flex-col sm:flex-row items-center gap-2">
            {/* Input with icon */}
            <div className="flex items-center gap-3 px-3 py-2 flex-1 w-full">
              <span className="shrink-0">{getPlatformIcon()}</span>
              <input
                type="text"
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Paste video, reel, or audio link here (e.g. YouTube, Instagram, TikTok)..."
                className="w-full bg-transparent text-white placeholder-slate-500 text-sm sm:text-base focus:outline-none"
              />
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
              <button
                type="button"
                onClick={onPaste}
                className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
                title="Paste from clipboard"
              >
                <Clipboard className="w-3.5 h-3.5" />
                <span>Paste</span>
              </button>

              <button
                type="button"
                onClick={onFetch}
                disabled={loading || !url.trim()}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-bold text-sm shadow-lg shadow-rose-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
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
          <span className="text-slate-500 font-medium">Quick examples:</span>
          <button
            onClick={() => setUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
          >
            YouTube Video
          </button>
          <button
            onClick={() => setUrl('https://www.youtube.com/watch?v=aqz-KE-bpKQ')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
          >
            YouTube Shorts
          </button>
          <button
            onClick={() => setUrl('https://www.instagram.com/reels/')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
          >
            Instagram Reel
          </button>
          <button
            onClick={() => setUrl('https://www.tiktok.com/')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
          >
            TikTok
          </button>
        </div>
      </div>
    </section>
  );
}
