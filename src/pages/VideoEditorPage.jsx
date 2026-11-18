import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Upload, Wand2, Mic, Captions, Play, Pause, Loader2, CheckCircle2, AlertCircle, Download, Copy, Check,
  Film, FileText, RotateCcw, Sparkles, Clock, ChevronDown, Video, Music2, Type, Crown
} from 'lucide-react';
import UserAccountBar from '../components/UserAccountBar';
import PricingModal from '../components/PricingModal';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';
const API = `${BACKEND_BASE}/api/editor`;
const JOB_KEY = 'ovd_editor_job';

const EXAMPLE_BRIEF = `I want to upload this on YouTube so it can go viral and trend.
I want title, description and tags for YouTube for my [Channel Name] channel.
All links value is [Your Link]
Include in description:
- Topics Covered in this Video (according to the video)
- Expanded Keywords 20-30 (according to the video)
- Queries: 20-30 short search queries (according to the video)
- Disclaimer`;

const STAGE_ORDER = ['queued', 'analyzing', 'transcribing', 'scripting', 'voiceover', 'captions', 'rendering', 'metadata', 'done'];
const STAGE_LABEL = {
  queued: 'Waiting in queue', analyzing: 'Watching your video', transcribing: 'Listening to the audio',
  scripting: 'Writing the script', voiceover: 'Recording the voiceover', captions: 'Timing the captions',
  rendering: 'Rendering the video', metadata: 'Writing title, description & tags', done: 'Done',
};

function fmtMB(bytes) { return `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
function fmtSec(s) { const m = Math.floor(s / 60); return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`; }

async function apiJson(path, opts) {
  const r = await fetch(`${API}${path}`, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok || data.ok === false) {
    const err = new Error(data?.error?.message || `Request failed (${r.status})`);
    err.code = data?.error?.code; err.quota = data?.error?.quota;
    throw err;
  }
  return data;
}

function CopyButton({ text, label = 'Copy' }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button" onClick={() => { navigator.clipboard?.writeText(text || ''); setDone(true); setTimeout(() => setDone(false), 1500); }}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)]">
      {done ? <Check className="w-3.5 h-3.5 text-[var(--positive)]" /> : <Copy className="w-3.5 h-3.5" />}
      {done ? 'Copied' : label}
    </button>
  );
}

