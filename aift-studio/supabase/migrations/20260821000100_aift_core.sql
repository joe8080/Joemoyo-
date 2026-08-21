-- =============================================================================
-- AI Finance Toolkit Studio — core schema
--
-- Every table here is owned by a single user, has RLS enabled, and has explicit
-- policies. There is no table, column or function in this file that stores or
-- exposes broker, trade, benefits, income or account data.
--
-- Review before applying. See docs/SECURITY.md for the migration process.
-- =============================================================================

create extension if not exists "pgcrypto";

-- --- enums -------------------------------------------------------------------

do $$ begin
  create type aift_content_state as enum (
    'queued','researching','evidence_ready','drafting','visual_planning',
    'rendering','qa_running','needs_review','rework_required',
    'approved_for_archive','archived','blocked'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type aift_research_state as enum ('queued','researching','evidence_ready','blocked');
exception when duplicate_object then null; end $$;

do $$ begin
  create type aift_format as enum ('deep_dive','short','radar');
exception when duplicate_object then null; end $$;

do $$ begin
  create type aift_severity as enum ('blocking','warning','note');
exception when duplicate_object then null; end $$;

do $$ begin
  create type aift_check_result as enum ('pass','fail','skipped');
exception when duplicate_object then null; end $$;

-- --- brand settings ----------------------------------------------------------

create table if not exists public.aift_brand_settings (
  user_id                  uuid primary key references auth.users(id) on delete cascade,
  channel_name             text not null default 'AI Finance Toolkit',
  voice_guide              text not null default '',
  audience_profile         text not null default '',
  visual_style_json        jsonb not null default '{}'::jsonb,
  approved_source_domains  text[] not null default '{}',
  banned_phrases           text[] not null default '{}',
  disclosure_text          text not null,
  default_video_length_minutes int not null default 10
    check (default_video_length_minutes between 1 and 60),
  shorts_enabled           boolean not null default true,
  -- Allow-list for the private research context. Every flag defaults to false.
  private_context_allowlist jsonb not null default
    '{"research_topics":false,"agent_rules":false,"intelligence_flags":false,
      "market_snapshots":false,"macro_indicators":false,"portfolio_themes":false,
      "portfolio_values":false}'::jsonb,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now(),
  -- Belt and braces: this flag may never be turned on. Portfolio values are not
  -- content input, and the constraint says so in a place nobody can overlook.
  constraint aift_no_portfolio_values
    check ((private_context_allowlist->>'portfolio_values')::boolean is not true)
);

-- --- research ----------------------------------------------------------------

create table if not exists public.aift_research_jobs (
  id                    uuid primary key default gen_random_uuid(),
  user_id               uuid not null references auth.users(id) on delete cascade,
  topic                 text not null check (length(trim(topic)) > 0),
  ticker                text,
  job_type              aift_format not null default 'deep_dive',
  source_policy_version text not null,
  status                aift_research_state not null default 'queued',
  reference_date        date not null,
  search_plan           jsonb,
  brief                 jsonb,
  created_at            timestamptz not null default now(),
  completed_at          timestamptz,
  failure_reason        text,
  -- Re-running the same topic on the same reference date is the same job.
  unique (user_id, topic, reference_date, job_type)
);
create index if not exists aift_research_jobs_user_status_idx
  on public.aift_research_jobs (user_id, status, created_at desc);

create table if not exists public.aift_source_documents (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references auth.users(id) on delete cascade,
  research_job_id   uuid not null references public.aift_research_jobs(id) on delete cascade,
  canonical_url     text not null,
  publisher         text not null default '',
  published_at      date,
  accessed_at       timestamptz not null default now(),
  source_tier       text not null,
  title             text not null default '',
  excerpt           text not null default '',
  content_hash      text not null default '',
  licence_notes     text not null default '',
  retrieval_status  text not null default 'fetched'
    check (retrieval_status in ('fetched','failed','blocked_by_policy')),
  created_at        timestamptz not null default now(),
  -- Idempotency: the same URL in the same job is one record, always.
  unique (research_job_id, canonical_url)
);

