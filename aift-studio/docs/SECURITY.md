# Security

This document covers four things: the data boundary, the open RLS finding, where keys live, and how
migrations get reviewed.

---

## 1. The data boundary

The studio reads the existing **finance chief** database through exactly one door:

```
public.aift_content_context(date, …six allow-list booleans)   ← SECURITY DEFINER wrapper
        └── private.aift_content_context(…)                   ← the redaction lives here
```

`SupabaseContextProvider` calls that RPC and issues no other query. It contains no `.from(` at all,
which a test asserts. One door is what makes the boundary auditable: there is a single place to
read, and the redaction is behind it.

### What the function may return

| Category | What is returned | What is not |
|---|---|---|
| Research topics | Topic line, ticker, priority, requested fields | Requester, rationale, any link to a holding |
| Guardrails | Rule name, text, scope | — |
| Intelligence flags | Label, coarse strength band | Underlying score inputs |
| Market snapshots | Symbol, metric, value, unit, as-of date, source | Quantity held, cost basis, position value |
| Macro indicators | Indicator, value, unit, as-of date, source | — |
| Portfolio themes | Bucket **labels**, and only where more than one bucket shares a label | Weights, values, counts. A count is a value in disguise |

Everything else is excluded at the source: the function selects from no broker table, no
`trade_journal`, no `decision_log`, no benefits, income or asset register. A test strips SQL
comments and then greps the executable body for `cost_basis`, `market_value`, `quantity`,
`shares_held`, `total_value` and `account_id` — the migration's own prose names the columns it
excludes, and a naive substring scan would have passed for the wrong reason.

### Three layers, not one

1. **Database.** The function selects only the columns above.
2. **Allow-list.** Every category is gated by a flag that ships `false`. `applyAllowlist` drops
   anything not enabled.
3. **Recursive scan.** `assertContextIsSafe` walks the payload and **throws** on any forbidden key
   at any depth — before the allow-list and again after. It throws rather than stripping, because a
   silent strip is a leak you find out about later.

`portfolio_values` has no branch anywhere. There is no `allow.portfolio_values ? … : …` in the
codebase, a test asserts its absence, and a `CHECK` constraint on `aift_brand_settings` refuses the
setting outright.

### What never reaches a model

Broker statements, account snapshots, executions, cash events, dividends, position snapshots, import
audit, trade journal, decision log, benefits, income, asset register, serial numbers, personal
names, account identifiers, portfolio values, position sizes, allocations.

And separately from the *input* boundary: the **financial-safety gate** scans the *output* — every
public-facing surface, including narration, on-screen text, title, description, tags and scene
headlines — for anything that reads as private finance. That gate matters more than the input one,
because output is where an accident actually reaches an audience.

---

## 2. Open finding — RLS disabled on seven broker tables

A schema-only inspection of project `qxwfrsoztfddwicqtuar` found **Row Level Security disabled** on:

`broker_statements` · `broker_account_snapshots` · `broker_executions` · `broker_cash_events` ·
`broker_dividends` · `broker_position_snapshots` · `broker_import_audit`

With RLS off, any role holding a table grant can read every row. Postgres applies RLS only when it
is enabled, and the service-role key bypasses it regardless. The actual exposure therefore depends
on which roles hold grants today — which is why the proposal starts by asking, not by changing.

### This repository does not fix it for you

Enabling RLS with no matching policy denies all access to non-owner roles. If an importer,
dashboard, notebook or scheduled job reads these tables today, turning RLS on without first writing
its policy breaks it silently at the next run. Locking a door is only safe once you know who is
currently walking through it.

So the fix ships as a **proposal**, in `supabase/migrations-pending-review/`, a directory no tool in
this repository reads. It contains:

- **Step 0 — inspect first.** Read-only queries for the current RLS state, the grant list (this is
  your list of what will break), and whether every table even has an ownership column.
