import os
from pathlib import Path

def find_skills():
    skills = []
    for root, dirs, files in os.walk("skills/sakthai"):
        if "SKILL.md" in files:
            skills.append(Path(root) / "SKILL.md")
    return skills

def finalize_skill(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"Skipping {path}: not three parts")
        return

    frontmatter = parts[1].strip()
    body = parts[2].strip()

    # Get name from frontmatter
    import yaml
    try:
        front = yaml.safe_load(frontmatter)
        name = front.get("name", "Skill")
    except:
        name = "Skill"

    # Standardize H1: use the name if no H1 exists
    if not body.startswith("# "):
        # Convert slug-case to Title Case
        title = name.replace("-", " ").title()
        body = f"# {title}\n\n" + body

    new_text = f"---\n{frontmatter}\n---\n\n{body}\n"
    path.write_text(new_text, encoding="utf-8")
    print(f"Finalized {path}")

if __name__ == "__main__":
    for s in find_skills():
        finalize_skill(s)
