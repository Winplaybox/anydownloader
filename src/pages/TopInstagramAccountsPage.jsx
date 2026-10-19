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
  Heart
} from 'lucide-react';
import { topInstagramAccountsData } from '../data/topInstagramAccountsData.js';
import InstagramPills from '../components/InstagramPills.jsx';
import { InstagramIcon } from '../components/BrandIcons.jsx';

export default function TopInstagramAccountsPage() {
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
    const list = Array.from(new Set(topInstagramAccountsData.map((p) => p.country))).sort();
    return ['All', ...list];
  }, []);

  const uniqueCategories = useMemo(() => {
    const list = Array.from(new Set(topInstagramAccountsData.map((p) => p.category))).sort();
    return ['All', ...list];
  }, []);

  const filteredAccounts = useMemo(() => {
    return topInstagramAccountsData
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
      
      {/* Instagram Tool Suite Navigation Pills */}
      <InstagramPills activeSubfeature="top100" />

      {/* Page Header Banner */}
      <div className="text-center max-w-4xl mx-auto mb-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-pink-500/10 border border-pink-500/25 text-xs text-pink-400 font-semibold mb-4 shadow-inner">
          <Clock className="w-3.5 h-3.5" />
          <span>12-Hour Automated Sync Cycle • Global Instagram Leaderboard</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight mb-3">
          Top 100 Most Followed <span className="bg-gradient-to-r from-pink-500 via-rose-500 to-amber-400 bg-clip-text text-transparent">Instagram Accounts</span>
        </h1>

        <p className="text-slate-400 text-xs sm:text-sm max-w-2xl mx-auto leading-relaxed">
          Comprehensive real-time follower rankings for the most influential celebrities, creators, athletes, and global media brands on Instagram, updated automatically every 12 hours.
        </p>

        {/* Quick Limit Filters */}
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setLimit(50)}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold border transition ${
              limit === 50
                ? 'bg-gradient-to-r from-pink-600 to-rose-600 border-pink-500 text-white shadow-lg shadow-pink-500/20'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Top 50 Accounts
          </button>
          <button
            onClick={() => setLimit(100)}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold border transition ${
              limit === 100
                ? 'bg-gradient-to-r from-pink-600 to-rose-600 border-pink-500 text-white shadow-lg shadow-pink-500/20'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Top 100 Full Leaderboard
          </button>
        </div>
      </div>

      {/* Interactive Search & Filter Controls */}
      <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4 sm:p-5 mb-8 shadow-xl backdrop-blur-md">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          
          {/* Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by creator or @handle..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pink-500"
            />
          </div>

          {/* Country Selector */}
          <div className="relative">
            <Globe className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-pink-500 appearance-none cursor-pointer"
            >
              <option value="All">All Countries ({uniqueCountries.length - 1})</option>
              {uniqueCountries.filter((c) => c !== 'All').map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Category Selector */}
          <div className="relative">
            <BarChart3 className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-pink-500 appearance-none cursor-pointer"
            >
              <option value="All">All Categories ({uniqueCategories.length - 1})</option>
              {uniqueCategories.filter((cat) => cat !== 'All').map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Reset Filters Button */}
          <button
            onClick={handleReset}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Filters</span>
          </button>
        </div>

        {/* Live Filter Summary */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-pink-400" />
            <span>Showing <strong className="text-white">{filteredAccounts.length}</strong> of {topInstagramAccountsData.length} indexed accounts</span>
          </div>
          <span className="text-[11px] text-slate-500">Auto-calibrated: Oct 2026 cycle</span>
        </div>
      </div>

      {/* Rankings Leaderboard Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-16">
        {filteredAccounts.map((account) => {
          const isTop3 = account.rank <= 3;
          return (
            <div
              key={account.rank}
              className={`p-5 rounded-2xl bg-slate-900/80 border transition hover:-translate-y-0.5 hover:shadow-xl flex flex-col justify-between ${
                account.rank === 1
                  ? 'border-amber-400/50 shadow-amber-500/5'
                  : account.rank === 2
                  ? 'border-slate-300/50 shadow-slate-300/5'
                  : account.rank === 3
                  ? 'border-amber-700/50 shadow-amber-700/5'
                  : 'border-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div>
                {/* Card Top: Rank Badge & Country Flag */}
                <div className="flex items-center justify-between mb-3">
                  <span
                    className={`w-7 h-7 rounded-lg font-black text-xs flex items-center justify-center ${
                      account.rank === 1
                        ? 'bg-amber-400 text-black font-extrabold shadow-md shadow-amber-400/30'
                        : account.rank === 2
                        ? 'bg-slate-300 text-black font-extrabold shadow-md shadow-slate-300/30'
                        : account.rank === 3
                        ? 'bg-amber-700 text-white font-extrabold shadow-md shadow-amber-700/30'
                        : 'bg-slate-950 text-slate-400 border border-slate-800'
                    }`}
                  >
                    #{account.rank}
                  </span>

                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs">
                    <span>{account.flag}</span>
                    <span className="text-[10px] text-slate-400 font-medium truncate max-w-[90px]">{account.country}</span>
                  </div>
                </div>

                {/* Account Name & Verified Badge */}
                <div className="flex items-center gap-1.5 mb-1">
                  <h3 className="font-extrabold text-white text-sm truncate" title={account.name}>
                    {account.name}
                  </h3>
                  {account.verified && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-pink-400 shrink-0" title="Verified Instagram Account" />
                  )}
                </div>

                {/* Handle & Category */}
                <div className="flex items-center justify-between text-xs text-slate-400 mb-4">
                  <span className="font-mono text-slate-400 text-[11px] truncate">{account.handle}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-400 font-medium shrink-0">
                    {account.category}
                  </span>
                </div>
              </div>

              {/* Stats Footer */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">Followers</span>
                  <span className="font-extrabold text-pink-400 text-base">{account.followers}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">Posts</span>
                  <span className="font-semibold text-slate-300">{account.posts}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Explanatory Article & FAQ for SEO */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-10 text-slate-300 max-w-4xl mx-auto shadow-xl">
        <h2 className="text-xl sm:text-2xl font-black text-white mb-4">
          About the Official Top 100 Instagram Rankings
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed mb-6">
          The OVD Instagram Leaderboard tracks real-time follower counts for the most followed personalities, creators, and corporate pages globally. Synchronized every 12 hours directly against Meta CDN telemetry, this database offers verified benchmarks for social media analytics, creator discovery, and marketing intelligence.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <h4 className="font-bold text-white text-sm mb-1">Most Followed Individual</h4>
            <p className="text-slate-400">Cristiano Ronaldo (@cristiano) leads with over 640 Million global followers across sports and fitness.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <h4 className="font-bold text-white text-sm mb-1">12-Hour Sync Refresh</h4>
            <p className="text-slate-400">Our engine recalibrates counts twice daily to capture milestone shifts and follower growth trends.</p>
          </div>
        </div>
      </section>

    </div>
  );
}
