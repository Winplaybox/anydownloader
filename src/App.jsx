import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import ToolPage from './pages/ToolPage.jsx';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage.jsx';
import TermsPage from './pages/TermsPage.jsx';
import ContactPage from './pages/ContactPage.jsx';
import SecurityPage from './pages/SecurityPage.jsx';
import { pagesConfig } from './data/pagesConfig.js';

// Auto scroll to top on navigation
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

// Strict Phase 1 SEO Head Updater
function SEOHead() {
  const { pathname } = useLocation();

  useEffect(() => {
    const cleanPath = pathname.replace(/^\/+|\/+$/g, '');
    let title = 'OVD - Fast Social Video & Image Downloader (X, YouTube, Facebook, Instagram, TikTok)';
    let desc = 'Download public videos and photos from Twitter/X, YouTube, Facebook, Instagram, and TikTok in high quality. Fast, free, no login or software required.';

    if (cleanPath.includes('twitter') || cleanPath.includes('x-')) {
      title = 'Twitter/X Video & Photo Downloader - OVD';
      desc = 'Download Twitter/X video clips, GIFs, and high-resolution photos in original quality for free.';
    } else if (cleanPath.includes('youtube')) {
      title = 'YouTube Video & Thumbnail Downloader - OVD';
      desc = 'Download YouTube videos in MP4 format and save high-resolution video thumbnails instantly.';
    } else if (cleanPath.includes('facebook')) {
      title = 'Facebook Video & Reels Downloader - OVD';
      desc = 'Download Facebook videos and public reels in HD MP4 format for offline viewing.';
    } else if (cleanPath.includes('instagram')) {
      title = 'Instagram Reels & Carousel Downloader - OVD';
      desc = 'Download Instagram reels, video posts, and full multi-photo carousel albums in original resolution.';
    } else if (cleanPath.includes('tiktok')) {
      title = 'TikTok Video Downloader Without Watermark - OVD';
      desc = 'Download high quality TikTok videos without watermark and save photo slideshows quickly.';
    }

    document.title = title;
    const descMeta = document.querySelector('meta[name="description"]');
    if (descMeta) descMeta.setAttribute('content', desc);
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute('content', title);
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) ogDesc.setAttribute('content', desc);
  }, [pathname]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <SEOHead />
      <div className="min-h-screen flex flex-col bg-[var(--bg)] text-[var(--text)] transition-colors duration-150">
        <Header />
        <main className="flex-1">
          <Routes>
            {/* Home / Universal Auto-Detect */}
            <Route path="/" element={<HomePage />} />

            {/* Direct Landing Routes as per Section 4.3 */}
            <Route path="/twitter-video-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-video-downloader']} />} />
            <Route path="/twitter-image-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-image-downloader']} />} />
            <Route path="/youtube-video-downloader" element={<ToolPage config={pagesConfig['youtube/youtube-video-downloader']} />} />
            <Route path="/youtube-thumbnail-downloader" element={<ToolPage config={pagesConfig['youtube/youtube-thumbnails']} />} />
            <Route path="/facebook-video-downloader" element={<ToolPage config={pagesConfig['facebook/facebook-video-downloader']} />} />
            <Route path="/facebook-photo-downloader" element={<ToolPage config={pagesConfig['facebook/facebook-posts']} />} />
            <Route path="/instagram-video-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-video-downloader']} />} />
            <Route path="/instagram-photo-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-photo-downloader']} />} />
            <Route path="/tiktok-video-downloader" element={<ToolPage config={pagesConfig['tiktok/tiktok-downloader']} />} />
            <Route path="/tiktok-photo-downloader" element={<ToolPage config={pagesConfig['tiktok/tiktok-downloader']} />} />

            {/* Legacy aliases and nested paths */}
            <Route path="/twitter" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/x" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/twitter/twitter-video-downloader" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/twitter/twitter-image-downloader" element={<Navigate to="/twitter-image-downloader" replace />} />
            <Route path="/twitter/twitter-downloader" element={<Navigate to="/twitter-video-downloader" replace />} />
            
            <Route path="/youtube" element={<Navigate to="/youtube-video-downloader" replace />} />
            <Route path="/youtube/youtube-video-downloader" element={<Navigate to="/youtube-video-downloader" replace />} />
            <Route path="/youtube/youtube-thumbnails" element={<Navigate to="/youtube-thumbnail-downloader" replace />} />

            <Route path="/facebook" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-video-downloader" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-reels" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-posts" element={<Navigate to="/facebook-photo-downloader" replace />} />

            <Route path="/instagram" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-video-downloader" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-photo-downloader" element={<Navigate to="/instagram-photo-downloader" replace />} />
            <Route path="/instagram/instagram-reels-downloader" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-reels" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-carousel-downloader" element={<Navigate to="/instagram-photo-downloader" replace />} />

            <Route path="/tiktok" element={<Navigate to="/tiktok-video-downloader" replace />} />
            <Route path="/tiktok/tiktok-downloader" element={<Navigate to="/tiktok-video-downloader" replace />} />

            {/* Legal & Static Routes */}
            <Route path="/privacy" element={<PrivacyPolicyPage />} />
            <Route path="/privacy-policy" element={<Navigate to="/privacy" replace />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/terms-of-service" element={<Navigate to="/terms" replace />} />
            <Route path="/dmca" element={<SecurityPage />} />
            <Route path="/security" element={<Navigate to="/dmca" replace />} />
            <Route path="/contact" element={<ContactPage />} />

            {/* Fallback 404 / Catch-all */}
            <Route path="*" element={<HomePage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
