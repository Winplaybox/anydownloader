import React from 'react';
import { ClipboardCopy, Download, MousePointerClick } from 'lucide-react';

export default function HowItWorks({ platformLabel = 'the app or website' }) {
  const steps = [
    { icon: ClipboardCopy, title: 'Copy the link', text: `Open the post in ${platformLabel}, tap Share and choose Copy link.` },
    { icon: MousePointerClick, title: 'Paste it above', text: 'Paste the link in the box at the top. OVD finds the video or photos by itself.' },
    { icon: Download, title: 'Pick a quality and save', text: 'Choose the quality you want and tap Download. The file goes to your Downloads folder.' },
  ];
  return (
    <section className="w-full max-w-5xl mx-auto px-4 py-12 sm:py-16" aria-labelledby="how-title">
      <h2 id="how-title" className="text-2xl sm:text-3xl font-bold text-[var(--text)] text-center">Three steps, no sign-up</h2>
      <ol className="mt-8 grid gap-4 md:grid-cols-3">
        {steps.map(({ icon: Icon, title, text }, i) => (
          <li key={title} className="relative rounded-3xl bg-[var(--surface)] border border-[var(--border)] p-5 sm:p-6">
            <span className="absolute top-4 right-5 font-display text-5xl font-extrabold text-[var(--border)] select-none" style={{ fontFamily: 'var(--font-display)' }}>{i + 1}</span>
            <span className="w-11 h-11 rounded-2xl bg-[var(--accent-bg)] text-[var(--accent)] grid place-items-center"><Icon className="w-5 h-5" /></span>
            <h3 className="mt-4 text-lg font-bold text-[var(--text)]">{title}</h3>
            <p className="mt-1.5 text-[var(--text-muted)]">{text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
