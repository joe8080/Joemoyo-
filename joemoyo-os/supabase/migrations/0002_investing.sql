-- Investing module — holdings the OS reads to build your portfolio.
-- Run in your Supabase SQL editor. The OS server uses the service-role key.

create table if not exists public.holdings (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  shares numeric not null default 0,
  cost_basis numeric not null default 0,   -- average cost per share
  account text,                            -- e.g. ISA, GIA, crypto
  updated_at timestamptz not null default now()
);

alter table public.holdings enable row level security;

create policy "owner reads holdings"
  on public.holdings for select to authenticated using (true);

-- Example rows (edit to your real positions):
-- insert into public.holdings (symbol, shares, cost_basis, account) values
--   ('AAPL', 10, 180.50, 'ISA'),
--   ('NVDA', 5, 95.20, 'GIA'),
--   ('VWRP.L', 40, 105.00, 'ISA');
