---
name: migration-import
description: Import the normalized export into the NEW Next.js site using the content layer chosen in architecture (file-based MDX or headless CMS). Writes content, places assets, rewrites internal links, and generates the redirect map. Produces import-report.md + a source→target mapping. Trigger after migration-export and migration-architecture. For export+import in one go, use migration-full.
metadata:
  short-description: Import normalized content into the Next.js site
---

# Migration Import

## Overview

Takes the canonical normalized dataset from `migration-export` and writes it into the **new** Next.js
site in the shape the architecture chose. This is the only phase that touches the target repo's
content/config. It maps *out of* the canonical schema, which is what keeps a future alternate target
(e.g. WordPress) a matter of one new importer.

## Prerequisites

1. Read `migration/manifest.json`. Require **both** `phases.architecture.status == "done"` and
   `phases.export.status == "done"`. If either is missing, name the skill to run first and stop.
2. Require `target.contentLayer` to be set (`"mdx"` or `"headless-cms"`). If `null`, stop and point
   to **migration-architecture**.
3. Read `migration/architecture.md` (route map, data model, redirect/image/i18n strategy),
   `${CLAUDE_PLUGIN_ROOT}/references/targets/nextjs.md`, and
   `${CLAUDE_PLUGIN_ROOT}/references/normalized-content.md`. Set `phases.import` to `in_progress`.

## Workflow

1. **Build the source→target map** first: for every normalized item, compute its final `targetPath`
   and target location (MDX file path or CMS record id) per the architecture route map. Keep this map
   in memory and persist it (see Outputs) — link rewriting and redirects depend on it.
2. **Write content** per `target.contentLayer`:
   - **`mdx`** — render each item to an `.mdx` file with frontmatter (title, slug, dates, author,
     taxonomies, SEO) in the architecture's content dir. Use `body.markdown` when present and
     non-lossy; otherwise embed sanitized `body.raw`.
   - **`headless-cms`** — create/update records via the CMS write API (or generate its import file),
     mapping normalized fields to the CMS schema from architecture.
3. **Place assets** — copy `migration/export/assets/**` into `public/` (or upload to the CMS/image
   host for headless), and rewrite each `media[].localPath` to the new public URL. Wire `next/image`
   with the captured `width`/`height`/`alt`.
4. **Rewrite internal links** in bodies from old URLs/paths to `targetPath` using the map. Record any
   link that can't be resolved as a warning (the test phase re-checks these).
5. **Generate the redirect map** — aggregate every item's `redirects[]` plus
   `_site/redirects.json` into the target's redirect mechanism (`next.config.js redirects()` or a
   middleware map for large sets), each `permanent: true`.
6. **Generate supporting structures** the architecture called for: navigation from
   `_site/navigation.json`, taxonomy index data, and SEO metadata wiring (Metadata API), plus
   `sitemap.ts`/`robots.ts` source data if specified.
7. **Write the report.**

## Outputs

- Content written into the target repo (MDX files) or CMS records created.
- Assets placed under `public/` (or uploaded) with references rewritten.
- Redirect configuration generated/updated.
- `migration/import/mapping.json` — `{ id, sourceUrl, targetPath, targetLocation }[]` for every item.
- `migration/import/import-report.md`:
  - **Counts**: items imported / skipped / failed, per type.
  - **Assets**: placed / failed.
  - **Links**: rewritten / unresolved (list the unresolved).
  - **Redirects**: generated count and where they live.
  - **Manual follow-ups** carried forward (forms, embeds, smart content).
- Manifest: `phases.import` → `done` (or `failed`); `outputs` set.

## Guardrails

- Don't invent a content layer — honor `target.contentLayer`. If it's unset, stop.
- Writes are confined to the target site's content/assets/config and the `migration/import/` folder —
  don't touch the `migration/export/` source-of-truth dataset.
- Prefer additive/idempotent writes; re-running should update rather than duplicate items (key on
  `id`/`slug`). Don't silently overwrite hand-edited target files without noting it in the report.
- Sanitize embedded raw HTML before placing it in MDX.
- Every unresolved internal link and dropped element must appear in the report — no silent loss.
