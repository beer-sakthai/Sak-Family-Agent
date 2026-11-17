"""Tests for Marketplace Actions SHA pinning, concurrency, and security invariants."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.lint_workflow_permissions import find_scalar_permissions

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

PINNED_ACTIONS = {
    "devops-infra/action-pull-request": "e66e2ba93519dc63b9884a26e620e2fd0cffab2c",
    "devops-infra/action-commit-push": "be5ba37125c79eb0016cbd8cc385f0aa160538c5",
    "Andrew-Chen-Wang/github-wiki-action": "1bbb4280446f9630e8e21a18012cbacf3b0f992e",
    "connor-baer/action-sync-branch": "f5d20b6a6944c70909c187b558313dfc1d8daa48",
    "dineshsonachalam/markdown-autodocs": "6596b4a049f087c7abe84cc7457e2c53652df810",
    "Khan/pull-request-comment-trigger": "edab8d9ba7759221187ef7120592a6fbfada0d18",
    "chrnorm/deployment-action": "55729fcebec3d284f60f5bcabbd8376437d696b1",
    "bakunyo/git-pr-release-action": "035b7151a53745c03b85c6274ab1ae4bc734eccd",
    "hngprojects/pr-deploy": "2f8b3e0dce07f0c6f7e6e80018dc52081a61b63b",
    "benchmark-action/github-action-benchmark": "4322e5726e6334590d251fc4f92bec0efafc45dc",
    "ghalactic/github-release-from-tag": "30770b91acccc8e1e2f14562d813cb30af08f1c6",
    "jamesgeorge007/github-activity-readme": "4aefbfa1c222d70537dc6a02f0519266aab2b1ea",
    "renovatebot/github-action": "acdd6bda8b035c99ce59d5675816af2aa65a1774",
    "wearerequired/lint-action": "124229c6e2974984ba137c67a499ba28bfc33e33",
    "actions/create-github-app-token": "64ab729a6294000f5aa4a4bc0b73d1f32bc45510",
    "fastify/github-action-merge-dependabot": "73ec4cbb5e56df5591eae286972d5b2201ffe90f",
    "seferov/pr-lint-action": "cbef81c153f36262fbcd92fe97d6c6b8736d891d",
    "Optimal-AI/PR-Label-Checker": "48d46fe6336aedcbb836ca580e86f195f9d14b01",
    "trstringer/manual-approval": "fa642940caf8412403569b28b2db4a1df08a83a3",
    "stepci/stepci": "570a42a52dcb9c7864031da79b047ffbaa268847",
    "benc-uk/workflow-dispatch": "d004979be141727c7a17c28f603e2facc40d0855",
    "BetaHuhn/repo-file-sync-action": "8b92be3375cf1d1b0cd579af488a9255572e4619",
    "convictional/trigger-workflow-and-wait": "f69fa9eedd3c62a599220f4d5745230e237904be",
    "technote-space/workflow-conclusion-action": "45ce8e0eb155657ab8ccf346ade734257fd196a5",
    "saadmk11/github-actions-version-updater": "764bee6cd2905c6c91624f35332f1472fa736c23",
    "rokibhasansagar/slimhub_actions": "5560c2d964bc240edfc5a0855b4b2c8261a29f29",
    "the-actions-org/workflow-dispatch": "3133c5d135c7dbe4be4f9793872b6ef331b53bc7",
    "ahmadnassri/action-workflow-queue": "542658b3a8270cac81ae15d401b0d974732808ac",
    "varunsridharan/action-github-workflow-sync": "3c60cce5ee8e615a7c68ac75fc14893dcac62d49",
    "technote-space/auto-cancel-redundant-workflow": "7d35aba30420fc2368f8aeed50371e99e7fa3239",
    "ahmadnassri/action-workflow-run-wait": "2aa3d9e1a12ecaaa9908e368eaf2123bb084323e",
    "hoangvvo/gitflow-workflow-action": "a8dcd721fe5390b7f837873d5af2497980890a7e",
    "github/setup-licensed": "be11bcbb82e3140b6cf260e647c3efeeca8fcefd",
    "PhrozenByte/gh-workflow-immortality": "39378c27dcacbc17e6fbf83057d1fc40c574000d",
    "fergusmacd/github-actions-usage": "86eef42173b5fe9778e33326468f51cc5a34348c",
    "martialonline/workflow-status": "326830cacf79872efe767e15031f58d1ea0508c4",
    "lasith-kg/dispatch-workflow": "2597e9a3d222d7959052dea1c009560bbeb495e4",
    "wadackel/checkbox-workflow-action": "39a84e680429bb174302beed9f222e06972cecf9",
    "NejcZdovc/comment-pr": "a423635d183a8259308e80593c96fecf31539c26",
    "ArcticLampyrid/action-wait-for-workflow": "ff297b23789206858260877c4b83026d90c6db8c",
    "kvendingoldo/git-flow-action": "ca756ba150c376eb9bf35e3ff3ed591913bb7f11",
    "dortort/gemini-actions": "c7ce09711c46a567055a16a762c0c99fdf181aeb",
    "hoverkraft-tech/ci-dokumentor": "93a10eb9c637d6b06ef394f12d60189b192b87c2",
    "rubensflinco/gemini-code-review-action": "eff35325520e8afcd9ed86618920a4804925c05f",
    "jgunnink/gemini-review-bot": "a1912666a1c394f0f7b51cb0910d02d54c1a93f7",
    "stefanzweifel/git-auto-commit-action": "d0b01107b5db882071f96de5dd4b54961ea93f4c",
    "ahmadnassri/action-dependabot-auto-merge": "45fc124d949b19b6b8bf6645b6c9d55f4f9ac61a",
    "autofix-ci/action": "c5b2d67aa2274e7b5a18224e8171550871fc7e4a",
    "necojackarc/auto-request-review": "9a4b11888f2d60c79120c5413f13eb63febc2b68",
    "wow-actions/auto-assign": "67fafa03df61d7e5f201734a2fa60d1ab111880d",
    "lucasbento/auto-close-issues": "667e4f3cd71f2760a3869680944b8df55325b005",
    "reitermarkus/automerge": "634d0a4b51134c163eee182ac9aa79133eb33e8d",
    "mschilde/auto-label-merge-conflicts": "3fdaf1c8b3f8e5b0f88753d9cb3c9c779370b3ef",
    "JAI0705/DevOps_Pipeline_healer_agent": "a23105b6783cdd78c9a1417f1d20d66d5cb7598d",
    "Shawnchee/the-auditor": "fdc6bdd022bbe244c9134d14b8241f04e4537142",
    "johnmanjiro13/auto-reviewer-assign": "cac72d552c3f3163adfb7bc4a3f676163911d0ef",
    "3lvia/gh-actions-docs": "2db29362f0d6d92052f6fa49b71743af5f0c11f8",
    "desbo/merge-pr-action": "1accf075c170137f89b939d6f5d7b2600d0dc344",
    "casassg/auto-merge-bot": "5d2a038b1b9ac48a0ac698519001d3e6cd299747",
    "BaharaJr/merge-pr": "28444c475789780e15b5b4f5e67a5309a7f48d6a",
    "devjoes/pr-automation": "b9f61eef9e676ad2253aa4a08a2313468e7e57b7",
    "nicklegan/github-repo-self-approve-action": "bea11671222460fbc41ad06797a0de470985f602",
    "pratikmallya/autolabeler-codeowners": "cca9694441f25116fcb5d5f16757a6e43e5c4375",
    "Bhupesh-V/update-pr-reminder-action": "9ccd3478ba932042624093b7153300ce63a68b66",
    "salehhashemi1992/ai-code-guard": "769ff29bf912ecf13a432773cb8bbd076b850207",
    "wow-actions/add-badges": "43f2c1eaecfb2596b89a8136a3fbda4f18d1d188",
    "LucasRuy/sync-branch-action": "2208081dfed383bf8e9c13ce862061a3e7a58239",
    "vargiuscuola/genshdoc": "0f2a1895670c474de679631a33eae9369743af5f",
    "DiogoRibeiro7/safe-dependabot": "6108108e756497ce9c7b4e9e38d76fea453c1181",
    "onebalaban/DependabotHelper": "9455093e7f3d2338e9eeb42984865e29660e3ad8",
    "invi5H/dependabot-automerge": "aea0b2bd7e72af2f06118ce377821568046589f6",
    "GavinMeierSonos/dependabot-action": "a0789e7b36fd4cf0ba2906e77568ae5deae85f95",
    "dependabot/fetch-metadata": "25dd0e34f4fe68f24cc83900b1fe3fe149efef98",
    "goatandsheep/dependabot-issue-action": "085384c6fc7247bf455bcd86178c6fc8a5ffc1d5",
    "halostatue/dependabot-automerge": "61a7c53cf7dd144b2e874cb0bc163ed4d3a89f22",
    "github/automatic-contrib-prs": "fbb93799968fd54783c29339b95e9fcf888c8709",
    "chinthakagodawita/autoupdate": "0707656cd062a3b0cf8fa9b2cda1d1404d74437e",
    "inat-get/action-is-roadmap": "9fecd4863d39e5033e9c641a381e00d9c1a21265",
}


def test_marketplace_workflows_exist_and_pinned() -> None:
    for action_name, expected_sha in PINNED_ACTIONS.items():
        found = False
        pattern = re.compile(rf"{re.escape(action_name)}@([a-f0-9]+)")
        for workflow_path in WORKFLOWS_DIR.glob("*.yml"):
            if workflow_path.name.endswith(".lock.yml"):
                continue
            content = workflow_path.read_text(encoding="utf-8")
            if action_name in content:
                found = True
                matches = pattern.findall(content)
                assert matches, f"{workflow_path.name} uses unpinned {action_name}"
                for sha in matches:
                    assert sha == expected_sha, (
                        f"{workflow_path.name} uses unexpected SHA {sha} for {action_name}"
                    )
        assert found, f"No active workflow found utilizing {action_name}"


MARKETPLACE_WORKFLOW_FILES = [
    "wiki-sync.yml",
    "pr-comment-trigger.yml",
    "autodocs.yml",
    "reusable-deployment.yml",
    "branch-sync.yml",
    "automated-pr-maintenance.yml",
    "git-pr-release.yml",
    "reusable-pr-deploy.yml",
    "continuous-benchmark.yml",
    "release-from-tag.yml",
    "activity-readme.yml",
    "renovate.yml",
    "lint-check.yml",
    "reusable-app-token.yml",
    "dependabot-auto-merge.yml",
    "pr-lint.yml",
    "pr-label-checker.yml",
    "reusable-manual-approval-gate.yml",
    "step-ci.yml",
    "actions-version-updater.yml",
    "runner-disk-cleaner.yml",
    "workflow-queue.yml",
    "workflow-conclusion.yml",
    "auto-cancel-redundant.yml",
    "reusable-workflow-dispatch.yml",
    "reusable-workflow-dispatch-wait.yml",
    "reusable-trigger-workflow-wait.yml",
    "repo-file-sync.yml",
    "github-workflow-sync.yml",
    "workflow-run-wait.yml",
    "gitflow-lifecycle.yml",
    "licensed-audit.yml",
    "workflow-immortality.yml",
    "actions-usage-audit.yml",
    "workflow-status-indicator.yml",
    "reusable-dispatch-method.yml",
    "checkbox-trigger.yml",
    "reusable-comment-pr.yml",
    "wait-for-workflow.yml",
    "git-flow-action.yml",
    "gemini-actions.yml",
    "ci-dokumentor.yml",
    "gemini-code-review-action.yml",
    "gemini-review-bot.yml",
    "git-auto-commit.yml",
    "dependabot-auto-merge-cli.yml",
    "autofix.yml",
    "auto-request-review.yml",
    "auto-assign.yml",
    "auto-close-issues.yml",
    "automerge-pr.yml",
    "auto-label-merge-conflicts.yml",
    "pipeline-healer.yml",
    "the-auditor.yml",
    "auto-reviewer-assign.yml",
    "gh-actions-docs.yml",
    "merge-pr-action.yml",
    "auto-merge-bot.yml",
    "merge-pr.yml",
    "pr-automation.yml",
    "self-approve.yml",
    "autolabeler-codeowners.yml",
    "update-pr-reminder.yml",
    "ai-code-guard.yml",
    "add-badges.yml",
    "sync-branch-action.yml",
    "genshdoc.yml",
    "safe-dependabot.yml",
    "dependabot-helper.yml",
    "dependabot-automerge.yml",
    "dependabot-workflow.yml",
    "dependabot-fetch-metadata.yml",
    "dependabot-issue.yml",
    "enable-automerge-dependabot.yml",
    "auto-contrib-pr.yml",
    "autoupdate-branches.yml",
    "generate-roadmap.yml",
]


def test_marketplace_workflows_have_concurrency_and_harden_runner() -> None:
    """Ensure all marketplace workflow files declare concurrency and harden-runner."""
    for filename in MARKETPLACE_WORKFLOW_FILES:
        workflow_path = WORKFLOWS_DIR / filename
        assert workflow_path.is_file(), f"{filename} does not exist"
        content = workflow_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        assert isinstance(data, dict), f"{filename} is not valid YAML"
        assert "concurrency" in data, f"{filename} is missing concurrency declaration"
        assert "step-security/harden-runner" in content, (
            f"{filename} is missing StepSecurity harden-runner"
        )


def test_marketplace_workflow_permissions_remain_strict_mappings() -> None:
    """Ensure no scalar permissions exist across any workflow file."""
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Found scalar permissions: {findings}"
