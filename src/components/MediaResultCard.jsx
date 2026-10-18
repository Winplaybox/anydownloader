import React, { useState } from 'react';
import { 
  Download, 
  Video, 
  Music, 
  Check, 
  Copy, 
  Clock, 
  User, 
  Eye, 
  ArrowDownToLine, 
  ExternalLink,
  Volume2,
  VolumeX,
  Sparkles
} from 'lucide-react';

export default function MediaResultCard({ data }) {
  const [activeTab, setActiveTab] = useState('video');
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  function copyUrl() {
    navigator.clipboard.writeText(data.original_url || window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="max-w-4xl mx-auto px-4 mb-20 animate-in fade-in slide-in-from-bottom-6 duration-300">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
        {/* Media Header Preview */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start pb-6 border-b border-slate-800">
          {/* Thumbnail */}
          <div className="md:col-span-4 relative rounded-2xl overflow-hidden aspect-video bg-slate-800 border border-slate-700/60 shadow-md group">
            {data.thumbnail ? (
              <img
                src={data.thumbnail}
                alt={data.title}
                className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-600">
                <Video className="w-10 h-10" />
              </div>
            )}
            {data.duration && (
              <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-[10px] font-mono-data font-bold text-white flex items-center gap-1">
                <Clock className="w-3 h-3 text-rose-400" />
                <span>{data.duration}</span>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="md:col-span-8 flex flex-col justify-between h-full">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {data.platform || 'Media Stream'}
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1 font-medium">
                  <User className="w-3 h-3 text-slate-500" />
                  {data.uploader}
                </span>
              </div>

              <h2 className="text-lg sm:text-xl font-bold text-white leading-snug line-clamp-2 mb-3">
                {data.title}
              </h2>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
              {data.views && (
                <span className="text-slate-400 flex items-center gap-1 font-mono-data">
                  <Eye className="w-3.5 h-3.5 text-slate-500" />
                  {data.views} views
                </span>
              )}

              <button
                type="button"
                onClick={copyUrl}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Share Link'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 my-6 p-1 rounded-2xl bg-slate-950 border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('video')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'video'
                ? 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Video Formats (MP4)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('audio')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'audio'
                ? 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Music className="w-4 h-4" />
            <span>Audio Tracks (MP3 / M4A)</span>
          </button>
        </div>

        {/* Video Quality List */}
        {activeTab === 'video' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between px-1">
              <span>Resolution & Quality</span>
              <span>Direct Fast Download</span>
            </div>

            {data.video_formats && data.video_formats.length > 0 ? (
              data.video_formats.map((fmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700/90 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-rose-500/10 to-amber-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center font-black text-xs shrink-0">
                      {fmt.height >= 720 ? 'HD' : 'SD'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-white text-sm">
                          {fmt.quality}
                        </span>
                        {fmt.has_audio ? (
                          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            <Volume2 className="w-3 h-3" /> Audio Included
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 bg-slate-800/60 px-1.5 py-0.5 rounded border border-slate-700">
                            Video Track
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 font-mono-data mt-0.5">
                        Format: {fmt.ext?.toUpperCase() || 'MP4'} &bull; Size: {fmt.size}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <a
                      href={fmt.stream_url || fmt.url}
                      download={fmt.download_name}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white text-xs font-bold shadow-lg shadow-rose-600/20 transition cursor-pointer"
                    >
                      <ArrowDownToLine className="w-4 h-4" />
                      <span>Download MP4</span>
                    </a>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-xs text-slate-400 bg-slate-950/40 rounded-2xl border border-slate-800/60">
                No video tracks detected. Please check the provided link.
              </div>
            )}
          </div>
        )}

        {/* Audio Quality List */}
        {activeTab === 'audio' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between px-1">
              <span>Bitrate & Audio Tier</span>
              <span>Audio Download</span>
            </div>

            {data.audio_formats && data.audio_formats.length > 0 ? (
              data.audio_formats.map((fmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700/90 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-500/10 to-blue-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center font-black text-xs shrink-0">
                      {fmt.format || 'MP3'}
                    </div>
                    <div>
                      <div className="font-extrabold text-white text-sm">
                        {fmt.quality}
                      </div>
                      <div className="text-xs text-slate-400 font-mono-data mt-0.5">
                        Audio format: {fmt.format} &bull; Approx. Size: {fmt.size}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <a
                      href={fmt.stream_url || fmt.url}
                      download={fmt.download_name}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-600/20 transition cursor-pointer"
                    >
                      <ArrowDownToLine className="w-4 h-4" />
                      <span>Download {fmt.format}</span>
                    </a>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-xs text-slate-400 bg-slate-950/40 rounded-2xl border border-slate-800/60">
                No audio tracks detected.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
