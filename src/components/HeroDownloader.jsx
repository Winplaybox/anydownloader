import React from 'react';
import { Link, useLocation } from 'react-router-dom';
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
  Trophy
} from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from './BrandIcons.jsx';
import YouTubePills from './YouTubePills.jsx';
import FacebookPills from './FacebookPills.jsx';
import InstagramPills from './InstagramPills.jsx';

export default function HeroDownloader({ 
  url = '', 
  setUrl = () => {}, 
  onFetch = () => {}, 
  loading = false, 
  error = '',
  onPaste = () => {},
  activeCategory = 'youtube',
  activeSubfeature = 'all'
}) {
  const safeUrl = typeof url === 'string' ? url : (url ? String(url) : '');
  const location = useLocation();

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      onFetch();
    }
  }

  

  function getTitleAndDesc() {
    if (activeCategory === 'youtube') {
      if (activeSubfeature === 'mp4') {
        return {
          badge: 'YouTube MP4 Video Downloader',
          title: 'YouTube MP4 Downloader',
          gradient: 'Download 1080p, 720p & 4K MP4 Videos',
          desc: 'Save YouTube videos directly in universal MP4 format with audio included at the highest available visual quality.'
        };
      }
      if (activeSubfeature === 'shorts') {
        return {
          badge: 'YouTube Shorts Downloader',
          title: 'YouTube Shorts Downloader',
          gradient: 'Vertical Video Clips with Original Sound',
          desc: 'Download YouTube Shorts in 9:16 vertical format directly to your phone or PC with zero watermarks.'
        };
      }
      if (activeSubfeature === 'mp3') {
        return {
          badge: 'YouTube to MP3 Audio Converter',
          title: 'YouTube MP3 Downloader',
          gradient: 'High Fidelity 320kbps & 192kbps MP3',
          desc: 'Convert YouTube videos to high-bitrate MP3 audio. Ideal for music tracks, podcasts, speeches, and study audio.'
        };
      }
      if (activeSubfeature === 'transcript') {
        return {
          badge: 'YouTube Transcript & Caption Extractor',
          title: 'YouTube Transcript Generator',
          gradient: 'Searchable Timestamped Cues & Text Export',
          desc: 'Generate interactive text transcripts from YouTube videos with clickable timestamps, keyword search, and .TXT export.'
        };
      }
      if (activeSubfeature === 'subtitles') {
        return {
          badge: 'YouTube Subtitles Downloader',
          title: 'YouTube Subtitles Downloader',
          gradient: 'Multi-Language SRT & VTT Subtitle Files',
          desc: 'Extract multi-language subtitle tracks (.srt & .vtt) from YouTube videos for VLC, video editing, or language translation.'
        };
      }
      if (activeSubfeature === 'thumbnails') {
        return {
          badge: 'YouTube Thumbnail Images Downloader',
          title: 'YouTube Thumbnails Downloader',
          gradient: 'Full HD 1080p, 720p, 480p & SD Images',
          desc: 'Download full-resolution YouTube cover images in Maxres 1080p, 720p HQ, 480p SD, and 360p MQ qualities.'
        };
      }
      return {
        badge: 'YouTube All-in-One Pro Downloader & Explorer',
        title: 'YouTube Video Downloader',
        gradient: 'YouTube MP4, Shorts, MP3 & Transcripts',
        desc: 'Extract full HD 1080p & 4K videos, separate 320kbps MP3 tracks, interactive transcripts, multi-language subtitles, and full-resolution thumbnail images for any YouTube video.'
      };
    }
    if (activeCategory === 'facebook') {
      if (activeSubfeature === 'reels') {
        return {
          badge: 'Facebook Reels Downloader Without Watermark',
          title: 'Facebook Reels Downloader',
          gradient: 'Download HD 1080p Reels with Sound',
          desc: 'Save viral Facebook Reels in vertical 9:16 format with original synchronized audio directly to your device.'
        };
      }
      if (activeSubfeature === 'watch') {
        return {
          badge: 'Facebook Watch & Shows Saver',
          title: 'Facebook Watch Downloader',
          gradient: 'Full Episodes & Recorded Broadcasts',
          desc: 'Download episodic Facebook Watch shows, sports recaps, and recorded broadcasts in pristine 1080p MP4.'
        };
      }
      if (activeSubfeature === 'stories') {
        return {
          badge: 'Facebook Story & Status Saver',
          title: 'Facebook Story Downloader',
          gradient: 'Save Public Video Stories in HD',
          desc: 'Archive public Facebook stories and video clips before they expire in high-definition MP4 format.'
        };
      }
      if (activeSubfeature === 'mp3') {
        return {
          badge: 'Facebook to MP3 Audio Converter',
          title: 'Facebook MP3 Downloader',
          gradient: 'High Fidelity 320kbps & 192kbps MP3',
          desc: 'Extract clean MP3 audio tracks from Facebook speeches, podcast clips, and live streams.'
        };
      }
      if (activeSubfeature === 'posts') {
        return {
          badge: 'Facebook Post & Photos Downloader',
          title: 'Facebook Posts Downloader',
          gradient: 'Download Photos, Carousels & Post Media',
          desc: 'Download high-resolution photos, single or multi-image albums, and media attachments from public Facebook posts.'
        };
      }
      if (activeSubfeature === 'transcript') {
        return {
          badge: 'Facebook Video Transcript & Captions',
          title: 'Facebook Transcript Downloader',
          gradient: 'Extract Speech Text & Captions',
          desc: 'Extract closed captions, speech text transcripts, and timestamped lines from Facebook videos and reels.'
        };
      }
      if (activeSubfeature === 'thumbnails') {
        return {
          badge: 'Facebook Video Cover & Artwork Downloader',
          title: 'Facebook Thumbnails Downloader',
          gradient: 'Full Resolution HD Artwork & Covers',
          desc: 'Save full-resolution video thumbnail frames and cover artwork from any public Facebook video.'
        };
      }
      return {
        badge: 'Facebook Watch, Reels & Video Downloader',
        title: 'Facebook Video Downloader',
        gradient: 'Full HD 1080p & High Quality MP4',
        desc: 'Download Facebook public videos, reels, stories, and watch clips directly in ultra high quality MP4 format.'
      };
    }
    if (activeCategory === 'instagram') {
      if (activeSubfeature === 'photo') {
        return {
          badge: 'High-Res Uncompressed Photo Downloader',
          title: 'Instagram Photo Downloader',
          gradient: 'Save Original HD Photos & Wallpapers',
          desc: 'Download original high-resolution Instagram photos, portrait shots, and full-size pictures in uncompressed clarity.'
        };
      }
      if (activeSubfeature === 'reels') {
        return {
          badge: 'Instagram Reels Downloader 1080p Full HD',
          title: 'Instagram Reels Downloader',
          gradient: 'Viral 9:16 Reels With Clean Audio',
          desc: 'Download trending viral Instagram Reels in 1080p Full HD MP4 with synchronized original audio and zero watermark.'
        };
      }
      if (activeSubfeature === 'story') {
        return {
          badge: 'Archive Stories & Highlights Privately',
          title: 'Instagram Story Downloader',
          gradient: 'Save Stories Before 24h Expiration',
          desc: 'Archive and download public Instagram stories, clips, and profile highlights before the 24-hour expiration window closes.'
        };
      }
      if (activeSubfeature === 'igtv') {
        return {
          badge: 'Long-Form Video Episodes & Shows in HD',
          title: 'Instagram IGTV Downloader',
          gradient: 'Full-Length 1080p MP4 Broadcasts',
          desc: 'Download extended Instagram IGTV broadcasts, series episodes, podcasts, and masterclass videos in 1080p MP4.'
        };
      }
      if (activeSubfeature === 'carousel') {
        return {
          badge: 'Multi-Slide Album & Carousel Downloader',
          title: 'Instagram Carousel Downloader',
          gradient: 'Download All Photos & Videos in Batch',
          desc: 'Download multi-slide Instagram carousel albums with all high-resolution photos and videos in full original quality.'
        };
      }
      if (activeSubfeature === 'viewer') {
        return {
          badge: 'Anonymous Profile Viewer & DP Downloader',
          title: 'Instagram Viewer & DP Downloader',
          gradient: 'Full-Size Profile Pictures & Metadata',
          desc: 'View public Instagram profiles anonymously and download original full-resolution profile pictures (DP) in full HD.'
        };
      }
      return {
        badge: 'Instagram 1080p Video, Reel & Photo Downloader',
        title: 'Instagram Downloader',
        gradient: 'Videos, Reels, Stories & Photos in HD',
        desc: 'Save high-definition Instagram feed videos, viral reels, stories, and carousel albums directly to your device.'
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
    if (activeCategory === 'facebook') {
      if (activeSubfeature === 'posts') return 'Paste Facebook post or photo link (e.g. https://www.facebook.com/.../posts/...)...';
      if (activeSubfeature === 'transcript') return 'Paste Facebook video or reel link to extract speech transcript...';
      if (activeSubfeature === 'reels') return 'Paste Facebook Reel link (e.g. https://www.facebook.com/share/r/...)...';
      if (activeSubfeature === 'mp3') return 'Paste Facebook video link to extract high-bitrate MP3...';
      return 'Paste Facebook video, reel, post, or story link...';
    }
    if (activeCategory === 'instagram') {
      if (activeSubfeature === 'photo') return 'Paste Instagram photo post link (e.g. https://www.instagram.com/p/...)...';
      if (activeSubfeature === 'reels') return 'Paste Instagram Reel link (e.g. https://www.instagram.com/reel/...)...';
      if (activeSubfeature === 'story') return 'Paste Instagram Story or profile link (e.g. https://www.instagram.com/stories/...)...';
      if (activeSubfeature === 'igtv') return 'Paste Instagram IGTV video link (e.g. https://www.instagram.com/tv/...)...';
      if (activeSubfeature === 'carousel') return 'Paste Instagram multi-photo carousel link (e.g. https://www.instagram.com/p/...)...';
      if (activeSubfeature === 'viewer') return 'Enter Instagram username or profile URL (e.g. https://www.instagram.com/cristiano/)...';
      return 'Paste Instagram video, reel, or photo link (e.g. https://www.instagram.com/p/...)...';
    }
    if (activeCategory === 'tiktok') return 'Paste TikTok video link (e.g. https://www.tiktok.com/@...)...';
    return 'Paste video, reel, or audio link here...';
  }

  const info = getTitleAndDesc();

  return (
    <section id="downloader-input" className="relative pt-6 pb-12 overflow-hidden">
      {/* Background Glow Orbs */}
      <div className={`absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[320px] blur-[130px] pointer-events-none rounded-full transition-colors duration-500 ${
        activeCategory === 'facebook'
          ? 'bg-gradient-to-r from-blue-600/20 via-indigo-600/20 to-sky-500/20'
          : activeCategory === 'instagram'
          ? 'bg-gradient-to-r from-purple-600/20 via-pink-600/20 to-amber-500/20'
          : activeCategory === 'tiktok'
          ? 'bg-gradient-to-r from-cyan-600/20 via-sky-600/20 to-pink-500/20'
          : 'bg-gradient-to-r from-rose-600/20 via-purple-600/20 to-amber-500/20'
      }`} />

      <div className="max-w-4xl mx-auto px-4 text-center relative z-10">

        {/* Platform-Themed Badge */}
        <div className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-semibold mb-5 shadow-inner transition ${
          activeCategory === 'facebook'
            ? 'bg-blue-500/10 border-blue-500/25 text-blue-400'
            : activeCategory === 'instagram'
            ? 'bg-pink-500/10 border-pink-500/25 text-pink-400'
            : activeCategory === 'tiktok'
            ? 'bg-cyan-500/10 border-cyan-500/25 text-cyan-400'
            : 'bg-rose-500/10 border-rose-500/25 text-rose-400'
        }`}>
          <Sparkles className="w-3.5 h-3.5" />
          <span>{info.badge}</span>
        </div>

        {/* Main Title */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-[1.1] mb-3">
          {info.title}
        </h1>

        {/* Dynamic Gradient Subtitle */}
        <p className={`text-base sm:text-xl font-bold bg-clip-text text-transparent mb-3 ${
          activeCategory === 'facebook'
            ? 'bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300'
            : activeCategory === 'instagram'
            ? 'bg-gradient-to-r from-pink-400 via-rose-300 to-amber-300'
            : activeCategory === 'tiktok'
            ? 'bg-gradient-to-r from-cyan-400 via-teal-300 to-pink-400'
            : 'bg-gradient-to-r from-rose-400 via-pink-400 to-amber-300'
        }`}>
          {info.gradient}
        </p>

        {/* Description */}
        <p className="text-slate-400 text-xs sm:text-sm max-w-2xl mx-auto mb-7 leading-relaxed">
          {info.desc}
        </p>

        {/* YouTube Tool Suite Pills */}
        {activeCategory === 'youtube' && (
          <YouTubePills activeSubfeature={activeSubfeature} />
        )}

        {/* Facebook Tool Suite Pills */}
        {activeCategory === 'facebook' && (
          <FacebookPills activeSubfeature={activeSubfeature} />
        )}

        {/* Instagram Tool Suite Pills */}
        {activeCategory === 'instagram' && (
          <InstagramPills activeSubfeature={activeSubfeature} />
        )}

        {/* Big Input Bar */}
        <div className={`max-w-3xl mx-auto bg-slate-900/90 border border-slate-700/80 p-2 sm:p-2.5 rounded-2xl sm:rounded-3xl shadow-2xl backdrop-blur-md transition duration-300 ${
          activeCategory === 'facebook'
            ? 'focus-within:border-blue-500/80 focus-within:ring-4 focus-within:ring-blue-500/10'
            : activeCategory === 'instagram'
            ? 'focus-within:border-pink-500/80 focus-within:ring-4 focus-within:ring-pink-500/10'
            : activeCategory === 'tiktok'
            ? 'focus-within:border-cyan-500/80 focus-within:ring-4 focus-within:ring-cyan-500/10'
            : 'focus-within:border-rose-500/80 focus-within:ring-4 focus-within:ring-rose-500/10'
        }`}>
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
                value={safeUrl}
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
                onClick={() => onFetch()}
                disabled={loading || !safeUrl || !safeUrl.trim()}
                className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-white font-bold text-xs sm:text-sm shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer ${
                  activeCategory === 'facebook'
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-600/30'
                    : activeCategory === 'instagram'
                    ? 'bg-gradient-to-r from-fuchsia-600 to-rose-600 hover:opacity-90 shadow-pink-600/30'
                    : activeCategory === 'tiktok'
                    ? 'bg-gradient-to-r from-cyan-600 to-pink-600 hover:opacity-90 shadow-cyan-600/30'
                    : 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 shadow-rose-600/30'
                }`}
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
                onClick={() => setUrl('https://www.youtube.com/watch?v=lcM52t9Jr2s')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Dhrusa Vlogs Ganpati Idol Video"
              >
                ▶️ Dhrusa Vlogs (Video)
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/shorts/h8o1zI7hU1A')}
                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition cursor-pointer font-medium"
                title="Dhrusa Vlogs Saptashrungi Mata Shorts"
              >
                ⚡ Saptashrungi Shorts
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/watch?v=uI3NLu5bXDg')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Epic Bharat Tandava Video"
              >
                ▶️ Epic Bharat (Video)
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/shorts/HzUZotoLhGM')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Digital Immortals Nav Durga Shorts"
              >
                ⚡ Digital Immortals
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.youtube.com/watch?v=P1l5Br04fTM')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Indian Horror Tapes Video"
              >
                ▶️ Indian Horror Tapes
              </button>
              <Link
                to="/youtube/top-100-youtube-channels"
                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition font-semibold"
              >
                View Top 100 Channels &rarr;
              </Link>
            </>
          ) : activeCategory === 'facebook' ? (
            <>
              <button
                type="button"
                onClick={() => setUrl('https://www.facebook.com/share/r/1Cq6zJtM5y/')}
                className="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 border border-blue-500/30 transition cursor-pointer font-medium"
                title="Jai Saptashrungi Mata Facebook Reel"
              >
                🎬 Saptashrungi Reel
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.facebook.com/profile.php?id=61591856780218')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Dhrusa Vlogs Facebook Page"
              >
                👤 Dhrusa Vlogs (Profile)
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.facebook.com/watch/?v=1646670223674007')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Facebook Watch Video"
              >
                📹 Facebook Video
              </button>
              <Link
                to="/facebook/top-100-facebook-pages"
                className="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 transition font-semibold"
              >
                Top 100 Pages &rarr;
              </Link>
            </>
          ) : activeCategory === 'instagram' ? (
            <>
              <button
                type="button"
                onClick={() => setUrl('https://www.instagram.com/cristiano/')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Cristiano Ronaldo Profile / Avatar"
              >
                📸 Cristiano (Profile)
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.instagram.com/reel/C8qXbO_I7Zq/')}
                className="px-2.5 py-1 rounded-lg bg-pink-500/10 hover:bg-pink-500/20 text-pink-300 border border-pink-500/30 transition cursor-pointer font-medium"
                title="Viral Instagram Reel"
              >
                ⚡ Viral Reel
              </button>
              <button
                type="button"
                onClick={() => setUrl('https://www.instagram.com/p/C9wXbO_I123/')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer"
                title="Photo / Carousel Post"
              >
                🖼️ Photo Post
              </button>
              <Link
                to="/instagram/top-100-instagram-accounts"
                className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-pink-500/20 to-purple-500/20 hover:from-pink-500/30 hover:to-purple-500/30 text-pink-300 border border-pink-500/30 transition font-semibold"
              >
                Top 100 Accounts &rarr;
              </Link>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setUrl('https://www.tiktok.com/@tiktok/video/7106594312292453678')}
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
