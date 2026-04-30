# Shared: Supabase client patterns

All vault sub-agents use the Supabase MCP server. Connection metadata
lives in `.claude/settings.local.json` (gitignored), not committed.

**Project:** `qxwfrsoztfddwicqtuar` (finance-chief / The Vault).

## Read patterns
- Always use parameterised values via the MCP `execute_sql` tool.
  Never interpolate user-supplied text into SQL.
- Prefer specific column lists over `SELECT *` so column drift surfaces
  early.
- Wrap reads in clear intent comments — the SQL ends up in
  `decision_log.payload` for traceability.

## Write patterns (only for tables an agent OWNS)
- Always run hard-rule pre-checks before proposing the write.
- Build the write inside a single statement (or a short transaction
  for multi-row operations).
- Never DELETE without an explicit operator instruction.
- For UPDATEs, always include the row's `id` in the WHERE clause AND
  a sanity predicate (e.g. `AND status != 'archived'`).

## Owned-table boundary
Sub-agents must refuse to write to tables they don't own (see each
agent's `CLAUDE.md`). Even if the MCP grants would allow it. The
boundary is enforced by the agent, not by Postgres.

## RLS / role
- The MCP server uses the `service_role` key under the hood; service
  role bypasses RLS. This is why operator-level discipline matters.
- 15 tables in this project currently expose `SELECT` to `anon` (see
  the public-read audit). Those are flagged for fix; do not rely on
  RLS to hide data from anon clients today.
