-- Copy-trade sleeve: signal inbox + its own journal.
--
-- An outside scout (Grok Bot) reads smart-money data and drops trade IDEAS into
-- public.bot_signals. It never places orders and never holds a database key
-- with real power: it can only call submit_signal() / signal_report() with an
-- ingest key, through the public (anon) API. The Railway copy engine reads the
-- inbox with the service-role key, applies its own risk caps, and trades a
-- SEPARATE Alpaca paper account, so none of this touches the bot_* tables the
-- swing/intraday battle test is scored on.

create table if not exists public.bot_signals (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  source text not null,              -- e.g. quiver_congress, quiver_insider
  source_ref text not null,          -- stable id for de-duplication
  actor text,                        -- who made the original trade
  symbol text not null,
  side text not null check (side in ('buy', 'sell')),
  traded_on date,                    -- when the actor traded
  disclosed_on date,                 -- when it became public
  amount_range text,
  conviction smallint not null default 3 check (conviction between 1 and 5),
  rationale text,
  status text not null default 'new'
    check (status in ('new', 'executing', 'executed', 'rejected', 'expired')),
  status_reason text,
  processed_at timestamptz,
  order_id text, qty numeric, est_price numeric,
  unique (source, source_ref)
);
create index if not exists bot_signals_status_idx on public.bot_signals (status, created_at);

create table if not exists public.bot_signal_ingest_keys (
  key_hash text primary key,         -- sha256 of the key; the key itself is never stored
  label text not null,
  created_at timestamptz not null default now(),
  last_used_at timestamptz,
  revoked boolean not null default false
);

create table if not exists public.bot_copy_trades (
  id bigint generated always as identity primary key,
  ts timestamptz not null default now(),
  signal_id bigint references public.bot_signals (id),
  symbol text not null, action text not null, qty numeric, price numeric,
  est_cost numeric, entry_price numeric, pnl_pct numeric,
  exit_reason text, reason text, status text
);

create table if not exists public.bot_copy_snapshots (
  id bigint generated always as identity primary key,
  snapshot_date date not null unique, equity numeric, cash numeric,
  deployed numeric, positions integer, holdings jsonb, budget numeric,
  sleeve_pnl numeric, sleeve_return_pct numeric,
  created_at timestamptz not null default now()
);

-- Same lock-down as the other bot tables: RLS on, service role only. The anon
-- role gets NO table access at all; it reaches the inbox only via the functions.
do $$
declare t text;
begin
  foreach t in array array['bot_signals', 'bot_signal_ingest_keys',
    'bot_copy_trades', 'bot_copy_snapshots']
  loop
    execute format('alter table public.%I enable row level security;', t);
    execute format('drop policy if exists service_all on public.%I;', t);
    execute format('create policy service_all on public.%I for all to service_role using (true) with check (true);', t);
  end loop;
end $$;

-- Mint an ingest key. Run once in the SQL editor:
--   select public.create_signal_ingest_key('grok-bot');
-- The key is shown ONCE; only its hash is kept. To cut a key off:
--   update public.bot_signal_ingest_keys set revoked = true where label = 'grok-bot';
create or replace function public.create_signal_ingest_key(p_label text)
returns text
language plpgsql security definer set search_path = ''
as $$
declare k text;
begin
  k := 'sig_' || replace(gen_random_uuid()::text, '-', '')
              || replace(gen_random_uuid()::text, '-', '');
  insert into public.bot_signal_ingest_keys (key_hash, label)
  values (encode(sha256(convert_to(k, 'UTF8')), 'hex'), coalesce(nullif(trim(p_label), ''), 'unnamed'));
  return k;
end $$;

create or replace function public._signal_key_ok(p_key text)
returns boolean
language plpgsql security definer set search_path = ''
as $$
declare h text;
begin
  if p_key is null or length(p_key) < 20 then
    return false;
  end if;
  h := encode(sha256(convert_to(p_key, 'UTF8')), 'hex');
  update public.bot_signal_ingest_keys set last_used_at = now()
   where key_hash = h and not revoked;
  return found;
end $$;

-- Drop one trade idea into the inbox. Validates everything, de-duplicates on
-- (source, source_ref), and refuses more than 50 ideas in 24 hours so a
-- confused or hijacked scout cannot flood the engine.
create or replace function public.submit_signal(ingest_key text, signal jsonb)
returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare
  v_symbol text := upper(trim(coalesce(signal->>'symbol', '')));
  v_side text := lower(trim(coalesce(signal->>'side', '')));
  v_source text := lower(trim(coalesce(signal->>'source', '')));
  v_actor text := left(trim(coalesce(signal->>'actor', '')), 120);
  v_ref text;
  v_traded date;
  v_disclosed date;
  v_conviction int;
  v_id bigint;
