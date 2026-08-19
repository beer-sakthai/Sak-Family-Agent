import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "skills-quality-scan.sh"


def test_skills_quality_scan_detection_and_fix(tmp_path: Path) -> None:
    # Set up mock persona skills directory structure
    personas_dir = tmp_path / "personas"
    sakthai_skills = personas_dir / "sakthai" / "skills"

    # Skill 1: Valid skill
    valid_skill = sakthai_skills / "SakThai-valid-skill"
    valid_skill.mkdir(parents=True)
    (valid_skill / "SKILL.md").write_text(
        "---\nname: SakThai-valid-skill\nversion: 1.0.0\ndescription: Valid skill description.\n---\n\n# Valid Skill\n",
        encoding="utf-8",
    )

    # Skill 2: Missing version field
    no_version_skill = sakthai_skills / "SakThai-no-version-skill"
    no_version_skill.mkdir(parents=True)
    no_version_md = no_version_skill / "SKILL.md"
    no_version_md.write_text(
        "---\nname: SakThai-no-version-skill\ndescription: Skill missing version.\n---\n\n# No Version Skill\n",
        encoding="utf-8",
    )

    test_env = {**os.environ, "SFA": str(personas_dir)}

    # Run scan without --fix flag
    proc = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        env=test_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "⚠️ 1 skill quality issues found:" in proc.stdout
    assert "SakThai-no-version-skill — missing version field" in proc.stdout

    # Confirm --fix was not applied yet
    assert "version: 1.0.0" not in no_version_md.read_text(encoding="utf-8")

    # Run scan with --fix flag
    proc_fix = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--fix"],
        env=test_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_fix.returncode == 0
    assert "✅ Auto-fixed 1 skills with --fix:" in proc_fix.stdout
    assert "SakThai-no-version-skill — added version: 1.0.0" in proc_fix.stdout

    # Verify content of fixed SKILL.md
    fixed_content = no_version_md.read_text(encoding="utf-8")
    assert "version: 1.0.0" in fixed_content

    # Run scan again to verify it is clean
    proc_clean = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        env=test_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_clean.returncode == 0
    assert proc_clean.stdout.strip() == ""
