import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import qrcode from 'qrcode-generator';
import { Copy, Check, ExternalLink, CirclePlay, QrCode, Code2, Share2, Download } from 'lucide-react';
import { buildSubscribeLink, subscribeButtonHtml } from '../utils/youtubeSubscribe.js';

const PAGE_URL = 'https://ovd.winplaybox.in/youtube-subscribe-link-generator';

const FAQS = [
  ['What is a YouTube subscribe link?',
    'It is your normal channel link with ?sub_confirmation=1 added at the end. When someone opens it, YouTube immediately shows its own "Subscribe to this channel?" popup, so they can subscribe with a single tap instead of searching for the button.'],
  ['Does the link subscribe people automatically?',
    'No. YouTube always asks the viewer to confirm. The link only opens the subscribe popup automatically, which removes friction and usually increases subscriber conversion. Forcing or faking subscriptions is against YouTube policy, and this tool never does that.'],
  ['Is this subscribe link generator free and safe?',
    'Yes. It is 100% free, needs no login, and runs entirely in your browser. We never ask for your YouTube password and nothing is sent to our servers.'],
  ['Which channel links are supported?',
    'All formats: @handle links (youtube.com/@name), channel ID links (youtube.com/channel/UC...), and older /c/ and /user/ custom URLs. You can also paste just your @handle or channel ID.'],
  ['Where should I share my YouTube subscribe link?',
    'In your video descriptions, pinned comments, Instagram and TikTok bio, WhatsApp status and groups, Telegram channels, email signature, website buttons, and on printed QR codes for shops, events and visiting cards.'],
  ['Does it work on mobile and in the YouTube app?',
    'Yes. On Android and iPhone the link opens the YouTube app (or browser) and shows the subscribe confirmation. Viewers who are not logged in are asked to sign in first.'],
  ['YouTube subscribe link kaise banaye? (Hindi)',
    'Apne channel ka link ya @handle upar box mein paste karein. OVD turant subscribe link bana dega jiske end mein ?sub_confirmation=1 hota hai. Is link ko description, WhatsApp ya Instagram bio mein share karein - kholte hi viewer ko Subscribe ka popup dikhega.'],
  ['Can I get a QR code for my subscribe link?',
    'Yes. A QR code is generated instantly below your link. Download it as a PNG and print it on posters, product packaging, visiting cards or your shop counter.'],
];

function setMeta() {
  const title = 'YouTube Subscribe Link Generator (Auto Subscribe Popup) - Free | OVD';
  const desc = 'Create a YouTube auto-subscribe link that opens the Subscribe popup instantly. Free sub_confirmation link, QR code and HTML button for any channel - no login.';
  document.title = title;
  const set = (sel, attr, val) => {
    let el = document.querySelector(sel);
    if (!el) {
      el = document.createElement(sel.startsWith('link') ? 'link' : 'meta');
      const m = sel.match(/\[(\w+)="([^"]+)"\]/);
      if (m) el.setAttribute(m[1], m[2]);
      document.head.appendChild(el);
    }
    el.setAttribute(attr, val);
  };
  set('meta[name="description"]', 'content', desc);
  set('meta[property="og:title"]', 'content', title);
  set('meta[property="og:description"]', 'content', desc);
  set('meta[property="og:url"]', 'content', PAGE_URL);
  set('link[rel="canonical"]', 'href', PAGE_URL);
}

const JSON_LD = JSON.stringify([
  {
    '@context': 'https://schema.org', '@type': 'WebApplication', name: 'YouTube Subscribe Link Generator',
    url: PAGE_URL, applicationCategory: 'UtilitiesApplication', operatingSystem: 'Any',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    publisher: { '@type': 'Organization', name: 'WinPlayBox', url: 'https://winplaybox.in' },
  },
  {
    '@context': 'https://schema.org', '@type': 'HowTo', name: 'How to create a YouTube subscribe link',
    step: [
      { '@type': 'HowToStep', name: 'Copy your channel link', text: 'Open YouTube, go to your channel and copy its link or @handle.' },
      { '@type': 'HowToStep', name: 'Paste it into OVD', text: 'Paste the link into the YouTube Subscribe Link Generator.' },
      { '@type': 'HowToStep', name: 'Share the subscribe link', text: 'Copy the generated link, QR code or HTML button and share it anywhere.' },
    ],
  },
  {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: FAQS.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })),
  },
  {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'OVD', item: 'https://ovd.winplaybox.in/' },
      { '@type': 'ListItem', position: 2, name: 'YouTube Subscribe Link Generator', item: PAGE_URL },
    ],
  },
]);

