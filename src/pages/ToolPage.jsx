import React, { useState } from 'react';
import HeroDownloader from '../components/HeroDownloader.jsx';
import MediaResultCard from '../components/MediaResultCard.jsx';
import SupportedPlatforms from '../components/SupportedPlatforms.jsx';
import { 
  CheckCircle2, 
  HelpCircle, 
  ShieldCheck, 
  Zap, 
  Sparkles, 
  ChevronDown, 
  ChevronUp,
  FileText,
  Video,
  Music,
  Download
} from 'lucide-react';

export default function ToolPage({ config = {} }) {
  const safeConfig = config || {};
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mediaData, setMediaData] = useState(null);
  const [openFaq, setOpenFaq] = useState(null);

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
      setError('Please enter a valid URL.');
      return;
    }

    if (validUrl) setUrl(validUrl);
    if (preferredTab) setActiveResultTab(preferredTab);
    setLoading(true);
    setError('');
    setMediaData(null);

    // Select dedicated platform endpoint for clean architectural isolation
    let endpoint = 'https://anydownloader-backend-vvbj.onrender.com/api/extract';
    const pKey = (safeConfig.platform || '').toLowerCase();
    const fKey = (safeConfig.subfeature || '').toLowerCase();
    if (pKey && ['instagram', 'facebook', 'youtube', 'tiktok', 'twitter'].includes(pKey)) {
      endpoint = fKey 
        ? `https://anydownloader-backend-vvbj.onrender.com/api/${pKey}/${fKey}`
        : `https://anydownloader-backend-vvbj.onrender.com/api/${pKey}/extract`;
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
      setError('Network connection error. Please ensure the Python extraction engine is running.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="py-6">
      {/* Hero Downloader with Pre-configured Category & Subfeature */}
      <HeroDownloader
        url={url}
        setUrl={setUrl}
        onFetch={fetchMedia}
        loading={loading}
        error={error}
        onPaste={handlePaste}
        activeCategory={safeConfig.category || 'youtube'}
        activeSubfeature={safeConfig.subfeature || 'all'}
      />

      {/* Media Result Card (Shows formats, thumbnails, transcript, subtitles) */}
      {mediaData && (
        <MediaResultCard 
          data={mediaData} 
          onSelectVideo={(vUrl) => fetchMedia(vUrl)}
          initialTab={
            safeConfig.subfeature === 'mp3' ? 'audio' :
            safeConfig.subfeature === 'transcript' ? 'transcript' :
            safeConfig.subfeature === 'subtitles' ? 'subtitles' :
            safeConfig.subfeature === 'thumbnails' ? 'thumbnails' : 'video'
          }
        />
      )}

      {/* AdSense Responsive Ad Placeholder Slot 1 */}
      <div className="max-w-4xl mx-auto px-4 mb-16">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Advertisement
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Responsive Display Ad Unit ]</span>
          </div>
        </div>
      </div>

      {/* Rich SEO Content Guide & Article (Required for Google AdSense Approval) */}
      <section className="max-w-4xl mx-auto px-4 mb-20 text-slate-300">
        <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xl">
          
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-4">
            {safeConfig.guideTitle || `How to Use the ${safeConfig.title}`}
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed mb-8">
            {safeConfig.guideIntro || `OVD provides the fastest and most secure way to download media directly to your PC, Mac, iPhone, or Android device without installing third-party software.`}
          </p>

          {/* Step-by-Step Guide */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <span className={`w-7 h-7 rounded-lg font-bold text-xs flex items-center justify-center mb-3 border ${
                  safeConfig.category === 'facebook'
                    ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                    : safeConfig.category === 'instagram'
                    ? 'bg-pink-500/15 text-pink-400 border-pink-500/30'
                    : safeConfig.category === 'tiktok'
                    ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
                    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                }`}>1</span>
                <h4 className="font-bold text-white text-sm mb-1">Copy Link</h4>
                <p className="text-xs text-slate-400">Copy the URL of the video, shorts, reel, or audio track from your app or browser.</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <span className={`w-7 h-7 rounded-lg font-bold text-xs flex items-center justify-center mb-3 border ${
                  safeConfig.category === 'facebook'
                    ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                    : safeConfig.category === 'instagram'
                    ? 'bg-pink-500/15 text-pink-400 border-pink-500/30'
                    : safeConfig.category === 'tiktok'
                    ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
                    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                }`}>2</span>
                <h4 className="font-bold text-white text-sm mb-1">Paste & Fetch</h4>
                <p className="text-xs text-slate-400">Paste the URL into the input field above and click "Fetch Media" to extract stream options.</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <span className={`w-7 h-7 rounded-lg font-bold text-xs flex items-center justify-center mb-3 border ${
                  safeConfig.category === 'facebook'
                    ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                    : safeConfig.category === 'instagram'
                    ? 'bg-pink-500/15 text-pink-400 border-pink-500/30'
                    : safeConfig.category === 'tiktok'
                    ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
                    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                }`}>3</span>
                <h4 className="font-bold text-white text-sm mb-1">Download & Save</h4>
                <p className="text-xs text-slate-400">Select your preferred resolution (1080p, 720p, MP3, Transcript, or Thumbnails) and download immediately.</p>
              </div>
            </div>
          </div>

          {/* Deep Content Sections */}
          {safeConfig.sections && safeConfig.sections.map((sec, idx) => (
            <div key={idx} className="mb-8 last:mb-0">
              <h3 className="text-lg sm:text-xl font-bold text-white mb-2">{sec.heading}</h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">{sec.body}</p>
            </div>
          ))}

          {/* Features Highlights */}
          <div className="mt-8 pt-8 border-t border-slate-800/80">
            <h3 className="text-base font-bold text-white mb-4">Key Benefits of OVD</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Zero registration or account required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Original audio and 1080p full resolution</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>No watermarks on supported platforms</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Unlimited free downloads every day</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Tool FAQ Accordion */}
      {safeConfig.faqs && safeConfig.faqs.length > 0 && (
        <section className="max-w-4xl mx-auto px-4 mb-20">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-black text-white">Frequently Asked Questions</h2>
            <p className="text-xs text-slate-400 mt-1">Everything you need to know about using {safeConfig.title}</p>
          </div>

          <div className="space-y-3">
            {safeConfig.faqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden transition"
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaq(isOpen ? null : idx)}
                    className="w-full text-left p-4 sm:p-5 flex items-center justify-between gap-4 text-xs sm:text-sm font-bold text-white cursor-pointer hover:bg-slate-850"
                  >
                    <span>{faq.q}</span>
                    {isOpen ? <ChevronUp className="w-4 h-4 text-rose-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />}
                  </button>
                  {isOpen && (
                    <div className="px-4 sm:px-5 pb-5 text-xs text-slate-400 leading-relaxed border-t border-slate-800/60 pt-3">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* AdSense In-Feed / Bottom Ad Unit */}
      <div className="max-w-4xl mx-auto px-4 mb-16">
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 text-center">
          <span className="text-[10px] uppercase font-bold text-slate-600 tracking-widest block mb-1">
            Sponsored Content
          </span>
          <div className="h-20 sm:h-24 bg-slate-950/60 rounded-xl flex items-center justify-center border border-slate-800/40 text-slate-600 text-xs font-mono">
            <span>[ Bottom Matched Content Ad Unit ]</span>
          </div>
        </div>
      </div>

      <SupportedPlatforms />
    </div>
  );
}
