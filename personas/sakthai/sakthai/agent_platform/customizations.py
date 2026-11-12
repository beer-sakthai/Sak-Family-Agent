from dataclasses import dataclass
from pathlib import Path
import re

@dataclass(frozen=True)
class SkillSummary:
    name: str
    description: str
    path: str

@dataclass(frozen=True)
class RuleDocument:
    scope: str
    content: str

class CustomizationRegistry:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self._skills_index: dict[str, Path] = {}
        self._index_skills()

    def _index_skills(self) -> None:
        search_paths = [
            self.workspace_root / ".agents" / "skills",
            self.workspace_root / ".gemini" / "skills",
        ]
        for base in search_paths:
            if base.exists():
                for skill_md in base.glob("*/SKILL.md"):
                    skill_name = skill_md.parent.name
                    self._skills_index[skill_name] = skill_md

    def list_available_skills(self) -> list[SkillSummary]:
        results: list[SkillSummary] = []
        for name, path in self._skills_index.items():
            content = path.read_text(encoding="utf-8")
            description = ""
            desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
            if desc_match:
                description = desc_match.group(1).strip()
            else:
                lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#") and not line.startswith("---")]
                description = lines[0] if lines else "Custom agent skill"

            results.append(SkillSummary(name=name, description=description, path=str(path)))
        return sorted(results, key=lambda s: s.name)

    def load_skill(self, name: str) -> str:
        if name not in self._skills_index:
            raise KeyError(f"Skill '{name}' not found in registry")
        return self._skills_index[name].read_text(encoding="utf-8")

    def resolve_rules_for_path(self, target_path: Path) -> list[RuleDocument]:
        rules: list[RuleDocument] = []
        current = target_path.resolve()
        if current.is_file():
            current = current.parent

        checkpoints: list[Path] = []
        while True:
            checkpoints.append(current)
            if current == self.workspace_root or current.parent == current:
                break
            current = current.parent

        # Order from root to deepest directory
        for dir_path in reversed(checkpoints):
            for candidate in ["AGENTS.md", "GEMINI.md"]:
                rule_file = dir_path / candidate
                if rule_file.exists():
                    rules.append(
                        RuleDocument(
                            scope=str(rule_file.relative_to(self.workspace_root)),
                            content=rule_file.read_text(encoding="utf-8").strip(),
                        )
                    )
        return rules
