import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import ToolPage from './pages/ToolPage.jsx';
import TopChannelsPage from './pages/TopChannelsPage.jsx';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage.jsx';
import TermsPage from './pages/TermsPage.jsx';
import ContactPage from './pages/ContactPage.jsx';
import { pagesConfig } from './data/pagesConfig.js';

// Auto scroll to top on navigation
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-rose-500 selection:text-white">
        <Header />

        <main className="flex-1">
          <Routes>
            {/* Home */}
            <Route path="/" element={<HomePage />} />

            {/* YouTube Suite Pages */}
            <Route path="/youtube-video-downloader" element={<ToolPage config={pagesConfig['youtube-video-downloader']} />} />
            <Route path="/youtube-mp4" element={<ToolPage config={pagesConfig['youtube-mp4']} />} />
            <Route path="/youtube-shorts" element={<ToolPage config={pagesConfig['youtube-shorts']} />} />
            <Route path="/youtube-mp3" element={<ToolPage config={pagesConfig['youtube-mp3']} />} />
            <Route path="/youtube-transcript" element={<ToolPage config={pagesConfig['youtube-transcript']} />} />
            <Route path="/youtube-subtitles" element={<ToolPage config={pagesConfig['youtube-subtitles']} />} />
            <Route path="/youtube-thumbnail" element={<ToolPage config={pagesConfig['youtube-thumbnail']} />} />

            {/* Top 100 YouTube Channels Dedicated Database Page */}
            <Route path="/top-100-youtube-channels" element={<TopChannelsPage />} />

            {/* Other Supported Platform Pages */}
            <Route path="/facebook-video-downloader" element={<ToolPage config={pagesConfig['facebook-video-downloader']} />} />
            <Route path="/instagram-downloader" element={<ToolPage config={pagesConfig['instagram-downloader']} />} />
            <Route path="/tiktok-downloader" element={<ToolPage config={pagesConfig['tiktok-downloader']} />} />

            {/* Mandatory Google AdSense Legal & Policy Pages */}
            <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
            <Route path="/terms-of-service" element={<TermsPage />} />
            <Route path="/contact" element={<ContactPage />} />

            {/* Fallback */}
            <Route path="*" element={<HomePage />} />
          </Routes>
        </main>

        <Footer />
      </div>
    </BrowserRouter>
  );
}
