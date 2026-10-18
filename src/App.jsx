import React, { useState } from 'react';
import Header from './components/Header.jsx';
import HeroDownloader from './components/HeroDownloader.jsx';
import MediaResultCard from './components/MediaResultCard.jsx';
import TopChannelsSection from './components/TopChannelsSection.jsx';
import SupportedPlatforms from './components/SupportedPlatforms.jsx';
import HowItWorks from './components/HowItWorks.jsx';
import Faq from './components/Faq.jsx';
import Footer from './components/Footer.jsx';

export default function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaData, setMediaData] = useState(null);

  // Categories & Subfeatures State
  const [activeCategory, setActiveCategory] = useState('youtube');
  const [activeSubfeature, setActiveSubfeature] = useState('all');
  const [topChannelsFilter, setTopChannelsFilter] = useState(null);

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

  function handleSelectCategory(cat, subfeature = 'all') {
    setActiveCategory(cat);
    setActiveSubfeature(subfeature);
  }

  function handleSelectTopChannelsFilter(filter) {
    setTopChannelsFilter(filter);
  }

  function handleResetTopChannelsFilter() {
    setTopChannelsFilter(null);
  }

  async function fetchMedia() {
    if (!url.trim()) {
      setError('Please enter a valid video, shorts, or audio URL.');
      return;
    }

    setLoading(true);
    setError('');
    setMediaData(null);

    try {
      const res = await fetch('https://anydownloader-backend-vvbj.onrender.com/api/extract', {
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
      setError('Network connection error. Ensure the Python extraction engine is running.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-rose-500 selection:text-white">
      {/* Header with Multi-Categories & Mega-Menu */}
      <Header
        onSelectCategory={handleSelectCategory}
        onSelectTopChannelsFilter={handleSelectTopChannelsFilter}
      />

      <main className="flex-1">
        {/* Hero Downloader with dynamic YouTube suite */}
        <HeroDownloader
          url={url}
          setUrl={setUrl}
          onFetch={fetchMedia}
          loading={loading}
          error={error}
          onPaste={handlePaste}
          activeCategory={activeCategory}
          onSelectCategory={handleSelectCategory}
          activeSubfeature={activeSubfeature}
          onSelectSubfeature={setActiveSubfeature}
        />

        {/* Media Results: Video, Audio, Thumbnails, Transcript, Subtitles */}
        {mediaData && (
          <MediaResultCard data={mediaData} />
        )}

        {/* Top 100 YouTube Channels Section (Refreshed every 12 hours) */}
        <TopChannelsSection
          activeFilter={topChannelsFilter}
          onResetFilter={handleResetTopChannelsFilter}
        />

        {/* Other Sections */}
        <SupportedPlatforms />
        <HowItWorks />
        <Faq />
      </main>

      <Footer />
    </div>
  );
}