function CopyButton({ text, label }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1800); } catch { /* ignore */ }
      }}
      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] text-sm font-semibold hover:opacity-90"
    >
      {done ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      {done ? 'Copied' : label}
    </button>
  );
}

export default function YouTubeSubscribeLinkPage() {
  const [input, setInput] = useState('');
  const result = useMemo(() => (input.trim() ? buildSubscribeLink(input) : null), [input]);

  useEffect(() => {
    setMeta();
    const s = document.createElement('script');
    s.type = 'application/ld+json';
    s.id = 'ld-yt-subscribe';
    s.text = JSON_LD;
    document.head.appendChild(s);
    return () => { document.getElementById('ld-yt-subscribe')?.remove(); };
  }, []);

  const qrDataUrl = useMemo(() => {
    if (!result?.ok) return null;
    const q = qrcode(0, 'M');
    q.addData(result.subscribeUrl);
    q.make();
    return q.createDataURL(8, 16);
  }, [result]);

  const share = result?.ok ? encodeURIComponent(`Subscribe to my YouTube channel 👉 ${result.subscribeUrl}`) : '';

  return (
    <div className="w-full">
      <section className="max-w-3xl mx-auto px-4 pt-10 pb-6 text-center">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
          <CirclePlay className="w-3.5 h-3.5" /> Free YouTube growth tool
        </span>
        <h1 className="mt-4 text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text)]">
          YouTube Subscribe Link Generator
        </h1>
        <p className="mt-3 text-[var(--text-muted)] text-base sm:text-lg">
          Turn your channel link into an <strong>auto-subscribe link</strong> that opens YouTube&apos;s Subscribe popup instantly.
          Get the link, a printable QR code and a website button - free, no login.
        </p>
      </section>

      <section className="max-w-3xl mx-auto px-4" aria-label="Generator">
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface,var(--bg))] p-4 sm:p-6 shadow-sm">
          <label htmlFor="yt-channel" className="block text-sm font-semibold text-[var(--text)] mb-2">
            Your YouTube channel link, @handle or channel ID
          </label>
          <input
            id="yt-channel"
            type="text"
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, 300))}
            placeholder="youtube.com/@YourChannel"
            className="w-full px-4 py-3 rounded-xl border border-[var(--border)] bg-[var(--bg)] text-[var(--text)] text-base focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
          />
          <p className="mt-2 text-xs text-[var(--text-muted)]">Examples: youtube.com/@MrBeast · @dhrusavlogs · UC…  (channel links only, not video links)</p>

          {result && !result.ok && (
            <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{result.error}</p>
          )}

          {result?.ok && (
            <div className="mt-6 space-y-6" aria-live="polite">
              <div>
                <p className="text-sm font-semibold text-[var(--text)] mb-2">Your subscribe link</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <code className="flex-1 break-all px-3 py-2.5 rounded-lg bg-[var(--bg-alt)] border border-[var(--border)] text-sm text-[var(--text)]">
                    {result.subscribeUrl}
                  </code>
                  <div className="flex gap-2">
                    <CopyButton text={result.subscribeUrl} label="Copy link" />
                    <a href={result.subscribeUrl} target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-[var(--border)] text-sm font-semibold text-[var(--text)] hover:bg-[var(--bg-alt)]">
                      <ExternalLink className="w-4 h-4" /> Test
                    </a>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-[var(--text)] mb-2 flex items-center gap-1.5"><Share2 className="w-4 h-4" /> Share in one tap</p>
                <div className="flex flex-wrap gap-2 text-sm">
                  <a className="px-3 py-2 rounded-lg bg-[#25D366] text-white font-semibold" target="_blank" rel="noopener noreferrer" href={`https://wa.me/?text=${share}`}>WhatsApp</a>
                  <a className="px-3 py-2 rounded-lg bg-black text-white font-semibold" target="_blank" rel="noopener noreferrer" href={`https://twitter.com/intent/tweet?text=${share}`}>X (Twitter)</a>
                  <a className="px-3 py-2 rounded-lg bg-[#229ED9] text-white font-semibold" target="_blank" rel="noopener noreferrer" href={`https://t.me/share/url?url=${encodeURIComponent(result.subscribeUrl)}&text=${encodeURIComponent('Subscribe to my YouTube channel')}`}>Telegram</a>
                  <a className="px-3 py-2 rounded-lg bg-[#1877F2] text-white font-semibold" target="_blank" rel="noopener noreferrer" href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(result.subscribeUrl)}`}>Facebook</a>
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm font-semibold text-[var(--text)] mb-2 flex items-center gap-1.5"><QrCode className="w-4 h-4" /> QR code</p>
                  {qrDataUrl && (
                    <div className="inline-flex flex-col items-center gap-2 p-3 rounded-xl bg-white border border-[var(--border)]">
                      <img src={qrDataUrl} alt={`QR code to subscribe to ${result.id} on YouTube`} width="200" height="200" />
                      <a download={`youtube-subscribe-${result.id}.gif`} href={qrDataUrl}
                        className="inline-flex items-center gap-1.5 text-sm font-semibold text-black">
                        <Download className="w-4 h-4" /> Download QR
                      </a>
                    </div>
                  )}
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--text)] mb-2 flex items-center gap-1.5"><Code2 className="w-4 h-4" /> Website button</p>
                  <div className="p-3 rounded-xl border border-[var(--border)] bg-[var(--bg-alt)]">
                    <div dangerouslySetInnerHTML={{ __html: subscribeButtonHtml(result.subscribeUrl) }} />
                    <textarea readOnly rows={4} value={subscribeButtonHtml(result.subscribeUrl)}
                      className="mt-3 w-full text-xs font-mono p-2 rounded-lg border border-[var(--border)] bg-[var(--bg)] text-[var(--text)]" aria-label="HTML button code" />
                    <div className="mt-2"><CopyButton text={subscribeButtonHtml(result.subscribeUrl)} label="Copy HTML" /></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      <article className="max-w-3xl mx-auto px-4 py-12 space-y-10 text-[var(--text)]">
        <section>
          <h2 className="text-2xl font-bold">How to make a YouTube subscribe link</h2>
          <ol className="mt-4 space-y-2 list-decimal pl-5 text-[var(--text-muted)]">
            <li><strong className="text-[var(--text)]">Copy your channel link</strong> - open YouTube, tap your profile picture, choose <em>Your channel</em> and copy the link (or just your @handle).</li>
            <li><strong className="text-[var(--text)]">Paste it above</strong> - OVD instantly adds <code>?sub_confirmation=1</code> to create your subscribe link.</li>
            <li><strong className="text-[var(--text)]">Share it everywhere</strong> - copy the link, download the QR code or add the HTML button to your website.</li>
          </ol>
        </section>

        <section>
          <h2 className="text-2xl font-bold">Why a subscribe link gets you more subscribers</h2>
          <p className="mt-3 text-[var(--text-muted)]">
            Every extra step loses viewers. A normal channel link makes people find and press the Subscribe button themselves.
            A subscribe link opens YouTube&apos;s confirmation popup the moment the page loads, so the only thing left is one tap on
            <em> Subscribe</em>. Creators commonly use it in video end screens, pinned comments, link-in-bio pages and WhatsApp
            broadcasts to turn interested viewers into subscribers.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-bold">Best places to use your link</h2>
          <ul className="mt-3 grid sm:grid-cols-2 gap-2 text-[var(--text-muted)] list-disc pl-5">
            <li>First line of every video description</li>
            <li>Pinned comment on your top videos</li>
            <li>Instagram, TikTok and X bio (link-in-bio)</li>
            <li>WhatsApp status, groups and Telegram channels</li>
            <li>Email signature and newsletters</li>
            <li>Printed QR on shop counters, posters and visiting cards</li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-bold">Free tools for YouTube creators</h2>
          <ul className="mt-3 space-y-1.5">
            <li><Link className="text-[var(--accent)] hover:underline" to="/youtube-thumbnail-downloader">YouTube Thumbnail Downloader (HD &amp; 4K)</Link></li>
            <li><Link className="text-[var(--accent)] hover:underline" to="/ai-video-editor">AI Video Editor - voiceover, captions, title &amp; tags</Link></li>
            <li><Link className="text-[var(--accent)] hover:underline" to="/youtube-shorts-downloader">YouTube Shorts Downloader</Link></li>
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-bold">Frequently asked questions</h2>
          <div className="mt-4 divide-y divide-[var(--border)] border border-[var(--border)] rounded-xl">
            {FAQS.map(([q, a]) => (
              <details key={q} className="group p-4">
                <summary className="cursor-pointer font-semibold list-none flex justify-between gap-4">
                  <h3 className="text-base">{q}</h3>
                  <span className="text-[var(--text-muted)] group-open:rotate-45 transition-transform">+</span>
                </summary>
                <p className="mt-2 text-[var(--text-muted)]">{a}</p>
              </details>
            ))}
          </div>
        </section>
      </article>
    </div>
  );
}
