import React from 'react';
import { Link } from 'react-router-dom';
import { Download, Heart, Shield, Lock, FileText, Mail, Award } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 text-slate-400 text-xs py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          
          {/* Brand Col */}
          <div>
            <Link to="/" className="flex items-center gap-2 mb-3 group">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-rose-600 via-pink-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-rose-600/20">
                <Download className="w-4 h-4 stroke-[2.5]" />
              </div>
              <span className="font-extrabold text-base text-white">
                OVD <span className="bg-gradient-to-r from-rose-500 to-amber-400 bg-clip-text text-transparent">Downloader</span>
              </span>
            </Link>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Fast, high-fidelity universal media downloader and YouTube channel analytics platform recorded by <strong className="text-rose-400 font-semibold">OVD.winplaybox.in</strong>.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Safe & Secure SSL Protected</span>
            </div>
          </div>

          {/* YouTube Tools */}
          <div>
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">
              YouTube Tool Suite
            </h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/youtube/youtube-video-downloader" className="hover:text-rose-400 transition">YouTube Video Downloader</Link></li>
              <li><Link to="/youtube/youtube-mp4" className="hover:text-rose-400 transition">YouTube MP4 1080p</Link></li>
              <li><Link to="/youtube/youtube-shorts" className="hover:text-rose-400 transition">YouTube Shorts Downloader</Link></li>
              <li><Link to="/youtube/youtube-mp3" className="hover:text-rose-400 transition">YouTube to MP3 (320kbps)</Link></li>
              <li><Link to="/youtube/youtube-transcript" className="hover:text-rose-400 transition">YouTube Transcript Generator</Link></li>
              <li><Link to="/youtube/youtube-subtitles" className="hover:text-rose-400 transition">YouTube Subtitles (SRT/VTT)</Link></li>
              <li><Link to="/youtube/youtube-thumbnails" className="hover:text-rose-400 transition">YouTube Thumbnails (All Qualities)</Link></li>
            </ul>
          </div>

          {/* Supported Platforms & Ranks */}
          <div>
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">
              Platforms & Rankings
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/youtube/top-100-youtube-channels" className="text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1.5 transition">
                  <Award className="w-3.5 h-3.5" />
                  <span>Top 100 YouTube Channels</span>
                </Link>
              </li>
              <li>
                <Link to="/facebook/top-100-facebook-pages" className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1.5 transition">
                  <Award className="w-3.5 h-3.5" />
                  <span>Top 100 Facebook Pages</span>
                </Link>
              </li>
              <li><Link to="/facebook/facebook-video-downloader" className="hover:text-blue-400 transition">Facebook Video Downloader</Link></li>
              <li><Link to="/facebook/facebook-reels" className="hover:text-blue-400 transition">Facebook Reels Downloader</Link></li>
              <li><Link to="/facebook/facebook-posts" className="hover:text-blue-400 transition">Facebook Posts & Photos</Link></li>
              <li><Link to="/facebook/facebook-transcript" className="hover:text-blue-400 transition">Facebook Video Transcripts</Link></li>
              <li><Link to="/instagram/instagram-downloader" className="hover:text-pink-400 transition">Instagram Reels Downloader</Link></li>
              <li><Link to="/tiktok/tiktok-downloader" className="hover:text-cyan-400 transition">TikTok (No Watermark)</Link></li>
              <li><Link to="/blogs" className="hover:text-amber-400 transition">Social Media Updates Blog</Link></li>
              <li><Link to="/updates" className="hover:text-rose-400 transition">Product Releases & Changelog</Link></li>
            </ul>
          </div>

          {/* Legal & AdSense Compliance */}
          <div>
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">
              Legal & Policies
            </h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/security" className="text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1.5 transition"><Lock className="w-3.5 h-3.5" />Security & Self-XSS</Link></li>
              <li><Link to="/privacy-policy" className="hover:text-slate-200 transition">Privacy Policy</Link></li>
              <li><Link to="/terms-of-service" className="hover:text-slate-200 transition">Terms of Service</Link></li>
              <li><Link to="/contact" className="hover:text-slate-200 transition">Contact Us & Feedback</Link></li>
            </ul>
            <p className="text-[10px] text-slate-500 mt-4 leading-relaxed">
              Disclaimer: OVD does not host or store any copyright media on its servers. All media streams are delivered directly from official CDNs for personal and fair use purposes.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px]">
          <p>&copy; {new Date().getFullYear()} OVD.winplaybox.in. All rights reserved.</p>
          <p className="flex items-center gap-1">
            Engineered with <Heart className="w-3 h-3 text-rose-500 fill-rose-500 inline" /> by Winplaybox.
          </p>
        </div>
      </div>
    </footer>
  );
}
