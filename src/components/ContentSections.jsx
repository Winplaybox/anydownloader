import React from 'react';

/** The long-form guide copy from pagesConfig, rendered as real headings + paragraphs for search engines. */
export default function ContentSections({ cfg }) {
  if (!cfg || !cfg.sections || !cfg.sections.length) return null;
  return (
    <section className="w-full max-w-3xl mx-auto px-4 py-10 sm:py-14" aria-labelledby="guide-title">
      <h2 id="guide-title" className="text-2xl sm:text-3xl font-bold text-[var(--text)]">{cfg.guideTitle || cfg.title}</h2>
      {cfg.guideIntro && <p className="mt-3 text-lg text-[var(--text-muted)] leading-relaxed">{cfg.guideIntro}</p>}
      <div className="mt-8 space-y-7">
        {cfg.sections.map((s) => (
          <article key={s.heading}>
            <h3 className="text-xl font-bold text-[var(--text)]">{s.heading}</h3>
            <p className="mt-2 text-[var(--text-muted)] leading-[1.75] max-w-[68ch]">{s.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
