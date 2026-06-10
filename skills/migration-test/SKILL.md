---
name: migration-test
description: Validate a completed migration — content parity (counts + spot field checks between export and import), redirect resolution, asset integrity, internal link checking, a next build check, and SEO-metadata parity. Writes per-check pass/fail to test/test-report.md. Trigger after migration-import (or migration-full), or when the user asks to verify/QA the migration.
metadata:
  short-description: Validate the migration with parity and integrity checks
---

# Migration Test

## Overview

Verifies that what landed in the new Next.js site matches the source-of-truth normalized export and
that the new site is internally sound. It compares the **export** dataset against the **import**
results and the built site, reporting each check as pass/fail with specifics.

## Prerequisites

1. Read `migration/manifest.json`. Require `phases.import.status == "done"`. If missing, name the
   skill to run first and stop.
2. Read `migration/export/export-report.md`, `migration/import/import-report.md`, and
   `migration/import/mapping.json`. Set `phases.test` to `in_progress`.

## Workflow

Run each check and record a result:

1. **Content parity (counts)** — for every type, compare exported item count
   (`export/content/*.json`) to imported count (`mapping.json`). Flag any shortfall with the missing
   ids.
2. **Content parity (spot fields)** — sample N items per type and verify key fields survived
   (title, slug/`targetPath`, body non-empty, author, publish date, hero image) between the
   normalized item and the imported output.
3. **Redirect resolution** — for a sample of `redirects[]` (and `_site/redirects.json`), confirm each
   `from` is present in the generated redirect config and points at a real `targetPath`. Flag
   duplicates and loops.
4. **Asset integrity** — every `media[].localPath` referenced by an imported item resolves to a file
   that was actually placed in `public/` (or exists at the CMS/remote URL). Flag missing/broken
   assets.
5. **Internal link check** — scan imported bodies for internal links; confirm each resolves to a
   known `targetPath` or an external URL. Surface the unresolved set (cross-check the import report).
6. **Build check** — run the target's build (`next build`, or the repo's documented build command).
   Report success/failure and surface errors. Skip with a clear note if the toolchain isn't available.
7. **SEO metadata parity** — sample pages and confirm `seo.*` (meta title/description, canonical,
   noindex) made it into the Metadata API output.

## Outputs

- `migration/test/test-report.md`:
  - A **results table**: each check → `PASS` / `FAIL` / `SKIPPED` + a count of issues.
  - Per failing check, a **details** subsection listing the specific offending ids/URLs/assets.
  - A short **verdict**: is the migration ready, or what must be fixed first.
- Manifest: `phases.test` → `done` (the phase completing is distinct from every check passing — record
  the pass/fail tally in `outputs`/`decisions`, not by refusing to finish).

## Guardrails

- Tests **report**; they don't fix. Don't edit imported content or config to make a check pass — that
  hides the problem. (If the user wants fixes, that's a follow-up import re-run.)
- Sample sizes should scale with volume; state the sample size used so results are interpretable.
- Be honest about `SKIPPED` checks (e.g. no build toolchain, no live redirect host) rather than
  marking them green.
- Don't call the migration ready if parity, asset, or build checks fail — say what's blocking.
