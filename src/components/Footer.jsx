import React from 'react';
import { Link } from 'react-router-dom';

const COLS = [
  { title: 'Downloaders', links: [
    ['YouTube', '/youtube-video-downloader'], ['Instagram', '/instagram-video-downloader'], ['TikTok', '/tiktok-video-downloader'],
    ['Facebook', '/facebook-video-downloader'], ['X (Twitter)', '/twitter-video-downloader'], ['Pinterest', '/pinterest-video-downloader'],
    ['Reddit', '/reddit-video-downloader'], ['Threads', '/threads-video-downloader'], ['Any website', '/any-website-downloader'],
  ] },
  { title: 'Tools', links: [
    ['YouTube thumbnails', '/youtube-thumbnail-downloader'], ['YouTube Shorts', '/youtube-shorts-downloader'],
    ['Instagram Reels', '/instagram-reels-downloader'], ['YouTube Subscribe Link', '/youtube-subscribe-link-generator'],
    ['AI Video Editor', '/ai-video-editor'], ['Chrome Extension', '/extension'],
  ] },
  { title: 'Company', links: [
    ['Blog and guides', '/blog'], ['Updates', '/updates'], ['Contact', '/contact'],
    ['Terms of Service', '/terms'], ['Privacy Policy', '/privacy'], ['DMCA and security', '/dmca'],
  ] },
];

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-[var(--border)] bg-[var(--surface)]" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 grid gap-10 md:grid-cols-[1.3fr_repeat(3,1fr)]">
        <div>
          <Link to="/" className="inline-flex items-center gap-2" aria-label="OVD home">
            <span className="w-9 h-9 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center font-extrabold text-lg" style={{ fontFamily: 'var(--font-display)' }}>o</span>
            <span className="font-extrabold text-xl tracking-tight" style={{ fontFamily: 'var(--font-display)' }}>ovd</span>
          </Link>
          <p className="mt-3 text-sm text-[var(--text-muted)] max-w-xs leading-relaxed">
            Free video and photo downloader for public posts. No account, no app, nothing stored on our servers.
          </p>
        </div>
        {COLS.map((c) => (
          <nav key={c.title} aria-label={c.title}>
            <h2 className="text-sm font-bold text-[var(--text)]" style={{ fontFamily: 'var(--font)' }}>{c.title}</h2>
            <ul className="mt-3 space-y-2.5">
              {c.links.map(([label, to]) => (
                <li key={to}><Link to={to} className="text-sm text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">{label}</Link></li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <div className="border-t border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5 flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between text-xs text-[var(--text-muted)]">
          <p>© {new Date().getFullYear()} OVD (ovd.winplaybox.in)</p>
          <p className="max-w-lg">OVD is an independent tool and does not host media. Only download content you own or have permission to save.</p>
        </div>
      </div>
    </footer>
  );
}
