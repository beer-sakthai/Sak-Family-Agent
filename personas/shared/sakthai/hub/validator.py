"""Card validator enforcing House of Sak quality invariants and frontmatter standards."""

from __future__ import annotations

import re

from .models import CardValidationIssue, CardValidationReport


class ModelCardValidator:
    """Audits repository README content against House of Sak guidelines."""

    def validate_card(self, repo_id: str, content: str) -> CardValidationReport:
        issues: list[CardValidationIssue] = []
        score = 100

        # Rule 1: No hardcoded download numbers in markdown body
        hardcoded_dl = re.findall(r"\b(\d+[\d,]*\+?\s*downloads?)\b", content, re.IGNORECASE)
        if hardcoded_dl:
            issues.append(
                CardValidationIssue(
                    rule="no_hardcoded_downloads",
                    message=f"Found hardcoded download mentions ('{hardcoded_dl[0]}'). Use dynamic shields.io badge instead.",
                    severity="warning",
                )
            )
            score -= 15

        # Rule 2: Single Family Table (not repeated 3x)
        family_tables = re.findall(r"\|.*context-1\.5b-merged.*\|", content)
        if len(family_tables) > 1:
            issues.append(
                CardValidationIssue(
                    rule="single_family_table",
                    message=f"Family table appears {len(family_tables)} times. Keep a single canonical table.",
                    severity="warning",
                )
            )
            score -= 15

        # Rule 3: Honest evals (no fake verified: true)
        if re.search(r"verified:\s*true", content, re.IGNORECASE):
            issues.append(
                CardValidationIssue(
                    rule="honest_evals",
                    message="Found 'verified: true'. Internal evaluations must be labeled 'verified: false' with disclaimer.",
                    severity="error",
                )
            )
            score -= 30

        # Rule 4: Correct food-penguin description
        if "food-penguin" in content and re.search(
            r"food\s+image\s+classification", content, re.IGNORECASE
        ):
            issues.append(
                CardValidationIssue(
                    rule="canonical_dataset_facts",
                    message="food-penguin incorrectly labeled as 'food image classification'; should be 'restaurant-analytics tool-calling'.",
                    severity="error",
                )
            )
            score -= 20

        # Rule 5: YAML frontmatter presence
        if not content.startswith("---") or "\n---\n" not in content[3:]:
            issues.append(
                CardValidationIssue(
                    rule="yaml_frontmatter",
                    message="Missing or malformed YAML frontmatter delimiters (must start and close with ---).",
                    severity="error",
                )
            )
            score -= 20

        valid = not any(i.severity == "error" for i in issues) and score >= 70

        return CardValidationReport(
            repo_id=repo_id,
            valid=valid,
            score=max(0, score),
            issues=issues,
        )
