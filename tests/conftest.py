"""Shared paths and helpers for the website-migration plugin tests."""
import json
import re
from pathlib import Path

import pytest

# Repo root = the plugin root (this repo is both the plugin and its marketplace).
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PLUGIN_ROOT / "skills"
REFERENCES_DIR = PLUGIN_ROOT / "references"

EXPECTED_SKILLS = {
    "migration-plan",
    "migration-discovery",
    "migration-architecture",
    "migration-export",
    "migration-import",
    "migration-full",
    "migration-test",
    "migration-summary",
}

# Matches ${CLAUDE_PLUGIN_ROOT}/some/path referenced inside SKILL.md bodies.
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[\w./-]+)")


def read_frontmatter(skill_md: Path):
    """Return (frontmatter_dict, body_str) for a SKILL.md, or raise AssertionError."""
    import yaml

    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill_md} must start with YAML frontmatter (---)"
    end = text.find("\n---", 4)
    assert end != -1, f"{skill_md} frontmatter is not terminated with a closing ---"
    fm = yaml.safe_load(text[4:end])
    body = text[end + 4 :]
    assert isinstance(fm, dict), f"{skill_md} frontmatter did not parse to a mapping"
    return fm, body


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def plugin_root() -> Path:
    return PLUGIN_ROOT
