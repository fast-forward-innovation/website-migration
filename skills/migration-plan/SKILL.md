---
name: migration-plan
description: Start a website migration off Drupal, WordPress, or HubSpot onto Next.js. Use this first — it detects or asks the source platform, target, and access method, then scaffolds the migration/ folder, manifest.json, and plan.md that every later phase reads. Trigger when the user says they want to migrate/move/replatform a site, or invokes any migration-* skill before the manifest exists.
metadata:
  short-description: Set up a website migration and its plan
---

# Migration Plan

## Overview

This is the **entry point** of the website-migration pipeline. It does no extraction — it establishes
the contract that every later phase depends on: which platform we're migrating **from**, what we're
migrating **to**, how we'll access the source, and the recommended sequence of phases.

Output lives in the **target project** (the Next.js repo you're migrating into) under `migration/`.

## Prerequisites

None. This skill bootstraps the migration. If `migration/manifest.json` already exists, read it and
**update** rather than overwrite — confirm with the user before changing `source.platform` or
`target.platform`, since later phases key off them.

## Workflow

1. **Read the contract docs** `${CLAUDE_PLUGIN_ROOT}/references/manifest-schema.md` and
   `${CLAUDE_PLUGIN_ROOT}/references/normalized-content.md` so the scaffolding you write is valid.
2. **Determine the source platform.** Look for signals in the current directory and any URL the user
   gave (e.g. `/wp-json/`, `X-Generator: Drupal`, HubSpot CMS markers). If ambiguous, ask the user:
   `drupal | wordpress | hubspot`.
3. **Confirm the target.** `nextjs` is the only supported target today; state that explicitly. If the
   user asks for another target (e.g. WordPress), tell them it's planned but not yet available.
4. **Determine access method(s).** Ask which apply: `live-api` (credentials), `native-export`
   (SQL/WXR/Drupal-migrate/HubSpot export files), or both. For `native-export`, ask the user to place
   files under `migration/_input/` and record their paths. For `live-api`, capture the **env-var
   names** that will hold credentials (never the secret values) — see the relevant
   `${CLAUDE_PLUGIN_ROOT}/references/sources/<platform>.md`.
5. **Capture scope** briefly: base URL of the old site, content types in/out of scope, and any
   hard constraints (launch date, URL-preservation requirements).
6. **Scaffold** the folder (do not create secret files):
   ```
   migration/
     manifest.json
     plan.md
     _input/        (only if native-export is used)
   ```
7. **Write `manifest.json`** following the schema, with `phases.plan.status = "done"` and all other
   phases `"pending"`. Fill `source`, `target` (with `contentLayer: null`), and `project`.
8. **Write `plan.md`** — the human-readable migration plan (see Outputs).

## Outputs

- `migration/manifest.json` — initialized per `references/manifest-schema.md`.
- `migration/plan.md` containing:
  - **Summary** — source platform, target, access method(s), base URL, scope.
  - **Phase sequence** with the recommended order and the skill that runs each:
    `migration-discovery → migration-architecture → migration-export → migration-import`
    (or `migration-full` for export+import) `→ migration-test → migration-summary`.
  - **Prerequisites & gates** — restate the prerequisite graph so the user knows what unlocks what.
  - **Open questions / risks** — anything that needs the user (credentials pending, builder markup,
    forms, personalized content).
- Manifest: `phases.plan` → `done`; `source`, `target`, `decisions` populated.

## Guardrails

- **Never write secret values** anywhere — only env-var names in `source.credentialEnvVars`.
- Don't start discovery or extraction here; this skill only plans and scaffolds.
- If `migration/` already exists from a prior run, preserve completed phases — update, don't clobber.
- Be explicit that Next.js is the only target today; don't silently accept an unsupported target.
