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
    return <Newspaper className="w-3.5 h-3.5 text-rose-400" />;
  }

  return (
    <div className="py-10 max-w-7xl mx-auto px-4 sm:px-6">
      
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-rose-400 font-semibold mb-4 shadow-inner">
          <Sparkles className="w-3.5 h-3.5 text-rose-400" />
          <span>Real-Time Social Media Intelligence</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
          Social Media Updates & Trends
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
          Stay ahead of algorithmic shifts, new creator monetization policies, video compression guidelines, and viral audience growth strategies.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-10 pb-6 border-b border-slate-800/80">
        {/* Platform Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-slate-900 border border-slate-800 overflow-x-auto w-full sm:w-auto">
          {platforms.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setSelectedPlatform(p)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                selectedPlatform === p
                  ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {p !== 'All' && getPlatformIcon(p)}
              <span>{p}</span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search articles & updates..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition"
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
        {filteredPosts.map((post) => (
          <article
            key={post.id}
            className="bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-slate-700/90 rounded-3xl overflow-hidden flex flex-col justify-between transition duration-300 group shadow-lg"
          >
            <div>
              {/* Cover Image */}
              <div className="relative aspect-video overflow-hidden bg-slate-950">
                <img
                  src={post.image}
                  alt={post.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-500 opacity-90 group-hover:opacity-100"
                />
                <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/80 backdrop-blur-md border border-slate-800 text-[10px] font-bold text-white">
                  {getPlatformIcon(post.platform)}
                  <span>{post.platform}</span>
                </div>
                <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold">
                  {post.category}
                </div>
              </div>

              {/* Body */}
              <div className="p-6">
                <div className="flex items-center gap-3 text-[11px] text-slate-500 mb-2.5">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    {post.date}
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {post.readTime}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white group-hover:text-rose-400 transition leading-snug mb-2.5 line-clamp-2">
                  {post.title}
                </h3>

                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  {post.summary}
                </p>
              </div>
            </div>

            {/* Read CTA */}
            <div className="px-6 pb-6 pt-2">
              <button
                type="button"
                onClick={() => setActiveArticle(post)}
                className="w-full py-2.5 px-4 rounded-xl bg-slate-950 hover:bg-rose-600 text-slate-300 hover:text-white border border-slate-800 hover:border-transparent text-xs font-bold transition flex items-center justify-between cursor-pointer group/btn"
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
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ In-Feed Social Media Blog Display Unit ]</span>
          </div>
        </div>
      </div>

      {/* Modal Article Reader */}
      {activeArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setActiveArticle(null)}
              className="absolute top-5 right-5 p-2 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Metadata */}
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] font-bold">
                {activeArticle.category}
              </span>
              <span className="text-xs text-slate-500">&bull; {activeArticle.date}</span>
              <span className="text-xs text-slate-500">&bull; {activeArticle.readTime}</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-black text-white leading-tight mb-4">
              {activeArticle.title}
            </h2>

            {/* Image */}
            <div className="rounded-2xl overflow-hidden aspect-video mb-6 border border-slate-800">
              <img
                src={activeArticle.image}
                alt={activeArticle.title}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Article Content */}
            <div className="prose prose-invert prose-rose max-w-none text-xs sm:text-sm text-slate-300 leading-relaxed whitespace-pre-line mb-8">
              {activeArticle.content.trim()}
            </div>

            {/* Footer Actions */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <button
                type="button"
                onClick={() => handleShare(activeArticle.slug)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition cursor-pointer"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
                <span>{copiedLink ? 'Link Copied' : 'Share Article'}</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveArticle(null)}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition cursor-pointer"
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
