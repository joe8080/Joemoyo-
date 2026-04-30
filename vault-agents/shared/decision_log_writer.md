# Shared: decision_log writer + advise envelope

## decision_log row shape
The current `decision_log` table is in use (8 rows). Confirm columns
on first run; if columns differ from the canonical shape below,
surface and ask before writing.

Canonical shape (proposed; align to whatever exists):
```
id          uuid (default gen_random_uuid)
ts          timestamptz (default now())
agent       text                 -- 'orchestrator' | 'ogx' | 'invest' | 'scip'
intent      text                 -- sub-task name, e.g. 'verify_claim'
status      text                 -- 'applied' | 'surfaced' | 'cancelled'
                                 -- | 'refused' | 'refused_deprivation'
                                 -- | 'blocked' | 'error'
summary     text                 -- one-line human-readable
payload     jsonb                -- structured details
error       text                 -- nullable; only on status='error'
```

## When to log
- **Always** on any write (insert/update/delete).
- **Always** on a refusal (`refused`, `refused_deprivation`, `blocked`).
- **Always** on an error.
- On read-only sweeps: only when at least one flag was raised.
- Health checks / no-op reads: do NOT log (avoids table swamping).

## Append-only discipline
The agents must not UPDATE or DELETE `decision_log` rows. If an entry
needs a correction, INSERT a new row referencing the previous via
`payload.corrects = "<previous_id>"`. (A future migration can enforce
this with a `BEFORE UPDATE/DELETE` trigger.)

## Advise envelope (used by all advise-mode agents)

The structured prompt the agent prints to the operator before any
write. Components (in order):

1. `PROPOSED CHANGE` — table, op, diff or new row.
2. `PRE-CHECKS` — every hard-rule check, with PASS / WARN / BLOCK.
3. `RISK FLAGS` — narrative of any non-PASS items.
4. `SOURCES` — which `agent_rules` rows informed the decision
   (`rule_name` only — never include `rule_text` value).
5. Final line: `To apply, reply: confirm` / `cancel` / `edit <field>=<value>`.

The agent must not proceed unless the operator's next message is
exactly `confirm` (case-insensitive). Any other message → cancel
the proposal and offer to revise.

## Example log payload (after a confirmed write)
```json
{
  "diff": {"holdings": {"VWRP": {"qty": "12 → 14"}}},
  "rules_applied": ["benefits.uc_check", "portfolio.isa_first",
                    "tax.cgt_discipline"],
  "checks": {"uc_check": "PASS", "isa_first": "SUGGEST_ALT",
             "cgt_discipline": "PASS"}
}
```
