import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  PlaySquare, 
  Image as ImageIcon, 
  Film, 
  Clock, 
  Tv, 
  Layers, 
  Eye, 
  Trophy 
} from 'lucide-react';

export const igSubfeatures = [
  { id: 'video', label: 'Video', icon: PlaySquare, path: '/instagram/instagram-video-downloader', hint: 'Download public Instagram videos in 1080p Full HD' },
  { id: 'photo', label: 'Photo', icon: ImageIcon, path: '/instagram/instagram-photo-downloader', hint: 'Save high-resolution original Instagram photos' },
  { id: 'reels', label: 'Reels', icon: Film, path: '/instagram/instagram-reels-downloader', hint: 'Save viral 9:16 Instagram Reels with audio' },
  { id: 'story', label: 'Story', icon: Clock, path: '/instagram/instagram-story-downloader', hint: 'Archive public Instagram stories before they expire' },
  { id: 'igtv', label: 'Igtv', icon: Tv, path: '/instagram/instagram-igtv-downloader', hint: 'Download long-form IGTV video broadcasts in HD' },
  { id: 'carousel', label: 'Carousel', icon: Layers, path: '/instagram/instagram-carousel-downloader', hint: 'Download multi-slide photo and video carousel albums' },
  { id: 'viewer', label: 'Viewer', icon: Eye, path: '/instagram/instagram-viewer', hint: 'Anonymous profile viewer & HD avatar picture downloader' },
  { id: 'top100', label: 'Top 100 Accounts', icon: Trophy, path: '/instagram/top-100-instagram-accounts', hint: 'Global ranking by current Instagram follower count' },
];

export default function InstagramPills({ activeSubfeature }) {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-5xl mx-auto px-4">
      {igSubfeatures.map((sub) => {
        const SubIcon = sub.icon;
        const isSelected = 
          path === sub.path ||
          (sub.id === 'video' && (path === '/instagram' || path === '/instagram/instagram-downloader' || path === '/instagram-downloader' || activeSubfeature === 'all' || activeSubfeature === 'video')) ||
          (sub.id === 'reels' && (path === '/instagram/instagram-reels' || path === '/instagram-reels')) ||
          (sub.id === 'photo' && (path === '/instagram/instagram-photos' || path === '/instagram-photo')) ||
          (sub.id === 'top100' && path.includes('top-100-instagram-accounts')) ||
          (sub.id === activeSubfeature);

        return (
          <Link
            key={sub.id}
            to={sub.path}
            title={sub.hint}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
              isSelected
                ? 'bg-gradient-to-r from-pink-500/25 via-purple-500/25 to-amber-500/20 border-pink-500/60 text-white shadow-md shadow-pink-500/10'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-800'
            }`}
          >
            <SubIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-pink-400' : 'text-slate-400'}`} />
            <span>{sub.label}</span>
            {sub.id === 'top100' && (
              <span className="text-[10px] bg-gradient-to-r from-pink-500 to-rose-500 text-white font-extrabold px-1.5 py-0.2 rounded-full ml-0.5">
                12H
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}
