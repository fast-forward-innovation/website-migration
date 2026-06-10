# Hosting: Pantheon (via Terminus)

The default host for migrated sites. Pantheon hosts the **Next.js frontend** as a
[**Front-End Site**](https://docs.pantheon.io/guides/decoupled) and can also host a **CMS backend**
(WordPress/Drupal) when the architecture chose a `headless-cms` content layer on Pantheon.

[Terminus](https://docs.pantheon.io/terminus) is Pantheon's CLI. Skills use it to inspect and
(with confirmation) provision sites. Treat `site:create`, `domain:add`, and `env:deploy` as
**outward-facing actions** — confirm with the user before running them.

## Auth (no secrets in the repo)

Terminus authenticates with a **machine token**. Store the token in an environment variable whose
**name** is recorded in `target.hosting.credentialEnvVars` (default `PANTHEON_MACHINE_TOKEN`); never
write the token value into the manifest or any file.

```bash
terminus auth:login --machine-token="$PANTHEON_MACHINE_TOKEN"
terminus whoami            # verify
```

## Inspecting existing sites

```bash
terminus site:list
terminus site:info <site>
terminus env:list <site>
terminus domain:list <site>.<env>
```

## Provision the Next.js Front-End Site

Front-End Sites build a Git-connected Next.js app. Provisioning is partly dashboard-driven, so
**verify the exact flow for the account** before automating — the steps below are the Terminus-side
pieces; connecting the GitHub repo and build settings may be done in the Pantheon dashboard.

```bash
# Create the front-end site (confirm name + region with the user first)
terminus site:create <frontend-siteName> "<Human Label>" --region=<region>
# Connect the repo / build config per Front-End Sites docs, then verify environments:
terminus env:list <frontend-siteName>
```

Record `target.hosting.frontend.siteName` and set `provisioned: true` once created.

## Provision a CMS backend (only for a Pantheon-hosted headless CMS)

When `target.contentLayer == "headless-cms"` and the CMS is WordPress/Drupal on Pantheon:

```bash
# Create from an upstream (WordPress or a Drupal upstream)
terminus site:create <cms-siteName> "<Human Label>" <upstream-id>
terminus connection:set <cms-siteName>.dev git     # to push code if needed
```

`import` writes content into this CMS via its API; `target.hosting.cms.siteName` identifies it.

## Domains & environments

```bash
# Attach the production base domain (from target.hosting.baseDomain)
terminus domain:add <frontend-siteName>.live <baseDomain>
terminus domain:list <frontend-siteName>.live
```

Standard Pantheon environments are `dev` → `test` → `live`. Promote with:

```bash
terminus env:deploy <site>.test    # dev  -> test
terminus env:deploy <site>.live    # test -> live
terminus env:clear-cache <site>.<env>
```

## Deploy (used by `migration-import`)

For the Front-End Site, push the built Next.js repo to the connected Git remote (Pantheon builds on
push), or follow the Front-End Sites deploy flow, then promote through `test` → `live` with
`terminus env:deploy`. For a Pantheon CMS backend, push code via the `git` connection and run
`terminus wp ...` / `terminus drush ...` for backend tasks.

## Guardrails

- **Confirm before creating or changing infrastructure** (`site:create`, `domain:add`, `env:deploy`).
  Recording hosting config in the manifest is safe and default; provisioning is an explicit step.
- Read the machine token from its env var only; never persist it.
- If Terminus isn't installed or the token is unset, capture the hosting config anyway and tell the
  user which step to run later — don't block the migration on provisioning.
