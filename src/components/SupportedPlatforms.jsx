import React from 'react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon, 
  TwitterXIcon, 
  PinterestIcon 
} from './BrandIcons.jsx';

const PLATFORMS = [
  {
    name: 'YouTube',
    desc: 'Videos, Shorts, Playlists, 1080p, 4K & MP3 Audio',
    icon: YoutubeIcon,
    color: 'from-red-600 to-rose-600'
  },
  {
    name: 'Instagram',
    desc: 'Reels, Stories, Posts & IGTV video in Full HD',
    icon: InstagramIcon,
    color: 'from-pink-600 to-purple-600'
  },
  {
    name: 'TikTok',
    desc: 'Watermark-free HD videos & audio sound tracks',
    icon: TiktokIcon,
    color: 'from-cyan-500 to-blue-600'
  },
  {
    name: 'Facebook',
    desc: 'Public Reels, Watch clips & high-res videos',
    icon: FacebookIcon,
    color: 'from-blue-600 to-indigo-600'
  },
  {
    name: 'X (Twitter)',
    desc: 'Tweets with MP4 video streams & GIFs',
    icon: TwitterXIcon,
    color: 'from-slate-700 to-slate-900'
  },
  {
    name: 'Pinterest',
    desc: 'Idea pins, video pins & animation clips',
    icon: PinterestIcon,
    color: 'from-rose-600 to-red-700'
  }
];

export default function SupportedPlatforms() {
  return (
    <section id="supported-platforms" className="py-16 max-w-7xl mx-auto px-4">
      <div className="text-center mb-12">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">
          Supported Platforms & Websites
        </h2>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          AnyDownloader works seamlessly across over 1,700 sites. No software installation needed.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {PLATFORMS.map(p => {
          const Icon = p.icon;
          return (
            <div
              key={p.name}
              className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition hover:shadow-xl group"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${p.color} flex items-center justify-center text-white shadow-md`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base group-hover:text-rose-400 transition">
                    {p.name}
                  </h3>
                  <span className="text-[10px] uppercase font-bold text-emerald-400">Supported</span>
                </div>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {p.desc}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
