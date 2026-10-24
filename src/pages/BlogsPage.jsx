import React, { useState, useMemo } from 'react';
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
  Tag
} from 'lucide-react';
import { blogPosts } from '../data/blogData.js';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon,
  TwitterXIcon,
  PinterestIcon
} from '../components/BrandIcons.jsx';

export default function BlogsPage() {
  const [selectedPlatform, setSelectedPlatform] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const platforms = ['All', 'YouTube', 'Instagram', 'TikTok', 'Facebook'];

  const filteredPosts = useMemo(() => {
    return blogPosts.filter((post) => {
      const matchPlatform = selectedPlatform === 'All' || post.platform === selectedPlatform;
      const matchSearch = 
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.category.toLowerCase().includes(searchQuery.toLowerCase());
      return matchPlatform && matchSearch;
    });
  }, [selectedPlatform, searchQuery]);

  function handleShare(slug) {
    const url = `${window.location.origin}/blog#${slug}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  }

  function getPlatformIcon(p) {
    if (p === 'YouTube') return <YoutubeIcon className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />;
    if (p === 'Instagram') return <InstagramIcon className="w-3.5 h-3.5 text-pink-600 dark:text-pink-400" />;
    if (p === 'TikTok') return <TiktokIcon className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />;
    if (p === 'Facebook') return <FacebookIcon className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />;
    return <Newspaper className="w-3.5 h-3.5 text-[var(--accent)]" />;
  }

  return (
    <div className="py-10 max-w-7xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--text)] font-semibold mb-4 shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span>Real-Time Social Media Intelligence</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-4">
          Social Media Updates & Trends
        </h1>
        <p className="text-[var(--text-muted)] text-xs sm:text-sm leading-relaxed">
          Stay ahead of algorithmic shifts, new creator monetization policies, video compression guidelines, and viral audience growth strategies.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-10 pb-6 border-b border-[var(--border)]">
        {/* Platform Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-[var(--surface)] border border-[var(--border)] overflow-x-auto w-full sm:w-auto">
          {platforms.map((p) => {
            const isSelected = selectedPlatform === p;
            return (
              <button
                key={p}
                type="button"
                onClick={() => setSelectedPlatform(p)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                  isSelected
                    ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)]'
                }`}
              >
                {p !== 'All' && getPlatformIcon(p)}
                <span>{p}</span>
              </button>
            );
          })}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search articles & updates..."
            className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl pl-10 pr-4 py-2 text-xs text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {filteredPosts.map((post) => (
          <article
            key={post.id}
            className="bg-[var(--surface)] hover:bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-2xl overflow-hidden flex flex-col justify-between transition duration-300 group shadow-sm hover:shadow-md"
          >
            <div>
              {/* Cover Image */}
              <div className="relative aspect-video overflow-hidden bg-[var(--bg-alt)]">
                <img
                  src={post.image}
                  alt={post.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500 opacity-95 group-hover:opacity-100"
                />
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--bg)]/90 backdrop-blur-md border border-[var(--border)] text-[10px] font-bold text-[var(--text)]">
                  {getPlatformIcon(post.platform)}
                  <span>{post.platform}</span>
                </div>
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-[var(--surface)]/90 backdrop-blur-md text-[var(--text-muted)] border border-[var(--border)] text-[10px] font-semibold">
                  {post.category}
                </div>
              </div>

              {/* Body */}
              <div className="p-6">
                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)] mb-2.5">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-[var(--text-muted)]" />
                    {post.date}
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-[var(--text-muted)]" />
                    {post.readTime}
                  </span>
                </div>

                <h3 className="text-base font-bold text-[var(--text)] group-hover:text-[var(--accent)] transition leading-snug mb-2.5 line-clamp-2">
                  {post.title}
                </h3>

                <p className="text-xs text-[var(--text-muted)] leading-relaxed line-clamp-3">
                  {post.summary}
                </p>
              </div>
            </div>

            {/* Read CTA */}
            <div className="px-6 pb-6 pt-2">
              <button
                type="button"
                onClick={() => setActiveArticle(post)}
                className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)] border border-[var(--border)] hover:border-[var(--border-strong)] flex items-center justify-between transition-all cursor-pointer"
              >
                <span>Read Full Article</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </article>
        ))}
      </div>

      {/* Article Modal */}
      {activeArticle && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[var(--bg)] border border-[var(--border)] rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
            <button
              onClick={() => setActiveArticle(null)}
              className="absolute top-5 right-5 p-2 rounded-full hover:bg-[var(--bg-alt)] text-[var(--text-muted)] hover:text-[var(--text)] transition cursor-pointer"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <span className="px-2.5 py-1 rounded-full bg-[var(--surface)] text-[var(--text-muted)] border border-[var(--border)] text-xs font-semibold">
                {activeArticle.category}
              </span>
              <span className="text-xs text-[var(--text-muted)]">&bull;</span>
              <span className="text-xs text-[var(--text-muted)]">{activeArticle.date}</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-black text-[var(--text)] mb-4 leading-snug">
              {activeArticle.title}
            </h2>

            <div className="aspect-video w-full rounded-2xl overflow-hidden mb-6 bg-[var(--bg-alt)]">
              <img src={activeArticle.image} alt={activeArticle.title} className="w-full h-full object-cover" />
            </div>

            <div className="space-y-4 text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed mb-8">
              {activeArticle.content.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <button
                onClick={() => handleShare(activeArticle.slug)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold border border-[var(--border)] hover:bg-[var(--bg-alt)] text-[var(--text)] transition cursor-pointer"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Share2 className="w-3.5 h-3.5" />}
                <span>{copiedLink ? 'Link Copied!' : 'Share Article'}</span>
              </button>

              <button
                onClick={() => setActiveArticle(null)}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
