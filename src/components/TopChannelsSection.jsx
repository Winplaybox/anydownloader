import React, { useState, useMemo } from 'react';
import { 
  Trophy, 
  Search, 
  Filter, 
  ExternalLink, 
  CheckCircle2, 
  RotateCcw,
  Clock, 
  Users, 
  Eye, 
  Video, 
  Sparkles 
} from 'lucide-react';
import { topChannelsData } from '../data/topChannelsData.js';

export default function TopChannelsSection({ activeFilter, onResetFilter }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [limit, setLimit] = useState(100);

  // Sync external filter when triggered from header mega menu
  React.useEffect(() => {
    if (activeFilter) {
      if (activeFilter.type === 'country') {
        setSelectedCountry(activeFilter.value);
        setSelectedCategory('All');
        setSearchTerm('');
      } else if (activeFilter.type === 'category') {
        setSelectedCategory(activeFilter.value);
        setSelectedCountry('All');
        setSearchTerm('');
      } else if (activeFilter.type === 'chart') {
        setLimit(activeFilter.value === 'all' ? 100 : activeFilter.value);
        setSelectedCountry('All');
        setSelectedCategory('All');
        setSearchTerm('');
      } else if (activeFilter.type === 'search') {
        setSearchTerm(activeFilter.value);
      }
    }
  }, [activeFilter]);

  const uniqueCountries = useMemo(() => {
    const list = Array.from(new Set(topChannelsData.map((c) => c.country))).sort();
    return ['All', ...list];
  }, []);

  const uniqueCategories = useMemo(() => {
    const list = Array.from(new Set(topChannelsData.map((c) => c.category))).sort();
    return ['All', ...list];
  }, []);

  const filteredChannels = useMemo(() => {
    return topChannelsData
      .filter((ch) => {
        const matchesSearch = 
          ch.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ch.handle.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCountry = selectedCountry === 'All' || ch.country === selectedCountry;
        const matchesCategory = selectedCategory === 'All' || ch.category === selectedCategory;
        return matchesSearch && matchesCountry && matchesCategory;
      })
      .slice(0, limit);
  }, [searchTerm, selectedCountry, selectedCategory, limit]);

  function handleReset() {
    setSearchTerm('');
    setSelectedCountry('All');
    setSelectedCategory('All');
    setLimit(100);
    if (onResetFilter) onResetFilter();
  }

  const isFiltered = searchTerm || selectedCountry !== 'All' || selectedCategory !== 'All' || limit !== 100;

  return (
    <section id="top-youtube-channels" className="py-20 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-rose-950/30 to-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 mb-10 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2.5 mb-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-bold uppercase tracking-wider">
              <Trophy className="w-3.5 h-3.5" />
              Official OVD Live Ranks
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 text-emerald-400 text-xs font-medium">
              <Clock className="w-3 h-3" />
              Refreshed every 12 hours
            </span>
          </div>

          <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight mb-3">
            Top 100 Most Subscribed YouTube Channels in the World
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
            This list ranks YouTube channels worldwide by current subscriber count, as recorded by <strong className="text-rose-400 font-semibold">OVD.winplaybox.in</strong> and refreshed every 12 hours. Discover the most popular creators, music labels, and media titans across countries and genres.
          </p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 mb-6 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-lg">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search channel name, handle or genre..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Country Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2">
            <span className="text-slate-400 text-[11px]">Country:</span>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
            >
              {uniqueCountries.map((c) => (
                <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>
              ))}
            </select>
          </div>

          {/* Category Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2">
            <span className="text-slate-400 text-[11px]">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
            >
              {uniqueCategories.map((cat) => (
                <option key={cat} value={cat} className="bg-slate-900 text-white">{cat}</option>
              ))}
            </select>
          </div>

          {/* Limit pill */}
          <div className="flex items-center p-1 bg-slate-950 border border-slate-800 rounded-xl">
            <button
              type="button"
              onClick={() => setLimit(50)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${limit === 50 ? 'bg-rose-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Top 50
            </button>
            <button
              type="button"
              onClick={() => setLimit(100)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${limit === 100 ? 'bg-rose-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Top 100
            </button>
          </div>

          {/* Reset button if filtered */}
          {isFiltered && (
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Results Count Banner */}
      <div className="flex items-center justify-between px-2 mb-4 text-xs text-slate-400">
        <span>Showing {filteredChannels.length} of {topChannelsData.length} indexed channels</span>
        <span className="font-mono-data text-[11px] text-slate-500">Source: OVD Intelligence Engine</span>
      </div>

      {/* Ranking Table Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase font-bold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-4 px-4 sm:px-6 w-16 text-center">Rank</th>
                <th className="py-4 px-4 sm:px-6">Channel</th>
                <th className="py-4 px-4 sm:px-6">Subscribers</th>
                <th className="py-4 px-4 sm:px-6 hidden md:table-cell">Total Views</th>
                <th className="py-4 px-4 sm:px-6 hidden lg:table-cell">Videos</th>
                <th className="py-4 px-4 sm:px-6 hidden sm:table-cell">Country</th>
                <th className="py-4 px-4 sm:px-6">Category</th>
                <th className="py-4 px-4 sm:px-6 text-right">Channel Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredChannels.map((ch) => (
                <tr key={ch.rank} className="hover:bg-slate-800/40 transition group">
                  {/* Rank */}
                  <td className="py-4 px-4 sm:px-6 text-center">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-xl font-black text-xs ${
                      ch.rank === 1 
                        ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/30' 
                        : ch.rank === 2 
                        ? 'bg-slate-300 text-black shadow-md' 
                        : ch.rank === 3 
                        ? 'bg-amber-700 text-white shadow-md' 
                        : 'bg-slate-800 text-slate-300 group-hover:text-white'
                    }`}>
                      {ch.rank}
                    </span>
                  </td>

                  {/* Channel Details */}
                  <td className="py-4 px-4 sm:px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 flex items-center justify-center font-extrabold text-white text-xs shrink-0 shadow-sm">
                        {ch.name.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-white text-sm group-hover:text-rose-400 transition truncate">
                            {ch.name}
                          </span>
                          {ch.verified && (
                            <CheckCircle2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-rose-400 shrink-0" />
                          )}
                        </div>
                        <span className="text-[11px] text-slate-500 font-mono-data truncate block">
                          {ch.handle}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Subscribers */}
                  <td className="py-4 px-4 sm:px-6 font-mono-data font-extrabold text-white">
                    <div className="flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-rose-500" />
                      <span>{ch.subs}</span>
                    </div>
                  </td>

                  {/* Total Views */}
                  <td className="py-4 px-4 sm:px-6 font-mono-data text-slate-400 hidden md:table-cell">
                    <div className="flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-slate-500" />
                      <span>{ch.views}</span>
                    </div>
                  </td>

                  {/* Videos Count */}
                  <td className="py-4 px-4 sm:px-6 font-mono-data text-slate-400 hidden lg:table-cell">
                    <div className="flex items-center gap-1.5">
                      <Video className="w-3.5 h-3.5 text-slate-500" />
                      <span>{ch.videos}</span>
                    </div>
                  </td>

                  {/* Country */}
                  <td className="py-4 px-4 sm:px-6 hidden sm:table-cell">
                    <span className="inline-flex items-center gap-1.5 text-xs text-slate-300">
                      <span>{ch.flag}</span>
                      <span className="truncate">{ch.country}</span>
                    </span>
                  </td>

                  {/* Category */}
                  <td className="py-4 px-4 sm:px-6">
                    <span className="inline-block px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700/60">
                      {ch.category}
                    </span>
                  </td>

                  {/* Link Action */}
                  <td className="py-4 px-4 sm:px-6 text-right">
                    <a
                      href={`https://youtube.com/${ch.handle}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-rose-600 text-slate-300 hover:text-white transition text-xs font-semibold cursor-pointer"
                    >
                      <span>Visit</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
