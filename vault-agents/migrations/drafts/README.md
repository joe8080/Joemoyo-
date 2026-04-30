# Vault migration drafts

These are **draft** SQL migrations against `qxwfrsoztfddwicqtuar`
(finance-chief / The Vault). None has been applied to the database.

Apply each one individually after operator review via the Supabase MCP:
`mcp__supabase-vault__apply_migration` (write-grant lives in
gitignored `.claude/settings.local.json`).

| # | File | Priority | Status | Touches |
|---|---|---|---|---|
| 1 | `001_drop_public_read_policies.draft.sql` | **HIGHEST** (live privacy leak) | **APPLIED** as `drop_anon_read_on_personal_tables` | DROPs 15 anon/public SELECT policies |
| 2 | `002_add_missing_agent_rules.draft.sql` | Medium (unblocks INVEST agent) | **APPLIED** as `add_missing_agent_rules_invest_tax` (final values supplied inline by operator; not committed to git, by design) | INSERTs 5 new `agent_rules` rows |
| 3 | `003_moddatetime_and_updated_at_triggers.draft.sql` | Low–Medium (fixes spurious staleness flags) | **APPLIED** as `enable_moddatetime_and_fix_defaults` | Installs `moddatetime`, adds 3 triggers, drops `scip_outreach.led_by` default |
| 4 | `004_add_updated_at_to_research_and_intel.draft.sql` | Low (queued follow-up to Draft 3) | **DRAFT** — not applied | ADDs `updated_at` column + trigger to `ogx_research_claims` and `scip_intelligence` |

## Order of application

1. **001 first** (privacy)
2. Either of 2/3 next (independent)

## Each draft includes

- Rationale + decision log
- Blast-radius assessment
- The DDL inside a single transaction
- A verification block to run after apply
- A rollback block (commented out)
- Pre-apply checklist where personal values must be filled in
- Cross-references to follow-up items not in scope

## Filename convention

`NNN_short_description.draft.sql` — the `.draft` suffix is intentional;
remove it (or rename when staging for `apply_migration`) only when
ready to apply.
