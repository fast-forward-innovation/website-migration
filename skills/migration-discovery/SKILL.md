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

Propose a **normalized `type` taxonomy** mapping each source type → a candidate normalized type for
architecture to confirm.

## Outputs

- `migration/discovery/inventory.json` — machine-readable, e.g.:
  ```json
  {
    "source": "wordpress",
    "contentTypes": [{ "sourceType": "post", "proposedType": "article", "count": 182 }],
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

- Read-only against the source — don't modify the old site.
- Don't download the full media library here; count and sample only (export does the downloading).
- If access partially fails (e.g. drafts need auth you don't have), record the gap in the report and
  inventory `warnings` rather than silently undercounting.
- Keep counts honest — if a type couldn't be fully enumerated, say so.