- **Step 1 — a backfill guard** that aborts if any table lacks `user_id` or has a row with a null
  one. Better to fail the migration than to enable RLS over rows whose owner is unknown.
- **Step 2 — enable and force RLS**, owner policies, `anon` revoked, `user_id` set `NOT NULL`.
  `FORCE` matters: without it the table owner sails past the policy.
- **Step 3 — an importer role sketch**, commented out until step 0b tells you what the importer is.
  A key that bypasses RLS has the whole database as its blast radius; a scoped role does not.
- **Step 4 — verification**, and a rollback, with a note that rolling back restores the exposure.

Then run `supabase/tests/broker_rls_policy_test.sql` **against a branch database**. It asserts RLS
is enabled *and forced*, that every table has at least one policy, that no policy is unconditional,
that `anon` holds no grants, that the context function is executable by neither `anon` nor
`authenticated`, that the `private` schema is unreachable from browser roles, and that the
database-side state machine refuses to archive without a reviewer.

### Meanwhile

AIFT Studio does not need these tables and never queries them. `npm run guard:no-secrets` fails the
build if any client module so much as names one. The finding is surfaced on the Security Checklist
screen, marked unresolved, and this application will not mark it resolved.

---

## 3. Key placement

| Key | Where it may live | Enforcement |
|---|---|---|
| `SUPABASE_ANON_KEY` | Browser | RLS applies to it; it grants nothing on its own |
| `SUPABASE_SERVICE_ROLE_KEY` | Server / worker only | `src/lib/supabase/admin.ts` imports `server-only`; a client import is a build error |
| `AIFT_LLM_API_KEY`, `AIFT_MEDIA_API_KEY`, `AIFT_TTS_API_KEY` | Server only | Read only through `src/lib/env`, which is itself server-only |
| `AIFT_JOB_SIGNING_SECRET` | Server only | Used to verify the scheduler HMAC |

`npm run guard:no-secrets` fails the build if a module carrying `'use client'` references any secret
name, imports the admin client, imports the env module, or names a restricted table. It also asserts
that the three server-only modules really do import `server-only`, so the first check is not
guarding a door with no lock behind it.

**The health report never reveals a value.** `secretHealth()` returns `{ name, present, note }` and
nothing else. A test feeds it a distinctive canary secret and asserts that no prefix of it — at any
length — survives into the report or into the provider-mode object.

Assets in the private bucket are reachable only through short-lived signed URLs minted server-side.
`SupabaseStorageProvider` has no public-URL method, by design.

---

## 4. Migration review process

1. **Read the migration.** Every file in `supabase/migrations/` is meant to be read start to finish.
2. **Apply to a branch database**, never to production.
3. **Run the policy tests** against that branch. Every assertion raises on failure, so a clean run
   means every one passed.
4. **Check the grant list again** after applying, and confirm the consumers you found in step 0b
   still work.
5. **Only then** promote. Moving a file out of `migrations-pending-review/` is a deliberate act.

No CI job, deploy step or npm script in this repository applies a migration to a production
database. That is not an oversight.

---

## 5. What this system cannot do

Not "will not" — cannot, and the build proves it on every run.

| Capability | Status | How it is enforced |
|---|---|---|
| Upload to YouTube | Absent | No credential, no OAuth scope, no endpoint. `guard:no-publish` scans every source file |
| Schedule or publish a post | Absent | No such job state exists; the FSM's terminal state is `archived` |
| Place a trade | Absent | No brokerage client, no order API. Guard rule `broker-or-order-api` |
| Move money | Absent | Guard rule `money-movement` |
| Approve its own output | Absent | `needs_review → approved_for_archive` requires actor `reviewer`, in TypeScript and in a Postgres trigger |
| Read broker or trade data | Absent | Not selected by the context function; not reachable from any client module |

If you later want an upload workflow, it should be a separate, separately reviewed decision: add the
scope, add the credential, add the state, and change these guards deliberately. The point of the
guards is that it cannot happen by accident.
