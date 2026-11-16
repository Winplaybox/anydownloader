import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { pagesConfig } from '../data/pagesConfig.js';
import { TOOL_ROUTES } from '../data/toolRoutes.js';

export const SITE = 'https://ovd.winplaybox.in';

const STATIC_META = {
  '/': {
    title: 'OVD - Free Video & Photo Downloader for YouTube, Instagram, TikTok, X and More',
    description: 'Paste a link and save videos, reels, shorts and photos from YouTube, Instagram, TikTok, Facebook, X (Twitter), Pinterest and Reddit. Free, no sign-up, works on phone and desktop.',
  },
  '/ai-video-editor': {
    title: 'Free AI Video Editor - Voiceover, Auto Captions, Title and Tags | OVD',
    description: 'Upload a clip and get an AI voiceover, word-by-word captions, mastered audio and a ready YouTube title, description and tags. Free, 2 videos a day.',
  },
  '/youtube-subscribe-link-generator': {
    title: 'YouTube Subscribe Link Generator (Auto Subscribe Popup) - Free | OVD',
    description: 'Create a YouTube auto-subscribe link that opens the Subscribe popup instantly. Free sub_confirmation link, QR code and HTML button for any channel - no login.',
  },
  '/blog': {
    title: 'Blog - Guides for Saving Videos and Photos | OVD',
    description: 'Practical guides on saving videos, reels and photos from social media, with tips for quality, formats and devices.',
  },
  '/updates': { title: 'Updates and Changelog | OVD', description: 'The latest features, fixes and improvements to OVD.' },
  '/extension': { title: 'OVD Chrome Extension - One-Click Downloads | OVD', description: 'Install the OVD browser extension to save videos and photos right from the page you are watching.' },
  '/contact': { title: 'Contact OVD Support', description: 'Questions, bug reports or takedown requests - contact the OVD team.' },
  '/privacy': { title: 'Privacy Policy | OVD', description: 'How OVD handles your data: no accounts, no stored media.' },
  '/terms': { title: 'Terms of Service | OVD', description: 'The rules for using OVD.' },
  '/dmca': { title: 'DMCA and Security | OVD', description: 'Report copyright concerns or security issues with OVD.' },
  '/ovd-admin': { title: 'OVD Admin', description: 'Private dashboard.', noindex: true },
};

function clip(text, max = 158) {
  const t = String(text || '').replace(/\s+/g, ' ').trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max);
  return cut.slice(0, Math.max(cut.lastIndexOf(' '), 100)).replace(/[,;:.-]+$/, '') + '.';
}

export function getToolRoute(pathname) {
  const clean = pathname.replace(/\/+$/, '') || '/';
  return TOOL_ROUTES.find((r) => r.path === clean) || null;
}

export function getPageMeta(pathname) {
  const clean = pathname.replace(/\/+$/, '') || '/';
  const tool = getToolRoute(clean);
  if (tool) {
    const cfg = pagesConfig[tool.key] || {};
    const name = cfg.title || 'Video Downloader';
    return {
      title: `${name} - Free, No Sign-up | OVD`,
      description: clip(cfg.guideIntro || `Download videos and photos with ${name}. Free, fast, no sign-up.`),
      canonical: SITE + (tool.canonical || tool.path),
      tool,
      cfg,
    };
  }
  if (STATIC_META[clean]) return { ...STATIC_META[clean], canonical: SITE + (clean === '/' ? '/' : clean) };
  return null; // unknown route -> 404 handling
}

function setMeta(selector, attr, value, create) {
  let el = document.head.querySelector(selector);
  if (!el && create) {
    el = document.createElement(create.tag);
    Object.entries(create.attrs).forEach(([k, v]) => el.setAttribute(k, v));
    document.head.appendChild(el);
  }
  if (el) el.setAttribute(attr, value);
}

function setLd(id, json) {
  let el = document.getElementById(id);
  if (!json) { if (el) el.remove(); return; }
  if (!el) {
    el = document.createElement('script');
    el.type = 'application/ld+json';
    el.id = id;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(json);
}

export default function SEOHead() {
  const { pathname } = useLocation();

  useEffect(() => {
    const meta = getPageMeta(pathname);
    const known = !!meta && !meta.noindex;
    const m = meta || {
      title: 'Page not found | OVD',
      description: 'This page does not exist. Paste a link on the OVD home page to download videos and photos.',
      canonical: SITE + '/',
    };

    document.title = m.title;
    setMeta('meta[name="title"]', 'content', m.title);
    setMeta('meta[name="description"]', 'content', m.description);
    setMeta('meta[property="og:title"]', 'content', m.title);
    setMeta('meta[property="og:description"]', 'content', m.description);
    setMeta('meta[property="og:url"]', 'content', m.canonical);
    setMeta('meta[name="twitter:title"]', 'content', m.title);
    setMeta('meta[name="twitter:description"]', 'content', m.description);
    setMeta('meta[name="twitter:url"]', 'content', m.canonical);
    setMeta('link[rel="canonical"]', 'href', m.canonical, { tag: 'link', attrs: { rel: 'canonical' } });
    setMeta('meta[name="robots"]', 'content',
      known ? 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1' : 'noindex, follow',
      { tag: 'meta', attrs: { name: 'robots' } });

    // Page-level structured data (the site-wide Organization / WebApplication block lives in index.html)
    if (m.tool) {
      const faqs = (m.cfg.faqs || []).slice(0, 8);
      const graph = [
        {
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: SITE + '/' },
            { '@type': 'ListItem', position: 2, name: m.cfg.title || 'Downloader', item: m.canonical },
          ],
        },
        {
          '@type': 'HowTo',
          name: m.cfg.guideTitle || `How to use ${m.cfg.title}`,
          step: [
            { '@type': 'HowToStep', name: 'Copy the link', text: 'Open the post or video and copy its link.' },
            { '@type': 'HowToStep', name: 'Paste it in OVD', text: 'Paste the link in the box at the top of this page.' },
            { '@type': 'HowToStep', name: 'Choose a quality and download', text: 'Pick the quality you want and tap Download.' },
          ],
        },
      ];
      if (faqs.length) {
        graph.push({
          '@type': 'FAQPage',
          mainEntity: faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
        });
      }
      setLd('ld-page', { '@context': 'https://schema.org', '@graph': graph });
    } else if (pathname === '/') {
      setLd('ld-page', {
        '@context': 'https://schema.org',
        '@graph': [{
          '@type': 'FAQPage',
          mainEntity: HOME_FAQS.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
        }],
      });
    } else {
      setLd('ld-page', null);
    }
  }, [pathname]);

  return null;
}

export const HOME_FAQS = [
  { q: 'Which platforms does OVD support?', a: 'OVD works with public videos, reels, shorts and photos from YouTube, Instagram, TikTok, Facebook, X (Twitter), Pinterest, Reddit, Threads and many other websites.' },
  { q: 'Is OVD free? Do I need an account?', a: 'Yes, it is free and there is no sign-up. Paste a link, choose a quality and download.' },
  { q: 'Can I download Instagram carousels and multi-photo posts?', a: 'Yes. Every photo or video in a public carousel is listed separately, and you can download them all as one ZIP.' },
  { q: 'Can I save private or age-restricted videos?', a: 'No. OVD only works with public posts. Private, login-only or DRM-protected content cannot be downloaded.' },
  { q: 'Which video quality will I get?', a: 'OVD lists every quality the source offers, up to 1080p for YouTube, and marks which ones include sound.' },
  { q: 'Does it work on my phone?', a: 'Yes. Paste the link in any mobile browser. Saved files go to your Downloads folder or your Files app.' },
];
