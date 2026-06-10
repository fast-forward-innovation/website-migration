# Target: Next.js

Design + import notes for the new site. `migration-architecture` uses this to design routes and pick
a content layer; `migration-import` uses it to write content into the chosen layer.

Assume the **App Router** (`app/`) unless the target repo clearly uses the Pages Router (`pages/`).
Detect by which directory exists in `target.appDir`.

## Content layer decision (made in architecture, recorded in manifest)

| Choose | When | Import writes |
|--------|------|---------------|
| **`mdx`** (file-based) | Dev-owned content, low/medium volume (≈ < 500 items), few non-technical editors, content is mostly prose. | `.mdx` files + frontmatter into a content dir (e.g. `content/blog/<slug>.mdx`), parsed via `@next/mdx`, `next-mdx-remote`, or Contentlayer. |
| **`headless-cms`** | Non-technical editors need a UI, high volume, heavy relational/structured data, or frequent publishing. | Records created in the CMS (Sanity / Payload / Contentful) via its write API or import tooling; the Next.js app fetches at build/runtime. |

Record the choice as `target.contentLayer` plus a `decisions[]` entry with the rationale (volume,
editor profile, structure). For headless, capture the specific CMS in the decision.

## Routing
- Map each normalized `type` to a route segment:
  - `article`/`post` → `app/blog/[slug]/page.tsx` (+ `app/blog/page.tsx` index).
  - `page` → top-level segments (`app/<slug>/page.tsx`) or a catch-all `app/[...slug]/page.tsx`
    driven by the content layer.
  - taxonomy index → `app/blog/tag/[tag]/page.tsx`.
- Prefer **`generateStaticParams`** to pre-render known slugs from the content layer.
- Preserve old paths where reasonable; otherwise rely on redirects (below).

## Rendering strategy
- Default to **SSG** (static) for marketing/blog content.
- Use **ISR** (`export const revalidate = N`) when a headless CMS publishes frequently.
- Reserve **SSR** for genuinely dynamic/personalized pages (HubSpot smart content, gated content) —
  flag these from discovery as manual.

## Redirects
- Aggregate every normalized item's `redirects[]` + `_site/redirects.json` into **`next.config.js`
  `redirects()`** (or a `vercel.json` / middleware map if the list is large — Next inlines a few
  hundred fine; thousands belong in middleware or a host-level map).
- Every entry is `{ source, destination, permanent: true }` (301). Test verifies these resolve.

## Images & assets
- Copy `migration/export/assets/**` into `public/` (e.g. `public/migrated/...`) **or** upload to the
  CMS/image host for the headless path.
- Rewrite `media[].localPath` references to the new public URL and use **`next/image`** with the
  captured `width`/`height`/`alt`. Configure `images.remotePatterns` if assets stay remote.

## Internal links
- Rewrite in-body links from `sourceUrl`/old paths to `targetPath` using the source→target mapping
  import builds. Unresolved internal links → `import-report.md` warnings and the test link-check.

## i18n
- If normalized items carry non-default `locale`, set up the Next.js i18n routing
  (`app/[locale]/...` or `next.config` i18n) and import one document per locale.

## SEO
- Map `seo.*` to the **Metadata API** (`export const metadata` / `generateMetadata`): `title`,
  `description`, `alternates.canonical`, `openGraph.images`, `robots.index`.
- Generate `app/sitemap.ts` and `app/robots.ts` from the imported item set.
