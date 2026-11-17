import React, { useState, useEffect, useMemo } from 'react';
import { 
  Newspaper, 
  Search, 
  Calendar, 
  Clock, 
  ArrowRight, 
  X, 
  Share2, 
  Check, 
  Sparkles, 
  Tag,
  RefreshCw
} from 'lucide-react';
import { blogPosts as fallbackPosts } from '../data/blogData.js';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon,
  TwitterXIcon,
  PinterestIcon,
  RedditIcon,
  GlobeIcon
} from '../components/BrandIcons.jsx';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export default function BlogsPage() {
  const [posts, setPosts] = useState(fallbackPosts);
  const [selectedPlatform, setSelectedPlatform] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch autonomous scheduled articles from backend
  useEffect(() => {
    async function loadArticles() {
      try {
        const resp = await fetch(`${BACKEND_BASE}/api/blogs`);
        if (resp.ok) {
          const data = await resp.json();
          if (data && Array.isArray(data.articles) && data.articles.length > 0) {
            // Prepend new scheduled articles to curated baseline
            const combined = [...data.articles, ...fallbackPosts.filter(fp => !data.articles.some(da => da.id === fp.id))];
            setPosts(combined);
          }
        }
      } catch (err) {
        // Fallback to static articles
      }
    }
    loadArticles();
  }, []);

  const platforms = ['All', 'YouTube', 'Instagram', 'TikTok', 'Facebook', 'Twitter', 'Reddit'];

  const filteredPosts = useMemo(() => {
    return posts.filter((post) => {
      const matchPlatform = selectedPlatform === 'All' || (post.platform || '').toLowerCase() === selectedPlatform.toLowerCase();
      const matchSearch = 
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (post.summary || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (post.category || '').toLowerCase().includes(searchQuery.toLowerCase());
      return matchPlatform && matchSearch;
    });
  }, [posts, selectedPlatform, searchQuery]);

  function handleShare(slug) {
    const url = `${window.location.origin}/blog#${slug}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  }

  function getPlatformIcon(p) {
    const pl = (p || '').toLowerCase();
    if (pl === 'youtube') return <YoutubeIcon className="w-3.5 h-3.5 text-red-500" />;
    if (pl === 'instagram') return <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />;
    if (pl === 'tiktok') return <TiktokIcon className="w-3.5 h-3.5 text-cyan-400" />;
    if (pl === 'facebook') return <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />;
    if (pl === 'twitter' || pl === 'x') return <TwitterXIcon className="w-3.5 h-3.5" />;
    if (pl === 'reddit') return <RedditIcon className="w-3.5 h-3.5 text-orange-500" />;
    if (pl === 'pinterest') return <PinterestIcon className="w-3.5 h-3.5 text-red-600" />;
    return <GlobeIcon className="w-3.5 h-3.5 text-[var(--accent)]" />;
  }

  return (
    <div className="py-10 max-w-7xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] text-xs text-[var(--text-muted)] font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>New guides every week</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-3">
          Social Media Guides & Trends
        </h1>
        <p className="text-[var(--text-muted)] text-xs sm:text-sm leading-relaxed">
          Daily analytical insights, download tips, format guides, and viral creator strategy for YouTube, Instagram, TikTok, Facebook, and Twitter.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8 pb-6 border-b border-[var(--border)]">
        {/* Platform Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar w-full md:w-auto py-1">
          {platforms.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setSelectedPlatform(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                selectedPlatform === p
                  ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-xs'
                  : 'bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text)] border border-[var(--border)] hover:bg-[var(--bg-alt)]'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search guides..."
            className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-lg pl-9 pr-4 py-2 text-xs text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPosts.map((post) => (
          <article 
            key={post.id}
            className="bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden flex flex-col justify-between hover:border-[var(--border-strong)] transition-all shadow-xs group"
          >
            <div>
              {/* Thumbnail */}
              {post.image && (
                <div className="relative aspect-video overflow-hidden bg-[var(--bg-alt)]">
                  <img 
                    src={post.image} 
                    alt={post.title} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                  />
                  <div className="absolute top-2.5 left-2.5 bg-black/75 backdrop-blur-xs px-2.5 py-1 rounded-md flex items-center gap-1.5 text-white text-[11px] font-semibold">
                    {getPlatformIcon(post.platform)}
                    <span>{post.platform}</span>
                  </div>
                </div>
              )}

              {/* Content Body */}
              <div className="p-5">
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] mb-2 font-medium">
                  <span className="text-[var(--accent)] font-semibold">{post.category}</span>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{post.readTime}</span>
                  </div>
                </div>

                <h2 className="text-base font-bold text-[var(--text)] mb-2 group-hover:text-[var(--accent)] transition-colors line-clamp-2">
                  {post.title}
                </h2>

                <p className="text-xs text-[var(--text-muted)] leading-relaxed line-clamp-3">
                  {post.summary}
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-[var(--border)] bg-[var(--bg-alt)]/40 flex items-center justify-between">
              <span className="text-[11px] text-[var(--text-muted)] font-mono">{post.date}</span>
              <button
                type="button"
                onClick={() => setActiveArticle(post)}
                className="text-xs font-semibold text-[var(--primary)] hover:opacity-80 flex items-center gap-1 transition-opacity cursor-pointer"
              >
                <span>Read Guide</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </article>
        ))}
      </div>

      {/* Article Detail Lightbox */}
      {activeArticle && (
        <div 
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setActiveArticle(null)}
        >
          <div 
            className="bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-[var(--border)]">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-md bg-[var(--accent-bg)] text-[var(--accent)] text-xs font-semibold">
                  {activeArticle.platform}
                </span>
                <span className="text-xs text-[var(--text-muted)]">{activeArticle.category}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleShare(activeArticle.slug)}
                  className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
                  title="Share article link"
                >
                  {copiedLink ? <Check className="w-4 h-4 text-[var(--positive)]" /> : <Share2 className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveArticle(null)}
                  className="p-1.5 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
                  aria-label="Close article"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <h1 className="text-xl sm:text-2xl font-black text-[var(--text)] mb-3 leading-snug">
              {activeArticle.title}
            </h1>

            <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] mb-6">
              <span>{activeArticle.date}</span>
              <span>&bull;</span>
              <span>{activeArticle.readTime}</span>
            </div>

            <div className="text-xs sm:text-sm text-[var(--text)] leading-relaxed space-y-4 whitespace-pre-line border-t border-[var(--border)] pt-5">
              {activeArticle.content}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
