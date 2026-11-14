import React from 'react';
import DownloaderPage from './DownloaderPage.jsx';
import { pagesConfig } from '../data/pagesConfig.js';

const firstSentences = (t = '', max = 170) => {
  const s = t.replace(/\s+/g, ' ').trim();
  if (s.length <= max) return s;
  const cut = s.slice(0, max);
  return cut.slice(0, Math.max(cut.lastIndexOf(' '), 100)) + '...';
};

export default function ToolPage({ route }) {
  const cfg = pagesConfig[route.key] || {};
  return (
    <DownloaderPage
      title={cfg.title || 'Video Downloader'}
      subtitle={firstSentences(cfg.guideIntro) || 'Paste a link, pick a quality and download. Free, with no sign-up.'}
      platform={route.platform}
      cfg={cfg}
      faqs={cfg.faqs}
      route={route.path}
    />
  );
}
