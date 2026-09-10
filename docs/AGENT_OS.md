# Agent OS — the board

One screen for every agent: who is working, who needs you, what each one did
last, and the socket to plug a new one in.

The control plane is the Chief's Agent OS in Supabase ("finance chief"
project): the `agent_ops_roster` hierarchy, task queue, approvals, events and
per-agent keys, fronted by the `agent-os` edge function. This repo adds the
board page, plugs its own agents into that roster, and gives you a runner
that executes tasks for them.

## Open the board

1. Go to your gateway URL — the `agent-os` edge function
   (`https://<project-ref>.supabase.co/functions/v1/agent-os`; `/mj` is an alias).
2. Press **Connect** and paste the Agent OS admin key (starts with `mjos_`).
   It stays in that browser. The board refreshes every 15 s.
3. Press **Read out** to hear the headline, anything needing attention,
   approvals waiting, and what is running.

## What the board shows

- **Commander strip** — Mary Jane (the Chief), the headline, and four tiles you
  can press to filter: Working now · Need attention · Waiting on you · Resting.
- **Numbers** — the latest `agent_ops_metrics` (book value, risk regime, …).
- **Teams** — every supervisor with their agents. A card shows the state pill,
  what it is doing now or did last, its numbers, when it was last seen, and
  buttons: **Run** (built-ins) / **Task** (any agent), **Pause**/**Resume**,
  **Connect** (not yet OS-linked), **Open** (its logs).
- **Waiting on you** — approval gates with Approve / Reject.
- **Open tasks** and **Activity** — the OS task queue and the work log
  (`agent_ops_runs` + lifecycle events).

State pills: Running · Online · Working (telemetry in the last 20 min) ·
Seen recently · Done · Resting · Paused · Not plugged in (no key yet) ·
Logical role · and the red ones: Error · Failed · Stalled · Offline.

## Plug in an agent (n8n, Zapier, a script, another Claude or Grok)

Press **Plug in an agent**, give it a name, a supervisor and what it does. You
get a one-time key and a ready-made check-in call. The agent then POSTs to the
gateway with header `x-agent-key: <key>`:

```json
{"action": "heartbeat", "status": "running", "task": "Sorting 14 receipts"}
{"action": "heartbeat", "status": "done", "result": "12 filed", "metrics": {"receipts": 12}}
{"action": "heartbeat", "status": "error", "note": "Sheets quota exceeded — retry 07:40"}
```

Statuses: `running` · `done` · `idle` · `error` · `online`. `done`/`error` also
write a row to the OS work log. The reply carries `"paused": true` when you
pressed Pause — a well-behaved agent skips its cycle then. Agents can also
`pull_tasks`, `claim_task`, `start_task`, `complete_task`/`fail_task`,
`request_approval`, `emit_event`, `permissions`, `context`, `whoami`.

Existing agents that show **Not plugged in** get a key with the card's
**Connect** button — paste it into that agent as `x-agent-key`.

## The repo's agents

They are registered in the roster under the right supervisors:

| agent_key | reports to | runs where |
|---|---|---|
| `swing_trader`, `trading_coach` | finance_supervisor | GitHub Actions |
| `intraday_trader` | finance_supervisor | Railway (always on) |
| `trading_analyst` | finance_supervisor | OS Runner |
| `history_researcher`, `history_script_writer` | originex_supervisor | OS Runner |
| `finance_analyst_writer`, `finance_script_writer`, `marketing_writer` | content_supervisor | OS Runner |
| `studio_lead_generator`, `shopify_reporter` | venture_supervisor | OS Runner |
| `agent_os_runner` | systems_supervisor | wherever you run `os worker` |

Each host needs two variables (from `.env.example`):

```
AGENT_OS_URL=https://<project-ref>.supabase.co/functions/v1/agent-os
AGENT_OS_KEYS={"swing_trader": "agent_…", "trading_coach": "agent_…"}
```

- GitHub Actions → repo Settings → Secrets → `AGENT_OS_URL`, `AGENT_OS_KEYS`
  (the swing trader and coach keys). The workflows already pass them through.
- Railway intraday service → Variables → the same two (intraday key).
- Your laptop / a Railway "runner" service → the runner + on-demand agent keys,
  then `python main.py os worker`.

Without them the agents run exactly as before; they just don't appear live.

### The OS Runner

```
python main.py os worker
```

Heartbeats every agent it holds a key for, pulls their tasks from the OS,
executes them (`agent_os/runners.py`), and completes or fails them. **Run** on
a card creates such a task; so does the Chief delegating work to one of them.
Runs happen one at a time.

### Re-issuing keys

`python main.py os connect` registers all built-ins again and prints fresh
keys (needs `AGENT_OS_ADMIN_KEY` in your shell — your machine only). Old keys
stop working. `--only swing_trader,trading_coach` limits it.

## Updating the board or the gateway

- Board page: edit `agent_os/board.html`, then `python main.py os publish-board`
  (needs `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`). Live within a minute; no
  redeploy.
- Gateway: `agent_os/edge/agent-os/index.ts` is the Chief's function plus the
  additive actions the board uses (`whoami`, richer `heartbeat`, `dashboard`
  extras, board metadata on register/issue). Deploy with the Supabase CLI:
  `cd agent_os/edge && supabase functions deploy agent-os --no-verify-jwt`.

## Rules baked in

- Never put the admin key or a Supabase service-role key inside a worker.
- Real-money trading is denied at the OS level; the trading bots are paper only
  and the board's "Dry-run cycle" places nothing.
- External actions default to approval — that is the "Waiting on you" panel.
