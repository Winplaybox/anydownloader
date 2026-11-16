import React, { useEffect, useRef, useState } from 'react';
import { Check, Copy, Download, FileText, Loader2, Mic, Music, RotateCw, Sparkles, Volume2 } from 'lucide-react';
import { BACKEND_BASE } from '../utils/resolveMedia.js';

const VOICES = [
  ['hi-IN-MadhurNeural', 'Madhur - Hindi, male'],
  ['hi-IN-SwaraNeural', 'Swara - Hindi, female'],
  ['en-IN-PrabhatNeural', 'Prabhat - Indian English, male'],
  ['en-IN-NeerjaNeural', 'Neerja - Indian English, female'],
  ['en-US-ChristopherNeural', 'Christopher - US English, male'],
  ['en-US-JennyNeural', 'Jenny - US English, female'],
];

function saveText(content, filename, type, onToast) {
  if (!content) return;
  const href = URL.createObjectURL(new Blob([content], { type }));
  const a = Object.assign(document.createElement('a'), { href, download: filename });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 30000);
  onToast(`Saved ${filename}`);
}

const slug = (s, fb) => String(s || fb).slice(0, 30).replace(/[^a-zA-Z0-9_-]/g, '_');

export default function AiStudio({ data, title, caption, platform, audios, onDownload, onToast }) {
  const [ai, setAi] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [voice, setVoice] = useState(VOICES[0][0]);
  const [speaking, setSpeaking] = useState(false);
  const [voiceUri, setVoiceUri] = useState(null);
  const [copied, setCopied] = useState('');
  const started = useRef(false);

  async function load() {
    if (loading) return;
    setLoading(true); setError('');
    try {
      const r = await fetch(`${BACKEND_BASE}/api/ai/captions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: data.sourceUrl || data.url || '', title, caption, platform }),
      });
      const j = r.ok ? await r.json() : null;
      if (j && j.ok) setAi(j);
      else setError('AI captions are busy right now. Please try again in a moment.');
    } catch {
      setError('Could not reach the AI service. Check your connection and try again.');
    } finally { setLoading(false); }
  }

  useEffect(() => { if (!started.current) { started.current = true; load(); } }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function speak() {
    const text = ai?.transcript || caption || title;
    if (!text) return;
    setSpeaking(true);
    try {
      const r = await fetch(`${BACKEND_BASE}/api/ai/voice`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, voice }),
      });
      const j = r.ok ? await r.json() : null;
      if (j && j.ok && j.data_uri) { setVoiceUri(j.data_uri); onToast('Voiceover ready'); }
      else onToast('Voiceover failed. Try again.');
    } catch { onToast('Voiceover failed. Try again.'); }
    finally { setSpeaking(false); }
  }

  const copy = (text, id) => navigator.clipboard?.writeText(text).then(() => { setCopied(id); setTimeout(() => setCopied(''), 1800); });

  const action = 'rounded-2xl border border-[var(--border)] p-3.5 text-left flex items-center gap-3 hover:border-[var(--accent)] transition-colors min-h-14';

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3 rounded-2xl bg-[var(--accent-bg)] p-4">
        <Sparkles className="w-5 h-5 mt-0.5 text-[var(--accent)] shrink-0" />
        <div className="flex-1 text-sm">
          <p className="font-bold text-[var(--text)]">Subtitles, transcript and voiceover</p>
          <p className="text-[var(--text-muted)] mt-0.5">
            {ai?.is_real_speech ? 'Taken from the spoken audio in this video.' : 'Generated from the title and caption. Check it before you publish.'}
          </p>
        </div>
        {!loading && (
          <button type="button" onClick={load} className="shrink-0 h-9 px-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-sm font-semibold flex items-center gap-1.5">
            <RotateCw className="w-4 h-4" /> Redo
          </button>
        )}
      </div>

      {loading && (
        <div className="space-y-2.5" aria-busy="true">
          <div className="ovd-skeleton h-14 rounded-2xl" /><div className="ovd-skeleton h-14 rounded-2xl" /><div className="ovd-skeleton h-24 rounded-2xl" />
          <p className="text-sm text-[var(--text-muted)] text-center">Listening to the video...</p>
        </div>
      )}

      {error && !loading && (
        <div role="alert" className="rounded-2xl bg-[var(--negative-bg)] p-4 text-sm flex items-center justify-between gap-3">
          <span>{error}</span><button type="button" onClick={load} className="font-semibold underline">Try again</button>
        </div>
      )}

      {ai && !loading && (
        <>
          <div className="grid sm:grid-cols-2 gap-2.5">
            <button type="button" className={action} onClick={() => saveText(ai.srt, `${slug(title, 'captions')}.srt`, 'text/plain', onToast)}>
              <Download className="w-5 h-5 text-[var(--accent)]" /><span><b className="block text-sm">Subtitles (.srt)</b><span className="text-xs text-[var(--text-muted)]">For CapCut and Premiere</span></span>
            </button>
            <button type="button" className={action} onClick={() => saveText(ai.vtt, `${slug(title, 'captions')}.vtt`, 'text/vtt', onToast)}>
              <Download className="w-5 h-5 text-[var(--accent)]" /><span><b className="block text-sm">Subtitles (.vtt)</b><span className="text-xs text-[var(--text-muted)]">For websites and players</span></span>
            </button>
            <button type="button" className={action} onClick={() => saveText(ai.transcript, `${slug(title, 'transcript')}_transcript.txt`, 'text/plain', onToast)}>
              <FileText className="w-5 h-5 text-[var(--accent)]" /><span><b className="block text-sm">Transcript (.txt)</b><span className="text-xs text-[var(--text-muted)]">Full text of what is said</span></span>
            </button>
            <button type="button" className={action} onClick={() => copy(`${ai.caption}\n\n${ai.hashtags}`, 'post')}>
              {copied === 'post' ? <Check className="w-5 h-5 text-[var(--positive)]" /> : <Copy className="w-5 h-5 text-[var(--accent)]" />}
              <span><b className="block text-sm">{copied === 'post' ? 'Copied' : 'Copy caption and hashtags'}</b><span className="text-xs text-[var(--text-muted)]">Ready to paste in a post</span></span>
            </button>
            {audios[0] && (
              <button type="button" className={action} onClick={() => onDownload({ ...audios[0], kind: 'audio' }, 'ai_audio')}>
                <Music className="w-5 h-5 text-[var(--accent)]" /><span><b className="block text-sm">Original audio (MP3)</b><span className="text-xs text-[var(--text-muted)]">The sound from this video</span></span>
              </button>
            )}
          </div>

          <div className="rounded-2xl border border-[var(--border)] p-4 space-y-2.5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-bold">Transcript <span className="font-normal text-[var(--text-muted)]">({ai.transcript.split(/\s+/).filter(Boolean).length} words)</span></h3>
              <button type="button" onClick={() => copy(ai.transcript, 'tr')} className="text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1">
                {copied === 'tr' ? <><Check className="w-3.5 h-3.5" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy</>}
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto rounded-xl bg-[var(--bg-alt)] p-3 text-sm leading-relaxed select-text">{ai.transcript}</div>
          </div>

          {Array.isArray(ai.hooks) && ai.hooks.length > 0 && (
            <div>
              <h3 className="text-sm font-bold mb-2.5">Opening lines for Reels and Shorts</h3>
              <ul className="grid md:grid-cols-3 gap-2.5">
                {ai.hooks.map((h, i) => (
                  <li key={i} className="rounded-2xl border border-[var(--border)] p-3.5 flex flex-col justify-between gap-3">
                    <p className="text-sm font-medium leading-snug">&ldquo;{h}&rdquo;</p>
                    <button type="button" onClick={() => copy(h, `h${i}`)} className="self-end text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] flex items-center gap-1">
                      {copied === `h${i}` ? <><Check className="w-3.5 h-3.5" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy</>}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-2xl border border-[var(--border)] p-4 space-y-3">
            <div>
              <h3 className="text-sm font-bold">AI voiceover</h3>
              <p className="text-xs text-[var(--text-muted)]">Turn the transcript into a spoken MP3.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <label className="sr-only" htmlFor="ovd-voice">Voice</label>
              <select id="ovd-voice" value={voice} onChange={(e) => setVoice(e.target.value)}
                className="h-11 flex-1 rounded-xl bg-[var(--surface)] border border-[var(--border)] px-3 text-sm font-semibold">
                {VOICES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
              <button type="button" onClick={speak} disabled={speaking}
                className="h-11 px-5 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-60">
                {speaking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}{speaking ? 'Creating...' : 'Create voiceover'}
              </button>
            </div>
            {voiceUri && (
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl bg-[var(--bg-alt)] p-3">
                <Volume2 className="w-5 h-5 text-[var(--accent)] hidden sm:block" />
                <audio controls src={voiceUri} className="h-10 w-full sm:flex-1" />
                <a href={voiceUri} download={`${slug(title, 'voiceover')}_ai.mp3`}
                  className="h-10 px-4 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] text-sm font-bold flex items-center justify-center gap-1.5">
                  <Download className="w-4 h-4" /> MP3
                </a>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