function Section({ step, icon: Icon, title, children, right }) {
  return (
    <section className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-full bg-[var(--primary)] text-[var(--on-primary)] text-xs font-black flex items-center justify-center">{step}</span>
          <Icon className="w-5 h-5 text-[var(--accent)]" />
          <h2 className="text-base sm:text-lg font-black text-[var(--text)]">{title}</h2>
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

function StylePreview({ style, accent }) {
  const p = style.preview;
  if (!p) return <div className="h-full flex items-center justify-center text-[10px] font-semibold text-white/60">voice only</div>;
  const base = { fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 900, letterSpacing: '-0.01em' };
  const stroke = p.outline ? { WebkitTextStroke: '1.2px #000', paintOrder: 'stroke fill', textShadow: '0 2px 0 rgba(0,0,0,.5)' } : {};
  if (style.id === 'single') {
    return <div className="h-full flex items-end justify-center pb-5"><span style={{ ...base, ...stroke, fontSize: 22, color: accent }}>HAADSA</span></div>;
  }
  if (style.id === 'minimal') {
    return <div className="h-full flex items-end justify-center pb-3 px-2 text-center"><span style={{ fontWeight: 700, fontSize: 9, color: '#fff', textShadow: '0 1px 3px #000' }}>Raat ko road par achanak haadsa ho gaya</span></div>;
  }
  if (style.id === 'box') {
    return <div className="h-full flex items-end justify-center pb-5"><span style={{ ...base, fontSize: 11, background: '#000', color: '#fff', padding: '3px 5px', borderRadius: 2 }}>RAAT KO <span style={{ color: accent }}>ROAD</span> PAR</span></div>;
  }
  if (style.id === 'karaoke') {
    return <div className="h-full flex items-end justify-center pb-5"><span style={{ ...base, ...stroke, fontSize: 12 }}><span style={{ color: accent, whiteSpace: 'pre' }}>RAAT KO RO</span><span style={{ color: '#fff', whiteSpace: 'pre' }}>AD PAR</span></span></div>;
  }
  return <div className="h-full flex items-end justify-center pb-5"><span style={{ ...base, ...stroke, fontSize: 13, color: '#fff' }}>RAAT KO <span style={{ color: accent, display: 'inline-block', transform: 'scale(1.12)', margin: '0 4px' }}>ROAD</span> PAR</span></div>;
}

export default function VideoEditorPage() {
  const [opts, setOpts] = useState(null);
  const [optsError, setOptsError] = useState('');
  const [quota, setQuota] = useState(null);

  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState('');
  const [fileDur, setFileDur] = useState(0);
  const [fileError, setFileError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const [brief, setBrief] = useState('');
  const [channel, setChannel] = useState('');
  const [showScript, setShowScript] = useState(false);
  const [ownScript, setOwnScript] = useState('');
  const [language, setLanguage] = useState('hi');
  const [mode, setMode] = useState('ai_mix');
  const [voice, setVoice] = useState('hm_omega');
  const [captionStyle, setCaptionStyle] = useState('pop');
  const [captionScript, setCaptionScript] = useState('roman');
  const [accent, setAccent] = useState('#FFE500');
  const [format, setFormat] = useState('vertical');
  const [overlays, setOverlays] = useState(true);
  const navigate = useNavigate();
  const [paymentSuccess, setPaymentSuccess] = useState(() => {
    return typeof window !== 'undefined' && window.location.search.includes('payment=success');
  });
  const [resolution, setResolution] = useState(480);
  const [session, setSession] = useState(null);
  const [showPricingModal, setShowPricingModal] = useState(false);

  const [uploadPct, setUploadPct] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [job, setJob] = useState(null);
  const [playing, setPlaying] = useState('');
  const audioRef = useRef(null);
  const inputRef = useRef(null);

  // ---- load options, session + resume an unfinished job ----------------------------------------
  useEffect(() => {
    apiJson('/options').then((d) => { setOpts(d); setQuota(d.quota); }).catch((e) => setOptsError(e.message));

    const token = localStorage.getItem('wpb_token');
    const guestId = localStorage.getItem('wpb_guest_id');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (guestId) headers['x-guest-id'] = guestId;

    fetch(`${BACKEND_BASE}/api/auth/session`, { credentials: 'include', headers })
      .then((r) => r.json())
      .then((d) => {
        const iden = d.identity || d.session;
        if (d.ok && iden) {
          setSession(iden);
          if (iden.guest_id) localStorage.setItem('wpb_guest_id', iden.guest_id);
          const maxR = iden.max_resolution || 480;
          setResolution(maxR <= 480 ? 480 : maxR);
        }
      })
      .catch(console.error);

    const saved = typeof window !== 'undefined' ? localStorage.getItem(JOB_KEY) : null;
    if (saved) apiJson(`/jobs/${saved}`).then((d) => setJob(d.job)).catch(() => localStorage.removeItem(JOB_KEY));
  }, []);

  // ---- poll job ---------------------------------------------------------------------------
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed') return undefined;
    const t = setInterval(() => {
      apiJson(`/jobs/${job.id}`).then((d) => {
        setJob(d.job);
        if (d.job.status === 'done' || d.job.status === 'failed') apiJson('/quota').then((q) => setQuota(q.quota)).catch(() => {});
      }).catch(() => {});
    }, 2500);
    return () => clearInterval(t);
  }, [job]);

  const voices = useMemo(() => {
    if (!opts) return [];
    const fam = language.startsWith('en') ? ['en-in', 'en-us', 'en-gb'] : [language];
    return opts.voices.filter((v) => fam.includes(v.lang))
      .sort((a, b) => (a.lang !== language) - (b.lang !== language) || (a.engine !== 'kokoro') - (b.engine !== 'kokoro'));
  }, [opts, language]);
  const langInfo = opts?.languages.find((l) => l.id === language);

  useEffect(() => {
    if (voices.length && !voices.some((v) => v.id === voice)) setVoice(voices[0].id);
  }, [voices, voice]);
  useEffect(() => { if (langInfo && !langInfo.indic) setCaptionScript('native'); }, [langInfo]);

  // ---- file handling -------------------------------------------------------------------------
  const pickFile = useCallback((f) => {
    setFileError('');
    if (!f) return;
    if (!f.type.startsWith('video/') && !/\.(mp4|mov|m4v|webm|mkv|3gp|avi)$/i.test(f.name)) { setFileError('Please choose a video file.'); return; }
    const maxMb = opts?.limits?.max_upload_mb || 100;
    if (f.size > maxMb * 1024 * 1024) { setFileError(`Video must be under ${maxMb} MB (yours is ${fmtMB(f.size)}).`); return; }
    if (fileUrl) URL.revokeObjectURL(fileUrl);
    setFile(f); setFileUrl(URL.createObjectURL(f)); setFileDur(0);
  }, [opts, fileUrl]);

  function onMeta(e) {
    const d = e.currentTarget.duration || 0;
    setFileDur(d);
    const max = opts?.limits?.max_seconds || 180;
    if (d > max + 0.5) setFileError(`Video is ${Math.round(d)}s long; the limit is ${max}s. Trim it first.`);
  }

  function togglePreview(id) {
    const a = audioRef.current;
    if (!a) return;
    if (playing === id) { a.pause(); setPlaying(''); return; }
    a.src = `${API}/voice-preview?voice=${encodeURIComponent(id)}`;
    a.play().then(() => setPlaying(id)).catch(() => setPlaying(''));
  }

  // ---- submit -----------------------------------------------------------------------------------
  function submit() {
    if (!file || fileError) return;
    setSubmitting(true); setSubmitError(''); setUploadPct(0);
    const briefToSend = channel.trim() ? brief.replace(/\[Channel Name\]/gi, channel.trim()) : brief;
    const fd = new FormData();
    fd.append('file', file);
    Object.entries({
      language, mode, voice, caption_style: captionStyle, caption_script: captionScript, accent, format,
      resolution: String(resolution),
      overlays: overlays ? '1' : '0', brief: briefToSend, channel, script: showScript ? ownScript : '',
    }).forEach(([k, v]) => fd.append(k, v));
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API}/jobs`);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) setUploadPct(Math.round((e.loaded / e.total) * 100)); };
    xhr.onload = () => {
      setSubmitting(false);
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch { /* ignore */ }
      if (xhr.status === 202 && data.ok) {
        setJob(data.job); setQuota(data.quota);
        localStorage.setItem(JOB_KEY, data.job.id);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        setSubmitError(data?.error?.message || `Upload failed (${xhr.status}).`);
        if (data?.error?.quota) setQuota(data.error.quota);
      }
    };
    xhr.onerror = () => { setSubmitting(false); setSubmitError('Connection lost while uploading. Please try again.'); };
    xhr.send(fd);
  }

  function reset() {
    localStorage.removeItem(JOB_KEY);
    setJob(null); setSubmitError(''); setUploadPct(0);
  }

  const outOfQuota = quota && quota.remaining !== null && quota.remaining <= 0;

  const quote = useMemo(() => {
    // 1. Resolution Cost
    let resCost = 1;
    let resLabel = `${resolution}p SD Render`;
    if (resolution <= 480) { resCost = 1; resLabel = '480p SD Render (Free)'; }
    else if (resolution <= 720) { resCost = 1; resLabel = '720p HD Render'; }
    else if (resolution <= 1080) { resCost = 1; resLabel = '1080p FHD Render'; }
    else if (resolution <= 1440) { resCost = 2; resLabel = '2K QHD (1440p) Render'; }
    else if (resolution <= 1800) { resCost = 2; resLabel = '3K Ultra (1800p) Render'; }
    else if (resolution <= 2160) { resCost = 3; resLabel = '4K Cinema UHD Render'; }
    else { resCost = 5; resLabel = '8K Ultra Studio Render'; }

    // 2. Voiceover Engine
    const isAiVoice = mode !== 'original';
    const voiceCost = isAiVoice ? 1 : 0;
    const voiceLabel = isAiVoice ? `AI Neural Voice (${voice || 'Selected'})` : 'Original Video Audio';

    // 3. AI Scriptwriting vs User Custom Script
    const hasCustomScript = Boolean(showScript && ownScript && ownScript.trim());
    const isAiScript = isAiVoice && !hasCustomScript && Boolean(brief && brief.trim());
    const scriptCost = isAiScript ? 1 : 0;
    const scriptLabel = hasCustomScript
      ? 'Custom User Script'
      : isAiScript
      ? (brief.length > 250 ? 'Longform AI Viral Script' : 'AI Auto-Script from Brief')
      : 'Standard Script';

    // 4. Animated Captions Style
    const hasCaptions = captionStyle && captionStyle !== 'none';
    const captionCost = hasCaptions ? 1 : 0;
    const captionLabel = hasCaptions ? `Word-Synced Captions (${captionStyle})` : 'No Captions';

    // 5. Overlays (Hook title + CTA)
    const overlayCost = overlays ? 1 : 0;
    const overlayLabel = overlays ? 'Viral Hook Title + End CTA' : 'No Hook/CTA Overlays';

    const totalCost = resCost + voiceCost + scriptCost + captionCost + overlayCost;
    const userCredits = session?.credits ?? (quota?.remaining != null ? quota.remaining : 2);
    const canAfford = userCredits >= totalCost;
    const maxAllowedRes = session?.max_resolution || 480;
    const resAllowed = resolution <= maxAllowedRes;

    return {
      totalCost,
      userCredits,
      canAfford,
      resAllowed,
      maxAllowedRes,
      items: [
        { name: resLabel, cost: resCost, active: true },
        { name: voiceLabel, cost: voiceCost, active: isAiVoice },
        { name: scriptLabel, cost: scriptCost, active: isAiScript },
        { name: captionLabel, cost: captionCost, active: hasCaptions },
        { name: overlayLabel, cost: overlayCost, active: overlays },
      ]
    };
  }, [resolution, mode, voice, showScript, ownScript, brief, captionStyle, overlays, session, quota]);

  const canSubmit = file && !fileError && !submitting && !outOfQuota && (mode === 'original' || voice) && quote.canAfford && quote.resAllowed;

  // ===================================================================================================
  return (
    <div className="py-8 sm:py-12 max-w-5xl mx-auto px-4 sm:px-6">
      <audio ref={audioRef} onEnded={() => setPlaying('')} className="hidden" />

      {paymentSuccess && (
        <div className="mb-6 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-xs sm:text-sm flex items-center justify-between gap-3 shadow-md animate-in fade-in">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <span className="font-black block text-[var(--text)]">🎉 Payment Successful! Plan Entitlements Activated!</span>
              <span className="text-[var(--text-muted)] text-xs">
                Your credits and high-resolution export quality are now unlocked and ready to use.
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setPaymentSuccess(false)}
            className="text-[var(--text-muted)] hover:text-[var(--text)] text-xs font-bold px-2 py-1 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      <UserAccountBar
        session={session}
        onSessionUpdate={(s) => setSession(s)}
      />

      <div className="mb-6 sm:mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="px-2.5 py-0.5 rounded-md bg-[var(--accent-bg)] text-[var(--accent)] border border-[var(--accent)]/30 text-xs font-semibold uppercase tracking-wider">New · Free</span>
          {quota && (
            <span className={`px-2.5 py-0.5 rounded-md text-xs font-semibold border ${outOfQuota ? 'bg-[var(--negative-bg)] text-[var(--negative)] border-[var(--negative)]/30' : 'bg-[var(--positive-bg)] text-[var(--positive)] border-[var(--positive)]/30'}`}>
              {quota.unlimited ? 'Unlimited (admin)' : `${quota.remaining} of ${quota.limit} free edits left today`}
            </span>
          )}
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight mb-2">AI Video Editor</h1>
        <p className="text-sm text-[var(--text-muted)] max-w-2xl leading-relaxed">
          Upload a clip, tell us what you need. We write the script, add a natural AI voiceover, burn in animated captions,
          master the audio, and give you the title, description and tags ready to post on YouTube Shorts, Reels or TikTok.
        </p>
      </div>

      {optsError && (
        <div className="mb-6 p-4 rounded-xl border border-[var(--negative)]/30 bg-[var(--negative-bg)] text-[var(--negative)] text-sm flex gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" /> Editor is waking up or unavailable ({optsError}). Refresh in a minute.
        </div>
      )}

      {job ? <JobView job={job} onReset={reset} onOpenPricing={() => navigate('/pricing')} /> : (
        <div className="space-y-5">
          {/* 1. Upload */}
          <Section step={1} icon={Upload} title="Upload your video">
            {!file ? (
              <button type="button" onClick={() => inputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); pickFile(e.dataTransfer.files?.[0]); }}
                className={`w-full border-2 border-dashed rounded-xl py-10 px-4 flex flex-col items-center gap-2 transition-colors ${dragOver ? 'border-[var(--accent)] bg-[var(--accent-bg)]' : 'border-[var(--border)] hover:bg-[var(--bg-alt)]'}`}>
                <Video className="w-8 h-8 text-[var(--text-muted)]" />
                <span className="text-sm font-bold text-[var(--text)]">Drop a video here or tap to choose</span>
                <span className="text-xs text-[var(--text-muted)]">MP4 / MOV / WEBM · up to {opts?.limits?.max_upload_mb || 100} MB · max {opts?.limits?.max_seconds || 180} seconds</span>
              </button>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 items-start">
                <video src={fileUrl} onLoadedMetadata={onMeta} controls playsInline className="w-full sm:w-48 max-h-80 rounded-lg bg-black" />
                <div className="flex-1 min-w-0 space-y-2">
                  <p className="text-sm font-bold text-[var(--text)] break-all">{file.name}</p>
                  <p className="text-xs text-[var(--text-muted)]">{fmtMB(file.size)}{fileDur ? ` · ${fmtSec(fileDur)}` : ''}</p>
                  <button type="button" onClick={() => { setFile(null); setFileError(''); }} className="text-xs font-semibold text-[var(--accent)] hover:underline">Choose another video</button>
                </div>
              </div>
            )}
            <input ref={inputRef} type="file" accept="video/*" className="hidden" onChange={(e) => pickFile(e.target.files?.[0])} />
            {fileError && <p className="mt-3 text-xs font-semibold text-[var(--negative)] flex items-center gap-1.5"><AlertCircle className="w-4 h-4" />{fileError}</p>}
          </Section>

          {/* 2. Brief */}
          <Section step={2} icon={Wand2} title="Tell us what you need"
            right={<button type="button" onClick={() => setBrief(EXAMPLE_BRIEF)} className="text-xs font-semibold text-[var(--accent)] hover:underline">Use example</button>}>
            <div className="grid sm:grid-cols-3 gap-3 mb-3">
              <label className="sm:col-span-1 text-xs font-semibold text-[var(--text-muted)]">Channel name
                <input value={channel} onChange={(e) => setChannel(e.target.value)} maxLength={120} placeholder="[Channel Name]"
                  className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]" />
              </label>
              <p className="sm:col-span-2 text-xs text-[var(--text-muted)] self-end leading-relaxed">
                Write in any language (Hinglish is fine). Mention the platform, links, what happened in the video, the tone, and any sections you want (topics, keywords, queries, disclaimer, Instagram caption...).
              </p>
            </div>
            <textarea value={brief} onChange={(e) => setBrief(e.target.value)} rows={7} maxLength={4000}
              placeholder={'e.g. [Place] par raat ko accident hua. YouTube Shorts ke liye viral title, description, tags chahiye.\nLinks: [Your Link]\nDescription mein Topics Covered, 20-30 keywords, 20-30 queries aur Disclaimer daalo.'}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)] font-mono leading-relaxed" />
            {/\[(Your Link|Place)\]/i.test(brief) && (
              <p className="mt-1 text-[11px] font-semibold text-[var(--negative)]">Replace [Your Link] / [Place] in the brief with your real details.</p>
            )}
            <div className="flex justify-between text-[11px] text-[var(--text-muted)] mt-1"><span>Facts you mention here (place, date, names) are used; the AI won't invent them.</span><span>{brief.length}/4000</span></div>
            <button type="button" onClick={() => setShowScript((v) => !v)} className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[var(--text)]">
              <ChevronDown className={`w-4 h-4 transition-transform ${showScript ? 'rotate-180' : ''}`} /> I have my own voiceover script (optional)
            </button>
            {showScript && (
              <textarea value={ownScript} onChange={(e) => setOwnScript(e.target.value)} rows={5} maxLength={4000}
                placeholder="Paste your narration. The AI only splits and times it, it won't add new lines."
                className="mt-2 w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)]" />
            )}
          </Section>

          {/* 3. Voice */}
          <Section step={3} icon={Mic} title="Voice">
            <div className="grid sm:grid-cols-3 gap-2 mb-4">
              {(opts?.voiceover_modes || []).map((m) => (
                <button type="button" key={m.id} onClick={() => setMode(m.id)}
                  className={`text-left p-3 rounded-xl border transition-colors ${mode === m.id ? 'border-[var(--primary)] bg-[var(--bg-alt)] ring-1 ring-[var(--primary)]' : 'border-[var(--border)] hover:bg-[var(--bg-alt)]'}`}>
                  <span className="block text-sm font-bold text-[var(--text)]">{m.name}</span>
                  <span className="block text-xs text-[var(--text-muted)] mt-0.5">{m.desc}</span>
                </button>
              ))}
            </div>
            <label className="block text-xs font-semibold text-[var(--text-muted)] mb-3">Language
              <select value={language} onChange={(e) => setLanguage(e.target.value)}
                className="mt-1 block w-full sm:w-72 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm text-[var(--text)]">
                {(opts?.languages || []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </label>
            {mode !== 'original' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {voices.map((v) => (
                  <div key={v.id} role="button" tabIndex={0} onClick={() => setVoice(v.id)} onKeyDown={(e) => e.key === 'Enter' && setVoice(v.id)}
                    className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${voice === v.id ? 'border-[var(--primary)] bg-[var(--bg-alt)] ring-1 ring-[var(--primary)]' : 'border-[var(--border)] hover:bg-[var(--bg-alt)]'}`}>
                    <button type="button" onClick={(e) => { e.stopPropagation(); togglePreview(v.id); }} aria-label={`Preview ${v.name}`}
                      className="w-9 h-9 shrink-0 rounded-full bg-[var(--primary)] text-[var(--on-primary)] flex items-center justify-center">
                      {playing === v.id ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                    </button>
                    <div className="min-w-0">
                      <span className="block text-sm font-bold text-[var(--text)]">{v.name} <span className="font-medium text-[var(--text-muted)]">· {v.gender}</span></span>
                      <span className="block text-xs text-[var(--text-muted)] truncate">{v.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Section>

          {/* 4. Captions */}
          <Section step={4} icon={Captions} title="Caption style">
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4">
              {(opts?.caption_styles || []).map((s) => (
                <button type="button" key={s.id} onClick={() => setCaptionStyle(s.id)} title={s.desc}
                  className={`rounded-xl border overflow-hidden text-left transition-all ${captionStyle === s.id ? 'border-[var(--primary)] ring-2 ring-[var(--primary)]' : 'border-[var(--border)] hover:border-[var(--text-muted)]'}`}>
                  <div className="aspect-[9/14] bg-gradient-to-b from-slate-600 via-slate-800 to-slate-900"><StylePreview style={s} accent={accent} /></div>
                  <span className="block px-2 py-1.5 text-[11px] font-bold text-[var(--text)] leading-tight">{s.name}</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-4">{opts?.caption_styles?.find((s) => s.id === captionStyle)?.desc}</p>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <span className="block text-xs font-semibold text-[var(--text-muted)] mb-1.5">Highlight color</span>
                <div className="flex flex-wrap gap-2">
                  {(opts?.accent_presets || []).map((c) => (
                    <button type="button" key={c} onClick={() => setAccent(c)} aria-label={c} style={{ background: c }}
                      className={`w-8 h-8 rounded-full border-2 ${accent === c ? 'border-[var(--primary)] scale-110' : 'border-[var(--border)]'}`} />
                  ))}
                </div>
              </div>
              {langInfo?.indic && (
                <div>
                  <span className="block text-xs font-semibold text-[var(--text-muted)] mb-1.5">Caption script</span>
                  <div className="inline-flex rounded-lg border border-[var(--border)] p-0.5">
                    {(opts?.caption_scripts || []).map((c) => (
                      <button type="button" key={c.id} onClick={() => setCaptionScript(c.id)}
                        className={`px-3 py-1.5 rounded-md text-xs font-semibold ${captionScript === c.id ? 'bg-[var(--primary)] text-[var(--on-primary)]' : 'text-[var(--text)]'}`}>{c.id === 'roman' ? 'Roman (Hinglish)' : 'Native script'}</button>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <span className="block text-xs font-semibold text-[var(--text-muted)] mb-1.5">Output</span>
                <div className="inline-flex rounded-lg border border-[var(--border)] p-0.5">
                  {(opts?.output_formats || []).map((f) => (
                    <button type="button" key={f.id} onClick={() => setFormat(f.id)}
                      className={`px-3 py-1.5 rounded-md text-xs font-semibold ${format === f.id ? 'bg-[var(--primary)] text-[var(--on-primary)]' : 'text-[var(--text)]'}`}>{f.id === 'vertical' ? '9:16 Shorts/Reels' : 'Original shape'}</button>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-[var(--text)] self-end cursor-pointer">
                <input type="checkbox" checked={overlays} onChange={(e) => setOverlays(e.target.checked)} className="w-4 h-4 accent-[var(--primary)]" />
                Add hook title at the start and call-to-action at the end
              </label>
            </div>

            <div className="mt-5 pt-4 border-t border-[var(--border)]">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-xs font-bold text-[var(--text)] flex items-center gap-1.5">
                  <Film className="w-3.5 h-3.5 text-[var(--accent)]" /> Target Output Resolution
                </span>
                <span className="text-[11px] text-[var(--text-muted)]">
                  Active plan: <strong className="text-[var(--text)]">{session?.plan_name || 'Free Trial (480p SD)'}</strong>
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
                {[
                  { r: 480, label: '480p SD', req: 'Free (Included)' },
                  { r: 720, label: '720p HD', req: 'Plan 1 (Starter)' },
                  { r: 1080, label: '1080p FHD', req: 'Plan 2 (Creator)' },
                  { r: 1440, label: '2K QHD', req: 'Plan 3 (Pro)' },
                  { r: 1800, label: '3K Ultra', req: 'Plan 4 (Studio)' },
                  { r: 2160, label: '4K Cinema', req: 'Plan 5 (Business)' },
                  { r: 4320, label: '8K Ultra', req: 'Plan 6 (Enterprise)' },
                ].map((item) => {
                  const maxAllowed = session?.max_resolution || 480;
                  const isLocked = item.r > maxAllowed;
                  const isSelected = resolution === item.r;
                  return (
                    <button
                      key={item.r}
                      type="button"
                      onClick={() => {
                        if (isLocked) {
                          navigate('/pricing');
                        } else {
                          setResolution(item.r);
                        }
                      }}
                      className={`py-2 px-2.5 rounded-xl text-center border transition-all cursor-pointer ${
                        isSelected
                          ? 'border-[var(--primary)] bg-[var(--primary)] text-[var(--on-primary)] font-bold shadow-sm'
                          : isLocked
                          ? 'border-[var(--border)] opacity-60 hover:opacity-100 text-[var(--text-muted)]'
                          : 'border-[var(--border)] hover:border-[var(--text-muted)] text-[var(--text)]'
                      }`}
                    >
                      <div className="text-xs font-bold">{item.label}</div>
                      <div className="text-[10px] mt-0.5">
                        {isLocked ? (
                          <span className="text-amber-400 font-semibold">&#128274; {item.req}</span>
                        ) : (
                          <span className="text-emerald-400 font-semibold">&#10003; Unlocked</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </Section>

                    {/* Feature-Based Credit Breakdown Card */}
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-4 sm:p-5 shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-3 border-b border-[var(--border)]">
              <div>
                <h4 className="text-xs sm:text-sm font-black text-[var(--text)] flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <span>Feature Credit Breakdown</span>
                </h4>
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                  Transparent credits per feature: resolution export, neural voice, AI script, synced captions, and viral hook overlays.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--text-muted)]">Balance:</span>
                <span className="px-2.5 py-1 rounded-full bg-[var(--bg-alt)] border border-[var(--border)] text-xs font-black text-[var(--text)]">
                  {quote.userCredits} credits
                </span>
                <button
                  type="button"
                  onClick={() => setShowPricingModal(true)}
                  className="px-2.5 py-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-black text-[10px] font-black uppercase tracking-wider hover:opacity-90 cursor-pointer shadow-sm"
                >
                  + Top Up / Pass
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              {quote.items.map((it, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded-xl border flex items-center justify-between gap-2 ${
                    it.active && it.cost > 0
                      ? 'border-blue-500/30 bg-blue-500/5'
                      : 'border-[var(--border)] bg-[var(--bg-alt)] opacity-70'
                  }`}
                >
                  <span className="font-semibold text-[var(--text)] truncate">{it.name}</span>
                  <span
                    className={`shrink-0 font-mono text-[11px] font-bold px-2 py-0.5 rounded-md ${
                      it.cost > 0 ? 'bg-blue-600 text-white' : 'bg-[var(--border)] text-[var(--text-muted)]'
                    }`}
                  >
                    {it.cost > 0 ? `+${it.cost} cr` : '0 cr'}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-3 border-t border-[var(--border)]">
              <div className="flex items-center gap-2 text-xs">
                <span className="font-bold text-[var(--text)]">Total Required:</span>
                <span className="text-sm font-black text-amber-500">{quote.totalCost} Credits</span>
                <span className="text-[var(--text-muted)]">
                  ({quote.userCredits >= quote.totalCost ? `${quote.userCredits - quote.totalCost} will remain` : 'Not enough credits'})
                </span>
              </div>

              {!quote.canAfford && (
                <div className="flex items-center gap-2 text-xs text-amber-400 font-bold">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Need {quote.totalCost - quote.userCredits} more credit(s)</span>
                  <button
                    type="button"
                    onClick={() => setShowPricingModal(true)}
                    className="underline hover:text-amber-300 cursor-pointer"
                  >
                    Get 24h Pass (15 cr) or Pack
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Submit */}
          <div className="sticky bottom-3 z-10">
            <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-4 shadow-[var(--shadow-2)] flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <div className="flex-1 text-xs text-[var(--text-muted)]">
                {submitError ? (
                  <span className="text-[var(--negative)] font-semibold flex items-center gap-1.5"><AlertCircle className="w-4 h-4" />{submitError}</span>
                ) : !quote.resAllowed ? (
                  <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                    <Crown className="w-4 h-4 text-amber-400 shrink-0" />
                    Target {resolution}p export requires a plan upgrade (current allows {quote.maxAllowedRes}p).
                  </span>
                ) : !quote.canAfford ? (
                  <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                    Insufficient credits ({quote.totalCost} needed, {quote.userCredits} available). Adjust features or top up.
                  </span>
                ) : outOfQuota ? (
                  <span className="text-[var(--negative)] font-semibold">You've used today's {quota.limit} free edits. Come back after midnight (IST).</span>
                ) : submitting ? (
                  `Uploading… ${uploadPct}%`
                ) : (
                  `Ready to render with ${quote.totalCost} credits. Takes about 2–5 minutes.`
                )}
              </div>

              {!quote.canAfford || !quote.resAllowed ? (
                <button
                  type="button"
                  onClick={() => setShowPricingModal(true)}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-95 text-black text-sm font-black cursor-pointer shadow-md"
                >
                  <Crown className="w-4 h-4" />
                  {!quote.resAllowed ? `Unlock ${resolution}p Quality` : `Get Credits (${quote.totalCost} cr needed)`}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={!canSubmit}
                  onClick={submit}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] text-sm font-black disabled:opacity-40 disabled:cursor-not-allowed shadow-md cursor-pointer"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  {submitting ? `Uploading ${uploadPct}%` : `Create my video (${quote.totalCost} cr)`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PRICING MODAL POPUP */}
      <PricingModal
        isOpen={showPricingModal}
        onClose={() => setShowPricingModal(false)}
        userPlan={session?.plan || 'free'}
        onPlanUpgraded={() => {
          setShowPricingModal(false);
          window.location.reload();
        }}
      />

    </div>
  );
}

// =======================================================================================================
function JobView({ job, onReset, onOpenPricing }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (job.status === 'done' || job.status === 'failed') return undefined;
    const t = setInterval(() => setElapsed(Math.max(0, Date.now() / 1000 - (job.created_at || Date.now() / 1000))), 1000);
    return () => clearInterval(t);
  }, [job]);

  if (job.status === 'failed') {
    return (
      <div className="bg-[var(--surface)] border border-[var(--negative)]/40 rounded-2xl p-6 text-center max-w-xl mx-auto my-6 shadow-sm">
        <AlertCircle className="w-10 h-10 text-[var(--negative)] mx-auto mb-3" />
        <h2 className="text-lg font-black text-[var(--text)] mb-1">This edit failed</h2>
        <p className="text-sm text-[var(--text-muted)] mb-3 font-mono text-left bg-[var(--bg-alt)] p-3 rounded-xl border border-[var(--border)] break-all">{job.error || 'Something went wrong.'}</p>
        <p className="text-xs text-[var(--positive)] font-semibold mb-5">&#10003; Your free credit was returned.</p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button type="button" onClick={onReset} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] text-sm font-bold cursor-pointer">
            <RotateCcw className="w-4 h-4" />Try again
          </button>
          <button type="button" onClick={onOpenPricing} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-400 text-sm font-bold cursor-pointer">
            <Crown className="w-4 h-4 text-amber-400" />Explore 7 Plans
          </button>
        </div>
      </div>
    );
  }

  if (job.status !== 'done') {
    const idx = Math.max(0, STAGE_ORDER.indexOf(job.stage));
    return (
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-black text-[var(--text)] flex items-center gap-2"><Loader2 className="w-5 h-5 animate-spin text-[var(--accent)]" />Editing your video</h2>
          <span className="text-xs text-[var(--text-muted)] flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{fmtSec(elapsed)}</span>
        </div>
        <div className="h-2 rounded-full bg-[var(--bg-alt)] overflow-hidden mb-6">
          <div className="h-full bg-[var(--accent)] transition-all duration-700" style={{ width: `${Math.max(3, job.progress || 0)}%` }} />
        </div>
        {job.status === 'queued' && (
          <div className="mb-5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between font-medium">
            <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-amber-400" /> Waiting in render queue</span>
            <span>Position #{job.queue_position || 1} • ETA ~{job.estimated_wait_seconds || 45}s</span>
          </div>
        )}
        <ol className="space-y-2.5">
          {STAGE_ORDER.slice(1, -1).map((st, i) => {
            const state = i + 1 < idx ? 'done' : i + 1 === idx ? 'active' : 'todo';
            return (
              <li key={st} className="flex items-center gap-3 text-sm">
                {state === 'done' ? <CheckCircle2 className="w-5 h-5 text-[var(--positive)]" />
                  : state === 'active' ? <Loader2 className="w-5 h-5 animate-spin text-[var(--accent)]" />
                    : <span className="w-5 h-5 rounded-full border-2 border-[var(--border)]" />}
                <span className={state === 'todo' ? 'text-[var(--text-muted)]' : 'text-[var(--text)] font-semibold'}>{STAGE_LABEL[st]}</span>
              </li>
            );
          })}
        </ol>
        <p className="text-xs text-[var(--text-muted)] mt-6">Usually ready in 2–5 minutes. You can close this tab — open this page again on the same device and your video will be here.</p>
      </div>
    );
  }

  const r = job.result || {};
  const m = r.metadata;
  const f = (kind, inline) => `${API}/jobs/${job.id}/file/${kind}${inline ? '?inline=1' : ''}`;
  return (
    <div className="space-y-5">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5 sm:p-6">
        <div className="flex flex-col md:flex-row gap-6">
          <video src={f('video', true)} controls playsInline className="w-full md:w-72 max-h-[70vh] rounded-xl bg-black self-start" />
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-black text-[var(--text)] mb-1 flex items-center gap-2"><CheckCircle2 className="w-6 h-6 text-[var(--positive)]" />Your video is ready</h2>
            <p className="text-xs text-[var(--text-muted)] mb-4">
              {r.width}×{r.height} · {fmtSec(r.duration || 0)}{r.loudness?.lufs != null ? ` · audio ${r.loudness.lufs} LUFS` : ''}{r.voice?.engines ? ` · voice: ${r.voice.engines.join(', ')}` : ''}
            </p>
            <div className="flex flex-wrap gap-2 mb-4">
              <a href={f('video')} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] text-sm font-bold"><Download className="w-4 h-4" />Download MP4</a>
              {r.files?.srt && <a href={f('srt')} className="inline-flex items-center gap-2 px-3 py-2.5 rounded-xl border border-[var(--border)] text-sm font-semibold text-[var(--text)]"><Type className="w-4 h-4" />Captions .srt</a>}
              {r.files?.voiceover && <a href={f('voiceover')} className="inline-flex items-center gap-2 px-3 py-2.5 rounded-xl border border-[var(--border)] text-sm font-semibold text-[var(--text)]"><Music2 className="w-4 h-4" />Voiceover .wav</a>}
              {r.files?.metadata && <a href={f('metadata')} className="inline-flex items-center gap-2 px-3 py-2.5 rounded-xl border border-[var(--border)] text-sm font-semibold text-[var(--text)]"><FileText className="w-4 h-4" />All text .txt</a>}
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-3 flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />Download within 6 hours — after that the files are deleted from our server for your privacy.</p>
            {(job.warnings || []).map((w) => <p key={w} className="text-xs text-[var(--warning)] font-semibold mb-1">⚠ {w}</p>)}
            {r.script?.length > 0 && (
              <details className="mt-3">
                <summary className="text-sm font-bold text-[var(--text)] cursor-pointer">Voiceover script</summary>
                <ul className="mt-2 space-y-1 text-xs text-[var(--text-muted)]">
                  {r.script.map((l) => <li key={l.start}><span className="font-mono text-[var(--text)]">{fmtSec(l.start)}</span> {l.text}</li>)}
                </ul>
              </details>
            )}
            {/* Upgrade prompt on finished video */}
            <div className="mt-6 p-4 rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <p className="text-xs font-bold text-[var(--text)] flex items-center gap-1.5">
                  <Crown className="w-4 h-4 text-amber-500" />
                  <span>Want higher quality (1080p, 2K, 4K, 8K) or more renders?</span>
                </p>
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                  Free tier is 480p SD. Upgrade anytime to unlock Full HD / 4K and up to 1,500 credits.
                </p>
              </div>
              <button
                type="button"
                onClick={onOpenPricing}
                className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-95 text-black text-xs font-black uppercase tracking-wider shrink-0 cursor-pointer shadow-md"
              >
                View 7 Plans
              </button>
            </div>

            <div className="mt-4">
              <button type="button" onClick={onReset} className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline cursor-pointer"><Film className="w-4 h-4" />Edit another video</button>
            </div>
          </div>
        </div>
      </div>

      {m && (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-5 sm:p-6 space-y-6">
          <div>
            <h3 className="text-base font-black text-[var(--text)] mb-2">Title options</h3>
            <ul className="space-y-2">
              {m.titles.map((t, i) => (
                <li key={t} className="flex items-start justify-between gap-3 p-3 rounded-lg bg-[var(--bg-alt)]">
                  <span className="text-sm text-[var(--text)]"><b>{i + 1}.</b> {t} <span className="text-[10px] text-[var(--text-muted)]">({t.length})</span></span>
                  <CopyButton text={t} />
                </li>
              ))}
            </ul>
          </div>
          <TextBlock title="Description" text={m.description} rows={14} />
          <TextBlock title="Tags" text={m.tags} rows={4} note={`${m.tags.length}/500 characters`} />
          {m.hashtags?.length > 0 && <TextBlock title="Hashtags" text={m.hashtags.join(' ')} rows={2} />}
          {(m.extras || []).map((x) => <TextBlock key={x.heading} title={x.heading} text={x.content} rows={6} />)}
        </div>
      )}
    </div>
  );
}

function TextBlock({ title, text, rows, note }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-base font-black text-[var(--text)]">{title}{note && <span className="ml-2 text-[11px] font-medium text-[var(--text-muted)]">{note}</span>}</h3>
        <CopyButton text={text} />
      </div>
      <textarea readOnly value={text} rows={rows}
        className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm text-[var(--text)] font-mono leading-relaxed" />
    </div>
  );
}
