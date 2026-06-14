-- Durable memory for the paper bot. Tables live in `public` with a `bot_`
-- prefix (not a custom schema) so they're reachable over Supabase's REST API
-- with no "exposed schemas" dashboard step. They hold only paper-trading test
-- data and never touch your other tables.

create table if not exists public.bot_trades (
  id bigint generated always as identity primary key,
  ts timestamptz not null default now(),
  symbol text not null, action text not null, qty numeric, price numeric,
  est_cost numeric, entry_price numeric, pnl_pct numeric, exit_reason text,
  mode text default 'swing', reason text, status text
);

create table if not exists public.bot_round_trips (
  id bigint generated always as identity primary key,
  symbol text not null, qty numeric, entry_date date, entry_price numeric,
  exit_date date, exit_price numeric, pnl numeric, pnl_pct numeric,
  hold_days integer, exit_reason text, created_at timestamptz not null default now(),
  unique (symbol, entry_date, exit_date, entry_price, exit_price)
);

create table if not exists public.bot_equity_snapshots (
  id bigint generated always as identity primary key,
  snapshot_date date not null unique, equity numeric, cash numeric,
  buying_power numeric, positions integer, todays_pl numeric,
  budget numeric, bot_pnl numeric, bot_return_pct numeric,
  created_at timestamptz not null default now()
);

create table if not exists public.bot_coach_notes (
  id bigint generated always as identity primary key,
  note_date date not null default current_date, note text, stats jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.bot_tendencies (
  id bigint generated always as identity primary key,
  observed_at timestamptz not null default now(), tendency text
);

create table if not exists public.bot_pattern_performance (
  id bigint generated always as identity primary key,
  bucket_type text not null, bucket_key text not null, trades integer,
  wins integer, pnl numeric, updated_at timestamptz not null default now(),
  unique (bucket_type, bucket_key)
);

create table if not exists public.bot_manual_journal (
  id bigint generated always as identity primary key,
  entry_date text, symbol text, setup text, grade text, note text,
  created_at timestamptz not null default now()
);

-- RLS on; the server-side SERVICE-ROLE key has full access, anon clients none.
do $$
declare t text;
begin
  foreach t in array array['bot_trades','bot_round_trips','bot_equity_snapshots',
    'bot_coach_notes','bot_tendencies','bot_pattern_performance','bot_manual_journal']
  loop
    execute format('alter table public.%I enable row level security;', t);
    execute format('drop policy if exists service_all on public.%I;', t);
    execute format('create policy service_all on public.%I for all to service_role using (true) with check (true);', t);
  end loop;
end $$;
