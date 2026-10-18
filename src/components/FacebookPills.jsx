import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Download, 
  Sparkles, 
  Tv, 
  Clock, 
  Music, 
  Image as ImageIcon, 
  FileText,
  Layers,
  Trophy 
} from 'lucide-react';

export const fbSubfeatures = [
  { id: 'video', label: 'Facebook Video', icon: Download, path: '/facebook/facebook-video-downloader', hint: 'Download public Facebook videos in 1080p Full HD' },
  { id: 'reels', label: 'Facebook Reels', icon: Sparkles, path: '/facebook/facebook-reels', hint: 'Save vertical Facebook Reels with original audio' },
  { id: 'posts', label: 'Facebook Posts', icon: Layers, path: '/facebook/facebook-posts', hint: 'Download photos, carousels & status posts' },
  { id: 'watch', label: 'Facebook Watch', icon: Tv, path: '/facebook/facebook-watch', hint: 'Download Facebook Watch episodes and live streams' },
  { id: 'stories', label: 'Facebook Stories', icon: Clock, path: '/facebook/facebook-stories', hint: 'Save public Facebook stories and video statuses' },
  { id: 'mp3', label: 'Facebook MP3', icon: Music, path: '/facebook/facebook-mp3', hint: 'Extract 320kbps MP3 audio tracks from Facebook videos' },
  { id: 'transcript', label: 'Facebook Transcript', icon: FileText, path: '/facebook/facebook-transcript', hint: 'Extract speech transcript and video captions' },
  { id: 'thumbnails', label: 'Facebook Thumbnails', icon: ImageIcon, path: '/facebook/facebook-thumbnails', hint: 'Download full-resolution video cover artwork' },
  { id: 'top100', label: 'Top 100 Pages', icon: Trophy, path: '/facebook/top-100-facebook-pages', hint: 'Global ranking by current Facebook follower count' },
];

export default function FacebookPills({ activeSubfeature }) {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-5xl mx-auto px-4">
      {fbSubfeatures.map((sub) => {
        const SubIcon = sub.icon;
        const isSelected = 
          path === sub.path ||
          (sub.id === 'video' && (path === '/facebook' || path === '/facebook/facebook-video-downloader' || path === '/facebook-video-downloader' || activeSubfeature === 'all' || activeSubfeature === 'video')) ||
          (sub.id === 'top100' && path.includes('top-100-facebook-pages')) ||
          (sub.id === activeSubfeature);

        return (
          <Link
            key={sub.id}
            to={sub.path}
            title={sub.hint}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
              isSelected
                ? 'bg-blue-500/20 border-blue-500/60 text-white shadow-md shadow-blue-500/10'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-800'
            }`}
          >
            <SubIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-blue-400' : 'text-slate-400'}`} />
            <span>{sub.label}</span>
            {sub.id === 'top100' && (
              <span className="text-[10px] bg-blue-500 text-white font-extrabold px-1.5 py-0.2 rounded-full ml-0.5">
                12H
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}
