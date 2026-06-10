# Source: Drupal

Extraction notes for discovery and export. Works for Drupal 7 through 10+, but the channels differ
by major version — detect the version first (`/CHANGELOG.txt`, `drush status`, or the `X-Generator`
header).

## Access channels

### Live API
- **JSON:API** (`/jsonapi`, core in Drupal 8.7+) — preferred. Resource routes are
  `/jsonapi/node/<bundle>`, `/jsonapi/taxonomy_term/<vocab>`, `/jsonapi/user/user`,
  `/jsonapi/media/<bundle>`, `/jsonapi/file/file`.
  - Pagination: `?page[limit]=50&page[offset]=N` (max 50/page by default).
  - Use `?include=field_image,uid,field_tags` to sideload relationships and files.
  - Filtering: `?filter[status][value]=1` for published only.
- **Auth:** Basic auth or OAuth (`DRUPAL_USER` + `DRUPAL_PASS`, or `DRUPAL_OAUTH_TOKEN`). Names →
  `source.credentialEnvVars`.
- **RESTful Web Services / `core REST`** — older 8.x sites may expose `/node/<id>?_format=json`
  instead of JSON:API. Probe both.
- **Drupal 7:** no JSON:API. Use the **Services** or **RESTful** module if present; otherwise rely
  on Drush/DB export.

### Native export
- **Drush** (`drush`) — run on the source host:
  - `drush sql-dump` → full DB.
  - `drush php-eval` / Migrate API for structured extraction.
  - `drush field:info` / `drush config:status` to map bundles + fields.
- **Migrate API (`migrate_plus` + `migrate_tools`)** — Drupal's native migration framework; useful
  to enumerate source structure even if you export JSON yourself.
- **SQL dump** — read `node`, `node_field_data`, `node__field_*`, `taxonomy_term_field_data`,
  `file_managed`, `users_field_data`, `path_alias` (D8+) / `url_alias` (D7).

## Discovery checklist
- Content types (**bundles**) and per-bundle node counts.
- Fields per bundle (text, entity-reference, image, paragraphs) — **Paragraphs** and **Field
  Collections** are nested entities; flag them as conversion complexity.
- Vocabularies (taxonomy) + term hierarchy.
- URL aliases (`path_alias`) — the canonical source for redirects; also capture Pathauto patterns.
- Media: `file_managed` + media bundles; physical files under `sites/default/files/`.
- Menus (`menu_link_content`) → navigation.
- Multilingual: content translations (`langcode`) → normalized `locale`; one normalized item per
  translation.
- Modules that shape content/SEO: **Metatag** (SEO), **Redirect** (existing 301s), **Pathauto**,
  **Webform** (forms — manual follow-up).

## Normalization notes
- `id` → `node-<nid>` (append `-<langcode>` for translations). `sourceType` → `node:<bundle>`.
- `status` field (`1`/`0`) → `published`/`draft`.
- Image/file fields → `media[]`; download from `file_managed.uri` (resolve `public://` →
  `/sites/default/files/`).
- Flatten Paragraphs/Field Collections into `body` markup or structured `fields`; note lossy
  flattening in `source.warnings`.
- `path_alias` + Redirect module entries → item `redirects`. Metatag values → `seo.*`.
