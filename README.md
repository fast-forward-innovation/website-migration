# website-migration

A Claude Code plugin that drives a website migration end-to-end. It moves content and assets off a
legacy CMS — **Drupal**, **WordPress**, or **HubSpot** — and onto a **Next.js** site (the only
target today; a WordPress target is planned).

The plugin ships **8 skills** that form a pipeline. Each skill reads the prior phases' outputs from a
shared `migration/` folder in the target project, does its work, writes its own artifacts back, and
updates a single `migration/manifest.json` state file. That manifest is the contract spine: it lets
each phase run independently and hand off cleanly to the next.

## Pipeline

```
migration-plan ─▶ migration-discovery ─▶ migration-architecture ─┐
                                                                 ▼
            migration-summary ◀─ migration-test ◀─ migration-full (export ─▶ import)
                                                          │
                                              (or run migration-export / migration-import directly)
```

| Skill | Phase | What it does |
|-------|-------|--------------|
| `migration-plan` | `plan` | Detects source/target/access, scaffolds `migration/` + `manifest.json` + `plan.md`. |
| `migration-discovery` | `discovery` | Inventories the **old** site → `discovery/inventory.json` + `report.md`. |
| `migration-architecture` | `architecture` | Designs the **new** Next.js site, picks the content layer → `architecture.md`. |
| `migration-export` | `export` | Extracts + normalizes content/assets → `export/content/*.json` + `export/assets/`. |
| `migration-import` | `import` | Writes normalized content into the Next.js site → `import-report.md` + mapping. |
| `migration-full` | `export` + `import` | Runs export then import in sequence, stopping on first failure. |
| `migration-test` | `test` | Parity, redirect, asset-integrity, link, and build checks → `test/test-report.md`. |
| `migration-summary` | `summary` | Aggregates everything into a human-readable `summary.md`. |

## Install from GitHub

This repo is **both the plugin and its marketplace catalog** (`.claude-plugin/plugin.json` +
`.claude-plugin/marketplace.json`), so no public listing or registry is involved — teammates install
straight from this repo.

One-time, to publish to the existing
[`fast-forward-innovation/website-migration`](https://github.com/fast-forward-innovation/website-migration)
repo:

```bash
cd /path/to/this/repo
git init && git add . && git commit -m "website-migration plugin"
git remote add origin https://github.com/fast-forward-innovation/website-migration.git
git branch -M main
git push -u origin main
```

Each teammate then runs, in any project:

```
/plugin marketplace add fast-forward-innovation/website-migration
/plugin install website-migration@fastforward
```

(`fastforward` is the marketplace `name` from `.claude-plugin/marketplace.json` — change it there if
you want a different label after the `@`.)

### Auto-enable for a whole team

To have everyone on a project get the plugin automatically, commit this to that project's
`.claude/settings.json`. When teammates trust the folder, Claude Code prompts to add the marketplace
and enable the plugin:

```json
{
  "extraKnownMarketplaces": {
    "fastforward": {
      "source": { "source": "github", "repo": "fast-forward-innovation/website-migration" }
    }
  },
  "enabledPlugins": {
    "website-migration@fastforward": true
  }
}
```

Pin a version by setting `"version"` in `plugin.json` and bumping it per release; otherwise each
pushed commit is treated as a new version. Update an installed copy with `/plugin marketplace update`.

## Usage

Invoke the skills in order from the **target project** directory (the Next.js repo you're migrating
*into*). Start with:

```
/migration-plan
```

Then follow the recommended sequence in `migration/plan.md`. Any skill can be run standalone as long
as its prerequisite phases are marked `done` in the manifest — each skill checks this and refuses
clearly if a prerequisite is missing.

## Source access

Two access methods are supported (mix as needed per source):

- **Live API / credentials** — WordPress REST + WPGraphQL, Drupal JSON:API, HubSpot CMS + CRM API.
- **DB dump / native export** — SQL dump, Drupal migrate, WordPress WXR (eXtended RSS), HubSpot export.

Credentials are read from **environment variables** and only *referenced by name* in the manifest —
secrets are never written to the plugin or to the `migration/` folder.

## Reference material

Shared, source-agnostic reference docs live in `references/`:

- `references/manifest-schema.md` — the `migration/manifest.json` contract.
- `references/normalized-content.md` — the canonical intermediate content schema.
- `references/sources/{drupal,wordpress,hubspot}.md` — per-platform extraction notes.
- `references/targets/nextjs.md` — Next.js routing, rendering, images, redirects, content layers.
