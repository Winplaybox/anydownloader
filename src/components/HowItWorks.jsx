import React from 'react';
import { Copy, Sparkles, DownloadCloud } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      num: '01',
      title: 'Copy the Media Link',
      desc: 'Open YouTube, Instagram, TikTok, or Facebook and copy the link to the video, reel, or audio.',
      icon: Copy
    },
    {
      num: '02',
      title: 'Paste into AnyDownloader',
      desc: 'Paste the link into the search box above and click "Fetch Media". Our Python engine extracts all available formats.',
      icon: Sparkles
    },
    {
      num: '03',
      title: 'Select Quality & Download',
      desc: 'Choose your desired resolution (1080p, 720p, 480p) or audio quality (MP3) and download directly to your device.',
      icon: DownloadCloud
    }
  ];

  return (
    <section id="how-it-works" className="py-16 bg-slate-900/30 border-y border-slate-800/80">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <span className="text-xs font-bold text-rose-500 uppercase tracking-widest">Simple 3-Step Process</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
            How to Download Any Video or Audio
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map(s => {
            const Icon = s.icon;
            return (
              <div key={s.num} className="relative bg-slate-900 border border-slate-800 rounded-3xl p-6 text-center">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-rose-600 to-amber-500 flex items-center justify-center text-white mx-auto mb-4 shadow-lg shadow-rose-600/20">
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-mono-data font-bold text-rose-400 mb-1 block">STEP {s.num}</span>
                <h3 className="font-bold text-white text-lg mb-2">{s.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
