import React from 'react';
import { 
  Sparkles, 
  GitCommit, 
  Calendar, 
  Tag, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Cpu, 
  Zap, 
  Layers 
} from 'lucide-react';
import { releaseUpdates } from '../data/updatesData.js';

export default function UpdatesPage() {
  return (
    <div className="py-10 max-w-4xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-rose-400 font-semibold mb-4 shadow-inner">
          <Zap className="w-3.5 h-3.5 text-rose-400" />
          <span>Product Changelog & Engine Releases</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
          What&apos;s New in OVD
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
          Explore our continuous release log: new platform extractors, audio converters, 12-hour sync ranking updates, and cloud performance optimizations.
        </p>
      </div>

      {/* Timeline List */}
      <div className="space-y-10 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-slate-800/80 before:hidden sm:before:block">
        {releaseUpdates.map((rel, idx) => (
          <div key={rel.version} className="relative flex flex-col sm:flex-row gap-6 items-start">
            
            {/* Timeline Dot Icon */}
            <div className="hidden sm:flex w-10 h-10 rounded-2xl bg-slate-900 border border-slate-700/80 text-rose-400 items-center justify-center shrink-0 z-10 shadow-lg group-hover:scale-110 transition">
              <GitCommit className="w-5 h-5 text-rose-400" />
            </div>

            {/* Release Card */}
            <div className="bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-3xl p-6 sm:p-8 flex-1 shadow-xl transition">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-800/60">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-base font-black text-white bg-slate-950 px-3 py-1 rounded-xl border border-slate-800">
                    {rel.version}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${rel.badgeColor}`}>
                    {rel.badge}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  <span>{rel.date}</span>
                </div>
              </div>

              <h3 className="text-lg sm:text-xl font-bold text-white mb-2">
                {rel.title}
              </h3>

              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                {rel.description}
              </p>

              {/* Highlights */}
              <div className="space-y-2.5 bg-slate-950/70 p-4 rounded-2xl border border-slate-800/60 text-xs">
                {rel.highlights.map((item, hIdx) => (
                  <div key={hIdx} className="flex items-start gap-2.5">
                    <CheckCircle2 className={`w-4 h-4 shrink-0 mt-0.5 ${item.color}`} />
                    <div className="text-slate-300 leading-normal">
                      <strong className={`${item.color} mr-1.5`}>[{item.tag}]</strong>
                      <span>{item.text}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AdSense In-Article Display Unit */}
      <div className="mt-16 text-center">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Responsive Release Log Leaderboard Ad Unit ]</span>
          </div>
        </div>
      </div>
    </div>
  );
}
