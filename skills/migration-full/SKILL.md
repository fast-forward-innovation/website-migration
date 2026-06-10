---
name: migration-full
description: Run the export and import phases back-to-back — extract+normalize from the old site, then write into the new Next.js site — validating the manifest between stages and stopping on the first failure. A convenience wrapper over migration-export + migration-import. Trigger when the user wants to "run the migration" / "do export and import" after discovery and architecture are done.
metadata:
  short-description: Run export then import in one sequence
---

# Migration Full

## Overview

A thin orchestrator that runs **migration-export** followed by **migration-import** in sequence,
checking the manifest between stages so a bad export never feeds a half-baked import. It owns no
extraction or writing logic of its own — it delegates to the two phase skills and enforces the gate.

## Prerequisites

1. Read `migration/manifest.json`. Require `phases.discovery.status == "done"` **and**
   `phases.architecture.status == "done"` (architecture is required because import needs
   `target.contentLayer`). If either is missing, name the skill to run first and stop.
2. Confirm source access is ready (credentials/env vars or export files), same checks as the export
   skill.

## Workflow

1. **Run the export phase** by following the **migration-export** skill's workflow end-to-end. Read
   `${CLAUDE_PLUGIN_ROOT}/skills/migration-export/SKILL.md` if you need its exact steps; otherwise apply
   its documented procedure. Let it write its outputs and update `phases.export`.
2. **Gate:** re-read the manifest. If `phases.export.status != "done"`, **stop** and report the
   export failure (surface its `error` and `export-report.md` highlights). Do not start import.
3. **Run the import phase** by following the **migration-import** skill's workflow end-to-end. Let it
   write its outputs and update `phases.import`.
4. **Gate:** re-read the manifest. If `phases.import.status != "done"`, stop and report the import
   failure.
5. **Summarize the run** — a short combined status pointing at `export-report.md` and
   `import-report.md`, and recommend running **migration-test** next.

## Outputs

- All outputs of `migration-export` and `migration-import` (this skill writes no new artifacts of its
  own beyond optionally noting the combined run in `migration/plan.md`'s decisions log).
- Manifest: `phases.export` and `phases.import` advanced by the delegated phases.

## Guardrails

- **Stop on first failure** — never run import on top of a failed/partial export.
- Don't duplicate or diverge from the phase skills' logic; this wrapper exists only to sequence and
  gate them. If behavior needs to change, change it in `migration-export` / `migration-import`.
- Preserve idempotency — re-running `migration-full` should resume export and update import, not
  duplicate content.
- Respect the same secret-handling and read-only-source rules as the underlying phases.
