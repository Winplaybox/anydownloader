import React from 'react';
import { ChevronDown } from 'lucide-react';
import { HOME_FAQS } from '../seo/SEOHead.jsx';

/** Native <details>: works without JavaScript, so crawlers and slow phones always get the answers. */
export default function Faq({ faqs }) {
  const list = faqs && faqs.length ? faqs : HOME_FAQS;
  return (
    <section className="w-full max-w-3xl mx-auto px-4 py-12 sm:py-16" aria-labelledby="faq-title">
      <h2 id="faq-title" className="text-2xl sm:text-3xl font-bold text-[var(--text)] text-center">Questions people ask</h2>
      <div className="mt-8 space-y-2.5">
        {list.map((f, i) => (
          <details key={i} className="group rounded-2xl border border-[var(--border)] bg-[var(--surface)] open:border-[var(--accent)]" open={i === 0}>
            <summary className="flex items-center justify-between gap-4 cursor-pointer list-none p-4 sm:p-5 font-semibold text-[var(--text)] min-h-14 [&::-webkit-details-marker]:hidden">
              <span>{f.q}</span>
              <ChevronDown className="w-5 h-5 shrink-0 text-[var(--text-muted)] transition-transform group-open:rotate-180" />
            </summary>
            <p className="px-4 sm:px-5 pb-5 text-[var(--text-muted)] leading-relaxed">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
