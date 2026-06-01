-- ============================================================================
-- DRAFT MIGRATION 001 — Video Production Schema
-- Project: ORIGINEX HUMAN ARCHIVES (qvlllknedilztozxwscj)
--
-- STATUS: DRAFT — review before applying. Apply via Supabase MCP `apply_migration`
--         (or the SQL editor) only after operator sign-off.
--
-- Purpose: make Supabase the source of truth for the JoeMoyo video production
-- crew. Episodes originate from the existing `content_ideas` backlog and link
-- to the existing knowledge graph (people / events / places / civilizations /
-- citations / documents) so every on-screen claim stays sourced. No existing
-- table is modified; all new objects are prefixed `video_`.
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists moddatetime schema extensions;

-- ----------------------------------------------------------------------------
-- video_episodes — one row per video, the spine of the pipeline.
-- ----------------------------------------------------------------------------
create table if not exists public.video_episodes (
    id                  uuid primary key default extensions.uuid_generate_v4(),
    content_idea_id     uuid references public.content_ideas(id) on delete set null,
    title               text not null,
    slug                text not null unique,
    channel             text not null default 'history_channel',
    topic               text,
    status              text not null default 'draft'
                        check (status = any (array[
                            'draft','researching','scripting','visualizing',
                            'voicing','assembling','rendering','rendered',
                            'published','archived'])),
    target_minutes      numeric default 12,
    -- Links into the existing knowledge graph (mirrors content_ideas.related_*)
    related_documents     uuid[] default '{}',
    related_people        uuid[] default '{}',
    related_events        uuid[] default '{}',
    related_places        uuid[] default '{}',
    related_civilizations uuid[] default '{}',
    related_citations     uuid[] default '{}',
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- video_agent_outputs — append-only log of each crew agent's output.
-- One row per (episode, role) run; latest by created_at is current.
-- ----------------------------------------------------------------------------
create table if not exists public.video_agent_outputs (
    id          uuid primary key default extensions.uuid_generate_v4(),
    episode_id  uuid not null references public.video_episodes(id) on delete cascade,
    role        text not null
                check (role = any (array[
                    'research','script','packaging','thumbnail','visual',
                    'motion','voiceover','manifest','director'])),
    payload     jsonb not null default '{}',   -- structured output (json artifacts)
    content_md  text,                          -- human-facing markdown, if any
    model       text,
    created_at  timestamptz not null default now()
);
create index if not exists video_agent_outputs_episode_role_idx
    on public.video_agent_outputs (episode_id, role, created_at desc);

-- ----------------------------------------------------------------------------
-- video_assets — binary artifacts (in Supabase Storage) + their metadata.
-- ----------------------------------------------------------------------------
create table if not exists public.video_assets (
    id           uuid primary key default extensions.uuid_generate_v4(),
    episode_id   uuid not null references public.video_episodes(id) on delete cascade,
    kind         text not null
                 check (kind = any (array[
                     'image','thumbnail','narration','music','clip',
                     'card','mp4','srt','other'])),
    sequence     integer,                       -- ordering for image/clip sets
    storage_path text,                          -- path within the storage bucket
    public_url   text,
    prompt       text,                          -- generation prompt (image/thumb)
    citation_id  uuid references public.citations(id) on delete set null,
    meta         jsonb default '{}',
    created_at   timestamptz not null default now()
);
create index if not exists video_assets_episode_kind_idx
    on public.video_assets (episode_id, kind, sequence);

-- ----------------------------------------------------------------------------
-- video_manifest — the render contract (video_agent manifest + Remotion props).
-- ----------------------------------------------------------------------------
create table if not exists public.video_manifest (
    id             uuid primary key default extensions.uuid_generate_v4(),
    episode_id     uuid not null unique references public.video_episodes(id) on delete cascade,
    manifest       jsonb,        -- video_agent clips[] schema
    remotion_props jsonb,        -- Remotion composition props
    srt            text,         -- burnt-in captions
    captions       jsonb,        -- word/segment timings from ElevenLabs
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- render_jobs — one row per render attempt.
-- ----------------------------------------------------------------------------
create table if not exists public.render_jobs (
    id               uuid primary key default extensions.uuid_generate_v4(),
    episode_id       uuid not null references public.video_episodes(id) on delete cascade,
    engine           text not null default 'remotion'
                     check (engine = any (array['remotion','ffmpeg'])),
    status           text not null default 'queued'
                     check (status = any (array['queued','running','succeeded','failed'])),
    out_path         text,
    out_url          text,
    logs             text,
    duration_seconds numeric,
    created_at       timestamptz not null default now(),
    finished_at      timestamptz
);
create index if not exists render_jobs_episode_idx
    on public.render_jobs (episode_id, created_at desc);

-- ----------------------------------------------------------------------------
-- video_decision_log — audit trail for every agent write (per supabase_client
-- discipline; scoped so it never collides with other projects' decision_log).
-- ----------------------------------------------------------------------------
create table if not exists public.video_decision_log (
    id          uuid primary key default extensions.uuid_generate_v4(),
    episode_id  uuid references public.video_episodes(id) on delete set null,
    agent       text,
    action      text,
    payload     jsonb,
    sql_text    text,
    created_at  timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- updated_at triggers (moddatetime), matching the archive's convention.
-- ----------------------------------------------------------------------------
drop trigger if exists set_updated_at on public.video_episodes;
create trigger set_updated_at before update on public.video_episodes
    for each row execute function extensions.moddatetime (updated_at);

drop trigger if exists set_updated_at on public.video_manifest;
create trigger set_updated_at before update on public.video_manifest
    for each row execute function extensions.moddatetime (updated_at);

-- ----------------------------------------------------------------------------
-- RLS — enabled on every new table. Writes go through the service_role key
-- (which bypasses RLS), matching how the rest of this project operates.
-- No anon policies are added: video production data is operator-only.
-- ----------------------------------------------------------------------------
alter table public.video_episodes      enable row level security;
alter table public.video_agent_outputs enable row level security;
alter table public.video_assets        enable row level security;
alter table public.video_manifest      enable row level security;
alter table public.render_jobs         enable row level security;
alter table public.video_decision_log  enable row level security;

-- ----------------------------------------------------------------------------
-- Storage bucket for generated assets (images, narration, renders).
-- ----------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('video-assets', 'video-assets', false)
on conflict (id) do nothing;
