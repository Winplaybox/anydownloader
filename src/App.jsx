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
import BlogsPage from './pages/BlogsPage.jsx';
import UpdatesPage from './pages/UpdatesPage.jsx';
import { pagesConfig } from './data/pagesConfig.js';
import { initAttribution } from './utils/attribution.js';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

function SEOHead() {
  const { pathname } = useLocation();
  useEffect(() => {
    const cleanPath = pathname.replace(/^\/+|\/+$/g, '');
    let title = 'OVD - Fast Social Video & Image Downloader (Twitter, YouTube, Facebook, Instagram, TikTok, Pinterest, Reddit)';
    let desc = 'Download public videos and images from Twitter/X, YouTube, Facebook, Instagram, TikTok, Pinterest, Reddit and any website. 100% free with no sign-up.';

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
    } else if (cleanPath.includes('pinterest')) {
      title = 'Pinterest Video & Image Downloader - OVD';
      desc = 'Download full resolution Pinterest videos, uncompressed original images, and GIFs for free.';
    } else if (cleanPath.includes('reddit')) {
      title = 'Reddit Video & Media Downloader - OVD';
      desc = 'Download Reddit videos with clean synchronized audio and save full-resolution photo posts.';
    } else if (cleanPath.includes('any-website') || cleanPath.includes('website')) {
      title = 'Any Website Video & Image Downloader - OVD';
      desc = 'Download videos, direct streams, and high-resolution photos from any public webpage across the web.';
    } else if (cleanPath.includes('blog')) {
      title = 'Blog - Tips & Guides for Downloading Videos - OVD';
      desc = 'Read the latest guides, tips, and how-tos on downloading videos and images from social media.';
    } else if (cleanPath.includes('updates')) {
      title = 'Updates & Changelog - OVD Downloader';
      desc = 'See the latest feature updates, bug fixes, and improvements to OVD Downloader.';
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
  // Initialize traffic origin & referrer attribution tracking
  useEffect(() => {
    initAttribution();
  }, []);

  return (
    <BrowserRouter>
      <ScrollToTop />
      <SEOHead />
      <div className="min-h-screen flex flex-col bg-[var(--bg)] text-[var(--text)] transition-colors duration-150">
        <Header />
        <main className="flex-1">
          <Routes>
            {/* Home */}
            <Route path="/" element={<HomePage />} />

            {/* Blog & Updates */}
            <Route path="/blog" element={<BlogsPage />} />
            <Route path="/updates" element={<UpdatesPage />} />
            <Route path="/changelog" element={<Navigate to="/updates" replace />} />

            {/* Twitter/X */}
            <Route path="/twitter-video-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-video-downloader']} />} />
            <Route path="/twitter-image-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-image-downloader']} />} />
            <Route path="/twitter" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/x" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/twitter/twitter-video-downloader" element={<Navigate to="/twitter-video-downloader" replace />} />
            <Route path="/twitter/twitter-image-downloader" element={<Navigate to="/twitter-image-downloader" replace />} />
            <Route path="/twitter/twitter-downloader" element={<Navigate to="/twitter-video-downloader" replace />} />

            {/* YouTube */}
            <Route path="/youtube-video-downloader" element={<ToolPage config={pagesConfig['youtube/youtube-video-downloader']} />} />
            <Route path="/youtube-thumbnail-downloader" element={<ToolPage config={pagesConfig['youtube/youtube-thumbnails']} />} />
            <Route path="/youtube" element={<Navigate to="/youtube-video-downloader" replace />} />
            <Route path="/youtube/youtube-video-downloader" element={<Navigate to="/youtube-video-downloader" replace />} />
            <Route path="/youtube/youtube-thumbnails" element={<Navigate to="/youtube-thumbnail-downloader" replace />} />

            {/* Facebook */}
            <Route path="/facebook-video-downloader" element={<ToolPage config={pagesConfig['facebook/facebook-video-downloader']} />} />
            <Route path="/facebook-photo-downloader" element={<ToolPage config={pagesConfig['facebook/facebook-posts']} />} />
            <Route path="/facebook" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-video-downloader" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-reels" element={<Navigate to="/facebook-video-downloader" replace />} />
            <Route path="/facebook/facebook-posts" element={<Navigate to="/facebook-photo-downloader" replace />} />

            {/* Instagram */}
            <Route path="/instagram-video-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-video-downloader']} />} />
            <Route path="/instagram-photo-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-photo-downloader']} />} />
            <Route path="/instagram" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-video-downloader" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-photo-downloader" element={<Navigate to="/instagram-photo-downloader" replace />} />
            <Route path="/instagram/instagram-reels-downloader" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-reels" element={<Navigate to="/instagram-video-downloader" replace />} />
            <Route path="/instagram/instagram-carousel-downloader" element={<Navigate to="/instagram-photo-downloader" replace />} />

            {/* TikTok */}
            <Route path="/tiktok-video-downloader" element={<ToolPage config={pagesConfig['tiktok/tiktok-downloader']} />} />
            <Route path="/tiktok-photo-downloader" element={<ToolPage config={pagesConfig['tiktok/tiktok-downloader']} />} />
            <Route path="/tiktok" element={<Navigate to="/tiktok-video-downloader" replace />} />
            <Route path="/tiktok/tiktok-downloader" element={<Navigate to="/tiktok-video-downloader" replace />} />

            {/* Pinterest */}
            <Route path="/pinterest-video-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-video-downloader']} />} />
            <Route path="/pinterest-photo-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-photo-downloader']} />} />
            <Route path="/pinterest" element={<Navigate to="/pinterest-video-downloader" replace />} />

            {/* Threads */}
            <Route path="/threads-video-downloader" element={<ToolPage config={pagesConfig['threads-video-downloader']} />} />
            <Route path="/threads" element={<Navigate to="/threads-video-downloader" replace />} />

            {/* Reddit */}
            <Route path="/reddit-video-downloader" element={<ToolPage config={pagesConfig['reddit-video-downloader']} />} />
            <Route path="/reddit" element={<Navigate to="/reddit-video-downloader" replace />} />

            {/* Any Website */}
            <Route path="/any-website-downloader" element={<ToolPage config={pagesConfig['any-website-downloader']} />} />
            <Route path="/website-downloader" element={<Navigate to="/any-website-downloader" replace />} />

            {/* Legal & Static */}
            <Route path="/privacy" element={<PrivacyPolicyPage />} />
            <Route path="/privacy-policy" element={<Navigate to="/privacy" replace />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/terms-of-service" element={<Navigate to="/terms" replace />} />
            <Route path="/dmca" element={<SecurityPage />} />
            <Route path="/security" element={<Navigate to="/dmca" replace />} />
            <Route path="/contact" element={<ContactPage />} />

            {/* Catch-all */}
            <Route path="*" element={<HomePage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
