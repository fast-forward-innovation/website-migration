"""Behavioral eval: run migration-discovery headless against an offline WXR fixture
and assert it produces a sane discovery/inventory.json.

This test is model-in-the-loop, so it asserts on *presence and rough parity* (the
fixture's entities and approximate counts) rather than an exact schema — that tolerates
normal model variation while still catching real logic regressions.

It self-skips when the `claude` CLI or an API key is unavailable, so the structural
suite still runs everywhere (local dev, PRs from forks, etc.).
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import PLUGIN_ROOT

FIXTURE = Path(__file__).parent / "fixtures" / "wordpress" / "sample.wxr.xml"
MODEL = os.environ.get("CLAUDE_TEST_MODEL", "sonnet")
TIMEOUT_S = int(os.environ.get("CLAUDE_TEST_TIMEOUT", "600"))

pytestmark = [
    pytest.mark.behavioral,
    pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed"),
    pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"),
]


def _seed_project(tmp_path: Path) -> Path:
    """Create a throwaway target project with a manifest whose plan phase is done and
    whose source is the offline WXR fixture (native-export, no network needed)."""
    migration = tmp_path / "migration"
    (migration / "_input").mkdir(parents=True)
    shutil.copy(FIXTURE, migration / "_input" / "sample.wxr.xml")

    manifest = {
        "schemaVersion": 1,
        "project": {"name": "behavioral-test", "createdAt": "2026-01-01T00:00:00Z",
                    "updatedAt": "2026-01-01T00:00:00Z"},
        "source": {
            "platform": "wordpress",
            "baseUrl": "https://old.acme.example",
            "accessMethods": ["native-export"],
            "credentialEnvVars": [],
            "exportFiles": ["./migration/_input/sample.wxr.xml"],
            "notes": "Offline WXR fixture; do not make network calls.",
        },
        "target": {"platform": "nextjs", "appDir": "./", "contentLayer": None,
                   "contentLayerDecidedBy": None},
        "phases": {
            "plan": {"status": "done", "outputs": ["migration/plan.md"]},
            "discovery": {"status": "pending", "outputs": []},
            "architecture": {"status": "pending", "outputs": []},
            "export": {"status": "pending", "outputs": []},
            "import": {"status": "pending", "outputs": []},
            "test": {"status": "pending", "outputs": []},
            "summary": {"status": "pending", "outputs": []},
        },
        "decisions": [],
    }
    (migration / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (migration / "plan.md").write_text("# Plan\nSource: WordPress (WXR fixture) -> Next.js\n",
                                       encoding="utf-8")
    return tmp_path


def test_discovery_produces_inventory(tmp_path):
    project = _seed_project(tmp_path)

    prompt = (
        "/website-migration:migration-discovery\n\n"
        "Use the WordPress WXR export already referenced in migration/manifest.json "
        "(migration/_input/sample.wxr.xml). Work entirely offline — do not make any "
        "network requests. Write migration/discovery/inventory.json and report.md."
    )
    cmd = [
        "claude", "-p", prompt,
        "--plugin-dir", str(PLUGIN_ROOT),
        "--permission-mode", "bypassPermissions",
        "--model", MODEL,
        "--output-format", "json",
    ]
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=TIMEOUT_S)

    inventory_path = project / "migration" / "discovery" / "inventory.json"
    # Primary signal is the artifact (headless exit codes are coarse). Surface logs on failure.
    assert inventory_path.is_file(), (
        f"discovery/inventory.json was not created.\n"
        f"exit={proc.returncode}\nstdout(tail)={proc.stdout[-1500:]}\nstderr(tail)={proc.stderr[-1500:]}"
    )

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert isinstance(inventory, dict), "inventory.json should be a JSON object"

    blob = json.dumps(inventory).lower()
    # Parity: the fixture's distinctive entities should surface somewhere in the inventory.
    assert "post" in blob and "page" in blob, "expected post and page content types"
    assert "wordpress" in blob, "expected the source platform to be recorded"

    # Rough count parity: at least one content type should reflect the 2 fixture posts.
    counts = _all_ints(inventory)
    assert any(c >= 2 for c in counts), f"expected a content count >= 2, saw {sorted(counts)}"

    # The manifest's discovery phase should have advanced to done.
    manifest = json.loads((project / "migration" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["phases"]["discovery"]["status"] == "done", (
        f"discovery phase not marked done: {manifest['phases']['discovery']}"
    )


def _all_ints(obj):
    """Collect every integer value anywhere in a nested JSON structure."""
    out = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, int):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(_all_ints(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_all_ints(v))
    return out
