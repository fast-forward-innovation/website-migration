---
name: migration-summary
description: Produce the final human-readable migration report by aggregating every phase's outputs from the manifest — what was migrated (counts), gaps, items needing manual follow-up, redirects to deploy, and recommended next steps. Writes summary.md. Trigger after migration-import (richer once migration-test has run), or when the user asks for a migration recap/handoff.
metadata:
  short-description: Summarize the migration outcome and next steps
---

# Migration Summary

## Overview

The closing report. It reads the manifest and each phase's artifacts and assembles one clear
document a stakeholder can read to understand what happened, what's left, and what to do next. It
produces no new data — it synthesizes.

## Prerequisites

1. Read `migration/manifest.json`. Require at least `phases.import.status == "done"`. The more phases
   are `done` (especially `test`), the richer the summary — note which phases are missing rather than
   failing. Set `phases.summary` to `in_progress`.
2. Read whatever exists: `plan.md`, `discovery/report.md` + `inventory.json`, `architecture.md`,
   `export/export-report.md`, `import/import-report.md`, `test/test-report.md`.

## Workflow

Aggregate across phases into a single narrative:

1. **Overview** — source platform → Next.js, access method, content layer chosen, hosting
   (provider + base domain + whether sites are provisioned), dates.
2. **What was migrated** — totals by type (exported vs. imported), assets placed, redirects
   generated. Pull numbers from the export/import reports, not re-counting.
3. **Quality** — summarize `test-report.md` results (parity, assets, links, build, SEO). If test
   didn't run, say so and recommend it.
4. **Gaps & manual follow-ups** — consolidate every warning/manual item surfaced across discovery
   (integrations/forms/builder markup), export (lossy conversions, unresolved shortcodes), and import
   (unresolved links, smart content). Present as an actionable checklist.
5. **Redirects to deploy** — where the redirect map lives and the count, with a reminder to ship it
   so inbound links survive cutover.
6. **Decisions log** — surface the `decisions[]` from the manifest (notably the content-layer
   choice).
7. **Recommended next steps** — e.g. run/re-run test, resolve the manual checklist, configure forms,
   QA on staging, plan DNS cutover.

## Outputs

- `migration/summary.md` — the sections above, written for a mixed technical/non-technical audience,
  with concrete counts and a clear follow-up checklist.
- Manifest: `phases.summary` → `done`, `outputs` set.

## Guardrails

- Don't re-derive or re-count from raw data when a phase report already has the numbers — cite them
  and stay consistent (flag contradictions instead of silently picking one).
- Be candid about gaps and skipped checks; a summary that hides manual follow-ups causes broken
  launches.
- No new extraction, import, or fixes here — this phase only reports.
