-- =============================================================================
-- The private research context boundary.
--
-- This is the ONLY intended integration point between the studio and the
-- existing "finance chief" data. It is a single function in a non-exposed
-- schema, wrapped by one SECURITY DEFINER entry point, returning a minimal
-- redacted payload.
--
-- What it must never return, at any allow-list setting:
--   broker_statements, broker_account_snapshots, broker_executions,
--   broker_cash_events, broker_dividends, broker_position_snapshots,
--   broker_import_audit, trade_journal, decision_log, benefits, income,
--   assets, account identifiers, personal names, serial numbers, and any
--   portfolio value, position size or allocation.
--
-- Review before applying. See docs/SECURITY.md.
-- =============================================================================

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

-- --- the redacted context ----------------------------------------------------

create or replace function private.aift_content_context(
  p_reference_date            date,
  p_allow_research_topics     boolean default false,
  p_allow_agent_rules         boolean default false,
  p_allow_intelligence_flags  boolean default false,
  p_allow_market_snapshots    boolean default false,
  p_allow_macro_indicators    boolean default false,
  p_allow_portfolio_themes    boolean default false
) returns jsonb
language plpgsql
stable
set search_path = private, public, pg_temp
as $$
declare
  v_topics jsonb := '[]'::jsonb;
  v_rules  jsonb := '[]'::jsonb;
  v_flags  jsonb := '[]'::jsonb;
  v_prices jsonb := '[]'::jsonb;
  v_macro  jsonb := '[]'::jsonb;
  v_themes jsonb := '[]'::jsonb;
begin
  -- Research topics: the subject line and desired fields only. No requester,
  -- no rationale free-text, no linkage to a holding.
  if p_allow_research_topics then
    select coalesce(jsonb_agg(jsonb_build_object(
             'topic', q.topic,
             'ticker', q.ticker,
             'priority', coalesce(q.priority, 5),
             'requested_fields', coalesce(q.requested_fields, array[]::text[])
           ) order by coalesce(q.priority, 5)), '[]'::jsonb)
      into v_topics
      from public.research_pull_queue q
     where coalesce(q.status, 'open') in ('open','queued','pending')
     limit 25;
  end if;

  -- Guardrails: shown so the audit trail can prove the workflow saw them.
  if p_allow_agent_rules then
    select coalesce(jsonb_agg(jsonb_build_object(
             'rule_name', r.rule_name, 'rule_text', r.rule_text, 'scope', coalesce(r.scope,'general')
           )), '[]'::jsonb)
      into v_rules
      from public.agent_rules r
     limit 50;
  end if;

  -- Intelligence flags: label and strength only. A flag is a prioritisation
  -- hint for private research; it never becomes a public claim on its own.
  if p_allow_intelligence_flags then
    select coalesce(jsonb_agg(jsonb_build_object(
             'label', f.label,
             'strength', case
               when coalesce(f.score, 0) >= 0.66 then 'high'
               when coalesce(f.score, 0) >= 0.33 then 'medium'
               else 'low' end
           )), '[]'::jsonb)
      into v_flags
      from public.agent_intelligence_flags f
     limit 25;
  end if;

  -- Market data: symbol, metric, value, unit, date, source. No quantity held,
  -- no cost basis, no position value — those columns are not selected and the
  -- output shape has nowhere to put them.
  if p_allow_market_snapshots then
    select coalesce(jsonb_agg(jsonb_build_object(
             'symbol', s.symbol, 'metric', 'close', 'value', s.close,
             'unit', coalesce(s.currency,'USD'), 'as_of', s.as_of_date, 'source', coalesce(s.source,'price_snapshots')
           )), '[]'::jsonb)
      into v_prices
      from public.price_snapshots s
     where s.as_of_date <= p_reference_date
       and s.as_of_date >= p_reference_date - interval '400 days'
     limit 400;
  end if;

  if p_allow_macro_indicators then
    select coalesce(jsonb_agg(jsonb_build_object(
             'indicator', m.indicator, 'value', m.value, 'unit', coalesce(m.unit,''),
             'as_of', m.as_of_date, 'source', coalesce(m.source,'macro_indicators')
           )), '[]'::jsonb)
      into v_macro
      from public.macro_indicators m
     where m.as_of_date <= p_reference_date
     limit 200;
  end if;

  -- Themes: bucket LABELS only, and only where more than one bucket shares the
  -- label, so a label cannot identify a single position. No weights, no values,
  -- no counts — a count is a value in disguise.
  if p_allow_portfolio_themes then
    select coalesce(jsonb_agg(t.theme), '[]'::jsonb)
      into v_themes
      from (
        select b.bucket_name as theme
          from public.portfolio_buckets b
         group by b.bucket_name
        having count(*) > 1
         limit 12
      ) t;
  end if;

  return jsonb_build_object(
    'reference_date', p_reference_date,
    'research_topics', v_topics,
    'agent_rules', v_rules,
    'intelligence_flags', v_flags,
    'market_snapshots', v_prices,
    'macro_indicators', v_macro,
    'portfolio_themes', v_themes,
    'redaction_notice',
      'Redacted research context. Broker, trade, benefits, income, asset-register, '
      || 'account-identifier and personal-name fields are excluded at the database '
      || 'boundary and are not retrievable through this path.'
  );
end;
$$;

-- --- the single exposed entry point -----------------------------------------
--
-- SECURITY DEFINER so the caller does not need rights on the underlying tables;
-- it returns the redacted payload and nothing else. This is the one door.

create or replace function public.aift_content_context(
  p_reference_date            date,
  p_allow_research_topics     boolean default false,
  p_allow_agent_rules         boolean default false,
  p_allow_intelligence_flags  boolean default false,
  p_allow_market_snapshots    boolean default false,
  p_allow_macro_indicators    boolean default false,
  p_allow_portfolio_themes    boolean default false
) returns jsonb
language sql
stable
security definer
set search_path = private, public, pg_temp
as $$
  select private.aift_content_context(
    p_reference_date, p_allow_research_topics, p_allow_agent_rules,
    p_allow_intelligence_flags, p_allow_market_snapshots,
    p_allow_macro_indicators, p_allow_portfolio_themes
  );
$$;

revoke all on function public.aift_content_context(date,boolean,boolean,boolean,boolean,boolean,boolean) from public, anon;
-- Deliberately NOT granted to `authenticated`: the browser never calls this.
-- Only the server-side worker role does.

do $$ begin
  if exists (select 1 from pg_roles where rolname = 'aift_worker') then
    grant execute on function public.aift_content_context(date,boolean,boolean,boolean,boolean,boolean,boolean) to aift_worker;
  end if;
end $$;

comment on function public.aift_content_context is
  'The only integration point between AIFT Studio and finance-chief research data. Returns a minimal redacted payload. Not granted to anon or authenticated.';
