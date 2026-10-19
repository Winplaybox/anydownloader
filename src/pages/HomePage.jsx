import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import SupportedPlatforms from '../components/SupportedPlatforms.jsx';
import HowItWorks from '../components/HowItWorks.jsx';
import Faq from '../components/Faq.jsx';
import { topChannelsData } from '../data/topChannelsData.js';
import { Trophy, TrendingUp, Sparkles, Video, Music, FileText, Image as ImageIcon, ArrowRight } from 'lucide-react';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaData, setMediaData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('youtube');
  const [activeSubfeature, setActiveSubfeature] = useState('all');

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setUrl(text.trim());
    } catch (e) {
      setError('Please allow clipboard permission to paste directly.');
    }
  }

  const [activeResultTab, setActiveResultTab] = useState(null);

  async function fetchMedia(overrideUrl, preferredTab = null) {
    const validUrl = typeof overrideUrl === 'string' && overrideUrl.trim() ? overrideUrl.trim() : null;
    const targetUrl = validUrl || (typeof url === 'string' ? url.trim() : '');
    if (!targetUrl) {
      setError('Please enter a valid video, reel, or audio link.');
      return;
    }

    if (validUrl) setUrl(validUrl);
    if (preferredTab) setActiveResultTab(preferredTab);
    setLoading(true);
    setError('');
    setMediaData(null);

    // Target dedicated platform endpoint based on URL
    let endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/extract';
    const lower = targetUrl.toLowerCase();
    if (lower.includes('instagram.com')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/instagram/extract';
    } else if (lower.includes('facebook.com') || lower.includes('fb.watch')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/facebook/extract';
    } else if (lower.includes('youtube.com') || lower.includes('youtu.be')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/youtube/extract';
    } else if (lower.includes('tiktok.com')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/tiktok/extract';
    } else if (lower.includes('twitter.com') || lower.includes('x.com')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/twitter/extract';
    } else if (lower.includes('pinterest.com') || lower.includes('pin.it')) {
      endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/pinterest/extract';
    }

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      });

      const json = await res.json();
      if (json.success && json.data) {
        setMediaData(json.data);
      } else {
        setError(json.error || 'Could not extract media. Please check the URL.');
      }
    } catch (e) {
      setError('Network connection error. Ensure the Python engine is running.');
    } finally {
      setLoading(false);
    }
  }

  const top10 = topChannelsData.slice(0, 10);

  return (
    <div>
      {/* Universal Hero Downloader */}
      <HeroDownloader
        url={url}
        setUrl={setUrl}
        onFetch={fetchMedia}
        loading={loading}
        error={error}
        onPaste={handlePaste}
        activeCategory={activeCategory}
        onSelectCategory={setActiveCategory}
        activeSubfeature={activeSubfeature}
        onSelectSubfeature={setActiveSubfeature}
      />

      {/* Media Results Card */}
      {mediaData && (
        <MediaResultCard data={mediaData} />
      )}

      {/* AdSense Leaderboard Slot */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 mb-16">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Homepage Responsive Display Ad Unit ]</span>
          </div>
        </div>
      </div>

      {/* Featured Tool Suite Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 mb-20">
        <div className="text-center mb-10">
          <span className="px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-bold uppercase tracking-wider mb-3 inline-block">
            Specialized Tool Suite
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
            Explore Dedicated Multi-Media Tools
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-xl mx-auto">
            Choose from our precision tools designed for YouTube, Facebook, Instagram, and TikTok media.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <Link
            to="/youtube/youtube-video-downloader"
            className="p-6 rounded-3xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-rose-500/50 transition duration-300 group shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-rose-500 group-hover:text-white transition">
                <Video className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-1.5 group-hover:text-rose-400 transition">
                YouTube Video Downloader
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Download YouTube videos in pristine 1080p, 720p, and 4K resolution with crystal-clear audio.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-1.5 text-xs font-bold text-rose-400">
              <span>Open Tool</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </Link>

          <Link
            to="/youtube/youtube-mp3"
            className="p-6 rounded-3xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition duration-300 group shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-cyan-500 group-hover:text-white transition">
                <Music className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-1.5 group-hover:text-cyan-400 transition">
                YouTube to MP3 Converter
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Extract high-bitrate 320kbps and 192kbps MP3 audio tracks, podcasts, and speeches with zero quality loss.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-1.5 text-xs font-bold text-cyan-400">
              <span>Open Tool</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </Link>

          <Link
            to="/youtube/youtube-transcript"
            className="p-6 rounded-3xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-amber-500/50 transition duration-300 group shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-amber-500 group-hover:text-white transition">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-1.5 group-hover:text-amber-400 transition">
                YouTube Transcript Generator
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generate interactive timestamped transcripts with live search, copy-all, and .txt export options.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-1.5 text-xs font-bold text-amber-400">
              <span>Open Tool</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </Link>

          <Link
            to="/youtube/youtube-thumbnails"
            className="p-6 rounded-3xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-emerald-500/50 transition duration-300 group shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-emerald-500 group-hover:text-white transition">
                <ImageIcon className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base mb-1.5 group-hover:text-emerald-400 transition">
                YouTube Thumbnails (All Qualities)
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Download full resolution cover artwork in 1080p Maxres, 720p HQ, 480p SD, and 360p MQ sizes.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-1.5 text-xs font-bold text-emerald-400">
              <span>Open Tool</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </Link>

          <Link
            to="/youtube/top-100-youtube-channels"
            className="p-6 rounded-3xl bg-gradient-to-br from-slate-900 via-rose-950/20 to-slate-900 border border-rose-500/30 hover:border-rose-500 transition duration-300 group shadow-lg flex flex-col justify-between sm:col-span-2 lg:col-span-2"
          >
            <div>
              <div className="w-10 h-10 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-rose-500 group-hover:text-white transition">
                <Trophy className="w-5 h-5" />
              </div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-black text-white text-lg group-hover:text-rose-400 transition">
                  Top 100 Most Subscribed YouTube Channels in the World
                </h3>
                <span className="text-[10px] bg-rose-500 text-white font-extrabold px-2 py-0.5 rounded-full">
                  12H Sync
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed max-w-xl">
                Official ranking database by current subscriber count, recorded by OVD.winplaybox.in and refreshed every 12 hours. Filter by Country, Genre, and subscriber milestones.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-1.5 text-xs font-bold text-rose-400">
              <span>Explore Live Global Rankings</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
            </div>
          </Link>
        </div>
      </section>

      {/* Live Preview: Top 10 Channels Leaderboard */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 mb-20">
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[11px] font-bold">
                  Top 10 Preview
                </span>
                <span className="text-xs text-slate-400">&bull; Refreshed every 12 hours</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white">
                World's Most Subscribed YouTube Channels
              </h2>
            </div>

            <Link
              to="/youtube/top-100-youtube-channels"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white text-xs font-bold shadow-lg shadow-rose-600/25 transition self-start sm:self-auto cursor-pointer"
            >
              <span>View Full Top 100 Ranks</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {top10.map((ch) => (
              <div
                key={ch.rank}
                className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800/80 flex items-center gap-3 hover:border-slate-700 transition"
              >
                <div className={`w-7 h-7 rounded-lg font-black text-xs flex items-center justify-center shrink-0 ${
                  ch.rank === 1 ? 'bg-amber-400 text-black' : ch.rank === 2 ? 'bg-slate-300 text-black' : ch.rank === 3 ? 'bg-amber-700 text-white' : 'bg-slate-800 text-slate-300'
                }`}>
                  #{ch.rank}
                </div>
                <div className="min-w-0">
                  <h4 className="font-bold text-white text-xs truncate">{ch.name}</h4>
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                    <span className="text-rose-400 font-bold">{ch.subs}</span>
                    <span>&bull;</span>
                    <span>{ch.countryFlag}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SupportedPlatforms />
      <HowItWorks />
      <Faq />
    </div>
  );
}
