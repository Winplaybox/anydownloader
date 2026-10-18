import React, { useState } from 'react';
import { Search, TrendingUp, Award, Globe, Tag } from 'lucide-react';

export default function TopChannelsMegaMenu({ onSelectFilter, onClose }) {
  const [searchQuery, setSearchQuery] = useState('');

  const topCharts = [
    { label: 'Top 50 YouTube Channels By Subscribers', filter: { type: 'chart', value: 50 } },
    { label: 'Top 100 YouTube Channels By Subscribers', filter: { type: 'chart', value: 100 } },
    { label: 'Top 500 YouTube Channels By Subscribers', filter: { type: 'chart', value: 500 } },
    { label: 'All YouTube Channel Rankings', filter: { type: 'chart', value: 'all' }, noTrend: true }
  ];

  const countries = [
    { name: 'United States', flag: '🇺🇸' },
    { name: 'Australia', flag: '🇦🇺' },
    { name: 'United Kingdom', flag: '🇬🇧' },
    { name: 'Japan', flag: '🇯🇵' },
    { name: 'Canada', flag: '🇨🇦' },
    { name: 'Spain', flag: '🇪🇸' },
    { name: 'India', flag: '🇮🇳' },
    { name: 'France', flag: '🇫🇷' },
    { name: 'Brazil', flag: '🇧🇷' },
    { name: 'Turkey', flag: '🇹🇷' },
    { name: 'Germany', flag: '🇩🇪' },
    { name: 'Philippines', flag: '🇵🇭' }
  ];

  const categories = [
    'Autos & Vehicles',
    'Music',
    'Education',
    'News & Politics',
    'Entertainment',
    'Pets & Animals',
    'Food',
    'Sports',
    'Gaming',
    'Technology',
    'Lifestyle',
    'Travel'
  ];

  function handleSearchSubmit(e) {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSelectFilter({ type: 'search', value: searchQuery.trim() });
      if (onClose) onClose();
    }
  }

  function handleFilterClick(filter) {
    onSelectFilter(filter);
    if (onClose) onClose();
  }

  return (
    <div className="w-full max-w-5xl bg-slate-950/95 border border-slate-800 rounded-3xl p-6 shadow-2xl backdrop-blur-xl text-slate-200">
      {/* Top Search Bar */}
      <form onSubmit={handleSearchSubmit} className="mb-6">
        <div className="relative max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Find channel"
            className="w-full bg-slate-900 border border-slate-800 rounded-full pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition"
          />
        </div>
      </form>

      {/* 3 Mega-Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-xs">
        {/* Column 1: YouTube Top Charts */}
        <div>
          <h4 className="font-bold text-white text-sm mb-4 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-rose-500" />
            <span>YouTube Top Charts</span>
          </h4>
          <div className="space-y-2.5">
            {topCharts.map((chart, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick(chart.filter)}
                className="w-full text-left px-4 py-2.5 rounded-2xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white flex items-center gap-2.5 transition group"
              >
                {!chart.noTrend ? (
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0 group-hover:scale-110 transition" />
                ) : (
                  <Globe className="w-3.5 h-3.5 text-rose-400 shrink-0 group-hover:scale-110 transition" />
                )}
                <span className="font-medium text-[11px] leading-tight">{chart.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Column 2: Top 100 Channels by Country */}
        <div>
          <h4 className="font-bold text-white text-sm mb-4 flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-cyan-400" />
            <span>Top 100 Channels by Country</span>
          </h4>
          <div className="grid grid-cols-2 gap-x-3 gap-y-2">
            {countries.map((c, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick({ type: 'country', value: c.name })}
                className="text-left px-2 py-1.5 rounded-lg hover:bg-slate-900 text-slate-300 hover:text-white flex items-center gap-2 transition"
              >
                <span className="text-base">{c.flag}</span>
                <span className="text-[11px] font-medium truncate">{c.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Column 3: Top 100 Channels by Category */}
        <div>
          <h4 className="font-bold text-white text-sm mb-4 flex items-center gap-1.5">
            <Tag className="w-4 h-4 text-amber-400" />
            <span>Top 100 Channels by Category</span>
          </h4>
          <div className="grid grid-cols-2 gap-x-3 gap-y-2.5">
            {categories.map((cat, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick({ type: 'category', value: cat })}
                className="text-left px-2 py-1.5 rounded-lg hover:bg-slate-900 text-slate-300 hover:text-white text-[11px] font-medium transition truncate"
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