begin
  if not public._signal_key_ok(ingest_key) then
    raise exception 'invalid or revoked ingest key' using errcode = '42501';
  end if;
  if v_symbol !~ '^[A-Z]{1,5}([.][A-Z])?$' then
    raise exception 'symbol must be a plain US ticker, got "%"', left(v_symbol, 20)
      using errcode = '22023';
  end if;
  if v_side not in ('buy', 'sell') then
    raise exception 'side must be buy or sell' using errcode = '22023';
  end if;
  if v_source !~ '^[a-z0-9_]{2,40}$' then
    raise exception 'source must be a short lowercase label, e.g. quiver_congress'
      using errcode = '22023';
  end if;
  begin
    v_traded := nullif(signal->>'traded_on', '')::date;
    v_disclosed := nullif(signal->>'disclosed_on', '')::date;
    v_conviction := coalesce(nullif(signal->>'conviction', '')::int, 3);
  exception when others then
    raise exception 'dates must be YYYY-MM-DD and conviction a whole number'
      using errcode = '22023';
  end;
  if v_conviction not between 1 and 5 then
    raise exception 'conviction must be 1 to 5' using errcode = '22023';
  end if;
  if coalesce(v_disclosed, v_traded) > current_date + 1 then
    raise exception 'dates cannot be in the future' using errcode = '22023';
  end if;
  if (select count(*) from public.bot_signals
       where created_at > now() - interval '24 hours') >= 50 then
    raise exception 'daily signal limit reached (50 in 24h)' using errcode = '54000';
  end if;

  v_ref := left(coalesce(nullif(trim(signal->>'source_ref'), ''),
             concat_ws('|', nullif(v_actor, ''), v_symbol, v_side,
                       coalesce(v_traded, v_disclosed, current_date)::text)), 200);

  insert into public.bot_signals
    (source, source_ref, actor, symbol, side, traded_on, disclosed_on,
     amount_range, conviction, rationale)
  values
    (v_source, v_ref, nullif(v_actor, ''), v_symbol, v_side, v_traded, v_disclosed,
     left(signal->>'amount_range', 60), v_conviction, left(signal->>'rationale', 1000))
  on conflict (source, source_ref) do nothing
  returning id into v_id;

  if v_id is null then
    return jsonb_build_object('ok', true, 'duplicate', true);
  end if;
  return jsonb_build_object('ok', true, 'duplicate', false, 'id', v_id);
end $$;

-- Read-only view of what the engine did with the ideas, for the scout's daily
-- brief and Friday review. Same ingest key; nothing can be changed through it.
create or replace function public.signal_report(ingest_key text, days int default 14)
returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare d int := least(greatest(coalesce(days, 14), 1), 90);
begin
  if not public._signal_key_ok(ingest_key) then
    raise exception 'invalid or revoked ingest key' using errcode = '42501';
  end if;
  return jsonb_build_object(
    'window_days', d,
    'signals', coalesce((select jsonb_agg(to_jsonb(s) order by s.created_at desc)
      from (select id, created_at, source, actor, symbol, side, traded_on,
                   disclosed_on, conviction, status, status_reason, processed_at,
                   qty, est_price
              from public.bot_signals
             where created_at > now() - make_interval(days => d)
             order by created_at desc limit 200) s), '[]'::jsonb),
    'trades', coalesce((select jsonb_agg(to_jsonb(t) order by t.ts desc)
      from (select ts, signal_id, symbol, action, qty, price, entry_price,
                   pnl_pct, exit_reason, reason, status
              from public.bot_copy_trades
             where ts > now() - make_interval(days => d)
             order by ts desc limit 200) t), '[]'::jsonb),
    'snapshots', coalesce((select jsonb_agg(to_jsonb(n) order by n.snapshot_date desc)
      from (select snapshot_date, equity, cash, deployed, positions, holdings,
                   budget, sleeve_pnl, sleeve_return_pct
              from public.bot_copy_snapshots
             where snapshot_date > current_date - d
             order by snapshot_date desc) n), '[]'::jsonb));
end $$;

-- Who may call what. Postgres (and Supabase) grant EXECUTE widely by default,
-- so take it all away first, then hand back only what each role needs.
revoke all on function public.create_signal_ingest_key(text) from public, anon, authenticated;
revoke all on function public._signal_key_ok(text) from public, anon, authenticated;
revoke all on function public.submit_signal(text, jsonb) from public, authenticated;
revoke all on function public.signal_report(text, int) from public, authenticated;
grant execute on function public.create_signal_ingest_key(text) to service_role;
grant execute on function public.submit_signal(text, jsonb) to anon, service_role;
grant execute on function public.signal_report(text, int) to anon, service_role;
