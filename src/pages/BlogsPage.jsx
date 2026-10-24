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
  Tag, 
  TrendingUp,
  Bookmark
} from 'lucide-react';
import { blogPosts } from '../data/blogData.js';
import { 
  YoutubeIcon, 
  InstagramIcon, 
  TiktokIcon, 
  FacebookIcon 
} from '../components/BrandIcons.jsx';

export default function BlogsPage() {
  const [selectedPlatform, setSelectedPlatform] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const platforms = ['All', 'YouTube', 'Instagram', 'TikTok'];

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
    const url = `${window.location.origin}/blogs#${slug}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  }

  function getPlatformIcon(p) {
    if (p === 'YouTube') return <YoutubeIcon className="w-3.5 h-3.5 text-red-500" />;
    if (p === 'Instagram') return <InstagramIcon className="w-3.5 h-3.5 text-pink-500" />;
    if (p === 'TikTok') return <TiktokIcon className="w-3.5 h-3.5 text-cyan-400" />;
    if (p === 'Facebook') return <FacebookIcon className="w-3.5 h-3.5 text-blue-500" />;
    return <Newspaper className="w-3.5 h-3.5 text-[var(--accent)]" />;
  }

  return (
    <div className="py-10 max-w-7xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--accent)] font-semibold mb-4 shadow-inner">
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
          {platforms.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setSelectedPlatform(p)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                selectedPlatform === p
                  ? 'bg-[var(--primary)] text-[var(--text)] shadow-md'
                  : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)]'
              }`}
            >
              {p !== 'All' && getPlatformIcon(p)}
              <span>{p}</span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search articles & updates..."
            className="w-full bg-[var(--surface)] border border-[var(--border)] rounded-xl pl-10 pr-4 py-2 text-xs text-[var(--text)] placeholder-slate-500 focus:outline-none focus:border-[var(--border-strong)] transition"
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {filteredPosts.map((post) => (
          <article
            key={post.id}
            className="bg-[var(--surface)]/80 hover:bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-3xl overflow-hidden flex flex-col justify-between transition duration-300 group shadow-lg"
          >
            <div>
              {/* Cover Image */}
              <div className="relative aspect-video overflow-hidden bg-[var(--bg)]">
                <img
                  src={post.image}
                  alt={post.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500 opacity-90 group-hover:opacity-100"
                />
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--bg)]/80 backdrop-blur-md border border-[var(--border)] text-[10px] font-bold text-[var(--text)]">
                  {getPlatformIcon(post.platform)}
                  <span>{post.platform}</span>
                </div>
                <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-[var(--accent-bg)] text-[var(--accent)] border border-[var(--border)] text-[10px] font-bold">
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
                className="w-full py-2.5 px-4 rounded-xl bg-[var(--bg)] hover:bg-[var(--primary)] text-[var(--text)] hover:text-[var(--text)] border border-[var(--border)] hover:border-transparent text-xs font-bold transition flex items-center justify-between cursor-pointer group/btn"
              >
                <span>Read Full Article</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-1 transition" />
              </button>
            </div>
          </article>
        ))}
      </div>

      {/* AdSense Leaderboard Placement */}
      <div className="max-w-4xl mx-auto mb-16">
        <div className="bg-[var(--surface)]/50 border border-[var(--border)] rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-[var(--bg)]/60 rounded-xl flex items-center justify-center border border-[var(--border)] text-[var(--text-muted)] text-xs font-mono">
            <span>[ In-Feed Social Media Blog Display Unit ]</span>
          </div>
        </div>
      </div>

      {/* Modal Article Reader */}
      {activeArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="bg-[var(--bg)] border border-[var(--border)] rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setActiveArticle(null)}
              className="absolute top-5 right-5 p-2 rounded-full bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text-muted)] hover:text-[var(--text)] transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Metadata */}
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-0.5 rounded-full bg-[var(--accent-bg)] text-[var(--accent)] border border-[var(--border)] text-[10px] font-bold">
                {activeArticle.category}
              </span>
              <span className="text-xs text-[var(--text-muted)]">&bull; {activeArticle.date}</span>
              <span className="text-xs text-[var(--text-muted)]">&bull; {activeArticle.readTime}</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-black text-[var(--text)] leading-tight mb-4">
              {activeArticle.title}
            </h2>

            {/* Image */}
            <div className="rounded-2xl overflow-hidden aspect-video mb-6 border border-[var(--border)]">
              <img
                src={activeArticle.image}
                alt={activeArticle.title}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Article Content */}
            <div className="prose max-w-none text-xs sm:text-sm text-[var(--text-muted)] leading-relaxed whitespace-pre-line mb-8">
              {(activeArticle?.content && typeof activeArticle.content === 'string') ? activeArticle.content.trim() : ''}
            </div>

            {/* Footer Actions */}
            <div className="pt-4 border-t border-[var(--border)] flex items-center justify-between">
              <button
                type="button"
                onClick={() => handleShare(activeArticle.slug)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)] hover:text-[var(--text)] text-xs font-semibold transition cursor-pointer"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
                <span>{copiedLink ? 'Link Copied' : 'Share Article'}</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveArticle(null)}
                className="px-5 py-2 rounded-xl bg-[var(--primary)] hover:bg-[var(--primary)] text-[var(--text)] text-xs font-bold transition cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


