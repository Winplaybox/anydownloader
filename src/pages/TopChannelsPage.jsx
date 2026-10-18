import React from 'react';
import { useSearchParams } from 'react-router-dom';
import TopChannelsSection from '../components/TopChannelsSection.jsx';
import SupportedPlatforms from '../components/SupportedPlatforms.jsx';
import { Trophy, TrendingUp, Globe, Sparkles, BarChart3, Users, Play, Clock } from 'lucide-react';

export default function TopChannelsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const countryParam = searchParams.get('country');
  const categoryParam = searchParams.get('category');
  const limitParam = searchParams.get('limit');
  const searchVal = searchParams.get('search');

  const activeFilter = React.useMemo(() => {
    if (countryParam) return { type: 'country', value: countryParam };
    if (categoryParam) return { type: 'category', value: categoryParam };
    if (limitParam) return { type: 'chart', value: limitParam === 'all' ? 100 : parseInt(limitParam) };
    if (searchVal) return { type: 'search', value: searchVal };
    return null;
  }, [countryParam, categoryParam, limitParam, searchVal]);

  function handleResetFilter() {
    setSearchParams({});
  }

  return (
    <div className="py-8">
      {/* Top Channels Section */}
      <TopChannelsSection
        activeFilter={activeFilter}
        onResetFilter={handleResetFilter}
      />

      {/* AdSense In-Article Display Ad Unit */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 mb-16">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Responsive Leaderboard Ad Unit ]</span>
          </div>
        </div>
      </div>

      {/* Deep Analytical Content & Methodology (High AdSense Value) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 mb-20 text-slate-300">
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xl">
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-4 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-rose-500" />
            <span>Ranking Methodology & Subscriber Analytics</span>
          </h2>

          <p className="text-sm text-slate-400 leading-relaxed mb-6">
            The <strong>Top 100 Most Subscribed YouTube Channels in the World</strong> index is continuously monitored, computed, and recorded by <strong className="text-rose-400">OVD.winplaybox.in</strong> with automated 12-hour synchronization cycles. The subscriber counts reflect public YouTube metric thresholds, filtered by verified creators, corporate media networks, and record labels.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-xs">
            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
              <Users className="w-5 h-5 text-rose-400 mb-2" />
              <h4 className="font-bold text-white mb-1">Subscriber Milestones</h4>
              <p className="text-slate-400">Tracking historic thresholds from 50M to 300M+ subscribers, including titans like MrBeast, T-Series, and Cocomelon.</p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
              <Globe className="w-5 h-5 text-cyan-400 mb-2" />
              <h4 className="font-bold text-white mb-1">Global Geographic Distribution</h4>
              <p className="text-slate-400">Comparative metrics across major digital markets: United States, India, Brazil, Japan, United Kingdom, and South Korea.</p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
              <Clock className="w-5 h-5 text-amber-400 mb-2" />
              <h4 className="font-bold text-white mb-1">12-Hour Refresh Interval</h4>
              <p className="text-slate-400">Data refreshes semi-daily to ensure accurate rankings, new entries, and channel movement tracking.</p>
            </div>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed">
            Note: All trademarks, channel names, and avatars belong to their respective creators and YouTube / Google LLC. Data is indexed for research, comparative analysis, and public informational purposes under fair use.
          </p>
        </div>
      </section>

      <SupportedPlatforms />
    </div>
  );
}
