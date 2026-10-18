import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Download, 
  Sparkles, 
  Music, 
  FileText, 
  Subtitles, 
  Image as ImageIcon, 
  Trophy,
  Video
} from 'lucide-react';

export const ytSubfeatures = [
  { id: 'video', label: 'YouTube Video', icon: Video, path: '/youtube/youtube-video-downloader', hint: 'Universal YouTube video & audio converter' },
  { id: 'mp4', label: 'YouTube MP4', icon: Download, path: '/youtube/youtube-mp4', hint: 'Direct 1080p, 720p & 4K MP4 video formats' },
  { id: 'shorts', label: 'YouTube Shorts', icon: Sparkles, path: '/youtube/youtube-shorts', hint: 'Fast download for YouTube Shorts vertical videos' },
  { id: 'mp3', label: 'YouTube MP3', icon: Music, path: '/youtube/youtube-mp3', hint: 'Convert & download audio up to 320 kbps high bitrate' },
  { id: 'transcript', label: 'YouTube Transcript', icon: FileText, path: '/youtube/youtube-transcript', hint: 'Interactive timestamped transcript & text exporter' },
  { id: 'subtitles', label: 'YouTube Subtitles', icon: Subtitles, path: '/youtube/youtube-subtitles', hint: 'Download multi-language subtitles in SRT & VTT' },
  { id: 'thumbnails', label: 'YouTube Thumbnails', icon: ImageIcon, path: '/youtube/youtube-thumbnails', hint: 'All quality thumbnail images (1080p, 720p, 480p, SD)' },
  { id: 'top100', label: 'Top 100 Channels', icon: Trophy, path: '/youtube/top-100-youtube-channels', hint: 'Global ranking by current subscriber count' },
];

export default function YouTubePills({ activeSubfeature }) {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-5xl mx-auto px-4">
      {ytSubfeatures.map((sub) => {
        const SubIcon = sub.icon;
        const isSelected = 
          path === sub.path ||
          (sub.id === 'video' && (path === '/youtube/youtube-video-downloader' || path === '/youtube-video-downloader' || activeSubfeature === 'video')) ||
          (sub.id === 'mp4' && (path === '/' || path === '/youtube' || path === '/youtube/youtube-mp4' || path === '/youtube-mp4' || activeSubfeature === 'all' || activeSubfeature === 'mp4')) ||
          (sub.id === 'thumbnails' && (path === '/youtube/youtube-thumbnail' || path === '/youtube-thumbnail')) ||
          (sub.id === 'top100' && (path.includes('top-100-youtube-channels') || path.includes('top-100-channels'))) ||
          (sub.id === activeSubfeature);

        return (
          <Link
            key={sub.id}
            to={sub.path}
            title={sub.hint}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
              isSelected
                ? 'bg-rose-500/20 border-rose-500/60 text-white shadow-md shadow-rose-500/10'
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
          </Link>
        );
      })}
    </div>
  );
}
