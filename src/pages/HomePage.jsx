import React, { useState } from 'react';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import HowItWorks from '../components/HowItWorks.jsx';
import Faq from '../components/Faq.jsx';
import { resolveMedia } from '../utils/resolveMedia.js';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState(null);
  const [mediaData, setMediaData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');

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
        {/* Hero Downloader Box */}
        <HeroDownloader
          url={url}
          setUrl={(newUrl) => { setUrl(newUrl); if (error) setError(''); }}
          onFetch={(target) => fetchMedia(target)}
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

        {/* How It Works & FAQ */}
        <HowItWorks />
        <Faq />
      </div>
    </div>
  );
}
