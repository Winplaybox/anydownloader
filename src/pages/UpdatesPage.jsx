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
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--text)] font-semibold mb-4 shadow-xs">
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
        {releaseUpdates.map((rel) => (
          <div key={rel.version} className="relative flex flex-col sm:flex-row gap-6 items-start">
            
            {/* Timeline Dot Icon */}
            <div className="hidden sm:flex w-10 h-10 rounded-2xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] items-center justify-center shrink-0 z-10 shadow-xs">
              <GitCommit className="w-5 h-5 text-[var(--accent)]" />
            </div>

            {/* Release Card */}
            <div className="bg-[var(--surface)] hover:bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-2xl p-6 sm:p-8 flex-1 shadow-sm transition">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-sm font-bold text-[var(--text)] bg-[var(--bg-alt)] px-3 py-1 rounded-lg border border-[var(--border)]">
                    {rel.version}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400">
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
              <div className="space-y-2.5 bg-[var(--bg-alt)] p-4 rounded-xl border border-[var(--border)] text-xs">
                {rel.highlights.map((item, hIdx) => (
                  <div key={hIdx} className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400" />
                    <div className="text-[var(--text)] leading-normal">
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
