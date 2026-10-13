-- Mary Jane learning loop (finance chief project).
--
-- Gives the mj-agent edge function three things the database did not have:
--   1. A read-only window onto the investment data (mj_readonly_query), so the
--      agent can answer any question with SQL but can never write, call the
--      network, or see secret / personal tables.
--   2. A grader (mj_grade_due_evaluations) that scores every logged
--      recommendation against SPY at 30 / 90 / 365 days, from price_snapshots.
--   3. Track-record and calibration views the dashboard and the weekly
--      reflection read, plus a run log for cost / health visibility.
-- The existing trigger trg_schedule_mj_recommendation_evaluations already
-- creates the 30/90/365 evaluation rows when a recommendation is inserted.

-- ---------------------------------------------------------------- reader role
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'mj_reader') then
    create role mj_reader nologin bypassrls;
  end if;
end $$;

grant mj_reader to postgres;
grant usage on schema public to mj_reader;
grant select on all tables in schema public to mj_reader;

-- Secrets, credentials and personal / family records stay invisible to the agent.
revoke select on
  public.agent_connections, public.agent_os_config, public.ai_memory_sources,
  public.t212_api_config, public.telegram_config,
  public.identity_core, public.health_timeline, public.care_assessments,
  public.benefits_status, public.contacts,
  public.scip_worthing_properties, public.scip_outreach, public.scip_intelligence,
  public.scip_pipeline
from mj_reader;

-- ------------------------------------------------------------ read-only query
create or replace function public.mj_readonly_query(p_sql text)
returns jsonb
language plpgsql
security definer
set search_path = public
set statement_timeout = '8s'
as $$
declare
  q text := regexp_replace(btrim(coalesce(p_sql, '')), ';\s*$', '');
  result jsonb;
begin
  -- Everything after this line runs in a read-only transaction: no INSERT /
  -- UPDATE / DELETE, and no pg_net requests (they queue via INSERT).
  perform set_config('transaction_read_only', 'on', true);
  if q = '' then
    raise exception 'empty query';
  end if;
  if position(';' in q) > 0 then
    raise exception 'one statement only';
  end if;
  if q !~* '^\s*(select|with)\s' then
    raise exception 'only SELECT / WITH queries are allowed';
  end if;
  execute format(
    'select coalesce(jsonb_agg(t), ''[]''::jsonb) from (select * from (%s) q limit 200) t', q)
    into result;
  return result;
end $$;

-- Owned by mj_reader so table access is limited to its grants. Changing owner
-- needs CREATE on the schema, granted only for the duration of the change.
grant create on schema public to mj_reader;
alter function public.mj_readonly_query(text) owner to mj_reader;
revoke create on schema public from mj_reader;
revoke all on function public.mj_readonly_query(text) from public, anon, authenticated;
grant execute on function public.mj_readonly_query(text) to service_role;

-- ------------------------------------------------------------------ run log
create table if not exists public.mj_agent_runs (
  id uuid primary key default gen_random_uuid(),
  run_type text not null check (run_type in ('chat', 'reflect')),
  conversation_id uuid references public.mj_conversations(id) on delete set null,
  status text not null default 'running' check (status in ('running', 'ok', 'error')),
  model text,
  input_tokens integer,
  output_tokens integer,
  cache_read_tokens integer,
  tool_calls integer,
  summary text,
  stats jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);
alter table public.mj_agent_runs enable row level security;
comment on table public.mj_agent_runs is
  'One row per Mary Jane agent run (chat turn or weekly reflection): tokens, tool calls, outcome. Server-only.';
grant select on public.mj_agent_runs to mj_reader;

-- ------------------------------------------------------------ price helpers
create or replace function public.mj_price_on_or_after(p_ticker text, p_date date)
returns numeric
language sql
stable
set search_path = public
as $$
  select price_usd from public.price_snapshots
  where upper(ticker) = upper(p_ticker) and snapshot_date >= p_date and price_usd is not null
  order by snapshot_date asc, created_at desc
  limit 1
$$;

create or replace function public.mj_latest_price(p_ticker text)
returns numeric
language sql
stable
set search_path = public
as $$
  select price_usd from public.price_snapshots
  where upper(ticker) = upper(p_ticker) and price_usd is not null
  order by snapshot_date desc, created_at desc
  limit 1
$$;

-- Direction of a call: +1 expects the stock to beat SPY, -1 expects it to lag.
create or replace function public.mj_action_direction(p_action text)
returns integer
language sql
immutable
as $$
  select case
    when upper(p_action) in ('BUY', 'ADD', 'HOLD') then 1
    when upper(p_action) in ('TRIM', 'SELL', 'AVOID') then -1
    else 0
  end
