import React, { useState, useEffect } from 'react';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import HowItWorks from '../components/HowItWorks.jsx';
import Faq from '../components/Faq.jsx';
import { resolveMedia } from '../utils/resolveMedia.js';

export default function ToolPage({ config = {} }) {
  const safeConfig = config || {};
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState(null);
  const [mediaData, setMediaData] = useState(null);

  // Auto-ingest search / url parameters from query string (?url=, ?link=, ?q=, ?search=)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const incoming = params.get('url') || params.get('link') || params.get('q') || params.get('search') || params.get('query');
      if (incoming && incoming.trim()) {
        const target = incoming.trim();
        setUrl(target);
        fetchMedia(target);
      }
    }
  }, []);

  async function fetchMedia(overrideUrl = null) {
    const rawTarget = typeof overrideUrl === 'string' && overrideUrl.trim() 
      ? overrideUrl.trim() 
      : (typeof url === 'string' ? url.trim() : '');

    if (!rawTarget) {
      setError('Paste a link to get started.');
      return;
    }

    setLoading(true);
    setError('');
    setErrorCode(null);
    setMediaData(null);

    try {
      const result = await resolveMedia(rawTarget);
      if (result.ok && result.data) {
        setMediaData(result.data);
      } else {
        setErrorCode(result.code);
        setError(result.error);
      }
    } catch (e) {
      setError('Connection interrupted. Please try again.');
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
        {/* Hero Downloader with Page Config Title & Description */}
        <HeroDownloader
          url={url}
          setUrl={(newUrl) => { setUrl(newUrl); if (error) setError(''); }}
          onFetch={(target) => fetchMedia(target)}
          loading={loading}
          error={error}
          errorCode={errorCode}
          onClear={handleReset}
          pageH1={safeConfig.h1}
          pageDesc={safeConfig.description}
        />

        {/* Media Result Card */}
        {mediaData && (
          <MediaResultCard 
            data={mediaData} 
            onReset={handleReset} 
          />
        )}

        {/* Platform How It Works & FAQ */}
        <HowItWorks customSteps={safeConfig.steps} />
        <Faq customFaqs={safeConfig.faqs} />
      </div>
    </div>
  );
}
