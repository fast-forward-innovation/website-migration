# Source: WordPress

Extraction notes for discovery and export. WordPress exposes content through several channels; pick
based on the manifest's `source.accessMethods` and what the site actually has installed.

## Access channels

### Live API
- **REST API** (`/wp-json/wp/v2/`) — always present on modern WP. Key endpoints:
  - `/wp-json/wp/v2/types` — list registered post types (incl. custom post types).
  - `/wp-json/wp/v2/posts`, `/pages`, and `/<custom-type>` — paginated content
    (`?per_page=100&page=N`, follow `X-WP-TotalPages`).
  - `/wp-json/wp/v2/categories`, `/tags`, `/users`, `/media`, `/menus` (or `/menu-items`).
  - `?_embed` to inline author, featured media, and terms in one call.
  - `&status=publish,draft,private` requires authentication.
- **Auth:** Application Passwords (`WP_APP_USER` + `WP_APP_PASSWORD`, Basic auth) is the standard.
  Names go in `source.credentialEnvVars`; values stay in the environment.
- **WPGraphQL** (`/graphql`) — present only if the plugin is installed. Better for relational pulls
  and ACF fields in one query. Probe for it; fall back to REST if absent.
- **ACF / custom fields:** the core REST API often **omits** meta. Check for the ACF-to-REST-API
  plugin (`acf` key in responses) or use WPGraphQL; otherwise fields may only live in the WXR/DB.

### Native export
- **WXR** (Tools → Export, "eXtended RSS" `.xml`) — covers posts, pages, custom types, terms,
  comments, and `postmeta`. Good for ACF/meta the REST API hides. Parse `<item>` elements; map
  `<wp:post_type>`, `<wp:status>`, `<content:encoded>`, `<wp:postmeta>`, `<category>`.
- **SQL dump** — last resort for fields exposed nowhere else; read `wp_posts`, `wp_postmeta`,
  `wp_terms`/`wp_term_taxonomy`/`wp_term_relationships`, `wp_users`.

## Discovery checklist
- Enumerate post types (built-in + custom) and per-type counts.
- Taxonomies: categories, tags, and any custom taxonomies + hierarchy.
- Permalink structure (Settings → Permalinks) — drives the redirect map.
- Media library size and upload path scheme (`/wp-content/uploads/YYYY/MM/`).
- Menus and widget areas → site navigation.
- Plugins that inject content/SEO: **Yoast / Rank Math** (meta, canonical, redirects, sitemaps),
  ACF (fields), page builders (**Elementor / Gutenberg blocks / shortcodes**) — flag builder markup
  as a conversion risk.
- Forms (Contact Form 7, Gravity Forms, WPForms) — these don't migrate as content; record as
  manual follow-up.

## Normalization notes
- `id` → `post-<ID>`. `sourceType` → the post type. Map `wp:status` → normalized `status`.
- Featured image (`_thumbnail_id` / `_embedded["wp:featuredmedia"]`) → `media[].role = "hero"`.
- Resolve `<!-- wp:image -->` blocks and `[shortcode]`s in `content:encoded`; unresolved shortcodes
  → `source.warnings`.
- Yoast/Rank Math meta → `seo.*`. Pull existing redirects from the SEO plugin → item `redirects`.
- Old permalink + any `?p=ID` and dated permalink variants → `redirects` so inbound links survive.
