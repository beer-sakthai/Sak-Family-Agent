    def test_no_frontmatter(self, tmp_path):
        content = "# Just content\nNo frontmatter here."
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)
        skill = load_skill(skill_file)

        assert skill["frontmatter"] == ""
        assert skill["body"] == content
        assert skill["name"] == ""
        assert skill["description"] == ""

    def test_malformed_frontmatter(self, tmp_path):
        content = "---\nname: malformed\nNo closing markers"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)
        skill = load_skill(skill_file)

        assert skill["frontmatter"] == ""
        assert skill["body"] == content

    def test_missing_optional_fields(self, tmp_path):
        content = "---\nother: field\n---\nBody"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)
        skill = load_skill(skill_file)

        assert skill["name"] == ""
        assert skill["description"] == ""
        assert skill["body"] == "Body"

    def test_empty_file(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")
        skill = load_skill(skill_file)

        assert skill["raw"] == ""
        assert skill["frontmatter"] == ""
        assert skill["body"] == ""
        assert skill["name"] == ""
        assert skill["description"] == ""

    def test_only_frontmatter(self, tmp_path):
        content = "---\nname: only-fm\n---"
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)
        skill = load_skill(skill_file)

        assert skill["name"] == "only-fm"
        assert skill["body"] == ""

    def test_quotes_handling(self, tmp_path):
        content = """---
name: "double-quoted"
description: 'single-quoted'
---
Body"""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(content)
        skill = load_skill(skill_file)

        assert skill["name"] == "double-quoted"
        assert skill["description"] == "single-quoted"
