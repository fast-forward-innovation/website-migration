---
name: migration-export
description: Extract content and assets from the OLD site (Drupal, WordPress, or HubSpot) via live API or native export files, normalize each item to the canonical schema, and download media. Writes export/content/*.json + export/assets/ + export-report.md. Idempotent and resumable. Trigger after migration-discovery (architecture optional but recommended). For export+import in one go, use migration-full.
metadata:
  short-description: Export and normalize source content and assets
---

# Migration Export

## Overview

Pulls content + assets out of the source platform and writes them in the **canonical normalized
schema**, decoupled from both the source and the eventual target. This is the heavy extraction phase.
It is **idempotent and resumable**: re-running skips items already written unless `--force` is asked.

## Prerequisites

1. Read `migration/manifest.json`. Require `phases.discovery.status == "done"`. (Architecture isn't
   strictly required to export, but warn if it's not done since the `type` taxonomy may still shift.)
2. Read `migration/discovery/inventory.json` for the type list, counts, and URL/media schemes.
3. Read `${CLAUDE_PLUGIN_ROOT}/references/sources/<platform>.md` (extraction channels) and
   `${CLAUDE_PLUGIN_ROOT}/references/normalized-content.md` (output schema).
4. Verify access: credential env vars set (`live-api`) or export files present (`native-export`).
   Set `phases.export` to `in_progress`.

## Workflow

1. **Plan the pull** — for each in-scope content type, choose the channel from the platform reference
   (e.g. WP REST `?_embed`, Drupal JSON:API `?include=`, HubSpot CMS API, or parse the WXR/SQL/export
   file). Prefer the channel that returns the most complete data; combine channels when one omits
   fields (e.g. ACF via WXR, body via REST).
2. **Extract page-by-page** with pagination; respect rate limits and back off on errors. Pull drafts
   too if status fidelity matters and auth allows.
3. **Normalize each item** into the canonical schema → one file per item at
   `migration/export/content/<id>.json`. Fill `body.raw` always; attempt `body.markdown` and flag
   lossy conversions in `source.warnings`. Build `redirects[]` from old permalinks/aliases.
4. **Download media** referenced by each item into `migration/export/assets/` preserving a stable
   path map; set `media[].localPath`. De-dupe by source URL. Capture `width`/`height`/`alt`/`mime`.
5. **Extract site-level records** to `migration/export/content/_site/`: `navigation.json`,
   `taxonomies.json`, `authors.json`, `redirects.json` (per the normalized-content reference).
6. **Track progress** so the run is resumable — skip items whose `<id>.json` already exists and whose
   assets are present, unless the user asked to force a re-pull.
7. **Write the report** with counts and any failures.

## Outputs

- `migration/export/content/<id>.json` — one normalized item each.
- `migration/export/content/_site/{navigation,taxonomies,authors,redirects}.json`.
- `migration/export/assets/**` — downloaded media.
- `migration/export/export-report.md`:
  - **Counts** per type: attempted / exported / skipped / failed.
  - **Assets**: downloaded / failed / total bytes.
  - **Warnings**: lossy conversions, unresolved shortcodes/modules, items needing manual review
    (aggregated from `source.warnings`).
  - **Resumability**: what a re-run would do.
- Manifest: `phases.export` → `done` (or `failed` with `error` if extraction couldn't complete);
  `outputs` set.

## Guardrails

- **Read-only against the source.** Never write to or mutate the old site.
- **Never persist secrets** — read credentials from env vars by the names in
  `source.credentialEnvVars`; don't echo them into reports or files.
- Don't transform content into target shape here — that's `migration-import`. Export's job is a clean,
  complete, source-of-truth normalized dataset.
- On partial failure, write what succeeded, set the phase `failed` with details, and tell the user
  exactly what to retry — don't mark `done` with gaps.
- Respect robots/rate limits and the site's load; throttle large media pulls.
