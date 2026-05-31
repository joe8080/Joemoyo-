-- Content Studio output saved to the Vault.
-- Run in your Supabase project (SQL editor) to enable "save to vault".

create table if not exists public.studio_content (
  id uuid primary key default gen_random_uuid(),
  task text not null,
  brand text not null,
  topic text,
  provider text,
  markdown text not null,
  created_at timestamptz not null default now()
);

alter table public.studio_content enable row level security;

-- Server uses the service-role key (bypasses RLS). This policy lets an
-- authenticated owner read their own rows from the browser later.
create policy "owner reads studio_content"
  on public.studio_content for select
  to authenticated
  using (true);