create table if not exists public.aift_claims (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references auth.users(id) on delete cascade,
  research_job_id     uuid not null references public.aift_research_jobs(id) on delete cascade,
  claim_id            text not null,
  claim_text          text not null,
  claim_type          text not null,
  source_document_ids uuid[] not null default '{}',
  source_excerpt      text not null default '',
  as_of_date          date,
  confidence          numeric(4,3) not null check (confidence >= 0 and confidence <= 1),
  uncertainty_note    text not null default '',
  review_status       text not null default 'unreviewed'
    check (review_status in ('unreviewed','accepted','rejected')),
  is_public_safe      boolean not null default false,
  public_safe_reason  text not null default '',
  created_at          timestamptz not null default now(),
  unique (research_job_id, claim_id)
);
create index if not exists aift_claims_job_safe_idx
  on public.aift_claims (research_job_id, is_public_safe);

-- --- content -----------------------------------------------------------------

create table if not exists public.aift_content_jobs (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references auth.users(id) on delete cascade,
  research_job_id    uuid not null references public.aift_research_jobs(id) on delete cascade,
  format             aift_format not null,
  working_title      text not null default '',
  status             aift_content_state not null default 'queued',
  review_stage       text not null default 'created',
  script_version     int not null default 0,
  asset_manifest_url text,
  editorial_plan     jsonb,
  script             jsonb,
  scene_plan         jsonb,
  thumbnail_brief    jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  approved_at        timestamptz,
  approved_by        uuid references auth.users(id),
  archived_at        timestamptz,
  unique (research_job_id, format),
  -- An approved job must name who approved it. Approval is an act by a person.
  constraint aift_approval_has_actor
    check ((status not in ('approved_for_archive','archived')) or approved_by is not null)
);
create index if not exists aift_content_jobs_user_status_idx
  on public.aift_content_jobs (user_id, status, created_at desc);

create table if not exists public.aift_content_assets (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id) on delete cascade,
  content_job_id   uuid not null references public.aift_content_jobs(id) on delete cascade,
  asset_type       text not null,
  storage_key      text not null,
  sha256           text not null default '',
  generator        text not null default '',
  prompt_version   text not null default '',
  source_claim_ids text[] not null default '{}',
  status           text not null default 'draft' check (status in ('draft','final','superseded')),
  duration_seconds numeric,
  aspect_ratio     text,
  bytes            bigint not null default 0,
  created_at       timestamptz not null default now(),
  unique (content_job_id, asset_type, storage_key)
);

create table if not exists public.aift_quality_checks (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  content_job_id uuid not null references public.aift_content_jobs(id) on delete cascade,
  gate           text not null,
  check_name     text not null,
  severity       aift_severity not null default 'blocking',
  result         aift_check_result not null,
  details_json   jsonb not null default '{}'::jsonb,
  run_at         timestamptz not null default now(),
  resolved_at    timestamptz,
  unique (content_job_id, gate, check_name)
);

create table if not exists public.aift_review_events (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id) on delete cascade,
  content_job_id   uuid not null references public.aift_content_jobs(id) on delete cascade,
  reviewer_id      uuid not null references auth.users(id),
  decision         text not null
    check (decision in ('approved_for_archive','rework_required','archived','unblocked')),
  reason_codes     text[] not null default '{}',
  freeform_feedback text not null default '',
  created_at       timestamptz not null default now()
);

create table if not exists public.aift_job_runs (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id) on delete cascade,
  job_type        text not null,
  idempotency_key text not null,
  status          text not null default 'running'
    check (status in ('running','succeeded','failed','skipped_duplicate')),
  started_at      timestamptz not null default now(),
  finished_at     timestamptz,
  attempt_count   int not null default 0,
  error_summary   text,
  trace_json      jsonb not null default '[]'::jsonb,
  provider_calls  jsonb not null default '[]'::jsonb,
  trace_url       text,
  -- The idempotency guarantee, expressed where it cannot be bypassed.
  unique (user_id, job_type, idempotency_key)
);

-- =============================================================================
-- Finite state machine
--
-- The TypeScript engine mirrors this table exactly and a test asserts the two
-- never drift. Enforcing it here as well means a direct SQL update — from psql,
-- from a future service, from anywhere — cannot skip review.
-- =============================================================================

