-- =============================================================================
-- Policy tests for the broker-table RLS proposal.
--
-- Run against a BRANCH database that has had
-- `supabase/migrations-pending-review/0001_REVIEW_REQUIRED_broker_rls.sql`
-- applied. Never against production.
--
--   psql "$BRANCH_DATABASE_URL" -f supabase/tests/broker_rls_policy_test.sql
--
-- Every assertion raises on failure, so a clean run means every one passed.
-- =============================================================================

begin;

do $$
declare
  t text;
  v_enabled boolean;
  v_forced boolean;
  v_policies int;
  v_anon_grants int;
begin
  foreach t in array array[
    'broker_statements','broker_account_snapshots','broker_executions',
    'broker_cash_events','broker_dividends','broker_position_snapshots',
    'broker_import_audit'
  ] loop
    select c.relrowsecurity, c.relforcerowsecurity
      into v_enabled, v_forced
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relname = t;

    if v_enabled is null then
      raise exception 'TEST FAIL: table public.% does not exist', t;
    end if;
    if not v_enabled then
      raise exception 'TEST FAIL: RLS is not enabled on public.%', t;
    end if;
    if not v_forced then
      raise exception 'TEST FAIL: RLS is not FORCED on public.% (the owner would bypass it)', t;
    end if;

    select count(*) into v_policies
      from pg_policies where schemaname = 'public' and tablename = t;
    if v_policies = 0 then
      raise exception 'TEST FAIL: RLS is enabled on public.% with no policy — every non-owner read is denied', t;
    end if;

    -- A policy that is always true is not a policy.
    if exists (
      select 1 from pg_policies
       where schemaname = 'public' and tablename = t
         and 'authenticated' = any(roles)
         and coalesce(qual, '') in ('true', '(true)')
    ) then
      raise exception 'TEST FAIL: public.% has an unconditional policy for authenticated', t;
    end if;

    select count(*) into v_anon_grants
      from information_schema.role_table_grants
     where table_schema = 'public' and table_name = t and grantee = 'anon';
    if v_anon_grants > 0 then
      raise exception 'TEST FAIL: anon still holds % grant(s) on public.%', v_anon_grants, t;
    end if;

    raise notice 'ok: public.% — RLS enabled + forced, % policy(ies), no anon grants', t, v_policies;
  end loop;
end $$;

-- --- the studio's own namespace must be equally locked down -------------------

do $$
declare t text; v_enabled boolean; v_policies int;
begin
  foreach t in array array[
    'aift_brand_settings','aift_research_jobs','aift_source_documents','aift_claims',
    'aift_content_jobs','aift_content_assets','aift_quality_checks',
    'aift_review_events','aift_job_runs'
  ] loop
    select c.relrowsecurity into v_enabled
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relname = t;
    if not coalesce(v_enabled, false) then
      raise exception 'TEST FAIL: RLS is not enabled on public.%', t;
    end if;
    select count(*) into v_policies from pg_policies where schemaname = 'public' and tablename = t;
    if v_policies = 0 then
      raise exception 'TEST FAIL: public.% has no policies', t;
    end if;
  end loop;
  raise notice 'ok: every aift_* table has RLS enabled with explicit policies';
end $$;

-- --- the context function must not be callable from the browser --------------

do $$
begin
  if has_function_privilege('anon', 'public.aift_content_context(date,boolean,boolean,boolean,boolean,boolean,boolean)', 'execute') then
    raise exception 'TEST FAIL: anon can execute aift_content_context';
  end if;
  if has_function_privilege('authenticated', 'public.aift_content_context(date,boolean,boolean,boolean,boolean,boolean,boolean)', 'execute') then
    raise exception 'TEST FAIL: authenticated can execute aift_content_context (it is a server-side door only)';
  end if;
  raise notice 'ok: aift_content_context is not executable by anon or authenticated';
end $$;

-- --- the private schema must not be reachable --------------------------------

do $$
begin
  if has_schema_privilege('anon', 'private', 'usage')
     or has_schema_privilege('authenticated', 'private', 'usage') then
    raise exception 'TEST FAIL: schema private is reachable from a browser role';
  end if;
  raise notice 'ok: schema private is not reachable from anon or authenticated';
end $$;

-- --- the FSM must refuse to archive without a reviewer -----------------------

do $$
begin
  if public.aift_transition_allowed('needs_review','archived','reviewer') then
    raise exception 'TEST FAIL: needs_review -> archived must not be a legal edge (approval comes first)';
  end if;
  if public.aift_transition_allowed('needs_review','approved_for_archive','workflow') then
    raise exception 'TEST FAIL: the workflow engine must not be able to approve its own output';
  end if;
  if public.aift_transition_allowed('approved_for_archive','archived','workflow') then
    raise exception 'TEST FAIL: archiving must require a reviewer';
  end if;
  if not public.aift_transition_allowed('needs_review','approved_for_archive','reviewer') then
    raise exception 'TEST FAIL: a reviewer must be able to approve';
  end if;
  if public.aift_transition_allowed('archived','drafting','reviewer') then
    raise exception 'TEST FAIL: archived must be terminal';
  end if;
  raise notice 'ok: the database-side FSM requires a reviewer for approval and archival';
end $$;

-- --- the portfolio-values flag must be un-settable ----------------------------

do $$
declare v_ok boolean := false;
begin
  begin
    insert into public.aift_brand_settings (user_id, disclosure_text, private_context_allowlist)
    values (gen_random_uuid(), 'test',
            '{"research_topics":true,"portfolio_values":true}'::jsonb);
  exception when check_violation then
    v_ok := true;
  end;
  if not v_ok then
    raise exception 'TEST FAIL: private_context_allowlist.portfolio_values was accepted as true';
  end if;
  raise notice 'ok: portfolio_values cannot be enabled in brand settings';
end $$;

rollback;
