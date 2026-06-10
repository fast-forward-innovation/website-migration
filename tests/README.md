# Tests

Two layers, both runnable from the repo root.

## Structural (deterministic — no API key, no network)

Validates that the plugin is well-formed and self-consistent: manifests parse and have
required fields, the marketplace root entry matches `plugin.json`, every skill has valid
frontmatter with a `name` matching its directory, and every `${CLAUDE_PLUGIN_ROOT}/...`
reference a skill cites actually exists.

```bash
pip install -r tests/requirements.txt
pytest tests/test_structure.py -v
```

## Behavioral (model-in-the-loop eval)

Runs `migration-discovery` headless against the offline WordPress WXR fixture in
`tests/fixtures/wordpress/sample.wxr.xml` and asserts it writes a sane
`discovery/inventory.json` (the fixture's entities appear, counts are in the right
ballpark, and the manifest's `discovery` phase advances to `done`). Assertions are
tolerant of model variation by design.

Requires the [Claude Code CLI](https://code.claude.com) on `PATH` and an API key. It
**auto-skips** when either is missing.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export CLAUDE_TEST_MODEL=sonnet   # optional; default sonnet
pytest tests/test_behavioral.py -v -m behavioral
```

Under the hood it runs:

```bash
claude -p "/website-migration:migration-discovery ..." \
  --plugin-dir <repo-root> \
  --permission-mode bypassPermissions \
  --model sonnet \
  --output-format json
```

## CI

`.github/workflows/test.yml` runs the structural job on every push/PR. The behavioral job
runs only when an `ANTHROPIC_API_KEY` repository secret is set (so PRs from forks, which
don't receive secrets, skip it automatically).

To enable it: add the secret under **Settings → Secrets and variables → Actions →
`ANTHROPIC_API_KEY`**. Note the behavioral job calls the API and costs tokens per run.
