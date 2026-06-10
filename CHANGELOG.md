# Changelog

All notable changes to the `website-migration` plugin.

## [0.2.0]

### Added
- **Source-code access.** `migration-plan` now asks whether we have the old site's codebase, as a
  **local folder** or **git repo** (cloned to `migration/_input/source-code/<role>`).
  `migration-discovery` scans it as an authoritative structural input and records each finding's
  provenance (`api` / `export` / `cms-code` / `frontend-code`).
- **Headless source support.** The plan records whether the source site is **coupled** (CMS renders
  pages) or **headless** (decoupled frontend + CMS API), and splits code access into `cms` and
  `frontend` roles (with frontend framework detection: Next/Gatsby/Nuxt/Vue/…). When the source is
  headless, `migration-discovery` extracts the frontend's routing, data-fetching/field-usage, and
  component inventory, and `migration-architecture` reuses that frontend (port React components, carry
  over design tokens, keep the data model lean).
- **Pantheon hosting + Terminus.** Default host is Pantheon. `migration-plan` prompts for the host
  provider and **production base domain**, and can provision sites via Terminus — the Next.js app as a
  Pantheon **Front-End Site**, and optionally a WordPress/Drupal **CMS backend** for a headless content
  layer. `migration-import` deploys to the Front-End Site and promotes `dev → test`. New reference
  `references/targets/pantheon.md` documents the Terminus workflow.
- **Tests + CI.** Structural validation suite and a behavioral eval (offline WordPress WXR fixture) in
  `tests/`, with a GitHub Actions workflow (structural on every push/PR; behavioral gated on an
  `ANTHROPIC_API_KEY` secret).

### Changed
- `migration/manifest.json` schema gained `source.architecture`, `source.codeAccess.{cms,frontend}`,
  and `target.hosting` (provider, baseDomain, credential env-var names, and per-role front-end/CMS
  site config). See `references/manifest-schema.md`.
- `migration-architecture` uses `target.hosting.baseDomain` for canonical URLs and absolute redirect
  targets. `migration-summary` reports hosting + domain + provisioning status.

### Guardrails
- Infrastructure-creating Terminus actions (`site:create`, `domain:add`, `env:deploy ... live`)
  require explicit confirmation; recording config is the safe default.
- Secrets and tokens are referenced by env-var **name** only — never written to the repo or the
  `migration/` folder. Source codebases are treated read-only.

## [0.1.0]

### Added
- Initial plugin: 8 migration skills (`migration-plan`, `migration-discovery`,
  `migration-architecture`, `migration-export`, `migration-import`, `migration-full`,
  `migration-test`, `migration-summary`) forming a pipeline that hands off through a shared
  `migration/` folder governed by `manifest.json`.
- Source platforms: Drupal, WordPress, HubSpot (live API + native export). Target: Next.js, with a
  canonical normalized content schema decoupling source from target.
- Marketplace catalog so the repo installs directly from GitHub.
