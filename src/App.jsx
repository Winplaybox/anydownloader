import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import ToolPage from './pages/ToolPage.jsx';
import TopChannelsPage from './pages/TopChannelsPage.jsx';
import TopFacebookPagesPage from './pages/TopFacebookPagesPage.jsx';
import TopInstagramAccountsPage from './pages/TopInstagramAccountsPage.jsx';
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

// Dynamic SEO Head Updater for Search Engines and Social Crawlers
function SEOHead() {
  const { pathname } = useLocation();

  useEffect(() => {
    const cleanPath = pathname.replace(/^\/+|\/+$/g, '');
    let title = 'OVD - Free Online Video, Reel & Audio Downloader';
    let desc = 'OVD is a fast, free media downloader. Download High-Definition Videos, YouTube 1080p/4K, Facebook Reels & Videos, Instagram Reels, TikTok without watermark, and 320kbps MP3 audio in seconds.';

    if (cleanPath === 'youtube/top-100-youtube-channels' || cleanPath === 'youtube/top-100-channels') {
      title = 'Top 100 YouTube Channels - Global Subscriber Rankings | OVD';
      desc = 'Explore the live top 100 most subscribed YouTube channels worldwide. 12-hour automated synchronization with country and category filters.';
    } else if (cleanPath === 'facebook/top-100-facebook-pages' || cleanPath === 'facebook/top-100-pages') {
      title = 'Top 100 Facebook Pages - Global Follower Rankings | OVD';
      desc = 'Explore the live top 100 most followed Facebook pages worldwide. 12-hour automated synchronization with country filtering.';
    } else if (cleanPath === 'instagram/top-100-instagram-accounts' || cleanPath === 'instagram/top-100-accounts') {
      title = 'Top 100 Instagram Accounts - Global Follower Rankings | OVD';
      desc = 'Explore the live top 100 most followed Instagram accounts worldwide. 12-hour automated synchronization with country and category filters.';
    } else if (cleanPath === 'blogs' || cleanPath === 'blog') {
      title = 'Social Media Updates Blog - Real-Time Creator News & Guides | OVD';
      desc = 'Stay ahead of social media algorithm shifts, video compression settings, TikTok audio guidelines, and creator monetization updates.';
    } else if (cleanPath === 'updates' || cleanPath === 'changelog') {
      title = 'Product Release Changelog & Engine Updates | OVD Downloader PRO';
      desc = 'Official release notes, feature launches, architecture updates, and engine changelogs for OVD Downloader PRO.';
    } else if (cleanPath === 'privacy-policy') {
      title = 'Privacy Policy - OVD Downloader PRO';
      desc = 'Privacy Policy, cookie guidelines, Google AdSense DART disclosure, CCPA, and GDPR compliance details for OVD Downloader.';
    } else if (cleanPath === 'terms-of-service') {
      title = 'Terms of Service - OVD Downloader PRO';
      desc = 'Terms of Service and acceptable use conditions for OVD Downloader PRO.';
    } else if (cleanPath === 'contact') {
      title = 'Contact Us - OVD Downloader PRO';
      desc = 'Get in touch with the OVD Downloader PRO support and development team.';
    } else if (pagesConfig[cleanPath]) {
      const cfg = pagesConfig[cleanPath];
      title = `${cfg.title} - Free Online Downloader | OVD`;
      desc = cfg.guideIntro || (cfg.sections && cfg.sections[0] ? cfg.sections[0].body : `${cfg.title} free download service.`);
    }

    // Set title
    document.title = title;

    // Set meta description
    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.setAttribute('name', 'description');
      document.head.appendChild(metaDesc);
    }
    metaDesc.setAttribute('content', desc);

    // Set canonical link
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', `https://ovd.winplaybox.in/${cleanPath}`);

    // Set Open Graph tags
    let ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) ogTitle.setAttribute('content', title);
    let ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) ogDesc.setAttribute('content', desc);
    let ogUrl = document.querySelector('meta[property="og:url"]');
    if (ogUrl) ogUrl.setAttribute('content', `https://ovd.winplaybox.in/${cleanPath}`);

  }, [pathname]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <SEOHead />
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
            <Route path="/instagram/instagram-video-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-video-downloader']} />} />
            <Route path="/instagram/instagram-photo-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-photo-downloader']} />} />
            <Route path="/instagram/instagram-reels-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-reels-downloader']} />} />
            <Route path="/instagram/instagram-reels" element={<ToolPage config={pagesConfig['instagram/instagram-reels']} />} />
            <Route path="/instagram/instagram-story-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-story-downloader']} />} />
            <Route path="/instagram/instagram-story" element={<Navigate to="/instagram/instagram-story-downloader" replace />} />
            <Route path="/instagram/instagram-igtv-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-igtv-downloader']} />} />
            <Route path="/instagram/instagram-igtv" element={<Navigate to="/instagram/instagram-igtv-downloader" replace />} />
            <Route path="/instagram/instagram-carousel-downloader" element={<ToolPage config={pagesConfig['instagram/instagram-carousel-downloader']} />} />
            <Route path="/instagram/instagram-carousel" element={<Navigate to="/instagram/instagram-carousel-downloader" replace />} />
            <Route path="/instagram/instagram-viewer" element={<ToolPage config={pagesConfig['instagram/instagram-viewer']} />} />

            {/* Top 100 Instagram Accounts Dedicated Database Page */}
            <Route path="/instagram/top-100-instagram-accounts" element={<TopInstagramAccountsPage />} />
            <Route path="/instagram/top-100-accounts" element={<Navigate to="/instagram/top-100-instagram-accounts" replace />} />

                        {/* Pinterest Category Nested Routes */}
            <Route path="/pinterest" element={<Navigate to="/pinterest/pinterest-downloader" replace />} />
            <Route path="/pinterest/pinterest-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-downloader']} />} />
            <Route path="/pinterest/pinterest-video-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-video-downloader']} />} />
            <Route path="/pinterest/pinterest-photo-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-photo-downloader']} />} />
            <Route path="/pinterest/pinterest-gif-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-gif-downloader']} />} />
            <Route path="/pinterest/pinterest-story-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-story-downloader']} />} />
            <Route path="/pinterest/pinterest-board-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-board-downloader']} />} />
            <Route path="/pinterest/pinterest-profile-downloader" element={<ToolPage config={pagesConfig['pinterest/pinterest-profile-downloader']} />} />

            {/* Twitter / X Category Nested Routes */}
            <Route path="/twitter" element={<Navigate to="/twitter/twitter-downloader" replace />} />
            <Route path="/x" element={<Navigate to="/twitter/twitter-downloader" replace />} />
            <Route path="/twitter/twitter-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-downloader']} />} />
            <Route path="/twitter/twitter-video-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-video-downloader']} />} />
            <Route path="/twitter/twitter-mp3-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-mp3-downloader']} />} />
            <Route path="/twitter/twitter-image-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-image-downloader']} />} />
            <Route path="/twitter/twitter-gif-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-gif-downloader']} />} />
            <Route path="/twitter/twitter-profile-downloader" element={<ToolPage config={pagesConfig['twitter/twitter-profile-downloader']} />} />


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
            <Route path="/instagram-video-downloader" element={<Navigate to="/instagram/instagram-video-downloader" replace />} />
            <Route path="/instagram-photo-downloader" element={<Navigate to="/instagram/instagram-photo-downloader" replace />} />
            <Route path="/instagram-reels-downloader" element={<Navigate to="/instagram/instagram-reels-downloader" replace />} />
            <Route path="/instagram-reels" element={<Navigate to="/instagram/instagram-reels-downloader" replace />} />
            <Route path="/instagram-story-downloader" element={<Navigate to="/instagram/instagram-story-downloader" replace />} />
            <Route path="/instagram-igtv-downloader" element={<Navigate to="/instagram/instagram-igtv-downloader" replace />} />
            <Route path="/instagram-carousel-downloader" element={<Navigate to="/instagram/instagram-carousel-downloader" replace />} />
            <Route path="/instagram-viewer" element={<Navigate to="/instagram/instagram-viewer" replace />} />
            <Route path="/top-100-instagram-accounts" element={<Navigate to="/instagram/top-100-instagram-accounts" replace />} />
            <Route path="/tiktok-downloader" element={<Navigate to="/tiktok/tiktok-downloader" replace />} />
            <Route path="/pinterest-downloader" element={<Navigate to="/pinterest/pinterest-downloader" replace />} />
            <Route path="/pinterest-video-downloader" element={<Navigate to="/pinterest/pinterest-video-downloader" replace />} />
            <Route path="/pinterest-photo-downloader" element={<Navigate to="/pinterest/pinterest-photo-downloader" replace />} />
            <Route path="/pinterest-image-downloader" element={<Navigate to="/pinterest/pinterest-photo-downloader" replace />} />
            <Route path="/pinterest-gif-downloader" element={<Navigate to="/pinterest/pinterest-gif-downloader" replace />} />
            <Route path="/pinterest-story-downloader" element={<Navigate to="/pinterest/pinterest-story-downloader" replace />} />
            <Route path="/pinterest-board-downloader" element={<Navigate to="/pinterest/pinterest-board-downloader" replace />} />
            <Route path="/pinterest-profile-downloader" element={<Navigate to="/pinterest/pinterest-profile-downloader" replace />} />

            <Route path="/twitter-downloader" element={<Navigate to="/twitter/twitter-downloader" replace />} />
            <Route path="/twitter-video-downloader" element={<Navigate to="/twitter/twitter-video-downloader" replace />} />
            <Route path="/twitter-mp4-downloader" element={<Navigate to="/twitter/twitter-video-downloader" replace />} />
            <Route path="/twitter-mp3-downloader" element={<Navigate to="/twitter/twitter-mp3-downloader" replace />} />
            <Route path="/twitter-audio-downloader" element={<Navigate to="/twitter/twitter-mp3-downloader" replace />} />
            <Route path="/twitter-image-downloader" element={<Navigate to="/twitter/twitter-image-downloader" replace />} />
            <Route path="/twitter-photo-downloader" element={<Navigate to="/twitter/twitter-image-downloader" replace />} />
            <Route path="/twitter-gif-downloader" element={<Navigate to="/twitter/twitter-gif-downloader" replace />} />
            <Route path="/twitter-profile-downloader" element={<Navigate to="/twitter/twitter-profile-downloader" replace />} />
            <Route path="/x-downloader" element={<Navigate to="/twitter/twitter-downloader" replace />} />
            <Route path="/x-video-downloader" element={<Navigate to="/twitter/twitter-video-downloader" replace />} />
            <Route path="/x-mp3-downloader" element={<Navigate to="/twitter/twitter-mp3-downloader" replace />} />
            <Route path="/x-image-downloader" element={<Navigate to="/twitter/twitter-image-downloader" replace />} />
            <Route path="/x-gif-downloader" element={<Navigate to="/twitter/twitter-gif-downloader" replace />} />
            <Route path="/x-profile-downloader" element={<Navigate to="/twitter/twitter-profile-downloader" replace />} />



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
