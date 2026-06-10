# Source: HubSpot

Extraction notes for discovery and export. HubSpot content lives across the **CMS Hub** (pages,
blog, HubDB) and optionally references **CRM** objects. Almost everything is API-only — there is no
single portable dump like WXR or a SQL file, so `live-api` is the primary access method.

## Access channels

### Live API (primary)
- **Auth:** Private App access token (`HUBSPOT_TOKEN`), sent as `Authorization: Bearer`. Name →
  `source.credentialEnvVars`. Required scopes: `content`, `cms.knowledge_base.articles.read`,
  `hubdb`, plus any CRM scopes if CRM objects are referenced.
- **CMS API** (`/cms/v3/`):
  - `/cms/v3/blogs/posts` — blog posts (paginated via `?limit=100&after=<cursor>`).
  - `/cms/v3/pages` and `/cms/v3/site-pages` / `/landing-pages` — site + landing pages.
  - `/cms/v3/blogs/authors`, `/blogs/tags` — blog taxonomy + authors.
  - `/cms/v3/hubdb/tables` and `/hubdb/tables/<id>/rows` — **HubDB** dynamic data (often powers
    resource listings, locations, team pages). Each table is effectively a content type.
  - `/cms/v3/knowledge-base` (if Service Hub KB is used).
- **Files API** (`/files/v3/files`) — hosted assets/images; download by `url`.
- **CRM API** (`/crm/v3/objects/...`) — only if pages render CRM data (e.g. custom objects). Pull
  the referenced object types; most marketing-site migrations don't need this.

### Native export
- HubSpot's UI export produces **per-area CSV/HTML exports** (blog export, page export). These are
  partial — they lack module/field structure — so treat them as a *supplement* to the API, recorded
  in `source.exportFiles`, not a replacement.

## Discovery checklist
- Blog(s): post count, tags, authors, blog URL slug structure.
- Pages: site pages vs. landing pages (landing pages often have campaign URLs to redirect).
- HubDB tables: list each table, its columns, row counts, and which page templates render them →
  each becomes a normalized `type`.
- Modules & templates: HubL modules and **forms** (HubSpot forms are embedded, not content — record
  as manual follow-up; the new site will need a forms strategy).
- SEO: per-page meta title/description, canonical, and HubSpot's automatic URL structure.
- Smart/personalized content and CTAs — flag as manual; they don't translate 1:1 to Next.js.
- Existing URL redirects (Settings → Website → URL Redirects, `/cms/v3/url-redirects` if available).

## Normalization notes
- `id` → `hs-<objectId>`. `sourceType` → `blog-post` / `site-page` / `landing-page` /
  `hubdb:<tableName>`.
- HubSpot post/page bodies are HubL-rendered HTML; store rendered HTML in `body.raw`. HubL
  modules/CTAs that can't be statically rendered → `source.warnings`.
- HubDB rows normalize as structured `fields` (one item per row) with the table as `type`.
- Featured image / social image → `media[]` and `seo.ogImage`.
- Landing-page campaign URLs and any URL-redirect entries → item `redirects`.
- Authors/tags → `_site/authors.json` and `_site/taxonomies.json`.