$$;

-- ------------------------------------------------------------------- grader
create or replace function public.mj_grade_due_evaluations()
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  e record;
  start_px numeric; end_px numeric; bench_start numeric; bench_end numeric;
  ret numeric; bench_ret numeric; dir integer; edge numeric;
  graded integer := 0; waiting integer := 0; unavailable integer := 0;
begin
  for e in
    select ev.id, ev.due_at, ev.start_price, r.ticker, r.action, r.created_at::date as decided_on
    from public.mj_recommendation_evaluations ev
    join public.mj_recommendations r on r.id = ev.recommendation_id
    where ev.status in ('pending', 'due') and ev.due_at <= current_date
  loop
    if e.ticker is null then
      update public.mj_recommendation_evaluations
         set status = 'unavailable', notes = 'No ticker on the recommendation', evaluated_at = now()
       where id = e.id;
      unavailable := unavailable + 1;
      continue;
    end if;

    start_px := coalesce(e.start_price, public.mj_price_on_or_after(e.ticker, e.decided_on));
    end_px := public.mj_price_on_or_after(e.ticker, e.due_at);

    if start_px is null or end_px is null or start_px = 0 then
      if current_date > e.due_at + 14 then
        update public.mj_recommendation_evaluations
           set status = 'unavailable', evaluated_at = now(),
               notes = 'No US price history for ' || e.ticker || ' in price_snapshots'
         where id = e.id;
        unavailable := unavailable + 1;
      else
        update public.mj_recommendation_evaluations set status = 'due' where id = e.id;
        waiting := waiting + 1;
      end if;
      continue;
    end if;

    bench_start := public.mj_price_on_or_after('SPY', e.decided_on);
    bench_end := public.mj_price_on_or_after('SPY', e.due_at);
    ret := round((end_px / start_px - 1) * 100, 2);
    bench_ret := case when bench_start > 0 and bench_end is not null
                      then round((bench_end / bench_start - 1) * 100, 2) end;
    dir := public.mj_action_direction(e.action);
    edge := dir * (ret - coalesce(bench_ret, 0));

    update public.mj_recommendation_evaluations set
      status = 'completed',
      start_price = start_px,
      end_price = end_px,
      return_pct = ret,
      benchmark_return_pct = bench_ret,
      outcome_grade = case when dir <> 0 then round(edge, 2) end,
      opportunity_cost_pct = case when dir <> 0 then round(greatest(0, -edge), 2) end,
      thesis_result = case
        when dir = 0 then 'not_directional'
        when edge > 1 then 'beat'
        when edge < -1 then 'lagged'
        else 'inline' end,
      notes = case when bench_ret is null
                   then 'SPY history unavailable for this window; graded on absolute return'
                   else 'Graded vs SPY' end,
      evaluated_at = now()
    where id = e.id;
    graded := graded + 1;
  end loop;

  return format('graded=%s waiting=%s unavailable=%s', graded, waiting, unavailable);
end $$;

revoke all on function public.mj_grade_due_evaluations() from public, anon, authenticated;

-- ---------------------------------------------------------- track record views
create or replace view public.v_mj_track_record with (security_invoker = true) as
select
  r.id,
  r.created_at,
  r.ticker,
  r.action,
  r.confidence,
  r.recommendation,
  r.rationale,
  r.success_criteria,
  r.warning_signs,
  r.thesis_health_at_decision,
  r.price_at_decision,
  public.mj_latest_price(r.ticker) as latest_price,
  case when r.price_at_decision > 0 and public.mj_latest_price(r.ticker) is not null
       then round((public.mj_latest_price(r.ticker) / r.price_at_decision - 1) * 100, 2) end as return_to_date_pct,
  max(ev.outcome_grade) filter (where ev.horizon_days = 30) as edge_30d_pct,
  max(ev.outcome_grade) filter (where ev.horizon_days = 90) as edge_90d_pct,
  max(ev.outcome_grade) filter (where ev.horizon_days = 365) as edge_365d_pct,
  max(ev.thesis_result) filter (where ev.horizon_days = 30) as result_30d,
  max(ev.thesis_result) filter (where ev.horizon_days = 90) as result_90d,
  max(ev.thesis_result) filter (where ev.horizon_days = 365) as result_365d,
  min(ev.due_at) filter (where ev.status in ('pending', 'due')) as next_check_due
from public.mj_recommendations r
left join public.mj_recommendation_evaluations ev on ev.recommendation_id = r.id
group by r.id;

