# SCIP modernization

Modernizing the **worthing database** (Supabase project
`ympbtirltohryxrcqhlm`) into a resident-facing civic data product:
semantic search, auto-briefings, FOI ingest, public dashboard —
on open-council-data posture.

**Audience:** Worthing / Adur residents.
**Status:** Phase 1 scaffolding.

## Track plan (5 tracks)

| # | Track | Status |
|---|---|---|
| A | Schema cleanup (comments, _new audit, geo-lookup dedupe) | In progress |
| B | Vector layer (pgvector + embeddings on scip_unified_data) | Blocked by A |
| C | Weekly AI briefings (pg_cron + Edge Function + Claude → Resend / Slack / dashboard) | Blocked by B |
| D | PDF/FOI ingest (Drive → OCR → extract → scip_intelligence) | Blocked by B |
| E | Public dashboard (Next.js on Vercel, free subdomain) | Blocked by A + B |

## Folder layout

```
scip/
├── README.md
└── migrations/
    └── drafts/
        ├── 001a_add_scip_table_comments.draft.sql    (safe, documentation)
        ├── 001b_audit_new_suffix_tables.draft.sql    (read-only audit)
        └── 001c_audit_geo_lookup_dedup.draft.sql     (read-only audit)
```

Follow-up migrations will land after each audit (`001d`, `001e`) once
the operator reviews audit output and chooses winners.

## Operating principles

1. **Open-council-data posture.** Every scip_* table in worthing is
   treated as public open data unless flagged otherwise. Attribution
   to source council / government published on the dashboard.
2. **No personal data in committed files.** This mirrors the vault
   convention — thresholds, trust info, PII, resident records all
   stay in the DB behind RLS, never in migration SQL.
3. **Draft migrations are reviewable.** Every file ends in
   `.draft.sql`, gets a rationale + verification + rollback block,
   and is applied by operator sign-off only.
4. **Audits before edits.** Any `_new` vs canonical ambiguity or
   suspected duplicate (e.g. geo_lookup vs postcodes_master) gets
   a read-only audit draft first, then a decided-upon migration.
