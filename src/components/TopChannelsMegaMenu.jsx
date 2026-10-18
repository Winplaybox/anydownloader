import React, { useState } from 'react';
import { Search, TrendingUp, Award, Globe, Tag, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function TopChannelsMegaMenu({ onSelectFilter, onClose }) {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

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
      navigate(`/youtube/top-100-youtube-channels?search=${encodeURIComponent(searchQuery.trim())}`);
      if (onSelectFilter) onSelectFilter({ type: 'search', value: searchQuery.trim() });
      if (onClose) onClose();
    }
  }

  function handleFilterClick(filter) {
    if (filter.type === 'country') {
      navigate(`/youtube/top-100-youtube-channels?country=${encodeURIComponent(filter.value)}`);
    } else if (filter.type === 'category') {
      navigate(`/youtube/top-100-youtube-channels?category=${encodeURIComponent(filter.value)}`);
    } else if (filter.type === 'chart') {
      navigate(`/youtube/top-100-youtube-channels?limit=${filter.value}`);
    } else {
      navigate('/youtube/top-100-youtube-channels');
    }
    if (onSelectFilter) onSelectFilter(filter);
    if (onClose) onClose();
  }

  return (
    <div className="w-full bg-slate-950/98 border border-slate-800 rounded-3xl p-5 sm:p-6 shadow-2xl backdrop-blur-2xl text-slate-200">
      {/* Top Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800/80">
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-sm">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Find channel (e.g. MrBeast, T-Series)..."
              className="w-full bg-slate-900/90 border border-slate-800 rounded-full pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition"
            />
          </div>
        </form>

        <button
          type="button"
          onClick={() => {
            navigate('/youtube/top-100-youtube-channels');
            if (onClose) onClose();
          }}
          className="text-xs font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1.5 transition self-end sm:self-auto cursor-pointer"
        >
          <span>View Full Top 100 Database &rarr;</span>
        </button>
      </div>

      {/* 3 Mega-Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 text-xs">
        {/* Column 1: YouTube Top Charts */}
        <div>
          <h4 className="font-bold text-white text-sm mb-3.5 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-rose-500" />
            <span>YouTube Top Charts</span>
          </h4>
          <div className="space-y-2">
            {topCharts.map((chart, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick(chart.filter)}
                className="w-full text-left px-3.5 py-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 hover:border-slate-700 text-slate-300 hover:text-white flex items-center gap-2.5 transition group cursor-pointer"
              >
                {!chart.noTrend ? (
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0 group-hover:scale-110 transition" />
                ) : (
                  <Globe className="w-3.5 h-3.5 text-rose-400 shrink-0 group-hover:scale-110 transition" />
                )}
                <span className="font-medium text-xs leading-snug">{chart.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Column 2: Top 100 Channels by Country */}
        <div>
          <h4 className="font-bold text-white text-sm mb-3.5 flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-cyan-400" />
            <span>Top 100 Channels by Country</span>
          </h4>
          <div className="grid grid-cols-2 gap-x-2 gap-y-1.5">
            {countries.map((c, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick({ type: 'country', value: c.name })}
                className="text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-900 text-slate-300 hover:text-white flex items-center gap-2 transition cursor-pointer group"
              >
                <span className="text-base shrink-0">{c.flag}</span>
                <span className="text-xs font-medium truncate group-hover:text-rose-400">{c.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Column 3: Top 100 Channels by Category */}
        <div>
          <h4 className="font-bold text-white text-sm mb-3.5 flex items-center gap-1.5">
            <Tag className="w-4 h-4 text-amber-400" />
            <span>Top Channels by Category</span>
          </h4>
          <div className="grid grid-cols-2 gap-x-2 gap-y-1.5">
            {categories.map((cat, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFilterClick({ type: 'category', value: cat })}
                className="text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-900 text-slate-300 hover:text-white transition cursor-pointer truncate hover:text-amber-300"
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
