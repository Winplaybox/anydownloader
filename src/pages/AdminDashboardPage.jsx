import React, { useCallback, useEffect, useRef, useState } from 'react';
import { RefreshCw, Lock, Activity, Users, Download, Search, TriangleAlert, CircleCheck } from 'lucide-react';
import { BACKEND_BASE } from '../utils/resolveMedia.js';

const KEY_STORE = 'ovd_admin_key';
const RANGES = [[1, 'Today'], [7, '7 days'], [30, '30 days'], [90, '90 days']];

const fmt = (n) => (n == null ? '-' : Number(n).toLocaleString('en-IN'));
const pct = (n) => (n == null ? '-' : `${n}%`);
const ago = (iso) => {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

function Card({ title, children, className = '' }) {
  return (
    <section className={`rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-5 shadow-[var(--shadow-1)] ${className}`}>
      <h2 className="text-sm font-bold text-[var(--text-muted)] mb-3" style={{ fontFamily: 'var(--font)' }}>{title}</h2>
      {children}
    </section>
  );
}

function Kpi({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow-1)]">
      <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]"><Icon className="w-4 h-4" />{label}</div>
      <div className="mt-1 text-3xl font-extrabold tracking-tight">{value}</div>
      {sub && <div className="text-xs text-[var(--text-muted)] mt-0.5">{sub}</div>}
    </div>
  );
}

function Bars({ data, getA, getB, labelOf }) {
  const max = Math.max(1, ...data.map((d) => getA(d) + (getB ? getB(d) : 0)));
  return (
    <div className="flex items-end gap-1 h-36" role="img" aria-label="Activity over time">
      {data.map((d, i) => {
        const a = getA(d); const b = getB ? getB(d) : 0;
        return (
          <div key={i} className="flex-1 min-w-0 flex flex-col justify-end h-full group relative" title={`${labelOf(d, i)}: ${a}${getB ? ` ok, ${b} failed` : ''}`}>
            {b > 0 && <div className="w-full bg-[var(--negative)] rounded-t-sm" style={{ height: `${(b / max) * 100}%` }} />}
            <div className={`w-full bg-[var(--text)] ${b > 0 ? '' : 'rounded-t-sm'}`} style={{ height: `${(a / max) * 100}%`, minHeight: a ? 2 : 0 }} />
          </div>
        );
      })}
    </div>
  );
}

