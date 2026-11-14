import React from 'react';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import HowItWorks from '../components/HowItWorks.jsx';
import ContentSections from '../components/ContentSections.jsx';
import PlatformGrid from '../components/PlatformGrid.jsx';
import Faq from '../components/Faq.jsx';
import useResolver from '../hooks/useResolver.js';
import { PLATFORM_LABEL } from '../data/toolRoutes.js';

function ResultSkeleton() {
  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-10" aria-hidden="true">
      <div className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-6 grid gap-4 md:grid-cols-[280px_1fr]">
        <div className="ovd-skeleton aspect-video md:aspect-[4/3] rounded-2xl" />
        <div className="space-y-3"><div className="ovd-skeleton h-5 w-1/3 rounded-lg" /><div className="ovd-skeleton h-8 w-4/5 rounded-lg" /><div className="ovd-skeleton h-16 rounded-xl" /></div>
      </div>
    </div>
  );
}

/** One page component for the home page and every platform landing page. */
export default function DownloaderPage({ title, subtitle, platform = 'all', cfg, faqs, route }) {
  const r = useResolver();
  return (
    <>
      <HeroDownloader
        url={r.url} setUrl={r.setUrl} onSubmit={r.fetchMedia} onClear={r.reset}
        loading={r.loading} error={r.error} errorCode={r.errorCode} retryable={r.retryable}
        title={title} subtitle={subtitle} platform={platform}
      />
      {r.loading && <ResultSkeleton />}
      {r.data && !r.loading && (
        <MediaResultCard data={r.data} onReset={r.reset} onRetry={() => r.fetchMedia(r.url)} innerRef={r.resultRef} />
      )}
      <HowItWorks platformLabel={platform === 'all' ? 'the app or website' : PLATFORM_LABEL[platform]} />
      <ContentSections cfg={cfg} />
      <PlatformGrid exclude={route} />
      <Faq faqs={faqs} />
    </>
  );
}
