"""Regression coverage for skill-manager fixes carried by the fork."""

from unittest.mock import patch


VALID_SKILL_CONTENT = """---
name: test-skill
description: Use when testing skill creation.
---
# Test Skill

Do the test.
"""


def test_find_skill_follows_symlinked_directory(tmp_path):
    """Skill discovery must descend into symlinked skill directories."""
    from tools.skill_manager_tool import _find_skill

    skills = tmp_path / "local-skills"
    skills.mkdir()
    real_dir = tmp_path / "real-skill"
    real_dir.mkdir()
    (real_dir / "SKILL.md").write_text(
        "---\nname: test-symlink\ndescription: test\n---\n# Test\n",
        encoding="utf-8",
    )
    symlink = skills / "test-symlink"
    symlink.symlink_to(real_dir, target_is_directory=True)

    with patch("agent.skill_utils.get_all_skills_dirs", return_value=[skills]):
        found = _find_skill("test-symlink")

    assert found is not None
    assert found["path"] == symlink


def test_create_rejects_existing_target_when_discovery_misses(tmp_path):
    """Creation must not overwrite an existing SKILL.md missed by discovery."""
    from tools.skill_manager_tool import _create_skill

    skill_dir = tmp_path / "dupe-skill"
    skill_dir.mkdir(parents=True)
    content = VALID_SKILL_CONTENT.replace("name: test-skill", "name: dupe-skill")
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    with patch("tools.skill_manager_tool.SKILLS_DIR", tmp_path), patch(
        "agent.skill_utils.get_all_skills_dirs", return_value=[]
    ):
        result = _create_skill("dupe-skill", content)

    assert result["success"] is False
    assert "already exists" in result["error"]


def test_create_still_creates_new_skill(tmp_path):
    """The collision guard must not block ordinary skill creation."""
    from tools.skill_manager_tool import _create_skill

    skill_dir = tmp_path / "test-skill"

    with patch("tools.skill_manager_tool.SKILLS_DIR", tmp_path), patch(
        "agent.skill_utils.get_all_skills_dirs", return_value=[]
    ), patch("tools.skill_manager_tool._security_scan_skill", return_value=None), patch(
        "tools.skill_manager_tool._attach_lint_findings"
    ):
        result = _create_skill("test-skill", VALID_SKILL_CONTENT)

    assert result["success"] is True
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == VALID_SKILL_CONTENT
