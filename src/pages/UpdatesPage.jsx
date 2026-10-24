import React from 'react';
import { 
  GitCommit, 
  Calendar, 
  CheckCircle2, 
  Zap 
} from 'lucide-react';
import { releaseUpdates } from '../data/updatesData.js';

export default function UpdatesPage() {
  return (
    <div className="py-10 max-w-4xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] text-xs text-[var(--text)] font-semibold mb-4 shadow-xs">
          <Zap className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>Product Changelog & Engine Releases</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-4">
          What's New in OVD
        </h1>
        <p className="text-[var(--text-muted)] text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
          Explore our continuous release log: new platform extractors, audio converters, 12-hour sync ranking updates, and cloud performance optimizations.
        </p>
      </div>

      {/* Timeline List */}
      <div className="space-y-8 relative before:absolute before:inset-0 before:left-4.5 before:w-0.5 before:bg-[var(--border)] before:hidden sm:before:block">
        {releaseUpdates.map((rel) => (
          <div key={rel.version} className="relative flex flex-col sm:flex-row gap-5 items-start">
            
            {/* Timeline Dot Icon */}
            <div className="hidden sm:flex w-9 h-9 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] items-center justify-center shrink-0 z-10 shadow-xs">
              <GitCommit className="w-4 h-4 text-[var(--accent)]" />
            </div>

            {/* Release Card */}
            <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 sm:p-7 flex-1 shadow-xs transition-colors">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-[var(--text)] bg-[var(--bg-alt)] px-2.5 py-1 rounded-md border border-[var(--border)]">
                    {rel.version}
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[var(--positive-bg)] text-[var(--positive)] border border-[var(--positive)]/30">
                    {rel.badge}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] font-medium">
                  <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span>{rel.date}</span>
                </div>
              </div>

              <h2 className="text-base sm:text-lg font-bold text-[var(--text)] mb-2">
                {rel.title}
              </h2>

              <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-5">
                {rel.description}
              </p>

              {/* Highlights */}
              <div className="space-y-2 bg-[var(--bg-alt)] p-3.5 rounded-lg border border-[var(--border)] text-xs">
                {rel.highlights.map((item, hIdx) => (
                  <div key={hIdx} className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--positive)]" />
                    <div className="text-[var(--text)] leading-relaxed">
                      <strong className="text-[var(--text)] mr-1.5 font-bold">[{item.tag}]</strong>
                      <span className="text-[var(--text-muted)]">{item.text}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
}
