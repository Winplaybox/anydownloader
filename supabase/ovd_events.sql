-- OVD analytics events. Written only by the backend (service role). RLS on, no public policies.
create table if not exists public.ovd_events (
  id bigint generated always as identity primary key,
  ts timestamptz not null default now(),
  kind text not null,              -- resolve | download
  platform text,
  status text not null,            -- ok | fail | degraded
  code text,                       -- error code when not ok
  http int,
  ms int,
  quality text,
  title text,
  url text,
  host text,
  visitor text,                    -- salted hash of IP, never the IP itself
  device text,                     -- mobile | tablet | desktop | bot
  browser text,
  ref text,
  country text,
  region text
);
create index if not exists ovd_events_ts_idx on public.ovd_events (ts desc);
create index if not exists ovd_events_kind_ts_idx on public.ovd_events (kind, ts desc);
alter table public.ovd_events enable row level security;
