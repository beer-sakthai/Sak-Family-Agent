import sys

file_path = "packages/agent-self-evolution/tests/skills/test_skill_module.py"
with open(file_path, "r") as f:
    lines = f.readlines()

new_tests = [
    '    def test_no_frontmatter(self, tmp_path):\n',
    '        content = "# Just content\nNo frontmatter here."\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text(content)\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["frontmatter"] == ""\n',
    '        assert skill["body"] == content\n',
    '        assert skill["name"] == ""\n',
    '        assert skill["description"] == ""\n',
    '\n',
    '    def test_malformed_frontmatter(self, tmp_path):\n',
    '        content = "---\nname: malformed\nNo closing markers"\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text(content)\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["frontmatter"] == ""\n',
    '        assert skill["body"] == content\n',
    '\n',
    '    def test_missing_optional_fields(self, tmp_path):\n',
    '        content = "---\nother: field\n---\nBody"\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text(content)\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["name"] == ""\n',
    '        assert skill["description"] == ""\n',
    '        assert skill["body"] == "Body"\n',
    '\n',
    '    def test_empty_file(self, tmp_path):\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text("")\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["raw"] == ""\n',
    '        assert skill["frontmatter"] == ""\n',
    '        assert skill["body"] == ""\n',
    '        assert skill["name"] == ""\n',
    '        assert skill["description"] == ""\n',
    '\n',
    '    def test_only_frontmatter(self, tmp_path):\n',
    '        content = "---\nname: only-fm\n---"\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text(content)\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["name"] == "only-fm"\n',
    '        assert skill["body"] == ""\n',
    '\n',
    '    def test_quotes_handling(self, tmp_path):\n',
    '        content = "---\nname: \"double-quoted\"\ndescription: \'single-quoted\'\n---\nBody"\n',
    '        skill_file = tmp_path / "SKILL.md"\n',
    '        skill_file.write_text(content)\n',
    '        skill = load_skill(skill_file)\n',
    '\n',
    '        assert skill["name"] == "double-quoted"\n',
    '        assert skill["description"] == "single-quoted"\n',
]

# Find the end of TestLoadSkill
insertion_point = -1
for i, line in enumerate(lines):
    if line.startswith("class TestReassembleSkill:"):
        insertion_point = i
        break

if insertion_point != -1:
    # Go back to find the last empty line before TestReassembleSkill
    while insertion_point > 0 and lines[insertion_point-1].strip() == "":
        insertion_point -= 1

    # Insert new tests
    lines[insertion_point:insertion_point] = ["\n"] + new_tests

with open(file_path, "w") as f:
    f.writelines(lines)
