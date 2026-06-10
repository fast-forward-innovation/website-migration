# `migration/manifest.json` — the contract spine

Every migration skill reads this file first, verifies its prerequisites, does its work, then updates
the relevant fields. It is the single source of truth for **what platform we're migrating from**,
**how we're accessing it**, **what we've decided**, and **which phases are done**.

`migration-plan` creates it. Every other skill mutates only its own phase block and never deletes
another phase's recorded output paths.

## Shape

```json
{
  "schemaVersion": 1,
  "project": {
    "name": "acme-www",
    "createdAt": "2026-06-09T00:00:00Z",
    "updatedAt": "2026-06-09T00:00:00Z"
  },
  "source": {
    "platform": "wordpress",
    "baseUrl": "https://old.acme.com",
    "accessMethods": ["live-api", "native-export"],
    "credentialEnvVars": ["WP_APP_USER", "WP_APP_PASSWORD"],
    "exportFiles": ["./migration/_input/acme.wordpress.2026-06-01.xml"],
    "architecture": "headless",
    "codeAccess": {
      "cms": {
        "type": "git",
        "path": null,
        "repoUrl": "https://github.com/acme/old-cms.git",
        "ref": "main",
        "localCheckout": "migration/_input/source-code/cms"
      },
      "frontend": {
        "type": "git",
        "framework": "gatsby",
        "path": null,
        "repoUrl": "https://github.com/acme/old-frontend.git",
        "ref": "main",
        "localCheckout": "migration/_input/source-code/frontend"
      }
    },
    "notes": "WPGraphQL not installed; using REST + WXR for ACF fields."
  },
  "target": {
    "platform": "nextjs",
    "appDir": "./",
    "contentLayer": null,
    "contentLayerDecidedBy": null
  },
  "phases": {
    "plan":         { "status": "done",    "outputs": ["migration/plan.md"], "completedAt": "..." },
    "discovery":    { "status": "pending", "outputs": [] },
    "architecture": { "status": "pending", "outputs": [] },
    "export":       { "status": "pending", "outputs": [] },
    "import":       { "status": "pending", "outputs": [] },
    "test":         { "status": "pending", "outputs": [] },
    "summary":      { "status": "pending", "outputs": [] }
  },
  "decisions": []
}
```

## Field reference

### `source`
- **`platform`** — one of `"drupal" | "wordpress" | "hubspot"`. Selects which
  `references/sources/<platform>.md` the discovery/export skills follow.
- **`baseUrl`** — public origin of the old site (used for URL mapping + asset download).
- **`accessMethods`** — any of `"live-api"`, `"native-export"`. Tells export which extraction path
  to use; both may be present (e.g. API for content, WXR for fields the API omits).
- **`credentialEnvVars`** — **names only** of environment variables holding secrets. Never store
  secret *values* here.
- **`exportFiles`** — paths to native dumps/exports (SQL, WXR, Drupal migrate, HubSpot export) the
  user has placed under `migration/_input/`.
- **`architecture`** — the shape of the **source** site: `"coupled"` (monolithic — the CMS renders
  pages via a theme/templates) or `"headless"` (decoupled — a separate frontend app consumes the CMS
  over an API). Determines whether there are one or two source codebases.
- **`codeAccess`** — whether we have the **source site's code** to inspect, split by role. Each role
  is independent (you may have one, both, or neither). `migration-discovery` scans whatever is
  present; `migration-architecture` reuses frontend findings when the source is already headless.
  - **`cms`** — the backend CMS code: content-type/field definitions, custom modules/plugins, and
    (for a `coupled` source) the theme/templates that render pages.
  - **`frontend`** — the decoupled frontend app (only meaningful when `architecture` is `"headless"`):
    components, routing, data-fetching, styling. Often the highest-value input, since it can map
    almost directly onto the new Next.js components.
  - Each role object has:
    - `type` — `"none" | "local" | "git"`.
    - `path` — for `"local"`, the folder to scan (absolute, or relative to the project root). `null`
      otherwise.
    - `repoUrl` — for `"git"`, the clone URL. Private repos use the user's existing git credentials;
      **no tokens are stored here**. `null` otherwise.
    - `ref` — optional branch/tag/commit to check out (defaults to the repo's default branch).
    - `framework` (frontend only) — detected/declared frontend framework (e.g. `"next"`, `"gatsby"`,
      `"nuxt"`, `"react"`, `"vue"`, `"unknown"`).
    - `localCheckout` — for `"git"`, the path discovery clones/pulls into (default
      `migration/_input/source-code/<role>`); `null` until discovery populates it.

### `target`
- **`platform`** — `"nextjs"` today. (`"wordpress"` is a planned future target.)
- **`appDir`** — root of the Next.js project relative to the migration folder's parent.
- **`contentLayer`** — set by `migration-architecture`. One of `"mdx" | "headless-cms"` (with the
  specific CMS captured in `decisions`). `null` until architecture runs. **`migration-import` reads
  this** to decide how to write content.
- **`contentLayerDecidedBy`** — `"architecture"` once chosen, for traceability.

### `phases`
Each phase has a `status` of `"pending" | "in_progress" | "done" | "failed"`, an `outputs` array of
artifact paths it wrote, and optional `completedAt` / `error`. Skills gate on prerequisite phases
being `"done"` (see each skill's Prerequisites step).

Prerequisite graph:

| Phase | Requires `done` |
|-------|-----------------|
| `plan` | — |
| `discovery` | `plan` |
| `architecture` | `discovery` |
| `export` | `discovery` |
| `import` | `architecture`, `export` |
| `test` | `import` |
| `summary` | at least `import` (more phases → richer report) |

### `decisions`
Append-only log of meaningful choices, each `{ "phase", "decision", "rationale", "at" }`. Example:
`{ "phase": "architecture", "decision": "contentLayer=mdx", "rationale": "~180 posts, dev-owned editing, no non-technical editors", "at": "..." }`.

## Update rules

1. **Read before write.** Load the whole file, mutate only your fields, write the whole file back.
2. **Set `in_progress` on entry, `done`/`failed` on exit**, and refresh `project.updatedAt`.
3. **Record every output path** you create under your phase's `outputs`.
4. **Never persist secrets** — only env-var *names*.
5. If a prerequisite phase is not `done`, **stop and tell the user which skill to run first** rather
   than proceeding with partial state.
