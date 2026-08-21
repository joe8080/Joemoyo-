-- =============================================================================
-- PROPOSAL — NOT PART OF THE APPLIED MIGRATION SET
--
-- This file lives in `supabase/migrations-pending-review/`, which no tool in
-- this repository applies. It is here to be read, argued with, tested against a
-- branch database, and only then moved into `supabase/migrations/`.
--
-- FINDING
-- A schema-only inspection of project `qxwfrsoztfddwicqtuar` ("finance chief")
-- found seven broker-import tables with Row Level Security DISABLED:
--
--   broker_statements, broker_account_snapshots, broker_executions,
--   broker_cash_events, broker_dividends, broker_position_snapshots,
--   broker_import_audit
--
-- With RLS off, any role holding a table grant can read every row. Postgres
-- applies RLS only when it is enabled; the service-role key bypasses it
-- entirely. So the exposure depends on which roles hold grants — which is why
-- step 0 below is an inspection, not a change.
--
-- WHY THIS IS NOT APPLIED AUTOMATICALLY
-- Enabling RLS with no matching policy denies *all* access to non-owner roles.
-- If an existing importer, dashboard, scheduled job or notebook reads these
-- tables through `authenticated` or a custom role, enabling RLS without first
-- writing its policy will break it silently at the next run. Locking a door is
-- only safe once you know who is currently walking through it.
--
-- AIFT Studio itself does not need these tables. It never queries them, and
-- `npm run guard:no-secrets` fails the build if any client module names one.
-- This proposal exists because the finding is real, not because the studio
-- depends on it being fixed.
--
-- =============================================================================
-- STEP 0 — INSPECT FIRST. Run these read-only queries and read the output
--          before running anything below them.
-- =============================================================================

-- 0a. Confirm the current state.
--
--   select c.relname,
--          c.relrowsecurity  as rls_enabled,
--          c.relforcerowsecurity as rls_forced,
--          (select count(*) from pg_policies p
--            where p.schemaname = 'public' and p.tablename = c.relname) as policy_count
--     from pg_class c
--     join pg_namespace n on n.oid = c.relnamespace
--    where n.nspname = 'public'
--      and c.relname like 'broker_%'
--    order by c.relname;

-- 0b. Who currently holds grants? This is the list of things that will break.
--
--   select table_name, grantee, string_agg(privilege_type, ', ' order by privilege_type) as privs
--     from information_schema.role_table_grants
--    where table_schema = 'public'
--      and table_name like 'broker_%'
--      and grantee not in ('postgres', 'supabase_admin')
--    group by table_name, grantee
--    order by table_name, grantee;

-- 0c. Does every table have an ownership column to write a policy against?
--
--   select table_name,
--          bool_or(column_name = 'user_id') as has_user_id,
--          bool_or(column_name = 'owner_id') as has_owner_id,
--          bool_or(column_name = 'account_id') as has_account_id
--     from information_schema.columns
--    where table_schema = 'public' and table_name like 'broker_%'
--    group by table_name order by table_name;

-- If 0c shows a table with no ownership column, STOP. Add and backfill one in a
-- separate, earlier migration. A policy cannot be written against a column that
-- does not exist, and `using (true)` is not a policy — it is RLS theatre.

-- =============================================================================
-- STEP 1 — Backfill guard.
-- Refuses to proceed if any row would become unreachable. Better to fail the
-- migration than to enable RLS over rows whose owner is unknown.
-- =============================================================================

do $$
declare
  t text;
  n bigint;
begin
  foreach t in array array[
    'broker_statements','broker_account_snapshots','broker_executions',
    'broker_cash_events','broker_dividends','broker_position_snapshots',
    'broker_import_audit'
  ] loop
    if not exists (
      select 1 from information_schema.columns
       where table_schema = 'public' and table_name = t and column_name = 'user_id'
    ) then
      raise exception
        'aborting: public.% has no user_id column. Add and backfill ownership before enabling RLS.', t;
    end if;

    execute format('select count(*) from public.%I where user_id is null', t) into n;
    if n > 0 then
      raise exception
        'aborting: public.% has % row(s) with a null user_id. Those rows would become unreachable.', t, n;
    end if;
  end loop;
end $$;

-- =============================================================================
-- STEP 2 — Enable RLS and write owner policies.
-- =============================================================================

do $$
declare t text;
begin
  foreach t in array array[
    'broker_statements','broker_account_snapshots','broker_executions',
    'broker_cash_events','broker_dividends','broker_position_snapshots',
    'broker_import_audit'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    -- FORCE applies the policy to the table owner too, so a superuser-owned
    -- connection does not quietly sail past it.
    execute format('alter table public.%I force row level security', t);

    execute format('drop policy if exists %I on public.%I', t || '_owner_rw', t);
    execute format(
      'create policy %I on public.%I for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid())',
      t || '_owner_rw', t);

    -- `anon` has no business here under any circumstances.
    execute format('revoke all on public.%I from anon', t);

    execute format('alter table public.%I alter column user_id set not null', t);
  end loop;
end $$;

-- =============================================================================
-- STEP 3 — The importer.
--
-- If a server-side importer writes these tables, give it a dedicated role and a
-- policy, rather than leaving it on the service-role key. A key that bypasses
-- RLS is a key whose blast radius is the whole database.
--
-- Uncomment and adapt once step 0b has told you what the importer actually is.
-- =============================================================================

-- do $$ begin
--   if not exists (select 1 from pg_roles where rolname = 'broker_importer') then
--     create role broker_importer nologin;
--   end if;
-- end $$;
--
-- do $$
-- declare t text;
-- begin
--   foreach t in array array[
--     'broker_statements','broker_account_snapshots','broker_executions',
--     'broker_cash_events','broker_dividends','broker_position_snapshots',
--     'broker_import_audit'
--   ] loop
--     execute format('grant select, insert, update on public.%I to broker_importer', t);
--     execute format('drop policy if exists %I on public.%I', t || '_importer', t);
--     execute format(
--       'create policy %I on public.%I for all to broker_importer using (true) with check (true)',
--       t || '_importer', t);
--   end loop;
-- end $$;

-- =============================================================================
-- STEP 4 — Verify. Run `supabase/tests/broker_rls_policy_test.sql` against a
-- BRANCH database and confirm every assertion passes before promoting this file.
-- =============================================================================

-- ROLLBACK, if step 0b turns out to have missed a consumer:
--
--   do $$ declare t text; begin
--     foreach t in array array[
--       'broker_statements','broker_account_snapshots','broker_executions',
--       'broker_cash_events','broker_dividends','broker_position_snapshots',
--       'broker_import_audit'
--     ] loop
--       execute format('alter table public.%I disable row level security', t);
--     end loop;
--   end $$;
--
-- Note that rolling back restores the exposure. Prefer fixing the broken
-- consumer's policy over turning the protection off again.
