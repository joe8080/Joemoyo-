# Phase 3 — Dashboard

**Goal:** see the account live in a browser/phone.

`dashboard/app.py` (Streamlit) shows: headline metrics (equity/cash/buying
power/open P&L), a 1-month equity curve, open positions with P&L, open and
filled orders, per-symbol candlesticks with the SMA overlay + current signal, a
built-in backtest runner, the Journal & Coach tabs (Phase 7), the scorecard
(Phase 9), and a tail of the activity log.

## Run / deploy
```bash
streamlit run dashboard/app.py     # http://localhost:8501
```
Free hosting on **Streamlit Community Cloud**: connect the GitHub repo, pick
`dashboard/app.py`, and paste secrets (`ALPACA_*`, optional `SUPABASE_*`) into
Settings → Secrets. The app mirrors `st.secrets` into env so the same modules
work locally (`.env`) and hosted.

## Gotchas
- **Ephemeral filesystem on Streamlit Cloud:** anything written at runtime resets
  on restart. Persist via Supabase (Phase 8), not local files.
- **Private repos** aren't visible to Streamlit until you grant access (or paste
  the `owner/repo` directly). The URL is public — don't share it if you'd rather
  keep the account view private.
- Cache Alpaca calls (`st.cache_data(ttl=...)`) so refreshes don't hammer the API.
