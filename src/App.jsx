import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import ToolPage from './pages/ToolPage.jsx';
import TopChannelsPage from './pages/TopChannelsPage.jsx';
import TopFacebookPagesPage from './pages/TopFacebookPagesPage.jsx';
import BlogsPage from './pages/BlogsPage.jsx';
import UpdatesPage from './pages/UpdatesPage.jsx';
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

            {/* YouTube Category Nested Routes */}
            <Route path="/youtube" element={<Navigate to="/youtube/youtube-video-downloader" replace />} />
            <Route path="/youtube/youtube-video-downloader" element={<ToolPage config={pagesConfig['youtube/youtube-video-downloader']} />} />
            <Route path="/youtube/youtube-mp4" element={<ToolPage config={pagesConfig['youtube/youtube-mp4']} />} />
            <Route path="/youtube/youtube-shorts" element={<ToolPage config={pagesConfig['youtube/youtube-shorts']} />} />
            <Route path="/youtube/youtube-mp3" element={<ToolPage config={pagesConfig['youtube/youtube-mp3']} />} />
            <Route path="/youtube/youtube-transcript" element={<ToolPage config={pagesConfig['youtube/youtube-transcript']} />} />
            <Route path="/youtube/youtube-subtitles" element={<ToolPage config={pagesConfig['youtube/youtube-subtitles']} />} />
            <Route path="/youtube/youtube-thumbnails" element={<ToolPage config={pagesConfig['youtube/youtube-thumbnails']} />} />
            <Route path="/youtube/youtube-thumbnail" element={<Navigate to="/youtube/youtube-thumbnails" replace />} />

            {/* Top 100 YouTube Channels Dedicated Database Page */}
            <Route path="/youtube/top-100-youtube-channels" element={<TopChannelsPage />} />
            <Route path="/youtube/top-100-channels" element={<Navigate to="/youtube/top-100-youtube-channels" replace />} />

            {/* Facebook Category Nested Routes */}
            <Route path="/facebook" element={<Navigate to="/facebook/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-video-downloader" element={<ToolPage config={pagesConfig['facebook/facebook-video-downloader']} />} />
            <Route path="/facebook/facebook-reels" element={<ToolPage config={pagesConfig['facebook/facebook-reels']} />} />
            <Route path="/facebook/facebook-posts" element={<ToolPage config={pagesConfig['facebook/facebook-posts']} />} />
            <Route path="/facebook/facebook-watch" element={<ToolPage config={pagesConfig['facebook/facebook-watch']} />} />
            <Route path="/facebook/facebook-stories" element={<ToolPage config={pagesConfig['facebook/facebook-stories']} />} />
            <Route path="/facebook/facebook-mp3" element={<ToolPage config={pagesConfig['facebook/facebook-mp3']} />} />
            <Route path="/facebook/facebook-transcript" element={<ToolPage config={pagesConfig['facebook/facebook-transcript']} />} />
            <Route path="/facebook/facebook-thumbnails" element={<ToolPage config={pagesConfig['facebook/facebook-thumbnails']} />} />

            {/* Top 100 Facebook Pages Dedicated Database Page */}
            <Route path="/facebook/top-100-facebook-pages" element={<TopFacebookPagesPage />} />
            <Route path="/facebook/top-100-pages" element={<Navigate to="/facebook/top-100-facebook-pages" replace />} />

            {/* Instagram Category Nested Routes */}
            <Route path="/instagram" element={<Navigate to="/instagram/instagram-downloader" replace />} />
            <Route path="/instagram/instagram-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-downloader']} />} />

            {/* TikTok Category Nested Routes */}
            <Route path="/tiktok" element={<Navigate to="/tiktok/tiktok-downloader" replace />} />
            <Route path="/tiktok/tiktok-downloader" element={<ToolPage config={pagesConfig['tiktok/tiktok-downloader']} />} />

            {/* Real-Time Social Media Updates Blog */}
            <Route path="/blogs" element={<BlogsPage />} />
            <Route path="/blog" element={<Navigate to="/blogs" replace />} />

            {/* Official Product Releases & Changelog */}
            <Route path="/updates" element={<UpdatesPage />} />
            <Route path="/changelog" element={<Navigate to="/updates" replace />} />

            {/* Legacy URL Aliases (Instant 301-style client redirects) */}
            <Route path="/youtube-video-downloader" element={<Navigate to="/youtube/youtube-video-downloader" replace />} />
            <Route path="/youtube-mp4" element={<Navigate to="/youtube/youtube-mp4" replace />} />
            <Route path="/youtube-shorts" element={<Navigate to="/youtube/youtube-shorts" replace />} />
            <Route path="/youtube-mp3" element={<Navigate to="/youtube/youtube-mp3" replace />} />
            <Route path="/youtube-transcript" element={<Navigate to="/youtube/youtube-transcript" replace />} />
            <Route path="/youtube-subtitles" element={<Navigate to="/youtube/youtube-subtitles" replace />} />
            <Route path="/youtube-thumbnail" element={<Navigate to="/youtube/youtube-thumbnails" replace />} />
            <Route path="/top-100-youtube-channels" element={<Navigate to="/youtube/top-100-youtube-channels" replace />} />
            <Route path="/facebook-video-downloader" element={<Navigate to="/facebook/facebook-video-downloader" replace />} />
            <Route path="/facebook-reels" element={<Navigate to="/facebook/facebook-reels" replace />} />
            <Route path="/facebook-posts" element={<Navigate to="/facebook/facebook-posts" replace />} />
            <Route path="/facebook-transcript" element={<Navigate to="/facebook/facebook-transcript" replace />} />
            <Route path="/top-100-facebook-pages" element={<Navigate to="/facebook/top-100-facebook-pages" replace />} />
            <Route path="/instagram-downloader" element={<Navigate to="/instagram/instagram-downloader" replace />} />
            <Route path="/tiktok-downloader" element={<Navigate to="/tiktok/tiktok-downloader" replace />} />

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
