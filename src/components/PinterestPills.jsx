import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  PlaySquare, 
  Image as ImageIcon, 
  Sparkles, 
  Layers, 
  FolderDown, 
  User 
} from 'lucide-react';

export const pinterestSubfeatures = [
  { id: 'video', label: 'Video', icon: PlaySquare, path: '/pinterest/pinterest-video-downloader', hint: 'Download Pinterest videos in 1080p Full HD MP4 with audio' },
  { id: 'photo', label: 'Photo', icon: ImageIcon, path: '/pinterest/pinterest-photo-downloader', hint: 'Save original uncompressed high-resolution Pinterest photos' },
  { id: 'gif', label: 'GIF', icon: Sparkles, path: '/pinterest/pinterest-gif-downloader', hint: 'Download animated Pinterest GIFs and video loops' },
  { id: 'story', label: 'Idea Pin / Story', icon: Layers, path: '/pinterest/pinterest-story-downloader', hint: 'Download multi-page Pinterest Idea Pins & Story clips' },
  { id: 'board', label: 'Board', icon: FolderDown, path: '/pinterest/pinterest-board-downloader', hint: 'Download all pins and photos from public Pinterest boards' },
  { id: 'profile', label: 'Profile & DP', icon: User, path: '/pinterest/pinterest-profile-downloader', hint: 'Anonymous profile viewer & HD avatar picture downloader' },
];

export default function PinterestPills({ activeSubfeature }) {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-5xl mx-auto px-4">
      {pinterestSubfeatures.map((sub) => {
        const SubIcon = sub.icon;
        const isSelected = 
          path === sub.path ||
          (sub.id === 'video' && (path === '/pinterest' || path === '/pinterest/pinterest-downloader' || path === '/pinterest-downloader' || activeSubfeature === 'all' || activeSubfeature === 'video')) ||
          (sub.id === 'photo' && (path === '/pinterest/pinterest-photos' || path === '/pinterest-photo' || path === '/pinterest-image-downloader')) ||
          (sub.id === activeSubfeature);

        return (
          <Link
            key={sub.id}
            to={sub.path}
            title={sub.hint}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
              isSelected
                ? 'bg-gradient-to-r from-red-600/30 via-rose-600/25 to-pink-600/25 border-red-500/60 text-white shadow-md shadow-red-500/10'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-800'
            }`}
          >
            <SubIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-red-400' : 'text-slate-400'}`} />
            <span>{sub.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
