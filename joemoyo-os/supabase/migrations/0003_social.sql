-- Social module — connected accounts and the scheduling queue.
-- Run in your Supabase SQL editor. The OS server uses the service-role key.

-- OAuth tokens for connected platforms (start with YouTube).
create table if not exists public.social_accounts (
  provider text primary key,            -- 'youtube', later 'instagram', ...
  channel_id text,
  channel_title text,
  access_token text not null,
  refresh_token text not null default '',
  expires_at timestamptz not null,
  updated_at timestamptz not null default now()
);

-- Drafted/queued posts. A worker publishes rows whose scheduled_for has passed.
create table if not exists public.scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  platform text not null,
  content text not null,
  scheduled_for timestamptz,
  status text not null default 'scheduled',   -- scheduled | published | failed
  created_at timestamptz not null default now()
);

-- Tokens are secret: RLS on, no client policies. Server (service role) bypasses RLS.
alter table public.social_accounts enable row level security;
alter table public.scheduled_posts enable row level security;

create policy "owner reads scheduled_posts"
  on public.scheduled_posts for select to authenticated using (true);
