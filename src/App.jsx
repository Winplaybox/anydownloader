import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Footer from './components/Footer.jsx';
import SEOHead from './seo/SEOHead.jsx';
import HomePage from './pages/HomePage.jsx';
import ToolPage from './pages/ToolPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage.jsx';
import TermsPage from './pages/TermsPage.jsx';
import ContactPage from './pages/ContactPage.jsx';
import SecurityPage from './pages/SecurityPage.jsx';
import BlogsPage from './pages/BlogsPage.jsx';
import UpdatesPage from './pages/UpdatesPage.jsx';
import ExtensionPage from './pages/ExtensionPage.jsx';
import VideoEditorPage from './pages/VideoEditorPage.jsx';
import PricingPage from './pages/PricingPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import SignUpPage from './pages/SignUpPage.jsx';
import YouTubeSubscribeLinkPage from './pages/YouTubeSubscribeLinkPage.jsx';
import AdminDashboardPage from './pages/AdminDashboardPage.jsx';
import { TOOL_ROUTES, TOOL_REDIRECTS } from './data/toolRoutes.js';
import { initAttribution } from './utils/attribution.js';

/** New page = start at the top, instantly (a smooth scroll on every navigation feels like lag). */
function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) return;
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [pathname, hash]);
  return null;
}

export default function App() {
  useEffect(() => { initAttribution(); }, []);

  return (
    <BrowserRouter>
      <ScrollToTop />
      <SEOHead />
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-xl focus:bg-[var(--text)] focus:px-4 focus:py-2 focus:text-[var(--bg)]">
        Skip to content
      </a>
      <div className="min-h-dvh flex flex-col bg-[var(--bg)] text-[var(--text)]">
        <Header />
        <main id="main" className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            {TOOL_ROUTES.map((r) => <Route key={r.path} path={r.path} element={<ToolPage route={r} />} />)}
            {Object.entries(TOOL_REDIRECTS).map(([from, to]) => <Route key={from} path={from} element={<Navigate to={to} replace />} />)}

            <Route path="/ai-video-editor" element={<VideoEditorPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/plans" element={<Navigate to="/pricing" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignUpPage />} />
            <Route path="/youtube-subscribe-link-generator" element={<YouTubeSubscribeLinkPage />} />
            <Route path="/extension" element={<ExtensionPage />} />
            <Route path="/blog" element={<BlogsPage />} />
            <Route path="/updates" element={<UpdatesPage />} />
            <Route path="/privacy" element={<PrivacyPolicyPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/dmca" element={<SecurityPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/ovd-admin" element={<AdminDashboardPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