function Top({ rows }) {
  if (!rows?.length) return <p className="text-sm text-[var(--text-muted)]">No data yet.</p>;
  const max = Math.max(...rows.map((r) => r.count));
  return (
    <ul className="space-y-1.5">
      {rows.map((r) => (
        <li key={r.name} className="text-sm">
          <div className="flex justify-between gap-3"><span className="truncate">{r.name}</span><b>{fmt(r.count)}</b></div>
          <div className="h-1 rounded bg-[var(--bg-alt)] mt-0.5"><div className="h-1 rounded bg-[var(--text)]" style={{ width: `${(r.count / max) * 100}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}

export default function AdminDashboardPage() {
  const [key, setKey] = useState(() => { try { return sessionStorage.getItem(KEY_STORE) || ''; } catch { return ''; } });
  const [input, setInput] = useState('');
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);
  const abort = useRef(null);

  const load = useCallback(async (k = key, d = days) => {
    if (!k) return;
    abort.current?.abort();
    const ctl = new AbortController(); abort.current = ctl;
    setLoading(true); setErr('');
    try {
      const r = await fetch(`${BACKEND_BASE}/admin/analytics?days=${d}`, { headers: { 'X-Admin-Key': k }, signal: ctl.signal });
      const j = await r.json().catch(() => ({}));
      if (r.status === 401) { setErr('Wrong admin key.'); setKey(''); try { sessionStorage.removeItem(KEY_STORE); } catch { /* ignore */ } return; }
      if (r.status === 429) { setErr('Too many wrong attempts. Wait a few minutes.'); return; }
      if (!r.ok || !j.ok) { setErr(j?.error?.message || j?.error || `Server error ${r.status}`); return; }
      setData(j);
    } catch (e) {
      if (e.name !== 'AbortError') setErr('Could not reach the server. It may be waking up, try again in a minute.');
    } finally { setLoading(false); }
  }, [key, days]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!key) return undefined;
    const t = setInterval(() => { if (!document.hidden) load(); }, 30000);
    return () => clearInterval(t);
  }, [key, load]);

  function login(e) {
    e.preventDefault();
    const k = input.trim(); if (!k) return;
    try { sessionStorage.setItem(KEY_STORE, k); } catch { /* ignore */ }
    setKey(k); setInput('');
  }

  if (!key) {
    return (
      <div className="max-w-sm mx-auto px-4 py-20">
        <form onSubmit={login} className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-2)] space-y-4">
          <div className="flex items-center gap-2 font-bold text-lg"><Lock className="w-5 h-5" />OVD admin</div>
          <label htmlFor="admin-key" className="text-sm text-[var(--text-muted)] block">Admin key</label>
          <input id="admin-key" type="password" autoComplete="off" value={input} onChange={(e) => setInput(e.target.value)}
            className="w-full h-11 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 outline-none focus:border-[var(--text)]" />
          {err && <p role="alert" className="text-sm text-[var(--negative)]">{err}</p>}
          <button type="submit" className="w-full h-11 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] font-bold">Open dashboard</button>
        </form>
      </div>
    );
  }

  const t = data?.totals; const yt = data?.youtube; const br = yt?.breaker;
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl sm:text-3xl font-extrabold">Usage and downloads</h1>
        <div className="flex items-center gap-2">
          <div className="flex rounded-xl border border-[var(--border)] overflow-hidden" role="group" aria-label="Range">
            {RANGES.map(([d, l]) => (
              <button key={d} type="button" onClick={() => setDays(d)} aria-pressed={days === d}
                className={`h-10 px-2.5 sm:px-3 text-sm font-semibold whitespace-nowrap ${days === d ? 'bg-[var(--text)] text-[var(--bg)]' : 'bg-[var(--surface)]'}`}>{l}</button>
            ))}
          </div>
          <button type="button" onClick={() => load()} aria-label="Refresh" className="w-10 h-10 grid place-items-center rounded-xl border border-[var(--border)] bg-[var(--surface)]">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button type="button" onClick={() => { try { sessionStorage.removeItem(KEY_STORE); } catch { /* ignore */ } setKey(''); setData(null); }}
            className="h-10 px-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm font-semibold">Lock</button>
        </div>
      </div>

      {err && <div role="alert" className="rounded-xl border border-[var(--negative)]/30 bg-[var(--negative-bg)] p-3 text-sm">{err}</div>}
      {data?.storage_warning && <div role="status" className="rounded-xl border border-[var(--warning)]/40 bg-[var(--warning-bg)] p-3 text-sm flex gap-2"><TriangleAlert className="w-4 h-4 mt-0.5 shrink-0" />{data.storage_warning}</div>}
      {data?.upload?.last_error && <div role="status" className="rounded-xl border border-[var(--warning)]/40 bg-[var(--warning-bg)] p-3 text-sm">Database upload problem: {data.upload.last_error}</div>}

      {!data ? <div className="ovd-skeleton h-40 rounded-2xl" /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Kpi icon={Users} label="Visitors" value={fmt(t.visitors)} sub={`${fmt(t.events)} actions`} />
            <Kpi icon={Search} label="Links checked" value={fmt(t.resolves)} sub={`${pct(t.resolve_ok_pct)} worked`} />
            <Kpi icon={Download} label="Downloads" value={fmt(t.downloads_ok)} sub={`${fmt(t.downloads)} tried`} />
            <Kpi icon={Activity} label="Download success" value={pct(t.download_ok_pct)} sub="of all attempts" />
          </div>

          <Card title="YouTube health (last 24 hours)">
            <div className="flex flex-wrap items-center gap-x-8 gap-y-2 text-sm">
              <span className="flex items-center gap-2 font-bold text-lg">
                {br?.open ? <><TriangleAlert className="w-5 h-5 text-[var(--negative)]" />Paused, retry in {br.retry_after_s}s</> : <><CircleCheck className="w-5 h-5 text-[var(--positive)]" />Allowing requests</>}
              </span>
              <span>Downloads: <b>{fmt(yt.ok_24h)}</b> of <b>{fmt(yt.downloads_24h)}</b> worked ({pct(yt.ok_pct_24h)})</span>
              <span className="text-[var(--text-muted)]">Last success: {br?.last_ok_ago_s != null ? `${Math.floor(br.last_ok_ago_s / 60)} min ago` : 'none since restart'}</span>
            </div>
          </Card>

          <div className="grid lg:grid-cols-3 gap-4">
            <Card title="Per day (black = ok downloads, red = failed)" className="lg:col-span-2">
              <Bars data={data.daily} getA={(d) => d.downloads_ok} getB={(d) => d.downloads_fail} labelOf={(d) => d.day} />
              <div className="flex justify-between text-xs text-[var(--text-muted)] mt-1"><span>{data.daily[0]?.day}</span><span>{data.daily.at(-1)?.day}</span></div>
            </Card>
            <Card title="Busy hours (IST)">
              <Bars data={data.hourly_ist} getA={(d) => d} labelOf={(_, i) => `${i}:00`} />
              <div className="flex justify-between text-xs text-[var(--text-muted)] mt-1"><span>12am</span><span>12pm</span><span>11pm</span></div>
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <Card title="Platforms">
              <div className="overflow-x-auto"><table className="w-full text-sm">
                <thead><tr className="text-left text-[var(--text-muted)]"><th className="py-1 pr-3">Platform</th><th className="pr-3">Checked</th><th className="pr-3">Downloads</th><th>Failed</th></tr></thead>
                <tbody>{data.platforms.map((p) => (
                  <tr key={p.platform} className="border-t border-[var(--border)]"><td className="py-1.5 pr-3 font-semibold capitalize">{p.platform}</td><td className="pr-3">{fmt(p.resolves)}</td><td className="pr-3">{fmt(p.downloads)}</td>
                    <td className={p.download_fail + p.resolve_fail ? 'text-[var(--negative)] font-semibold' : ''}>{fmt(p.download_fail + p.resolve_fail)}</td></tr>
                ))}</tbody></table></div>
            </Card>
            <Card title="What is failing">
              {data.errors.length ? (
                <ul className="space-y-2 text-sm">{data.errors.map((e, i) => (
                  <li key={i} className="flex justify-between gap-3"><span><b>{e.code}</b> <span className="text-[var(--text-muted)]">{e.platform}, {e.kind}</span></span><b>{fmt(e.count)}</b></li>
                ))}</ul>
              ) : <p className="text-sm text-[var(--text-muted)]">No errors in this period.</p>}
            </Card>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card title="Devices"><Top rows={data.devices} /></Card>
            <Card title="Browsers"><Top rows={data.browsers} /></Card>
            <Card title="Countries"><Top rows={data.countries} /></Card>
            <Card title="Came from"><Top rows={data.referrers} /></Card>
          </div>

          <Card title="Most downloaded links">
            {data.top_content.length ? (
              <ul className="divide-y divide-[var(--border)] text-sm">{data.top_content.map((c, i) => (
                <li key={i} className="py-2 flex justify-between gap-3">
                  <span className="min-w-0"><span className="font-semibold block truncate">{c.title || c.url}</span><a href={c.url} target="_blank" rel="noreferrer noopener" className="text-xs text-[var(--text-muted)] truncate block hover:underline">{c.url}</a></span>
                  <b>{fmt(c.count)}</b>
                </li>))}</ul>
            ) : <p className="text-sm text-[var(--text-muted)]">No downloads yet.</p>}
          </Card>

          <Card title="Live activity (newest first)">
            <div className="overflow-x-auto"><table className="w-full text-sm whitespace-nowrap">
              <thead><tr className="text-left text-[var(--text-muted)]"><th className="py-1 pr-3">When</th><th className="pr-3">What</th><th className="pr-3">Platform</th><th className="pr-3">Result</th><th className="pr-3">Quality</th><th className="pr-3">Visitor</th><th className="pr-3">Device</th><th className="pr-3">Country</th><th>Title</th></tr></thead>
              <tbody>{data.recent.map((r, i) => (
                <tr key={i} className="border-t border-[var(--border)]">
                  <td className="py-1.5 pr-3 text-[var(--text-muted)]">{ago(r.ts)}</td><td className="pr-3">{r.kind === 'resolve' ? 'check' : 'download'}</td><td className="pr-3 capitalize">{r.platform}</td>
                  <td className={`pr-3 font-semibold ${r.status === 'fail' ? 'text-[var(--negative)]' : r.status === 'degraded' ? 'text-[var(--warning)]' : 'text-[var(--positive)]'}`}>{r.status === 'ok' ? 'ok' : r.code || r.status}</td>
                  <td className="pr-3">{r.quality || '-'}</td><td className="pr-3 font-mono text-xs">{r.visitor || '-'}</td><td className="pr-3">{r.device || '-'}</td><td className="pr-3">{r.country || '-'}</td>
                  <td className="max-w-[18rem] truncate">{r.title || ''}</td></tr>))}</tbody></table></div>
          </Card>
          <p className="text-xs text-[var(--text-muted)]">Source: {data.source}. IP addresses are never stored, only a salted hash. Refreshes every 30 seconds.</p>
        </>
      )}
    </div>
  );
}
