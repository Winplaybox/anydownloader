import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Lock, FileText, Mail, Newspaper, Sparkles } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="w-full border-t border-[var(--border)] bg-[var(--surface)] text-[var(--text)] transition-colors mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">

          {/* Brand Col */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] flex items-center justify-center font-black text-xs">
                OVD
              </div>
              <span className="font-extrabold text-base tracking-tight text-[var(--text)]">
                OVD Downloader
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] max-w-sm leading-relaxed">
              Free, fast social media video and image downloader. Works with any public post from Twitter/X, YouTube, Facebook, Instagram, TikTok and more.
            </p>
            <div className="text-xs text-[var(--text-muted)]">
              Supported: X (Twitter) · YouTube · Facebook · Instagram · TikTok
            </div>
          </div>

          {/* Platform Links */}
          <div className="space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
              Platforms
            </div>
            <ul className="space-y-2 text-xs font-semibold">
              <li><Link to="/twitter-video-downloader" className="hover:text-[var(--accent)] transition-colors">Twitter/X Video & Photos</Link></li>
              <li><Link to="/youtube-video-downloader" className="hover:text-[var(--accent)] transition-colors">YouTube Videos & Thumbnails</Link></li>
              <li><Link to="/facebook-video-downloader" className="hover:text-[var(--accent)] transition-colors">Facebook Videos & Reels</Link></li>
              <li><Link to="/instagram-video-downloader" className="hover:text-[var(--accent)] transition-colors">Instagram Reels & Carousels</Link></li>
              <li><Link to="/tiktok-video-downloader" className="hover:text-[var(--accent)] transition-colors">TikTok Videos (No Watermark)</Link></li>
            </ul>
          </div>

          {/* Legal & Resources */}
          <div className="space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
              Resources
            </div>
            <ul className="space-y-2 text-xs font-semibold">
              <li><Link to="/blog" className="hover:text-[var(--accent)] transition-colors">Blog & Guides</Link></li>
              <li><Link to="/updates" className="hover:text-[var(--accent)] transition-colors">Updates & Changelog</Link></li>
              <li><Link to="/terms" className="hover:text-[var(--accent)] transition-colors">Terms of Service</Link></li>
              <li><Link to="/privacy" className="hover:text-[var(--accent)] transition-colors">Privacy Policy</Link></li>
              <li><Link to="/security" className="hover:text-[var(--accent)] transition-colors">DMCA & Security</Link></li>
              <li><Link to="/contact" className="hover:text-[var(--accent)] transition-colors">Contact Support</Link></li>
            </ul>
          </div>

        </div>

        {/* Bottom Disclaimer & Copyright */}
        <div className="pt-8 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--text-muted)]">
          <p>
            © {new Date().getFullYear()} OVD Downloader (ovd.winplaybox.in). All rights reserved.
          </p>
          <p className="text-center sm:text-right max-w-md">
            Disclaimer: OVD is an independent web tool and does not host copyrighted media. Users must ensure they have authorization to download content.
          </p>
        </div>
      </div>
    </footer>
  );
}
