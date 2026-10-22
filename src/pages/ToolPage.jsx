import React, { useState } from 'react';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import HowItWorks from '../components/HowItWorks.jsx';
import Faq from '../components/Faq.jsx';
import { normalizeUrl } from '../utils/normalizeUrl.js';
import { getErrorMessage, ErrorCode } from '../utils/errors.js';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

export default function ToolPage({ config = {} }) {
  const safeConfig = config || {};
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState(null);
  const [mediaData, setMediaData] = useState(null);

  async function fetchMedia(overrideUrl = null) {
    const rawTarget = typeof overrideUrl === 'string' && overrideUrl.trim() ? overrideUrl.trim() : (typeof url === 'string' ? url.trim() : '');
    
    // Client-side validation
    const norm = normalizeUrl(rawTarget);
    if (!norm.ok) {
      setErrorCode(norm.code);
      setError(getErrorMessage(norm.code, norm.error));
      setMediaData(null);
      return;
    }

    setLoading(true);
    setError('');
    setErrorCode(null);
    setMediaData(null);

    try {
      const response = await fetch(`${BACKEND_BASE}/api/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Origin': window.location.origin
        },
        body: JSON.stringify({ url: norm.url })
      });

      const json = await response.json();

      if (json.ok && json.data) {
        setMediaData(json.data);
      } else {
        const code = json.error?.code || ErrorCode.UPSTREAM_FAILED;
        setErrorCode(code);
        setError(getErrorMessage(code, json.error?.message));
      }
    } catch (e) {
      setErrorCode(ErrorCode.TIMEOUT);
      setError(getErrorMessage(ErrorCode.TIMEOUT));
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setUrl('');
    setError('');
    setErrorCode(null);
    setMediaData(null);
  }

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        <HeroDownloader
          url={url}
          setUrl={setUrl}
          onFetch={() => fetchMedia()}
          loading={loading}
          error={error}
          errorCode={errorCode}
          onClear={handleReset}
          activeCategory={safeConfig.category || 'all'}
          setActiveCategory={() => {}}
          pageH1={safeConfig.title}
          pageDesc={safeConfig.guideIntro}
        />

        {mediaData && (
          <MediaResultCard 
            data={mediaData} 
            onReset={handleReset} 
          />
        )}

        {/* Feature / Editorial Content */}
        {safeConfig.sections && safeConfig.sections.length > 0 && (
          <section className="w-full max-w-4xl mx-auto px-4 py-12 border-t border-[var(--border)]">
            <h2 className="base-heading text-xl sm:text-2xl font-extrabold text-[var(--text)] mb-6">
              About {safeConfig.title || 'This Downloader'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {safeConfig.sections.map((sec, idx) => (
                <div key={idx} className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-[var(--shadow-1)]">
                  <h3 className="font-bold text-base text-[var(--text)] mb-2">
                    {sec.heading}
                  </h3>
                  <p className="text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed">
                    {sec.body}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        <HowItWorks />
        <Faq />
      </div>
    </div>
  );
}