create or replace view public.v_mj_calibration with (security_invoker = true) as
select
  ev.horizon_days,
  case when r.confidence >= 80 then '80-100'
       when r.confidence >= 65 then '65-79'
       when r.confidence >= 50 then '50-64'
       else '0-49' end as confidence_band,
  count(*) as graded_calls,
  round(avg(r.confidence), 1) as avg_stated_confidence,
  round(100.0 * avg((ev.outcome_grade > 0)::int), 1) as hit_rate_pct,
  round(avg(ev.outcome_grade), 2) as avg_edge_vs_spy_pct
from public.mj_recommendation_evaluations ev
join public.mj_recommendations r on r.id = ev.recommendation_id
where ev.status = 'completed' and ev.outcome_grade is not null
group by 1, 2;

revoke all on public.v_mj_track_record, public.v_mj_calibration from anon, authenticated;
grant select on public.v_mj_track_record, public.v_mj_calibration to mj_reader;

-- ------------------------------------- benchmark + recommended tickers priced
-- Same nightly Alpaca snapshot as before, plus SPY / QQQ (benchmarks for the
-- grader) and any ticker Mary Jane recommended in the last ~13 months, so
-- every call can be graded even if it is not held or watch-listed.
create or replace function public.fn_fetch_prices()
returns text
language plpgsql
security definer
set search_path = public
as $function$
DECLARE kid text; sec text; syms text; rid bigint;
BEGIN
  SELECT decrypted_secret INTO kid FROM vault.decrypted_secrets WHERE name='ALPACA_PAPER_KEY_ID';
  SELECT decrypted_secret INTO sec FROM vault.decrypted_secrets WHERE name='ALPACA_PAPER_SECRET';
  SELECT string_agg(DISTINCT t, ',') INTO syms FROM (
    SELECT upper(ticker) AS t FROM public.v_current_portfolio
      WHERE upper(ticker) <> 'CASH' AND ticker !~ '[^A-Za-z.]'
    UNION
    SELECT upper(ticker) FROM public.watchlist
      WHERE coalesce(status,'active') NOT IN ('dropped','bought') AND ticker !~ '[^A-Za-z.]'
    UNION
    SELECT unnest(ARRAY['SPY','QQQ'])
    UNION
    SELECT upper(ticker) FROM public.mj_recommendations
      WHERE ticker IS NOT NULL AND ticker !~ '[^A-Za-z.]' AND created_at > now() - interval '400 days'
  ) x;
  IF syms IS NULL THEN RETURN 'no tickers'; END IF;
  rid := net.http_get(
    'https://data.alpaca.markets/v2/stocks/snapshots?feed=iex&symbols=' || syms,
    headers := jsonb_build_object('APCA-API-KEY-ID', kid, 'APCA-API-SECRET-KEY', sec));
  INSERT INTO public.price_fetch_requests(request_id) VALUES (rid);
  RETURN 'price request sent for: ' || syms;
END $function$;

-- -------------------------------------------------------------- dashboard auth
-- SHA-256 of the dashboard token (the token itself lives in Streamlit secrets
-- and in vault as MJ_AGENT_TOKEN for the scheduled reflection call).
insert into public.agent_os_config (config_key, config_value, updated_at)
values ('mj_agent_auth', jsonb_build_object('sha256', 'b9d77f894db73f1cbe3ebc0949a88aeb83295239533418c5683e8250a6ad52b8'), now())
on conflict (config_key) do update set config_value = excluded.config_value, updated_at = now();

-- ---------------------------------------------------------------- schedules
-- Grade after the evening price fetch (prices land 21:25 UTC on weekdays).
select cron.unschedule(jobid) from cron.job where jobname in ('mj-grade-evaluations', 'mj-weekly-reflection');
select cron.schedule('mj-grade-evaluations', '45 21 * * *', $$select public.mj_grade_due_evaluations()$$);
-- Saturday 07:50 UTC: Mary Jane reviews graded calls + Joe's own trade history
-- and writes / retires lessons.
select cron.schedule('mj-weekly-reflection', '50 7 * * 6', $$
  select net.http_post(
    url := 'https://qxwfrsoztfddwicqtuar.supabase.co/functions/v1/mj-agent',
    headers := jsonb_build_object(
      'content-type', 'application/json',
      'x-mj-token', (select decrypted_secret from vault.decrypted_secrets where name = 'MJ_AGENT_TOKEN')),
    body := '{"action":"reflect"}'::jsonb,
    timeout_milliseconds := 300000)
$$);
