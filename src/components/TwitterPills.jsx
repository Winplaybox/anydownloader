import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  PlaySquare, 
  Music, 
  Image as ImageIcon, 
  Sparkles, 
  User 
} from 'lucide-react';

export const twitterSubfeatures = [
  { id: 'video', label: 'Twitter Video (MP4)', icon: PlaySquare, path: '/twitter/twitter-video-downloader', hint: 'Download Twitter / X video clips in 1080p Full HD MP4 with audio' },
  { id: 'mp3', label: 'Twitter MP3 (Audio)', icon: Music, path: '/twitter/twitter-mp3-downloader', hint: 'Extract 320kbps MP3 audio tracks directly from Twitter clips' },
  { id: 'photo', label: 'Photos & Images', icon: ImageIcon, path: '/twitter/twitter-image-downloader', hint: 'Save original uncompressed high-resolution Tweet photos (up to 4 per tweet)' },
  { id: 'gif', label: 'Animated GIFs', icon: Sparkles, path: '/twitter/twitter-gif-downloader', hint: 'Download animated Twitter GIFs and looping animations' },
  { id: 'profile', label: 'Profile & DP', icon: User, path: '/twitter/twitter-profile-downloader', hint: 'Download full-resolution avatar DP and header banner from any X handle' },
];

export default function TwitterPills({ activeSubfeature }) {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 mb-8 max-w-5xl mx-auto px-4">
      {twitterSubfeatures.map((sub) => {
        const SubIcon = sub.icon;
        const isSelected = 
          path === sub.path ||
          (sub.id === 'video' && (path === '/twitter' || path === '/x' || path === '/twitter/twitter-downloader' || path === '/twitter-downloader' || activeSubfeature === 'all' || activeSubfeature === 'video')) ||
          (sub.id === 'mp3' && (path === '/twitter-mp3' || path === '/twitter/twitter-mp3-downloader' || activeSubfeature === 'audio' || activeSubfeature === 'mp3')) ||
          (sub.id === 'photo' && (path === '/twitter-images' || path === '/twitter/twitter-image-downloader' || activeSubfeature === 'photo' || activeSubfeature === 'image')) ||
          (sub.id === 'gif' && (path === '/twitter-gifs' || path === '/twitter/twitter-gif-downloader' || activeSubfeature === 'gif')) ||
          (sub.id === 'profile' && (path === '/twitter-profile' || path === '/twitter/twitter-profile-downloader' || activeSubfeature === 'profile')) ||
          (sub.id === activeSubfeature);

        return (
          <Link
            key={sub.id}
            to={sub.path}
            title={sub.hint}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
              isSelected
                ? 'bg-gradient-to-r from-sky-600/30 via-blue-600/25 to-slate-700/40 border-sky-500/60 text-white shadow-md shadow-sky-500/10'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-800'
            }`}
          >
            <SubIcon className={`w-3.5 h-3.5 ${isSelected ? 'text-sky-400' : 'text-slate-400'}`} />
            <span>{sub.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
