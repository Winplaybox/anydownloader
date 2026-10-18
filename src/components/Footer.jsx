import React from 'react';
import { Download, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-400 text-xs py-12">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-rose-600 to-amber-500 flex items-center justify-center text-white">
                <Download className="w-4 h-4 stroke-[2.5]" />
              </div>
              <span className="font-extrabold text-base text-white">
                Any<span className="text-rose-500">Downloader</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
              Universal media downloader powered by Python. Download high-definition videos, reels, and audio from any social platform.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">
              Supported Formats
            </h4>
            <ul className="space-y-1.5 text-xs">
              <li>YouTube MP4 & MP3</li>
              <li>Instagram Reels & Stories</li>
              <li>TikTok (No Watermark)</li>
              <li>Facebook Public Videos</li>
              <li>Twitter / X Video Clips</li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white uppercase text-[11px] tracking-wider mb-3">
              Legal & Disclaimer
            </h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              AnyDownloader does not host or store any copyrighted videos on its servers. All videos and audios are served directly from official CDN content delivery networks for educational and personal backup purposes only.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px]">
          <p>&copy; {new Date().getFullYear()} AnyDownloader. Powered by Winplaybox.</p>
          <p className="flex items-center gap-1">
            Engineered with <Heart className="w-3 h-3 text-rose-500 fill-rose-500 inline" /> for blazing fast speed.
          </p>
        </div>
      </div>
    </footer>
  );
}
