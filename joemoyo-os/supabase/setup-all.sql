-- ============================================================
-- JoeMoyo OS — full vault setup. Paste ALL of this into your
-- Supabase project → SQL Editor → New query → Run.
-- Safe to re-run (uses IF NOT EXISTS / OR REPLACE-style guards).
-- ============================================================

-- ---------- Content Studio ----------
create table if not exists public.studio_content (
  id uuid primary key default gen_random_uuid(),
  task text not null,
  brand text not null,
  topic text,
  provider text,
  markdown text not null,
  created_at timestamptz not null default now()
);

-- ---------- Investing ----------
create table if not exists public.holdings (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  shares numeric not null default 0,
  cost_basis numeric not null default 0,
  account text,
  updated_at timestamptz not null default now()
);

-- ---------- Social ----------
create table if not exists public.social_accounts (
  provider text primary key,
  channel_id text,
  channel_title text,
  access_token text not null,
  refresh_token text not null default '',
  expires_at timestamptz not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  platform text not null,
  content text not null,
  scheduled_for timestamptz,
  status text not null default 'scheduled',
  created_at timestamptz not null default now()
);

-- ---------- Row Level Security ----------
alter table public.studio_content  enable row level security;
alter table public.holdings        enable row level security;
alter table public.social_accounts enable row level security;  -- tokens: no client policy
alter table public.scheduled_posts enable row level security;

-- Authenticated reads (the OS server uses the service-role key and bypasses RLS).
do $$
begin
  if not exists (select 1 from pg_policies where tablename='studio_content' and policyname='owner reads studio_content') then
    create policy "owner reads studio_content" on public.studio_content for select to authenticated using (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='holdings' and policyname='owner reads holdings') then
    create policy "owner reads holdings" on public.holdings for select to authenticated using (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='scheduled_posts' and policyname='owner reads scheduled_posts') then
    create policy "owner reads scheduled_posts" on public.scheduled_posts for select to authenticated using (true);
  end if;
end $$;

-- ---------- Optional: your starting positions (edit then uncomment) ----------
-- insert into public.holdings (symbol, shares, cost_basis, account) values
--   ('AAPL', 10, 180.50, 'ISA'),
--   ('NVDA', 5, 95.20, 'GIA');
