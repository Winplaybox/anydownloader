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
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--accent)] font-semibold mb-4 shadow-inner">
          <Zap className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>Product Changelog & Engine Releases</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-4">
          What&apos;s New in OVD
        </h1>
        <p className="text-[var(--text-muted)] text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
          Explore our continuous release log: new platform extractors, audio converters, 12-hour sync ranking updates, and cloud performance optimizations.
        </p>
      </div>

      {/* Timeline List */}
      <div className="space-y-10 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-[var(--border)] before:hidden sm:before:block">
        {releaseUpdates.map((rel, idx) => (
          <div key={rel.version} className="relative flex flex-col sm:flex-row gap-6 items-start">
            
            {/* Timeline Dot Icon */}
            <div className="hidden sm:flex w-10 h-10 rounded-2xl bg-[var(--surface)] border border-[var(--border-strong)]/80 text-[var(--accent)] items-center justify-center shrink-0 z-10 shadow-lg group-hover:scale-110 transition">
              <GitCommit className="w-5 h-5 text-[var(--accent)]" />
            </div>

            {/* Release Card */}
            <div className="bg-[var(--surface)] hover:bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-3xl p-6 sm:p-8 flex-1 shadow-xl transition">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-base font-black text-[var(--text)] bg-[var(--bg)] px-3 py-1 rounded-xl border border-[var(--border)]">
                    {rel.version}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${rel.badgeColor}`}>
                    {rel.badge}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] font-medium">
                  <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>{rel.date}</span>
                </div>
              </div>

              <h3 className="text-lg sm:text-xl font-bold text-[var(--text)] mb-2">
                {rel.title}
              </h3>

              <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-6">
                {rel.description}
              </p>

              {/* Highlights */}
              <div className="space-y-2.5 bg-[var(--bg)]/70 p-4 rounded-2xl border border-[var(--border)] text-xs">
                {rel.highlights.map((item, hIdx) => (
                  <div key={hIdx} className="flex items-start gap-2.5">
                    <CheckCircle2 className={`w-4 h-4 shrink-0 mt-0.5 ${item.color}`} />
                    <div className="text-[var(--text)] leading-normal">
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
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-4">
          <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-[var(--bg-alt)] rounded-xl flex items-center justify-center border border-[var(--border)] text-[var(--text-muted)] text-xs font-mono">
            <span>[ Responsive Release Log Leaderboard Ad Unit ]</span>
          </div>
        </div>
      </div>
    </div>
  );
}