create or replace function public.aift_transition_allowed(
  p_from aift_content_state,
  p_to   aift_content_state,
  p_actor text
) returns boolean
language sql immutable as $$
  select case
    when p_from = p_to then false
    when p_from = 'archived' then false
    -- Human-only transitions.
    when (p_from, p_to) in (
      ('needs_review','approved_for_archive'),
      ('needs_review','rework_required'),
      ('approved_for_archive','archived'),
      ('blocked','drafting')
    ) then p_actor = 'reviewer'
    -- Workflow transitions.
    when (p_from, p_to) in (
      ('queued','researching'),
      ('researching','evidence_ready'),
      ('evidence_ready','drafting'),
      ('drafting','visual_planning'),
      ('visual_planning','rendering'),
      ('rendering','qa_running'),
      ('qa_running','needs_review'),
      ('rework_required','drafting')
    ) then true
    -- Any pre-review stage may be blocked.
    when p_to = 'blocked' and p_from in (
      'queued','researching','evidence_ready','drafting',
      'visual_planning','rendering','qa_running'
    ) then true
    else false
  end;
$$;

create or replace function public.aift_enforce_transition()
returns trigger language plpgsql as $$
declare
  v_actor text := coalesce(current_setting('aift.actor', true), 'workflow');
begin
  if new.status is distinct from old.status then
    if not public.aift_transition_allowed(old.status, new.status, v_actor) then
      raise exception
        'illegal content-job transition % -> % for actor %', old.status, new.status, v_actor
        using errcode = 'check_violation';
    end if;

    if new.status in ('approved_for_archive','archived') then
      if v_actor <> 'reviewer' then
        raise exception 'only an authenticated reviewer may move a job to %', new.status
          using errcode = 'insufficient_privilege';
      end if;
      new.approved_by := coalesce(new.approved_by, auth.uid());
      if new.approved_by is null then
        raise exception 'approval requires an authenticated user' using errcode = 'insufficient_privilege';
      end if;
    end if;

    if new.status = 'approved_for_archive' then new.approved_at := coalesce(new.approved_at, now()); end if;
    if new.status = 'archived' then new.archived_at := coalesce(new.archived_at, now()); end if;
  end if;

  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists aift_content_jobs_transition on public.aift_content_jobs;
create trigger aift_content_jobs_transition
  before update on public.aift_content_jobs
  for each row execute function public.aift_enforce_transition();

-- =============================================================================
-- Row Level Security — enabled on every table, owner-scoped, no exceptions.
-- =============================================================================

do $$
declare t text;
begin
  foreach t in array array[
    'aift_brand_settings','aift_research_jobs','aift_source_documents','aift_claims',
    'aift_content_jobs','aift_content_assets','aift_quality_checks',
    'aift_review_events','aift_job_runs'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('alter table public.%I force row level security', t);
    execute format('drop policy if exists %I on public.%I', t || '_owner_select', t);
    execute format('drop policy if exists %I on public.%I', t || '_owner_insert', t);
    execute format('drop policy if exists %I on public.%I', t || '_owner_update', t);
    execute format('drop policy if exists %I on public.%I', t || '_owner_delete', t);

    execute format(
      'create policy %I on public.%I for select to authenticated using (user_id = auth.uid())',
      t || '_owner_select', t);
    execute format(
      'create policy %I on public.%I for insert to authenticated with check (user_id = auth.uid())',
      t || '_owner_insert', t);
    execute format(
      'create policy %I on public.%I for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid())',
      t || '_owner_update', t);
    execute format(
      'create policy %I on public.%I for delete to authenticated using (user_id = auth.uid())',
      t || '_owner_delete', t);
  end loop;
end $$;

-- A review event is a historical record of a decision. It is never edited.
drop policy if exists aift_review_events_owner_update on public.aift_review_events;
drop policy if exists aift_review_events_owner_delete on public.aift_review_events;

-- `anon` gets nothing anywhere in this namespace.
do $$
declare t text;
begin
  foreach t in array array[
    'aift_brand_settings','aift_research_jobs','aift_source_documents','aift_claims',
    'aift_content_jobs','aift_content_assets','aift_quality_checks',
    'aift_review_events','aift_job_runs'
  ] loop
    execute format('revoke all on public.%I from anon', t);
  end loop;
end $$;

comment on table public.aift_content_jobs is
  'One video. Reaches `archived` only through an authenticated reviewer decision. There is no published state: this system does not upload.';
