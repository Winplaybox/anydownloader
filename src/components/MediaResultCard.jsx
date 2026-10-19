import React, { useState, useMemo, useEffect } from 'react';
import { 
  Download, 
  Video, 
  Music, 
  Check, 
  Copy, 
  Clock, 
  User, 
  Eye, 
  ArrowDownToLine, 
  ExternalLink,
  Volume2, 
  Sparkles, 
  Layers, 
  FileText, 
  Subtitles, 
  Image as ImageIcon, 
  Search,
  CheckCircle2,
  Share2
} from 'lucide-react';

const BACKEND_BASE = 'https://anydownloader-backend-vvbj.onrender.com';

export default function MediaResultCard({ data, initialTab = 'video', onSelectVideo }) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [copiedShare, setCopiedShare] = useState(false);
  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [transcriptSearch, setTranscriptSearch] = useState('');
  const [copiedThumbIdx, setCopiedThumbIdx] = useState(null);

  if (!data) return null;

  // Detect platform
  const platform = (data.platform || 'youtube').toLowerCase();
  const isFacebook = platform === 'facebook';
  const isYouTube = platform === 'youtube';
  const isInstagram = platform === 'instagram';
  const isTikTok = platform === 'tiktok';

  // Respect user intent: keep on requested tab, don't force carousel if user is on video or audio
  useEffect(() => {
    if (initialTab === 'carousel' || (data.is_carousel && initialTab !== 'video' && initialTab !== 'audio')) {
      setActiveTab('carousel');
    } else if (initialTab === 'profile' || (data.is_channel && initialTab === 'profile')) {
      setActiveTab('thumbnails');
    } else if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab, data]);

  // Extract YouTube ID if present
  const youtubeId = useMemo(() => {
    if (!isYouTube) return null;
    if (data.id && data.id.length === 11) return data.id;
    const match = (data.original_url || '').match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : null;
  }, [data, isYouTube]);

  // All Thumbnails List
  const thumbnails = useMemo(() => {
    if (data.thumbnails && data.thumbnails.length > 0) {
      return data.thumbnails;
    }
    if (youtubeId) {
      const titleClean = (data.title || 'youtube_video').replace(/[^a-zA-Z0-9_-]/g, '_');
      return [
        {
          quality: '1080p Full HD (Maxres)',
          resolution: '1920x1080',
          label: 'Ultra High Resolution',
          url: `https://i.ytimg.com/vi/${youtubeId}/maxresdefault.jpg`,
          stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(`https://i.ytimg.com/vi/${youtubeId}/maxresdefault.jpg`)}&filename=${encodeURIComponent(`${titleClean}_1080p.jpg`)}`
        },
        {
          quality: '720p HD (High Quality)',
          resolution: '1280x720',
          label: 'High Definition',
          url: `https://i.ytimg.com/vi/${youtubeId}/hqdefault.jpg`,
          stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(`https://i.ytimg.com/vi/${youtubeId}/hqdefault.jpg`)}&filename=${encodeURIComponent(`${titleClean}_720p.jpg`)}`
        },
        {
          quality: '480p Standard (SD)',
          resolution: '640x480',
          label: 'Standard Definition',
          url: `https://i.ytimg.com/vi/${youtubeId}/sddefault.jpg`,
          stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(`https://i.ytimg.com/vi/${youtubeId}/sddefault.jpg`)}&filename=${encodeURIComponent(`${titleClean}_480p.jpg`)}`
        },
        {
          quality: '360p Medium (MQ)',
          resolution: '480x360',
          label: 'Medium Quality',
          url: `https://i.ytimg.com/vi/${youtubeId}/mqdefault.jpg`,
          stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(`https://i.ytimg.com/vi/${youtubeId}/mqdefault.jpg`)}&filename=${encodeURIComponent(`${titleClean}_360p.jpg`)}`
        },
        {
          quality: 'Default Thumbnail',
          resolution: '120x90',
          label: 'Default Low-Res',
          url: `https://i.ytimg.com/vi/${youtubeId}/default.jpg`,
          stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(`https://i.ytimg.com/vi/${youtubeId}/default.jpg`)}&filename=${encodeURIComponent(`${titleClean}_default.jpg`)}`
        }
      ];
    }
    if (data.thumbnail) {
      const cleanTitle = (data.title || 'media_cover').replace(/[^a-zA-Z0-9_-]/g, '_');
      return [{
        quality: isFacebook ? 'Facebook Cover / Photo' : 'Original Artwork',
        resolution: 'High Resolution',
        label: isFacebook ? 'Full Resolution Post Image' : 'Original Media Cover',
        url: data.thumbnail,
        stream_url: `${BACKEND_BASE}/api/stream?url=${encodeURIComponent(data.thumbnail)}&filename=${encodeURIComponent(`${cleanTitle}_cover.jpg`)}`
      }];
    }
    return [];
  }, [data, youtubeId, isFacebook]);

  // Transcripts
  const rawTranscript = data.transcript || [];
  const filteredTranscript = useMemo(() => {
    if (!transcriptSearch || typeof transcriptSearch !== 'string' || !transcriptSearch.trim()) return rawTranscript;
    const q = transcriptSearch.toLowerCase();
    return rawTranscript.filter(item => item.text.toLowerCase().includes(q));
  }, [rawTranscript, transcriptSearch]);

  const totalWords = useMemo(() => {
    return rawTranscript.reduce((acc, cur) => acc + (cur.text ? cur.text.split(/\s+/).length : 0), 0);
  }, [rawTranscript]);

  function copyShareUrl() {
    navigator.clipboard.writeText(data.original_url || window.location.href);
    setCopiedShare(true);
    setTimeout(() => setCopiedShare(false), 2000);
  }

  function copyAllTranscript() {
    const fullText = rawTranscript.map(c => `[${c.time}] ${c.text}`).join('\n');
    navigator.clipboard.writeText(fullText);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2000);
  }

  function downloadTranscriptText() {
    const fullText = rawTranscript.map(c => `[${c.time}] ${c.text}`).join('\n');
    const blob = new Blob([fullText], { type: 'text/plain;charset=utf-8' });
    const u = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = u;
    a.download = `${(data.title || 'transcript').replace(/[^a-zA-Z0-9_-]/g, '_')}_transcript.txt`;
    a.click();
    URL.revokeObjectURL(u);
  }

  function copyThumbUrl(url, idx) {
    navigator.clipboard.writeText(url);
    setCopiedThumbIdx(idx);
    setTimeout(() => setCopiedThumbIdx(null), 2000);
  }

  function formatStreamUrl(fmtUrl) {
    if (!fmtUrl) return '#';
    if (fmtUrl.startsWith('http')) return fmtUrl;
    return `${BACKEND_BASE}${fmtUrl}`;
  }

  // Determine Tab Configuration
  const tabs = useMemo(() => {
    const list = [];

    // Tab 0: Carousel Album (FastDl Style)
    if (data.is_carousel || (data.carousel_media && data.carousel_media.length > 0)) {
      list.push({
        id: 'carousel',
        label: `📸 Carousel Album (${data.carousel_media?.length || 0} Photos)`,
        icon: Sparkles
      });
    }

    // Tab 1: Video
    list.push({
      id: 'video',
      label: isFacebook 
        ? 'Facebook Video (MP4)' 
        : isInstagram 
        ? 'Instagram Video (MP4)' 
        : isTikTok 
        ? 'TikTok Video (MP4)' 
        : 'YouTube MP4 / Video',
      icon: Video
    });

    // Tab 2: Audio
    list.push({
      id: 'audio',
      label: isFacebook 
        ? 'Facebook Audio (MP3)' 
        : isInstagram 
        ? 'Audio (MP3)' 
        : isTikTok 
        ? 'Sound (MP3)' 
        : 'YouTube MP3 / Audio',
      icon: Music
    });

    // Tab 3: Thumbnails / Covers
    list.push({
      id: 'thumbnails',
      label: isFacebook 
        ? 'Cover & Photos' 
        : isInstagram 
        ? 'Cover Artwork' 
        : isTikTok 
        ? 'Video Cover' 
        : 'Thumbnails (All Qualities)',
      icon: ImageIcon
    });

    // Tab 4: Transcript (Show if cues exist or on YouTube)
    if (isYouTube || rawTranscript.length > 0) {
      list.push({
        id: 'transcript',
        label: isFacebook ? 'Facebook Transcript' : 'Transcript',
        icon: FileText
      });
    }

    // Tab 5: Subtitles (Show if subtitles exist or on YouTube)
    if (isYouTube || (data.subtitles && data.subtitles.length > 0)) {
      list.push({
        id: 'subtitles',
        label: isFacebook ? 'Facebook Captions' : 'Subtitles',
        icon: Subtitles
      });
    }

    return list;
  }, [isFacebook, isInstagram, isTikTok, isYouTube, rawTranscript.length, data.subtitles]);

  // Color theme tokens
  const theme = useMemo(() => {
    if (isFacebook) {
      return {
        badgeBg: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        activeTab: 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/30',
        btnGrad: 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/20',
        btnSolid: 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20',
        textAccent: 'text-blue-400',
        borderAccent: 'border-blue-500/30'
      };
    }
    if (isInstagram) {
      return {
        badgeBg: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
        activeTab: 'bg-gradient-to-r from-fuchsia-600 via-pink-600 to-rose-600 text-white shadow-md shadow-pink-600/30',
        btnGrad: 'bg-gradient-to-r from-fuchsia-600 via-pink-600 to-rose-600 hover:opacity-90 text-white shadow-lg shadow-pink-600/20',
        btnSolid: 'bg-pink-600 hover:bg-pink-500 text-white shadow-md shadow-pink-600/20',
        textAccent: 'text-pink-400',
        borderAccent: 'border-pink-500/30'
      };
    }
    if (isTikTok) {
      return {
        badgeBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
        activeTab: 'bg-gradient-to-r from-cyan-600 to-pink-600 text-white shadow-md shadow-cyan-600/30',
        btnGrad: 'bg-gradient-to-r from-cyan-600 to-pink-600 hover:opacity-90 text-white shadow-lg shadow-cyan-600/20',
        btnSolid: 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-md shadow-cyan-600/20',
        textAccent: 'text-cyan-400',
        borderAccent: 'border-cyan-500/30'
      };
    }
    // Default YouTube
    return {
      badgeBg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      activeTab: 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-md shadow-rose-600/30',
      btnGrad: 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-lg shadow-rose-600/20',
      btnSolid: 'bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/20',
      textAccent: 'text-rose-400',
      borderAccent: 'border-rose-500/30'
    };
  }, [isFacebook, isInstagram, isTikTok]);

  return (
    <div className="max-w-4xl mx-auto px-4 mb-20 animate-in fade-in slide-in-from-bottom-6 duration-300">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
        
        {/* Media Header Preview */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start pb-6 border-b border-slate-800">
          {/* Thumbnail */}
          <div className="md:col-span-4 relative rounded-2xl overflow-hidden aspect-video bg-slate-800 border border-slate-700/60 shadow-md group">
            {data.thumbnail ? (
              <img
                src={data.thumbnail}
                alt={data.title}
                className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-600">
                <Video className="w-10 h-10" />
              </div>
            )}
            {data.duration && (
              <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-[10px] font-mono-data font-bold text-white flex items-center gap-1">
                <Clock className={`w-3 h-3 ${theme.textAccent}`} />
                <span>{data.duration}</span>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="md:col-span-8 flex flex-col justify-between h-full">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${theme.badgeBg}`}>
                  {data.platform ? data.platform.toUpperCase() : 'MEDIA STREAM'}
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1 font-medium">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  {data.uploader || 'Creator'}
                </span>
              </div>

              <h2 className="text-lg sm:text-xl font-bold text-white leading-snug line-clamp-2 mb-3">
                {data.title}
              </h2>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
              {data.views && (
                <span className="text-slate-400 flex items-center gap-1 font-mono-data">
                  <Eye className="w-3.5 h-3.5 text-slate-500" />
                  {data.views} views
                </span>
              )}

              <button
                type="button"
                onClick={copyShareUrl}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
              >
                {copiedShare ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedShare ? 'Copied' : 'Share Link'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Informational Notification Banner (e.g., photo requested on video tab) */}
        {data.notice && (
          <div className="my-5 p-4 rounded-2xl bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-indigo-500/10 border border-pink-500/30 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2.5 text-xs text-slate-200">
              <Sparkles className="w-4 h-4 text-pink-400 shrink-0" />
              <span>{data.notice}</span>
            </div>
            {data.is_carousel && (
              <button
                type="button"
                onClick={() => setActiveTab('carousel')}
                className="px-3.5 py-1.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-md shadow-pink-600/30"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Switch to Carousel Tab ({data.carousel_media?.length || 0} Photos)</span>
              </button>
            )}
          </div>
        )}

        {/* Channel & Profile Link Notice */}
        {data.is_channel && (
          <div className={`my-6 p-5 rounded-2xl border ${
            isInstagram 
              ? 'bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-pink-500/30' 
              : isFacebook 
                ? 'bg-blue-500/10 border-blue-500/30' 
                : 'bg-rose-500/10 border-rose-500/30'
          }`}>
            <div className="flex items-center gap-2 mb-2 font-bold text-sm">
              <Sparkles className={`w-4 h-4 ${isInstagram ? 'text-pink-400' : isFacebook ? 'text-blue-400' : 'text-rose-400'}`} />
              <span className={isInstagram ? 'text-pink-300' : isFacebook ? 'text-blue-300' : 'text-rose-300'}>
                {isInstagram ? 'Instagram Profile Detected' : isFacebook ? 'Facebook Page / Profile Detected' : 'YouTube Channel Detected'}: {data.uploader || data.title}
              </span>
            </div>
            
            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              {isInstagram 
                ? 'Public Instagram profile found. You can download the original full-resolution profile picture (DP) below, or inspect follower stats:'
                : isFacebook 
                  ? 'Public Facebook page or profile found. Download official page artwork, avatar pictures, or related posts below:'
                  : 'Official YouTube Channel found. Download channel artwork below or choose any recent upload to extract Video (1080p MP4) or Audio (320kbps MP3):'
              }
            </p>

            {/* Instagram Profile Quick Action Card */}
            {isInstagram && data.thumbnail && (
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                <div className="flex items-center gap-3">
                  <img src={data.thumbnail} alt={data.title} className="w-14 h-14 rounded-full object-cover border-2 border-pink-500/50 shadow-md" />
                  <div>
                    <h4 className="text-xs font-bold text-white">{data.title}</h4>
                    <p className="text-[11px] text-slate-400">{data.views}</p>
                  </div>
                </div>
                {data.thumbnails && data.thumbnails[0] && (
                  <a
                    href={`${BACKEND_BASE}${data.thumbnails[0].stream_url}`}
                    target="_blank"
                    rel="noopener"
                    className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-md shadow-pink-600/20"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Full-Size DP (HD)</span>
                  </a>
                )}
              </div>
            )}

            {/* Instagram Recent / Pinned Posts with Instant HD Download */}
            {isInstagram && data.recent_posts && data.recent_posts.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between mb-3 px-1">
                  <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                    Latest Pinned & Profile Posts ({data.recent_posts.length})
                  </span>
                  <span className="text-[10px] text-pink-400 font-medium font-mono-data">
                    Original 1080p HD
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {data.recent_posts.map((post, pIdx) => (
                    <div
                      key={pIdx}
                      className="p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 hover:border-pink-500/40 flex flex-col justify-between group transition"
                    >
                      <div className="relative aspect-square rounded-lg overflow-hidden bg-slate-900 mb-2">
                        <img
                          src={post.preview || post.url}
                          alt={post.download_name}
                          className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                        />
                        <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-black/70 text-white">
                          #{post.index || pIdx + 1}
                        </span>
                      </div>
                      <a
                        href={formatStreamUrl(post.stream_url || post.url)}
                        download={post.download_name}
                        target="_blank"
                        rel="noopener"
                        className="w-full py-1.5 px-2 rounded-lg bg-pink-600/20 hover:bg-pink-600 text-pink-300 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1.5 transition border border-pink-500/30"
                      >
                        <Download className="w-3 h-3" />
                        <span>Download Post</span>
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* YouTube Recent Videos with Instant Video & MP3 options */}
            {data.recent_videos && data.recent_videos.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                {data.recent_videos.map((vid) => (
                  <div
                    key={vid.id}
                    className="p-3 rounded-xl bg-slate-950/90 border border-slate-800 hover:border-slate-700 flex flex-col justify-between group transition"
                  >
                    <div className="flex gap-3 items-center mb-2.5">
                      <img src={vid.thumbnail} alt={vid.title} className="w-20 h-14 object-cover rounded-lg shrink-0 border border-slate-800" />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-bold text-white line-clamp-2 leading-tight" title={vid.title}>
                          {vid.title}
                        </h4>
                      </div>
                    </div>
                    {/* Action buttons: Video (MP4) and Audio (MP3) */}
                    <div className="flex items-center gap-1.5 pt-2 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={() => onSelectVideo && onSelectVideo(vid.url, 'video')}
                        className="flex-1 py-1 px-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-[10px] font-bold flex items-center justify-center gap-1 transition cursor-pointer border border-rose-500/20"
                        title="Download Video (1080p MP4)"
                      >
                        <Video className="w-3 h-3 text-rose-400" />
                        <span>Video MP4</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onSelectVideo && onSelectVideo(vid.url, 'audio')}
                        className="flex-1 py-1 px-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-[10px] font-bold flex items-center justify-center gap-1 transition cursor-pointer border border-amber-500/20"
                        title="Extract Audio (320kbps MP3)"
                      >
                        <Music className="w-3 h-3 text-amber-400" />
                        <span>Audio MP3</span>
                      </button>
                      <a
                        href={vid.thumbnail}
                        target="_blank"
                        rel="noopener"
                        className="p-1 px-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white text-[10px] font-medium flex items-center justify-center transition border border-slate-800"
                        title="View Thumbnail"
                      >
                        <ImageIcon className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {data.is_post_or_profile && (
          <div className="my-6 p-5 rounded-2xl bg-blue-500/10 border border-blue-500/30 text-xs">
            <div className="flex items-center gap-2 mb-2 font-bold text-blue-400 text-sm">
              <User className="w-4 h-4" />
              <span>Facebook Page / Profile Link Detected</span>
            </div>
            <p className="text-slate-300 leading-relaxed mb-3">
              We extracted <strong>{data.title}</strong>'s high-resolution profile and cover media. You can download the full-resolution artwork in the <strong>Cover & Photos</strong> tab below.
            </p>
            <p className="text-slate-400 text-[11px]">
              💡 <em>To download specific Facebook videos or reels, copy the direct link of any individual video or reel (e.g. <code>facebook.com/share/r/...</code>).</em>
            </p>
          </div>
        )}

        {/* Dynamic Platform Tab Controls */}
        <div className="flex items-center gap-1.5 my-6 p-1 rounded-2xl bg-slate-950 border border-slate-800 overflow-x-auto max-w-full">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            const isTabActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                  isTabActive
                    ? theme.activeTab
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <TabIcon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* TAB 1: Video Formats */}
                {/* CAROUSEL ALBUM TAB (FastDl Style) */}
        {activeTab === 'carousel' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-pink-900/40 via-purple-900/30 to-indigo-900/40 border border-pink-500/30 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30">
                    📸 Instagram Carousel Album
                  </span>
                  <span className="text-xs text-slate-300 font-medium">
                    {data.carousel_media?.length || 0} High-Res Slides Extracted
                  </span>
                </div>
                <h4 className="text-white font-bold text-sm line-clamp-1">
                  {data.title || 'Instagram Album'}
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Real data fetched in full 1080p resolution directly from Instagram CDN
                </p>
              </div>

              {data.carousel_media && data.carousel_media.length > 0 && (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => {
                      data.carousel_media.forEach((slide, i) => {
                        setTimeout(() => {
                          const link = document.createElement('a');
                          link.href = formatStreamUrl(slide.stream_url || slide.url);
                          link.download = slide.download_name;
                          link.target = '_blank';
                          link.rel = 'noopener';
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }, i * 350);
                      });
                    }}
                    className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-pink-600/30 transition active:scale-95 cursor-pointer"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download All ({data.carousel_media.length}) Photos</span>
                  </button>
                </div>
              )}
            </div>

            {/* Responsive Grid matching FastDl */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {(data.carousel_media || []).map((slide, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/80 border border-slate-800/90 hover:border-pink-500/50 rounded-2xl overflow-hidden shadow-xl transition-all duration-300 flex flex-col group"
                >
                  <div className="relative aspect-[4/5] bg-slate-900 overflow-hidden">
                    <img
                      src={slide.preview || slide.url}
                      alt={slide.download_name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 opacity-70 group-hover:opacity-90 transition-opacity" />
                    
                    {/* Top Badges */}
                    <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-black/75 backdrop-blur text-white border border-white/20">
                        Photo {slide.index || idx + 1} of {data.carousel_media?.length}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-pink-600 text-white shadow-md">
                        1080p Full HD
                      </span>
                    </div>

                    {/* Bottom overlay info */}
                    <div className="absolute bottom-3 left-3 right-3 pointer-events-none">
                      <span className="text-[11px] text-slate-300 font-mono-data truncate block">
                        {slide.download_name}
                      </span>
                    </div>
                  </div>

                  <div className="p-4 flex flex-col gap-3 flex-1 justify-between bg-slate-900/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">
                        {slide.quality || `Photo ${idx + 1}`}
                      </span>
                      <span className="text-[11px] text-pink-400 font-mono-data font-bold">
                        {slide.resolution || 'Original HD'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={formatStreamUrl(slide.stream_url || slide.url)}
                        download={slide.download_name}
                        target="_blank"
                        rel="noopener"
                        className="flex-1 py-2.5 px-3 rounded-xl bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-pink-600/20 transition active:scale-95 cursor-pointer"
                      >
                        <ArrowDownToLine className="w-4 h-4" />
                        <span>Download Photo {slide.index || idx + 1}</span>
                      </a>
                      <button
                        onClick={() => copyThumbUrl(slide.url, idx)}
                        title="Copy direct image link"
                        className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition cursor-pointer"
                      >
                        {copiedThumbIdx === idx ? (
                          <Check className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'video' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between px-1">
              <span>Resolution & Quality</span>
              <span>Direct Fast Download</span>
            </div>

            {data.video_formats && data.video_formats.length > 0 ? (
              data.video_formats.map((fmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700/90 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3.5">
                    <div className={`w-11 h-11 rounded-xl bg-slate-900 border flex items-center justify-center font-black text-xs shrink-0 ${theme.borderAccent} ${theme.textAccent}`}>
                      {fmt.height >= 720 ? 'HD' : 'SD'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-white text-sm">
                          {fmt.quality}
                        </span>
                        {fmt.has_audio ? (
                          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            <Volume2 className="w-3 h-3" /> Audio Included
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 bg-slate-800/60 px-1.5 py-0.5 rounded border border-slate-700">
                            Video Track
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 font-mono-data mt-0.5">
                        Format: {fmt.ext?.toUpperCase() || 'MP4'} &bull; Size: {fmt.size}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <a
                      href={formatStreamUrl(fmt.stream_url || fmt.url)}
                      download={fmt.download_name}
                      target="_blank"
                      rel="noopener"
                      className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer ${theme.btnGrad}`}
                    >
                      <ArrowDownToLine className="w-4 h-4" />
                      <span>{fmt.has_audio ? "Download MP4 (With Sound)" : "Download MP4"}</span>
                    </a>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-10 px-5 text-center bg-slate-950/60 rounded-2xl border border-slate-800/80">
                {data.is_carousel || (data.carousel_media && data.carousel_media.length > 0) ? (
                  <div>
                    <Layers className="w-10 h-10 text-pink-400 mx-auto mb-2" />
                    <h4 className="text-sm sm:text-base font-bold text-white mb-1">
                      Instagram Carousel Album Detected ({data.carousel_media?.length || 0} Photos)
                    </h4>
                    <p className="text-xs text-slate-300 max-w-md mx-auto mb-4 leading-relaxed">
                      This post is a multi-slide carousel photo album, not a video clip. You can view all {data.carousel_media?.length || 0} high-res slides in the Carousel tab.
                    </p>
                    <button
                      type="button"
                      onClick={() => setActiveTab('carousel')}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:opacity-90 text-white shadow-lg shadow-pink-600/30 cursor-pointer"
                    >
                      <Layers className="w-4 h-4" />
                      <span>View & Download All {data.carousel_media?.length || 0} Photos</span>
                    </button>
                  </div>
                ) : (data.is_channel || data.is_profile) ? (
                  <div>
                    <User className="w-10 h-10 text-pink-400 mx-auto mb-2" />
                    <h4 className="text-sm font-bold text-white mb-1">
                      Instagram Profile: {data.uploader || data.title}
                    </h4>
                    <p className="text-xs text-slate-300 max-w-md mx-auto mb-4 leading-relaxed">
                      {data.views || 'Public Instagram profile found'}. Download the Full HD Avatar picture (DP) below:
                    </p>
                    <button
                      type="button"
                      onClick={() => setActiveTab('thumbnails')}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition bg-gradient-to-r from-pink-600 to-purple-600 hover:opacity-90 text-white shadow-lg shadow-pink-600/30 cursor-pointer"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download HD Profile Picture (DP)</span>
                    </button>
                  </div>
                ) : (
                  <div>
                    <ImageIcon className="w-9 h-9 text-pink-400 mx-auto mb-2" />
                    <h4 className="text-sm font-bold text-white mb-1">
                      {isInstagram ? 'Instagram Photo Post' : isFacebook ? 'Facebook Photo / Post' : 'No Video Stream Detected'}
                    </h4>
                    <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
                      {isInstagram 
                        ? 'This link contains a full-resolution photo post rather than a video stream. Download the original JPG below.'
                        : 'No direct video stream was found for this link. Check available artwork below.'}
                    </p>
                    {thumbnails.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setActiveTab('thumbnails')}
                        className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${theme.btnGrad}`}
                      >
                        <ImageIcon className="w-3.5 h-3.5" />
                        <span>View & Download Original Photo</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Audio Formats */}
        {activeTab === 'audio' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between px-1">
              <span>Bitrate & Audio Tier</span>
              <span>Audio Download</span>
            </div>

            {data.audio_formats && data.audio_formats.length > 0 ? (
              data.audio_formats.map((fmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700/90 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500/10 to-blue-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center font-black text-xs shrink-0">
                      {fmt.format || 'MP3'}
                    </div>
                    <div>
                      <div className="font-extrabold text-white text-sm">
                        {fmt.quality}
                      </div>
                      <div className="text-xs text-slate-400 font-mono-data mt-0.5">
                        Audio format: {fmt.format} &bull; Approx. Size: {fmt.size}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <a
                      href={formatStreamUrl(fmt.stream_url || fmt.url)}
                      download={fmt.download_name}
                      target="_blank"
                      rel="noopener"
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-600/20 transition cursor-pointer"
                    >
                      <ArrowDownToLine className="w-4 h-4" />
                      <span>Download {fmt.format}</span>
                    </a>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-xs text-slate-400 bg-slate-950/40 rounded-2xl border border-slate-800/60">
                No audio tracks detected.
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Thumbnails / Covers */}
        {activeTab === 'thumbnails' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                {isFacebook ? 'Facebook Cover & Photo Artwork' : isYouTube ? 'Full-Resolution YouTube Thumbnails' : 'Media Covers & Images'}
              </span>
              <span className={`text-xs font-medium ${theme.textAccent}`}>
                {thumbnails.length} Resolutions Available
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {thumbnails.map((thumb, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-3.5 flex flex-col justify-between transition group"
                >
                  <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-900 mb-3 border border-slate-800">
                    <img
                      src={thumb.url}
                      alt={thumb.quality}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                      onError={(e) => {
                        e.target.src = data.thumbnail || (youtubeId ? `https://i.ytimg.com/vi/${youtubeId}/hqdefault.jpg` : '');
                      }}
                    />
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-[10px] font-bold text-white border border-white/10">
                      {thumb.resolution}
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-1">
                    <div>
                      <h4 className="text-xs font-bold text-white">{thumb.quality}</h4>
                      <p className="text-[10px] text-slate-400">{thumb.label || thumb.resolution}</p>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        type="button"
                        onClick={() => copyThumbUrl(thumb.url, idx)}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
                        title="Copy image URL"
                      >
                        {copiedThumbIdx === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>

                      <a
                        href={formatStreamUrl(thumb.stream_url || thumb.url)}
                        download={`${(data.title || 'thumb').replace(/[^a-zA-Z0-9_-]/g, '_')}_${thumb.resolution}.jpg`}
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition ${theme.btnSolid}`}
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: Transcript */}
        {activeTab === 'transcript' && (
          <div>
            {/* Header / Actions */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {isFacebook ? 'Facebook Video Transcript' : 'Interactive Transcript'}
                </span>
                {rawTranscript.length > 0 && (
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${theme.badgeBg}`}>
                    {rawTranscript.length} cues &bull; {totalWords} words
                  </span>
                )}
              </div>

              {rawTranscript.length > 0 && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={copyAllTranscript}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer"
                  >
                    {copiedTranscript ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedTranscript ? 'Copied All' : 'Copy All'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={downloadTranscriptText}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${theme.btnSolid}`}
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .TXT</span>
                  </button>
                </div>
              )}
            </div>

            {/* Search Filter */}
            {rawTranscript.length > 0 && (
              <div className="relative mb-4">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={transcriptSearch}
                  onChange={(e) => setTranscriptSearch(e.target.value)}
                  placeholder="Search keywords inside transcript..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                />
              </div>
            )}

            {/* Transcript Cues List */}
            {rawTranscript.length > 0 ? (
              <div className="max-h-96 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {filteredTranscript.length > 0 ? (
                  filteredTranscript.map((cue, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 text-xs flex items-start gap-3 transition"
                    >
                      <span className={`font-mono-data font-bold px-2 py-0.5 rounded shrink-0 text-[11px] ${theme.badgeBg}`}>
                        {cue.time}
                      </span>
                      <p className="text-slate-300 leading-relaxed">{cue.text}</p>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-slate-500">
                    No transcript cues match "{transcriptSearch}".
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 px-4 text-center bg-slate-950/50 rounded-2xl border border-slate-800/80">
                <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-white mb-1">No Captions / Transcript Detected</h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  {isFacebook
                    ? 'This Facebook video does not contain uploaded closed captions or speech-to-text tracks.'
                    : 'This video may not have public closed captions or spoken audio enabled by the creator.'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: Subtitles */}
        {activeTab === 'subtitles' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Multi-Language Subtitle Tracks
              </span>
              <span className={`text-xs font-medium ${theme.textAccent}`}>
                {data.subtitles ? data.subtitles.length : 0} Available Languages
              </span>
            </div>

            {data.subtitles && data.subtitles.length > 0 ? (
              <div className="space-y-2.5">
                {data.subtitles.map((sub, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-xl border flex items-center justify-center font-bold text-xs uppercase shrink-0 ${theme.badgeBg}`}>
                        {sub.code}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-xs sm:text-sm">{sub.language}</span>
                          {sub.is_auto && (
                            <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded border border-slate-700">
                              Auto
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-400 font-mono-data">Code: {sub.code}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={formatStreamUrl(sub.srt_download || sub.srt_url)}
                        download={`${(data.title || 'sub').replace(/[^a-zA-Z0-9_-]/g, '_')}_${sub.code}.srt`}
                        target="_blank"
                        rel="noopener"
                        className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
                      >
                        <Download className={`w-3.5 h-3.5 ${theme.textAccent}`} />
                        <span>Download SRT</span>
                      </a>

                      <a
                        href={formatStreamUrl(sub.vtt_download || sub.vtt_url)}
                        download={`${(data.title || 'sub').replace(/[^a-zA-Z0-9_-]/g, '_')}_${sub.code}.vtt`}
                        target="_blank"
                        rel="noopener"
                        className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
                      >
                        <Download className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Download VTT</span>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 px-4 text-center bg-slate-950/50 rounded-2xl border border-slate-800/80">
                <Subtitles className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-white mb-1">No Subtitles Found</h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  {isFacebook
                    ? 'No separate subtitle files (.srt/.vtt) are attached to this Facebook video.'
                    : 'This video does not have separate subtitle tracks (.srt/.vtt) attached by the uploader.'}
                </p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
