import React from 'react';
import { Link } from 'react-router-dom';
import {
  TwitterXIcon, YoutubeIcon, FacebookIcon, InstagramIcon, TiktokIcon, PinterestIcon, RedditIcon, ThreadsIcon, GlobeIcon,
} from './BrandIcons.jsx';

const ITEMS = [
  { to: '/youtube-video-downloader', name: 'YouTube', note: 'Videos, Shorts, MP3, thumbnails', Icon: YoutubeIcon },
  { to: '/instagram-video-downloader', name: 'Instagram', note: 'Reels, posts, carousels', Icon: InstagramIcon },
  { to: '/tiktok-video-downloader', name: 'TikTok', note: 'Videos without watermark', Icon: TiktokIcon },
  { to: '/facebook-video-downloader', name: 'Facebook', note: 'Videos and Reels', Icon: FacebookIcon },
  { to: '/twitter-video-downloader', name: 'X (Twitter)', note: 'Videos, GIFs, photos', Icon: TwitterXIcon },
  { to: '/pinterest-video-downloader', name: 'Pinterest', note: 'Videos and images', Icon: PinterestIcon },
  { to: '/reddit-video-downloader', name: 'Reddit', note: 'Videos with sound', Icon: RedditIcon },
  { to: '/threads-video-downloader', name: 'Threads', note: 'Videos and photos', Icon: ThreadsIcon },
  { to: '/any-website-downloader', name: 'Any website', note: 'Any public page with media', Icon: GlobeIcon },
];

export default function PlatformGrid({ exclude }) {
  const list = ITEMS.filter((i) => i.to !== exclude);
  return (
    <section className="w-full max-w-5xl mx-auto px-4 py-12 sm:py-16" aria-labelledby="more-title">
      <h2 id="more-title" className="text-2xl sm:text-3xl font-bold text-[var(--text)] text-center">Download from other sites</h2>
      <ul className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
        {list.map(({ to, name, note, Icon }) => (
          <li key={to}>
            <Link to={to} className="h-full block rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 hover:border-[var(--accent)] transition-colors">
              <Icon className="w-6 h-6 text-[var(--text)]" />
              <span className="mt-3 block font-bold text-[var(--text)]">{name}</span>
              <span className="block text-sm text-[var(--text-muted)]">{note}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
