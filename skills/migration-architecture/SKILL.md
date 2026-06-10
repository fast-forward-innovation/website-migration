---
name: migration-architecture
description: Design the NEW Next.js site from the discovery inventory — choose the content layer (file-based MDX vs. headless CMS), map source content types to routes/data models/components, and define routing, redirects, rendering, images, and i18n. Writes architecture.md and records the content-layer decision in the manifest (migration-import depends on it). Trigger after migration-discovery.
metadata:
  short-description: Design the new Next.js site architecture
---

# Migration Architecture

## Overview

Turns the discovery inventory into a concrete design for the **new** Next.js site. Its most important
output is the **content-layer decision** (`mdx` vs. `headless-cms`), recorded in the manifest, because
`migration-import` branches on it. It also fixes the route map, redirect strategy, rendering modes,
image handling, and i18n.

## Prerequisites

1. Read `migration/manifest.json`. Require `phases.discovery.status == "done"`. If missing, tell the
   user to run **migration-discovery** first and stop.
2. Read `migration/discovery/inventory.json` and `report.md`.
3. Read `${CLAUDE_PLUGIN_ROOT}/references/targets/nextjs.md` and
   `${CLAUDE_PLUGIN_ROOT}/references/normalized-content.md`.
4. Inspect `target.appDir` to detect App Router vs. Pages Router and any existing content tooling.
   Set `phases.architecture` to `in_progress`.

## Workflow

1. **Choose the content layer** using the decision table in the Next.js reference, driven by
   discovery signals: total item count, editor profile (are non-technical editors involved?),
   structural/relational complexity, and publishing frequency. If discovery is ambiguous on the
   editor profile, **ask the user** — it's the deciding factor. For a headless CMS, pick the specific
   product (Sanity / Payload / Contentful) and say why.
2. **Finalize the normalized type taxonomy** from discovery's proposal — confirm or adjust each
   `sourceType → type` mapping.
3. **Map types to routes** — for each normalized type, define the Next.js route(s), index pages,
   taxonomy index routes, and `generateStaticParams` sources. Preserve old paths where reasonable.
4. **Define the redirect strategy** — how old URLs (and the existing redirects from discovery) will
   become Next.js redirects, and where they live (`next.config.js` vs. middleware if the count is
   large).
5. **Pick rendering modes** per route type (SSG default, ISR for frequently-published headless
   content, SSR only for genuinely dynamic pages flagged in discovery).
6. **Plan images** (where assets land — `public/` vs. CMS/image host — and `next/image` usage) and
   **i18n** if discovery found multiple locales.
7. **Address the risks/manual items** from discovery (forms, page-builder markup, smart content):
   propose how each is handled in the new site or explicitly defer it to manual follow-up.

## Outputs

- `migration/architecture.md` containing:
  - **Content-layer decision** with rationale.
  - **Type → route map** table (normalized type, route, index route, rendering mode).
  - **Data model / frontmatter or CMS schema** for each type.
  - **Redirect strategy**, **image strategy**, **i18n plan**.
  - **Component inventory** the new site needs (article layout, nav, taxonomy index, etc.).
  - **Manual follow-ups** carried from discovery with proposed handling.
- Manifest:
  - `target.contentLayer` set to `"mdx"` or `"headless-cms"`; `target.contentLayerDecidedBy` =
    `"architecture"`.
  - `decisions[]` appended with the content-layer choice (+ CMS product) and rationale.
  - `phases.architecture` → `done`, `outputs` set.

## Guardrails

- This phase **designs**; it does not write site code or extract content.
- The content-layer decision is mandatory — `migration-import` cannot run without
  `target.contentLayer` set. Don't leave it `null`.
- Honor URL preservation constraints from the plan; don't propose a route scheme that orphans
  inbound links without redirects.
- Keep the design proportional to the inventory — don't propose a headless CMS for 30 static pages,
  or raw MDX for 5,000 editor-managed records.
