-- Jarvis: lock down the seven Vault tables that still have Row Level Security
-- switched off. Run this in the finance-chief project SQL editor.
--
-- What changes: the anon and authenticated keys (browser dashboards, public
-- clients) can no longer read or write these tables. The service-role key
-- that Jarvis, n8n and the trading engine use bypasses RLS, so nothing
-- server-side breaks.
--
-- If a dashboard or automation of yours uses the ANON key against one of
-- these tables, uncomment the matching read policy at the bottom first.

ALTER TABLE public.kpi_definitions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_kpi_series         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.management_promise_ledger  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.t212_sync_requests         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.t212_api_config            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.t212_ticker_map            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telegram_config            ENABLE ROW LEVEL SECURITY;

-- Optional: read-only access for signed-in users on the non-secret tables.
-- t212_api_config and telegram_config hold configuration and must stay
-- service-role only.
--
-- CREATE POLICY "authenticated read" ON public.kpi_definitions
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "authenticated read" ON public.company_kpi_series
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "authenticated read" ON public.management_promise_ledger
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "authenticated read" ON public.t212_ticker_map
--   FOR SELECT TO authenticated USING (true);
