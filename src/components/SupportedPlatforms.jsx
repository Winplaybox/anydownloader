import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon, 
  TwitterXIcon, 
  PinterestIcon,
  RedditIcon,
  ThreadsIcon,
  GlobeIcon
} from './BrandIcons.jsx';

const PLATFORMS = [
  {
    name: 'YouTube',
    desc: 'Videos, Shorts, Playlists, 1080p, 4K & MP3 Audio',
    icon: YoutubeIcon,
    color: 'from-red-600 to-rose-600',
    link: '/youtube-video-downloader',
    badge: '1080p / 4K'
  },
  {
    name: 'Instagram',
    desc: 'Reels, Stories, Posts & IGTV video in Full HD',
    icon: InstagramIcon,
    color: 'from-pink-600 to-purple-600',
    link: '/instagram-video-downloader',
    badge: 'Reels & Photos'
  },
  {
    name: 'TikTok',
    desc: 'Watermark-free HD videos & audio sound tracks',
    icon: TiktokIcon,
    color: 'from-cyan-500 to-blue-600',
    link: '/tiktok-video-downloader',
    badge: 'No Watermark'
  },
  {
    name: 'Facebook',
    desc: 'Public Reels, Watch clips & high-res videos',
    icon: FacebookIcon,
    color: 'from-blue-600 to-indigo-600',
    link: '/facebook-video-downloader',
    badge: 'Reels & Watch'
  },
  {
    name: 'X (Twitter)',
    desc: 'Tweets with MP4 video streams, 320kbps MP3 audio & GIFs',
    icon: TwitterXIcon,
    color: 'from-sky-600 to-slate-900',
    link: '/twitter-video-downloader',
    badge: 'MP4, MP3 & DP'
  },
  {
    name: 'Pinterest',
    desc: 'Idea pins, video pins & animation clips',
    icon: PinterestIcon,
    color: 'from-rose-600 to-red-700',
    link: '/pinterest-video-downloader',
    badge: 'Video & Board'
  },
  {
    name: 'Reddit',
    desc: 'Reddit video posts with sound, gifs and comments media',
    icon: RedditIcon,
    color: 'from-orange-600 to-amber-700',
    link: '/reddit-video-downloader',
    badge: 'HD + Audio'
  },
  {
    name: 'Threads',
    desc: 'Instagram Threads videos, carousels and high-res photos',
    icon: ThreadsIcon,
    color: 'from-neutral-800 to-neutral-950',
    link: '/threads-video-downloader',
    badge: 'Video & Photos'
  },
  {
    name: 'Any Website',
    desc: 'Direct media crawler for blogs, video hosts and open web URLs',
    icon: GlobeIcon,
    color: 'from-emerald-600 to-teal-700',
    link: '/any-website-downloader',
    badge: 'Universal'
  }
];

export default function SupportedPlatforms() {
  return (
    <section id="supported-platforms" className="py-16 max-w-7xl mx-auto px-4">
      <div className="text-center mb-12">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[var(--text)] mb-3">
          Supported Platforms & Websites
        </h2>
        <p className="text-[var(--text-muted)] text-sm max-w-xl mx-auto">
          Fast, universal media downloader for all major social networks. 100% free, no registration required.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {PLATFORMS.map(p => {
          const Icon = p.icon;
          return (
            <Link
              key={p.name}
              to={p.link}
              className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 hover:border-[var(--primary)] hover:bg-[var(--surface)] transition hover:shadow-lg group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${p.color} flex items-center justify-center text-white shadow-md`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-[var(--text)] text-base group-hover:text-[var(--accent)] transition-colors">
                        {p.name}
                      </h3>
                      <span className="text-[10px] uppercase font-bold text-emerald-500">Supported</span>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold text-[var(--text-muted)] bg-[var(--bg-alt)] px-2 py-0.5 rounded-full border border-[var(--border)]">
                    {p.badge}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
                  {p.desc}
                </p>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] group-hover:opacity-80 transition-opacity">
                <span>Explore {p.name} Tools</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
