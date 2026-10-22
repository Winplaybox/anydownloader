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

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState(null);
  const [mediaData, setMediaData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');

  async function fetchMedia(overrideUrl = null) {
    const rawTarget = typeof overrideUrl === 'string' && overrideUrl.trim() ? overrideUrl.trim() : (typeof url === 'string' ? url.trim() : '');
    
    // 1. Client-Side Normalization & Instant Validation (zero unnecessary API calls)
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
        {/* Hero Downloader Box */}
        <HeroDownloader
          url={url}
          setUrl={setUrl}
          onFetch={() => fetchMedia()}
          loading={loading}
          error={error}
          errorCode={errorCode}
          onClear={handleReset}
          activeCategory={activeCategory}
          setActiveCategory={setActiveCategory}
        />

        {/* Media Result Card (when media successfully resolved) */}
        {mediaData && (
          <MediaResultCard 
            data={mediaData} 
            onReset={handleReset} 
          />
        )}

        {/* Steps / How It Works */}
        <HowItWorks />

        {/* FAQ Accordion */}
        <Faq />
      </div>
    </div>
  );
}
