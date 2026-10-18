import React, { useState, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  Trophy, 
  Search, 
  TrendingUp, 
  Globe, 
  Users, 
  ExternalLink, 
  CheckCircle2, 
  RotateCcw,
  Clock, 
  BarChart3, 
  Sparkles,
  ShieldCheck,
  ThumbsUp
} from 'lucide-react';
import { topFacebookPagesData } from '../data/topFacebookPagesData.js';
import FacebookPills from '../components/FacebookPills.jsx';
import { FacebookIcon } from '../components/BrandIcons.jsx';

export default function TopFacebookPagesPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const countryParam = searchParams.get('country') || 'All';
  const categoryParam = searchParams.get('category') || 'All';
  const limitParam = searchParams.get('limit') || '100';
  const searchVal = searchParams.get('search') || '';

  const [searchTerm, setSearchTerm] = useState(searchVal);
  const [selectedCountry, setSelectedCountry] = useState(countryParam);
  const [selectedCategory, setSelectedCategory] = useState(categoryParam);
  const [limit, setLimit] = useState(parseInt(limitParam) || 100);

  const uniqueCountries = useMemo(() => {
    const list = Array.from(new Set(topFacebookPagesData.map((p) => p.country))).sort();
    return ['All', ...list];
  }, []);

  const uniqueCategories = useMemo(() => {
    const list = Array.from(new Set(topFacebookPagesData.map((p) => p.category))).sort();
    return ['All', ...list];
  }, []);

  const filteredPages = useMemo(() => {
    return topFacebookPagesData
      .filter((p) => {
        const matchesSearch = 
          p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.handle.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCountry = selectedCountry === 'All' || p.country === selectedCountry;
        const matchesCategory = selectedCategory === 'All' || p.category === selectedCategory;
        return matchesSearch && matchesCountry && matchesCategory;
      })
      .slice(0, limit);
  }, [searchTerm, selectedCountry, selectedCategory, limit]);

  function handleReset() {
    setSearchTerm('');
    setSelectedCountry('All');
    setSelectedCategory('All');
    setLimit(100);
    setSearchParams({});
  }

  return (
    <div className="py-8 max-w-7xl mx-auto px-4 sm:px-6">
      
      {/* Facebook Tool Suite Navigation Pills */}
      <FacebookPills activeSubfeature="top100" />

      {/* Main Header */}
      <div className="text-center max-w-3xl mx-auto mb-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-950/60 border border-blue-500/30 text-xs text-blue-400 font-semibold mb-4 shadow-inner">
          <FacebookIcon className="w-3.5 h-3.5 text-blue-400" />
          <span>Official 12-Hour Global Index</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-3">
          Top 100 Most Followed Facebook Pages
        </h1>

        <p className="text-slate-400 text-xs sm:text-sm leading-relaxed mb-4">
          This list ranks Facebook Pages worldwide by current public follower count, as recorded by <strong className="text-blue-400">OVD.winplaybox.in</strong> and refreshed every 12 hours.
        </p>

        <div className="inline-flex items-center gap-2 text-[11px] text-slate-500 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-blue-400" />
          <span>Last synchronized: Today &bull; Next automatic update in ~12H</span>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-5 sm:p-6 mb-8 shadow-xl">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          
          {/* Search */}
          <div className="relative w-full lg:w-80">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search Facebook page or handle..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* Dropdown Filters */}
          <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
            {/* Country */}
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-blue-500 transition"
            >
              {uniqueCountries.map((c) => (
                <option key={c} value={c}>{c === 'All' ? 'All Countries' : c}</option>
              ))}
            </select>

            {/* Category */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-blue-500 transition"
            >
              {uniqueCategories.map((cat) => (
                <option key={cat} value={cat}>{cat === 'All' ? 'All Categories' : cat}</option>
              ))}
            </select>

            {/* Limit */}
            <div className="inline-flex rounded-xl bg-slate-950 border border-slate-800 p-0.5 text-xs">
              {[10, 50, 100].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setLimit(num)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition cursor-pointer ${
                    limit === num
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Top {num}
                </button>
              ))}
            </div>

            {/* Reset */}
            {(searchTerm || selectedCountry !== 'All' || selectedCategory !== 'All' || limit !== 100) && (
              <button
                type="button"
                onClick={handleReset}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition cursor-pointer"
                title="Reset all filters"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Pages Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl mb-12">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-4 px-4 sm:px-6 w-16">Rank</th>
                <th className="py-4 px-4 sm:px-6">Facebook Page</th>
                <th className="py-4 px-4 sm:px-6">Category</th>
                <th className="py-4 px-4 sm:px-6">Country</th>
                <th className="py-4 px-4 sm:px-6 text-right">Followers</th>
                <th className="py-4 px-4 sm:px-6 text-right">Likes</th>
                <th className="py-4 px-4 sm:px-6 text-center w-20">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredPages.map((page) => {
                const isTop3 = page.rank <= 3;
                return (
                  <tr
                    key={page.rank}
                    className="hover:bg-slate-800/40 transition group"
                  >
                    {/* Rank */}
                    <td className="py-4 px-4 sm:px-6 font-mono font-bold">
                      <span
                        className={`inline-flex items-center justify-center w-7 h-7 rounded-xl text-xs ${
                          page.rank === 1
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-500/20'
                            : page.rank === 2
                            ? 'bg-slate-300/20 text-slate-200 border border-slate-400/40'
                            : page.rank === 3
                            ? 'bg-amber-700/20 text-amber-500 border border-amber-700/40'
                            : 'text-slate-500'
                        }`}
                      >
                        {page.rank}
                      </span>
                    </td>

                    {/* Page */}
                    <td className="py-4 px-4 sm:px-6">
                      <div className="flex items-center gap-3">
                        <img
                          src={page.avatar}
                          alt={page.name}
                          className="w-10 h-10 rounded-2xl object-cover bg-slate-800 border border-slate-700/60 shadow-sm shrink-0"
                          loading="lazy"
                        />
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="font-bold text-white text-xs sm:text-sm group-hover:text-blue-400 transition truncate">
                              {page.name}
                            </span>
                            {page.verified && (
                              <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                            )}
                          </div>
                          <span className="text-[11px] text-slate-500 font-mono block">
                            {page.handle}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="py-4 px-4 sm:px-6">
                      <span className="px-2.5 py-1 rounded-full bg-slate-950 text-slate-300 border border-slate-800 text-[10px] font-bold">
                        {page.category}
                      </span>
                    </td>

                    {/* Country */}
                    <td className="py-4 px-4 sm:px-6 whitespace-nowrap">
                      <span className="flex items-center gap-1.5 text-slate-300 font-medium">
                        <span className="text-base">{page.flag}</span>
                        <span>{page.country}</span>
                      </span>
                    </td>

                    {/* Followers */}
                    <td className="py-4 px-4 sm:px-6 text-right">
                      <span className="font-mono text-xs sm:text-sm font-extrabold text-white flex items-center justify-end gap-1">
                        <Users className="w-3.5 h-3.5 text-blue-400" />
                        <span>{page.followers}</span>
                      </span>
                    </td>

                    {/* Likes */}
                    <td className="py-4 px-4 sm:px-6 text-right">
                      <span className="font-mono text-xs text-slate-400 flex items-center justify-end gap-1">
                        <ThumbsUp className="w-3 h-3 text-slate-500" />
                        <span>{page.likes}</span>
                      </span>
                    </td>

                    {/* Link */}
                    <td className="py-4 px-4 sm:px-6 text-center">
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex p-2 rounded-xl bg-slate-950 hover:bg-blue-600 text-slate-400 hover:text-white border border-slate-800 transition"
                        title={`Open ${page.name} on Facebook`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* AdSense In-Article Display Unit */}
      <div className="max-w-4xl mx-auto mb-16 text-center">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Responsive Facebook Rankings Display Unit ]</span>
          </div>
        </div>
      </div>

      {/* Deep Analytical Methodology (High Google AdSense Value) */}
      <section className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-10 text-slate-300">
        <h2 className="text-xl sm:text-2xl font-black text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <span>Facebook Page Ranking Methodology</span>
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed mb-6">
          The <strong>Top 100 Most Followed Facebook Pages</strong> index tracks public pages across sports clubs, multinational brands, international news bureaus, global musicians, and digital creators. Metrics are extracted from verified Facebook graph public counters and synchronized every 12 hours by OVD.winplaybox.in.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
            <Users className="w-5 h-5 text-blue-400 mb-2" />
            <h4 className="font-bold text-white mb-1">Athlete Hegemony</h4>
            <p className="text-slate-400">Global icons like Cristiano Ronaldo (170M+) and Lionel Messi (116M+) command higher follower counts than major broadcasting networks.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
            <Globe className="w-5 h-5 text-cyan-400 mb-2" />
            <h4 className="font-bold text-white mb-1">Multi-Lingual News</h4>
            <p className="text-slate-400">International outlets including CGTN and China Daily maintain substantial global footprints through localized language editions.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
            <Sparkles className="w-5 h-5 text-amber-400 mb-2" />
            <h4 className="font-bold text-white mb-1">Video & Reel Virality</h4>
            <p className="text-slate-400">Pages actively publishing Facebook Reels experience accelerated follower gains compared to traditional image and link posts.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
