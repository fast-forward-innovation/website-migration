---
name: migration-discovery
description: Inventory the OLD site being migrated (Drupal, WordPress, or HubSpot) — content types, counts, URLs, taxonomies, authors, media, navigation, integrations, SEO metadata, and existing redirects. Produces discovery/inventory.json + report.md for the architecture and export phases. Trigger after migration-plan, or when the user asks "what's on the old site" / "audit the source site".
metadata:
  short-description: Inventory the source site's content and structure
---

# Migration Discovery

## Overview

Analyzes the **old** site and produces a structured inventory the rest of the pipeline plans against.
It reads what exists; it does **not** extract full content (that's `migration-export`) and does not
design the new site (that's `migration-architecture`).

## Prerequisites

1. Read `migration/manifest.json`. Require `phases.plan.status == "done"`. If missing, tell the user
   to run **migration-plan** first and stop.
2. Note `source.platform` and `source.accessMethods`, and read the matching
   `${CLAUDE_PLUGIN_ROOT}/references/sources/<platform>.md` for how to enumerate this platform.
3. Read `${CLAUDE_PLUGIN_ROOT}/references/normalized-content.md` so your proposed `type` taxonomy
   lines up with what export/import will use.
4. Confirm access works: for `live-api`, verify the credential env vars in
   `source.credentialEnvVars` are set and a probe request succeeds; for `native-export`, confirm the
   files in `source.exportFiles` / `migration/_input/` exist and parse. Set `phases.discovery` to
   `in_progress`.
5. **Prepare source-code access** for each role present in `source.codeAccess` (`cms` and, for a
   `headless` source, `frontend`):
   - `type: "local"` — confirm `path` exists; you'll scan it in place.
   - `type: "git"` — clone into `localCheckout` (default `migration/_input/source-code/<role>`) if
     absent, otherwise `git pull` to refresh; check out `ref` if set. Use the user's existing git
     credentials; never store tokens. Record the resolved checkout path back into
     `source.codeAccess.<role>.localCheckout`.
   - `type: "none"` — skip that role.
   - If both roles are `none`, rely on API/export data only.

## Workflow

Follow the platform's discovery checklist in its reference doc. Gather, at minimum:

- **Content types & counts** — every native type/bundle/post-type and how many items each has.
- **URL structure** — permalink/alias scheme and a representative URL map (needed for redirects).
- **Taxonomies** — categories, tags, vocabularies, HubDB tables, with hierarchy and counts.
- **Authors** — the contributor directory.
- **Media** — count, total size, upload-path scheme, formats.
- **Navigation** — menus / nav structures.
- **Integrations & embeds** — page builders, shortcodes/HubL modules, forms, CTAs, smart/
  personalized content, third-party embeds. Flag each as a **conversion risk** or **manual
  follow-up** (forms and personalized content rarely migrate 1:1).
- **SEO metadata** — meta titles/descriptions, canonicals, robots, sitemap presence (Yoast/Rank
  Math/Metatag/HubSpot).
- **Existing redirects** — current 301s from the SEO/redirect modules.

**If the CMS code is available** (`source.codeAccess.cms.type` is `"local"` or `"git"`), scan it to
corroborate and enrich the above — code is often more authoritative than the API for *structure*:
- **WordPress** — `functions.php` and plugin files for `register_post_type` / `register_taxonomy`,
  ACF field-group definitions (`acf-json/` or PHP), theme `*-template.php` / block templates,
  `rewrite` rules, and `theme.json`.
- **Drupal** — config YAML under `config/sync/` (`node.type.*`, `field.field.*`,
  `taxonomy.vocabulary.*`, `core.entity_view_display.*`), custom module `*.routing.yml`, and theme
  `*.html.twig` templates.
- **HubSpot** — the design-manager/CMS theme export: `*.html` + `*.module` templates, `fields.json`
  per module, `theme.json`, and HubL partials.

Use it to pin down exact field names/types per content type, template→component mappings, and custom
routing the API may not expose.

**If the source is headless and the frontend code is available** (`source.codeAccess.frontend`),
scan it too — for a decoupled site this is where the real UI lives, and it often maps almost directly
onto the new Next.js build:
- **Detect the framework** (`package.json` deps: `next`, `gatsby`, `nuxt`, `vue`, plain `react`) and
  record it in `frontend.framework`.
- **Routing** — file-based routes (`pages/`, `app/`, Gatsby `gatsby-node.js` `createPages`, Nuxt
  `pages/`) → the URL map and which content type drives each route.
- **Data fetching** — how it queries the CMS (GraphQL queries/fragments, REST calls, SDK usage) →
  exactly which fields each page consumes (a precise field-usage inventory).
- **Component inventory** — reusable components, layouts, and design tokens that the new Next.js site
  can reuse or port (note React components as low-effort ports; Vue/other as rewrites).
- **Config** — env/config for CMS endpoints, image/CDN handling, i18n.

Record where each finding came from (`discoveredVia`: `api` / `export` / `cms-code` /
`frontend-code`) and flag any **discrepancies** between sources in the report.

Propose a **normalized `type` taxonomy** mapping each source type → a candidate normalized type for
architecture to confirm.

## Outputs

- `migration/discovery/inventory.json` — machine-readable, e.g.:
  ```json
  {
    "source": "wordpress",
    "sourceArchitecture": "headless",
    "codeScanned": { "cms": true, "frontend": true },
    "frontend": {
      "framework": "gatsby",
      "routes": [{ "path": "/blog/:slug", "type": "post", "from": "gatsby-node.js" }],
      "components": ["PostHero", "Prose", "TagList"],
      "dataLayer": "graphql",
      "fieldUsage": { "post": ["title", "slug", "body", "heroImage", "tags"] },
      "portability": "react-reusable"
    },
    "contentTypes": [{
      "sourceType": "post", "proposedType": "article", "count": 182,
      "fields": [{ "name": "subtitle", "type": "text", "from": "acf" }],
      "templates": ["single.php"], "discoveredVia": ["api", "cms-code", "frontend-code"]
    }],
    "taxonomies": { "category": 9, "tag": 140 },
    "authors": 6,
    "media": { "count": 1240, "approxBytes": 3100000000, "uploadScheme": "/wp-content/uploads/YYYY/MM/" },
    "navigation": ["primary", "footer"],
    "urlPatterns": ["/blog/%postname%", "/%pagename%"],
    "integrations": [{ "name": "Gravity Forms", "risk": "manual", "items": 4 }],
    "seo": { "plugin": "yoast", "sitemap": true },
    "existingRedirects": 37,
    "warnings": ["Elementor markup on 12 pages — conversion risk"]
  }
  ```
- `migration/discovery/report.md` — human-readable findings, organized by the checklist above, with a
  **Risks & manual follow-ups** section and the proposed type mapping.
- Manifest: `phases.discovery` → `done`, `outputs` set; append any notable `decisions`.

## Guardrails

- Read-only against the source — don't modify the old site, and treat a local or cloned codebase as
  read-only too (clone/pull only; never push or edit it).
- Don't download the full media library here; count and sample only (export does the downloading).
- If access partially fails (e.g. drafts need auth you don't have), record the gap in the report and
  inventory `warnings` rather than silently undercounting.
- Keep counts honest — if a type couldn't be fully enumerated, say so.
