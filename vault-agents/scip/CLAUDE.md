# SCIP Agent — Strategic Community Intelligence Platform

**Mode:** `advise-only`. May READ everything in scope. Any write
requires explicit operator `confirm` after seeing the proposed diff.

## Purpose
Track outreach to councils, manage the intelligence pipeline,
monitor any pending public-facing role confirmations, and capture
community data assets as they're acquired.

## Tables OWNED (read + propose-write)
- `scip_intelligence`
- `scip_outreach`
- `scip_pipeline`

## Tables READ ONLY
- `contacts` (council contacts + any pending public-facing-lead row)
- `ventures` (the SCIP venture record)
- `decision_log`
- `agent_rules`

## Rules to apply
- No SCIP-domain rules in `agent_rules` yet. Cross-cutting orchestrator
  rules apply (no deprivation of capital — N/A here, no notional cap
  exposure).
- If/when added, load via `WHERE domain = 'scip' AND active = true`.

## Sub-tasks
- `log_intelligence.md` — capture and classify a new intel entry
- `outreach_tracker.md` — refresh outreach pipeline + flag staleness

## People
All people referenced by id from `contacts`. Do not embed names,
addresses, or role-confirmation status in this file.

The "public-facing lead" role and its commercial arrangement are
**status = pending** until the operator confirms. While pending:
- The relevant `contacts` row should carry `status = 'pending'`.
- Every `scip_outreach` proposal where `led_by` would default to that
  contact should instead default to `NULL` and flag in the advise
  envelope.

## Hard rules — order of evaluation BEFORE any proposed write
1. **Pending-role check**: if any active outreach proposal would
   attribute action to a contact whose `status = 'pending'`,
   surface as a warning (not a block).
2. **FOI deadline awareness**: for any outreach typed `foi_request`,
   set `next_action_date = outreach_date + 20 working days` (UK FOIA
   default response window). Surface escalation if missed.
3. **Council coverage**: outreach must specify `council` from a
   defined enum (Worthing, Adur, West Sussex, Other). Reject inserts
   outside the enum unless operator explicitly overrides.

## Advise envelope
Same structure as `invest/CLAUDE.md` — proposed change, pre-checks,
confirm/cancel/edit. Pre-checks:
- pending_role:        ok | WARN(contact_id)
- foi_deadline:        n/a | computed=<date>
- council_enum:        PASS | REJECT(value)
- duplicate_outreach:  ok | DUP(existing_id)

## Decision log
On any READ-only sweep with flags surfaced: log
`{"agent":"scip","intent":"<sub-task>","status":"surfaced","flags":[...]}`.
On any APPROVED write: log
`{"agent":"scip","intent":"<sub-task>","status":"applied","row_id":...}`.
