import React, { useState } from 'react';
import Header from './components/Header.jsx';
import HeroDownloader from './components/HeroDownloader.jsx';
import MediaResultCard from './components/MediaResultCard.jsx';
import SupportedPlatforms from './components/SupportedPlatforms.jsx';
import HowItWorks from './components/HowItWorks.jsx';
import Faq from './components/Faq.jsx';
import Footer from './components/Footer.jsx';

export default function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaData, setMediaData] = useState(null);

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
      }
    } catch (e) {
      setError('Please allow clipboard permission to paste directly.');
    }
  }

  async function fetchMedia() {
    if (!url.trim()) {
      setError('Please enter a valid video or audio URL.');
      return;
    }

    setLoading(true);
    setError('');
    setMediaData(null);

    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() })
      });

      const json = await res.json();
      if (json.success && json.data) {
        setMediaData(json.data);
      } else {
        setError(json.error || 'Could not extract media. Please check the URL and try again.');
      }
    } catch (e) {
      setError('Network connection error. Ensure the Python engine is running.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Header />

      <main className="flex-1">
        <HeroDownloader
          url={url}
          setUrl={setUrl}
          onFetch={fetchMedia}
          loading={loading}
          error={error}
          onPaste={handlePaste}
        />

        {mediaData && (
          <MediaResultCard data={mediaData} />
        )}

        <SupportedPlatforms />
        <HowItWorks />
        <Faq />
      </main>

      <Footer />
    </div>
  );
}
