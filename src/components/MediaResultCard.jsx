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
  ShieldCheck 
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

  function handleDirectDownload(format) {
    if (!format.url) return;
    // Download via direct link or proxy stream
    const link = document.createElement('a');
    link.href = format.url;
    link.download = format.download_name || 'video.mp4';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <div className="max-w-4xl mx-auto px-4 mb-20 animate-in fade-in slide-in-from-bottom-6 duration-300">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
        {/* Media Header Preview */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start pb-6 border-b border-slate-800">
          {/* Thumbnail */}
          <div className="md:col-span-4 relative rounded-2xl overflow-hidden aspect-video bg-slate-800 border border-slate-700/60 shadow-md">
            {data.thumbnail ? (
              <img
                src={data.thumbnail}
                alt={data.title}
                className="w-full h-full object-cover"
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
          <div className="md:col-span-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {data.platform || 'Media Stream'}
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <User className="w-3 h-3" />
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
                <span className="text-slate-400 flex items-center gap-1">
                  <Eye className="w-3.5 h-3.5" />
                  {data.views} views
                </span>
              )}

              <button
                onClick={copyUrl}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied Link' : 'Copy Link'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 my-6 p-1 rounded-xl bg-slate-950 border border-slate-800 w-fit">
          <button
            onClick={() => setActiveTab('video')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              activeTab === 'video'
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Video (MP4)</span>
          </button>

          <button
            onClick={() => setActiveTab('audio')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
              activeTab === 'audio'
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Music className="w-3.5 h-3.5" />
            <span>Audio (MP3 / M4A)</span>
          </button>
        </div>

        {/* Video Quality List */}
        {activeTab === 'video' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Available Video Qualities</span>
              <span>Format: MP4</span>
            </div>

            {data.video_formats && data.video_formats.length > 0 ? (
              data.video_formats.map((fmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 p-3.5 sm:p-4 rounded-2xl flex items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-xs">
                      {fmt.height >= 720 ? 'HD' : 'SD'}
                    </div>
                    <div>
                      <div className="font-bold text-white text-sm">
                        {fmt.quality}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono-data">
                        Size: {fmt.size} &bull; {fmt.ext?.toUpperCase() || 'MP4'}
                      </div>
                    </div>
                  </div>

                  <a
                    href={fmt.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    download={fmt.download_name}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition cursor-pointer"
                  >
                    <ArrowDownToLine className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </a>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                No standard video tracks found. Check original URL.
              </div>
            )}
          </div>
        )}

        {/* Audio Quality List */}
        {activeTab === 'audio' && (
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Available Audio Streams</span>
              <span>High Fidelity</span>
            </div>

            {data.audio_formats && data.audio_formats.length > 0 ? (
              data.audio_formats.map((afmt, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 p-3.5 sm:p-4 rounded-2xl flex items-center justify-between gap-4 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-xs">
                      MP3
                    </div>
                    <div>
                      <div className="font-bold text-white text-sm">
                        {afmt.quality}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono-data">
                        Format: {afmt.format} &bull; Approx: {afmt.size}
                      </div>
                    </div>
                  </div>

                  <a
                    href={afmt.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    download={afmt.download_name}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-md shadow-amber-600/20 transition cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Audio</span>
                  </a>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                No audio-only stream available.
              </div>
            )}
          </div>
        )}

        {/* Guarantee Banner */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <ShieldCheck className="w-4 h-4" />
            <span>Fast, secure direct stream. No data stored on server.</span>
          </span>
          <span>100% Free</span>
        </div>
      </div>
    </div>
  );
}
