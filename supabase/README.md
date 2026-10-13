# Mary Jane — agent on the finance chief database

Mary Jane is a Claude agent that reads the finance chief Supabase database,
answers questions, logs her calls, gets graded on them and learns from the
grades.

## How the learning loop works

1. **Ask.** You chat on the dashboard page (`dashboard/pages/1_Mary_Jane.py`).
   The `mj-agent` edge function runs Claude with read-only SQL access.
2. **Log.** When she gives a real call on a ticker (BUY, ADD, HOLD, TRIM, SELL,
   AVOID or WATCH), she logs it to `mj_recommendations` with the price,
   position and risk regime at that moment.
3. **Grade.** Every night at 21:45 UTC, `mj_grade_due_evaluations()` scores each
   call against SPY at 30, 90 and 365 days.
4. **Reflect.** Every Saturday at 07:50 UTC (or on the dashboard button), she
   reviews the graded calls plus your own trade record. She then writes or
   retires lessons in `mj_semantic_memories`.
5. **Apply.** Every new conversation starts with those lessons and her
   calibration table, so later calls are made knowing how earlier ones went.

She cannot trade. Her database access is read only. The read-only role can't
see secret or personal tables: API configs, Telegram, health, care, benefits,
contacts and the SCIP property data.

## Files

| File | What it is |
|---|---|
| `migrations/20261013_mj_learning_loop.sql` | Read-only role, grader, track-record views, run log, benchmark prices, schedules |
| `functions/mj-agent/` | The agent (Deno edge function) |
| `../dashboard/pages/1_Mary_Jane.py` | The dashboard page (Streamlit) |

## Go-live steps

1. Apply the migration to the finance chief project.
2. Deploy the function: `supabase functions deploy mj-agent --no-verify-jwt`.
   It does its own token check.
3. In Supabase, go to **Edge Functions → Secrets** and add `ANTHROPIC_API_KEY`.
4. Store the dashboard token in vault as `MJ_AGENT_TOKEN`, so the weekly
   reflection can call the function.
5. In Streamlit, go to **App settings → Secrets** and add
   `MJ_DASHBOARD_TOKEN = "mjt_..."`.
6. Open the **Mary Jane** page, then press **Run reflection now** once to seed
   the first lessons from your trade history.

## Cost

The agent runs on Claude Opus 5.5. A typical question costs roughly $0.10 to
$0.40, and a weekly reflection roughly $0.30 to $0.80. The **Runs & cost** tab
shows the real figure for every run.
