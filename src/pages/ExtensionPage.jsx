import React, { useState, useEffect } from 'react';
import { Download, ShieldCheck, Zap, CheckCircle2, ArrowRight, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ChromeIcon, GlobeIcon } from '../components/BrandIcons.jsx';

function detectBrowser() {
  if (typeof window === 'undefined') return { name: 'Chrome', isChromium: true };
  const ua = navigator.userAgent;
  if (ua.includes('Edg/')) return { name: 'Edge', isChromium: true };
  if (ua.includes('Firefox/')) return { name: 'Firefox', isChromium: false };
  if (ua.includes('OPR/') || ua.includes('Opera/')) return { name: 'Opera', isChromium: true };
  if (ua.includes('Brave')) return { name: 'Brave', isChromium: true };
  if (ua.includes('Safari/') && !ua.includes('Chrome/')) return { name: 'Safari', isChromium: false };
  return { name: 'Chrome', isChromium: true };
}

export default function ExtensionPage() {
  const [browser, setBrowser] = useState({ name: 'Chrome', isChromium: true });
  const [installedNotice, setInstalledNotice] = useState(false);

  useEffect(() => {
    setBrowser(detectBrowser());
  }, []);

  // Web Store URL placeholder or published link
  const storeUrl = "https://chromewebstore.google.com/";

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] text-xs font-semibold text-[var(--text-muted)] mb-4">
          <ChromeIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>Official Browser Extension (Manifest V3)</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight">
          OVD Downloader for {browser.name}
        </h1>
        <p className="mt-3 text-sm sm:text-base text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">
          Download 1080p/4K YouTube videos, Instagram Reels, Facebook videos, and Twitter media in 1-click directly inside your browser.
        </p>

        {/* Dynamic Action Buttons */}
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <a
            href={storeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto px-6 py-3 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 font-semibold text-sm flex items-center justify-center gap-2 shadow-xs transition-opacity cursor-pointer"
          >
            <ChromeIcon className="w-4 h-4" />
            <span>Add to {browser.name}</span>
            <ExternalLink className="w-3.5 h-3.5 opacity-60" />
          </a>

          <a
            href="/ovd-extension.zip"
            download="ovd-extension.zip"
            className="w-full sm:w-auto px-5 py-3 rounded-lg bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--bg-alt)] font-semibold text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4 text-[var(--text-muted)]" />
            <span>Download ZIP (Developer Mode)</span>
          </a>
        </div>
      </div>

      {/* Benefits Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
        <div className="p-5 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <Zap className="w-5 h-5 text-[var(--accent)] mb-2" />
          <h3 className="font-bold text-[var(--text)] text-sm mb-1">1-Click Quick Download</h3>
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            Detects active tab media automatically. No need to copy and paste links manually.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <ShieldCheck className="w-5 h-5 text-[var(--positive)] mb-2" />
          <h3 className="font-bold text-[var(--text)] text-sm mb-1">Private Content Support</h3>
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            Download follower-only Instagram posts or private Facebook videos safely from your active browser session.
          </p>
        </div>

        <div className="p-5 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
          <CheckCircle2 className="w-5 h-5 text-[var(--text)] mb-2" />
          <h3 className="font-bold text-[var(--text)] text-sm mb-1">Zero Telemetry & 100% Free</h3>
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            We never collect your passwords, cookies, or history. Everything processes locally on your machine.
          </p>
        </div>
      </div>

      {/* Manual Install Guide */}
      <div className="p-6 md:p-8 rounded-2xl bg-[var(--surface)] border border-[var(--border)] mb-12">
        <h2 className="text-lg sm:text-xl font-bold text-[var(--text)] mb-6">
          How to Install in {browser.name} (Developer Mode)
        </h2>

        <ol className="space-y-4 text-xs sm:text-sm text-[var(--text)]">
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">1</span>
            <div>
              <strong>Download and Unzip:</strong> Click <strong>Download ZIP</strong> above and extract the files to a local folder.
            </div>
          </li>
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">2</span>
            <div>
              <strong>Open Extensions Page:</strong> In your browser, navigate to <code className="text-xs font-mono bg-[var(--bg-alt)] px-1.5 py-0.5 rounded">chrome://extensions/</code> (or <code className="text-xs font-mono bg-[var(--bg-alt)] px-1.5 py-0.5 rounded">edge://extensions/</code>).
            </div>
          </li>
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">3</span>
            <div>
              <strong>Enable Developer Mode:</strong> Toggle the <strong>Developer mode</strong> switch in the top-right corner.
            </div>
          </li>
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">4</span>
            <div>
              <strong>Load Unpacked:</strong> Click <strong>Load unpacked</strong> and select the extracted extension folder.
            </div>
          </li>
        </ol>

        <div className="mt-6 pt-6 border-t border-[var(--border)] text-xs text-[var(--text-muted)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <span>Ready to publish to the Chrome Web Store?</span>
          <span className="font-semibold text-[var(--text)]">ZIP is pre-packaged with root manifest.json</span>
        </div>
      </div>
    </div>
  );
}
