"""Deterministic structural validation of the website-migration plugin.

These tests need no API key, no network, and no Claude CLI. They assert the plugin
is well-formed and self-consistent so it will actually load and its skills can find
their reference docs.
"""
import pytest

from conftest import (
    EXPECTED_SKILLS,
    PLUGIN_ROOT,
    PLUGIN_ROOT_REF,
    REFERENCES_DIR,
    SKILLS_DIR,
    load_json,
    read_frontmatter,
)

# Skill description limit enforced by Claude Code.
MAX_DESCRIPTION = 1024

SKILL_DIRS = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []
SKILL_IDS = [p.name for p in SKILL_DIRS]


# --- Plugin manifest ---------------------------------------------------------

def test_plugin_manifest_valid():
    manifest = load_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
    assert manifest.get("name"), "plugin.json must have a name"
    assert manifest["name"] == manifest["name"].lower(), "plugin name should be kebab/lowercase"
    assert manifest.get("description"), "plugin.json must have a description"
    # version is optional, but if present it must look like a string
    if "version" in manifest:
        assert isinstance(manifest["version"], str)


# --- Marketplace catalog -----------------------------------------------------

def test_marketplace_manifest_valid():
    mkt = load_json(PLUGIN_ROOT / ".claude-plugin" / "marketplace.json")
    assert mkt.get("name"), "marketplace.json must have a name"
    assert mkt.get("owner", {}).get("name"), "marketplace.json must have owner.name"
    assert isinstance(mkt.get("plugins"), list) and mkt["plugins"], "marketplace.json needs plugins[]"
    for entry in mkt["plugins"]:
        assert entry.get("name"), "each marketplace plugin entry needs a name"
        assert "source" in entry, "each marketplace plugin entry needs a source"


def test_marketplace_root_source_points_at_this_plugin():
    mkt = load_json(PLUGIN_ROOT / ".claude-plugin" / "marketplace.json")
    plugin = load_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
    root_entries = [e for e in mkt["plugins"] if e.get("source") in (".", "./")]
    assert root_entries, 'expected a marketplace entry with source "." for the root plugin'
    assert any(e["name"] == plugin["name"] for e in root_entries), (
        "the root marketplace entry name must match plugin.json name"
    )


# --- Skill set ---------------------------------------------------------------

def test_all_expected_skills_present():
    assert set(SKILL_IDS) == EXPECTED_SKILLS, (
        f"skill dirs {set(SKILL_IDS)} do not match expected {EXPECTED_SKILLS}"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_skill_has_skill_md(skill_dir):
    assert (skill_dir / "SKILL.md").is_file(), f"{skill_dir.name} is missing SKILL.md"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_skill_frontmatter_valid(skill_dir):
    fm, _ = read_frontmatter(skill_dir / "SKILL.md")
    assert fm.get("name") == skill_dir.name, (
        f"frontmatter name '{fm.get('name')}' must match directory '{skill_dir.name}'"
    )
    desc = fm.get("description", "")
    assert desc, f"{skill_dir.name} needs a description"
    assert len(desc) <= MAX_DESCRIPTION, (
        f"{skill_dir.name} description is {len(desc)} chars (max {MAX_DESCRIPTION})"
    )
    assert fm.get("metadata", {}).get("short-description"), (
        f"{skill_dir.name} needs metadata.short-description"
    )


# --- Reference integrity -----------------------------------------------------

@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_skill_reference_paths_resolve(skill_dir):
    """Every ${CLAUDE_PLUGIN_ROOT}/... path a skill cites must exist.

    Placeholder paths containing <...> (e.g. sources/<platform>.md) are skipped here;
    the concrete source docs are checked in test_source_reference_docs_exist.
    """
    _, body = read_frontmatter(skill_dir / "SKILL.md")
    missing = []
    for rel in PLUGIN_ROOT_REF.findall(body):
        if "<" in rel or ">" in rel:
            continue
        target = PLUGIN_ROOT / rel.lstrip("/")
        if not target.exists():
            missing.append(rel)
    assert not missing, f"{skill_dir.name} cites missing reference paths: {missing}"


def test_source_reference_docs_exist():
    for platform in ("drupal", "wordpress", "hubspot"):
        assert (REFERENCES_DIR / "sources" / f"{platform}.md").is_file(), (
            f"missing references/sources/{platform}.md"
        )


def test_core_reference_docs_exist():
    for rel in ("manifest-schema.md", "normalized-content.md", "targets/nextjs.md"):
        assert (REFERENCES_DIR / rel).is_file(), f"missing references/{rel}"
