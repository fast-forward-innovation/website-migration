# Canonical normalized content schema

This is the **source-agnostic intermediate format**. Every source platform (Drupal, WordPress,
HubSpot) normalizes *into* it during `migration-export`; `migration-import` maps *out of* it into the
target (MDX files or a headless CMS).

This decoupling is the point: adding a new source means writing one normalizer *into* this schema,
and adding a new target (e.g. the planned WordPress target) means writing one importer *out of* it.

`migration-export` writes **one JSON file per content item** to `migration/export/content/<id>.json`
and downloads referenced media to `migration/export/assets/`.

## Item shape

```json
{
  "id": "post-1423",
  "sourceType": "post",
  "type": "article",
  "status": "published",
  "locale": "en",
  "title": "How we cut build times in half",
  "slug": "cut-build-times-in-half",
  "sourceUrl": "https://old.acme.com/blog/cut-build-times-in-half",
  "targetPath": "/blog/cut-build-times-in-half",
  "excerpt": "A short summary…",
  "body": {
    "format": "html",
    "raw": "<p>…original markup…</p>",
    "markdown": "…converted markdown/MDX (filled by export when feasible)…"
  },
  "fields": {
    "readTimeMinutes": 6,
    "featured": true
  },
  "taxonomies": {
    "category": ["engineering"],
    "tag": ["performance", "ci"]
  },
  "authors": [
    { "id": "u-12", "name": "Dana Lee", "email": null }
  ],
  "media": [
    {
      "role": "hero",
      "sourceUrl": "https://old.acme.com/wp-content/uploads/2025/03/hero.png",
      "localPath": "assets/2025/03/hero.png",
      "alt": "Build pipeline diagram",
      "width": 1600,
      "height": 900,
      "mime": "image/png"
    }
  ],
  "seo": {
    "metaTitle": "How we cut build times in half | Acme",
    "metaDescription": "…",
    "canonical": "https://old.acme.com/blog/cut-build-times-in-half",
    "ogImage": "assets/2025/03/hero.png",
    "noindex": false
  },
  "dates": {
    "created": "2025-03-04T10:00:00Z",
    "updated": "2025-03-06T14:00:00Z",
    "published": "2025-03-05T09:00:00Z"
  },
  "relations": {
    "parent": null,
    "related": ["post-1390"]
  },
  "redirects": [
    { "from": "/2025/03/05/old-permalink", "to": "/blog/cut-build-times-in-half", "status": 301 }
  ],
  "source": {
    "platform": "wordpress",
    "rawRef": "wxr://item[guid=1423]",
    "warnings": []
  }
}
```

## Field rules

- **`id`** — globally unique within this migration; stable across re-runs (derive from the source's
  primary key, e.g. `post-<wpId>`, `node-<nid>`, `hs-<contentId>`).
- **`sourceType`** — the platform's native type name (`post`, `node:article`, `landing-page`).
- **`type`** — the normalized type the architecture maps to a target route/model (e.g. `article`,
  `page`, `landing`). Discovery proposes the type taxonomy; architecture finalizes it.
- **`status`** — `"published" | "draft" | "scheduled" | "archived"`.
- **`body.raw`** is always the original markup. **`body.markdown`** is best-effort converted MDX;
  if conversion is lossy or unsafe, leave it `null` and flag in `source.warnings` so import can fall
  back to `raw`.
- **`media[].localPath`** is relative to `migration/export/` and must point at a file actually
  downloaded into `export/assets/`. Asset-integrity tests check this.
- **`targetPath`** — proposed new-site path; architecture's routing strategy may rewrite it. Keep
  the old path discoverable via `redirects` so no inbound link breaks.
- **`redirects`** — every old URL that should 301 to this item (permalinks, aliases, paginated or
  taxonomy variants). Aggregated by import into the Next.js redirect config.
- **`source.warnings`** — free-form strings for anything lossy or manual (unsupported shortcode,
  embedded form, paywalled field). Surfaced in export, test, and summary reports.

## Non-content records

Site-level structures that aren't a single content item get their own normalized files under
`migration/export/content/_site/`:

- `_site/navigation.json` — menus → `{ label, url, targetPath, children[] }`.
- `_site/taxonomies.json` — full term lists with hierarchy + counts.
- `_site/authors.json` — author directory.
- `_site/redirects.json` — global redirects not attached to a single item.

Keeping these separate lets import build navigation, taxonomy index pages, and the redirect map
without re-scanning every content file.
