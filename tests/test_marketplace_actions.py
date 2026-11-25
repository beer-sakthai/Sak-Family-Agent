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
    "renovatebot/github-action": "acdd6bda8b035c99ce59d5675816af2aa65a1774",
    "wearerequired/lint-action": "124229c6e2974984ba137c67a499ba28bfc33e33",
    "actions/create-github-app-token": "f418cff399f7aef4c2f0ad47e25ca7a6abbdd6fc",
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
    "IBM/devopsauto-testserver-actions": "c704855bdbbae4f0df152919d00fb0bd40f67ee0",
    "gizumon/github-actions-documenter": "843a0f92e66b5db20f76d3c707beb0329b48c628",
    "umonkey/github-wiki-tools": "72074b2f45265374a7571550ff7576cbae15af60",
    "pndurette/gh-actions-auto-docs": "e6b4c8b27a1ddd45e1b3157d68ebacd83dd02cd5",
    "dependfix/dependfix": "80883880c7016b093c4721cc5a8b2d51eef102a0",
    "harishrsk/dependafix-action": "a5c537144e03f8c2d42734060736dacdc22e53d5",
    "PrismorSec/patchbot": "60906559fec33549e4ac97f5f3e707c517342486",
    "advanced-security/python-lint-code-scanning-action": "7ebf81c5860ee4d41849872bc2f95b4243c8dc28",
    "IAreKyleW00t/verified-bot-commit": "3a1e72c2443cce5574f76a9b2bb36e355d667743",
    "imjohnbo/issue-bot": "3188c6ce06249206709d3b1f274d0d4c5a521601",
    "fluttercandies/no-free-usage-action": "84718b1a36661a646d795bf4a7fd15a3f6f087e2",
    "cli-stuff/setup-github-actions-bot": "6f48e564efbb89283f4ec530312d3cfd23a95f58",
    "autoissue/autoissuebot": "5af0465ff89575e2b7d9650c9a2d3fb3b6faea36",
    "gotmax23/set-bot-git-user-action": "f098db822a2e5baf8a268d7a0c7529734755b6ae",
    "wzshiming/gh-ci-bot": "91068dab3f3130054b3569e2b0dd2db07cd53c2a",
    "dtherhtun/google-chat-action": "dec309966ac02aa06cf79fb930096919ed8d7baf",
    "gmolau/codeowners": "efba36333e402884498dc49d216d2f9612bd69a8",
    "jmaxdev/automatic-answer": "18cb23e840a04d7b2644a767f6246cc850475885",
    "dinakars777/pr-triage-action": "423e4bee6992248223e6bc4f5840c0ca2e9c0dcf",
    "teohsinyee/ai-pr-opener-bot": "4c36fd7b3830433b7c7f0cd5f8c16ed6cd524351",
    "gh-bot/fix-labeler": "82c1402f0c82ebadc301f508ab3f1f69184752d2",
    "AhmedHoussou/action-test-failure-triage": "e0d3f0498d8518bf8a7da1356005b09e7109ed55",
    "Lucky3028/git-as-gha": "48a4d96a17acfb1f4f54604785693b1f03ba1524",
    "dohyeon5626/bot-check-action": "4f0b434cd4999aa880bd4ed4855105a1c9cefba5",
    "SimonMarquis/setup-github-app-as-bot": "a778f68e0790a7d0dbebc9fbc2187048026b1a15",
    "nolekek/AutoHeal-CI": "eafa410862f761d5a8f96ea946d07c9d0d7f33d7",
    "kakaotech-25/Hackathon-PR-Review": "17f9b3fe3a8b5333c1828e902276897cdeae8e8b",
    "drengskapur/gitbot-config": "00aecab0a790b146951f9e0c48f564eaf26a9df6",
    "crxqhuinvaiuoznzedkh/actions-add-reviewers": "31c8c487b1642f4b7cad9556bf9b759882b57914",
    "actions/dependency-review-action": "bbc44d14a204704ccc493733616cd1e93a0321ec",
    "oke-py/npm-audit-action": "da53d502b06a0bc95f9ce3c0ebab0c4c713fae4a",
    "mlaplante/githubprreviewhelperextension": "84c713e117ecfb6fa835075bf23f5dc48d6d657b",
    "actions/attest": "1e69f48acb82d1966a394da916b4c1698aa569d6",
    "reviewdog/action-suggester": "fd22a83b1ebc13fd8aee5d57b06793fce6f20fb9",
    "reviewdog/action-actionlint": "ae857e78c1b42b3d0a49637181b09d3d56d402b4",
    "reviewdog/action-misspell": "c846b6b0996029d2d39540c8ffebebbd957072db",
    "rossjrw/pr-preview-action": "873417d2df72380da1f3978378fb58560bcde976",
    "anchore/sbom-action": "66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c",
    "devantler-tech/setup-agent-skills-action": "aaf3bf62f137e3157e38fa8c44bb0fe6427a74ff",
    "mvkaran/setup-copilot-cli": "d05a47209e6b3185c9c55702bef49f28e6eebef7",
    "austenstone/copilot-cli": "5a9fbe56fd6cdb5e50d329fd87c751748cf5182f",
    "depmedicdev-byte/ci-doctor": "131c2c50a4487787b4f6ceb3eb3b409198be5b7c",
    "iamarunbrahma/workflow-doctor": "c7d9497acff1acb398ed1da76add1cc92536afd2",
    "ravi-arnan/agent-skills-doctor": "bfe08bdbe5ff00ded2a3d8f4afdab47282319826",
    "wow-actions/auto-close-fixed-issues": "d87a73261d3881451f5b35a80cfe0eaed3e95931",
    "grandmasterdev/github-action-npm-audit-fix": "acb53f70fb4406f6b03e9df77ab5a76611b024b5",
    "houselearning/Clean": "837a968808c96d6c317449b7e9e2bc75af4e5832",
    "DigiCatalyst-Systems/dependabot-risk": "b52f928fe6f146f7aa29d5c820d7cd1cc57ece41",
    "meanusarcanus/ai-pr-reviewer-action": "9a2e09833376f54db095b71ca638d2204485c31a",
    "mtl1979/dependencies-autoupdate": "7230f7c4e5c186601a03e3e9f8d7ad16c6b4e122",
    "ryanclark/lint-action": "316d8bd29e28a292657682f6c6e45ca1dab41496",
    "maxgfr/github-multi-deployments": "ed720d528c8e44c33cca444d1b5375a866ec724c",
    "oleg-koval/dependabot-lockfile-fixer": "c7002b60b8621ba70c11ec3ab793cc845c1b236d",
    "oven-sh/setup-bun": "0c5077e51419868618aeaa5fe8019c62421857d6",
    "docker/login-action": "8aa5831fb8d48d8f76594c7ddde61ae58019f550",
    "docker/setup-buildx-action": "f87e5991a6d7451dcb8d9637bfbc97413f497069",
    "docker/setup-qemu-action": "99012661954931238ded8c8b007157a8430204e1",
    "docker/build-push-action": "c3c9e263c25d99ce0380d002d59b67737d91b0dc",
    "docker/metadata-action": "dc802804100637a589fabce1cb79ff13a1411302",
    "cloudposse/github-action-sync-docker-repos": "a1a04d57b75e6d64c978f02f777307ad03f6f605",
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
    "rational-test-server.yml",
    "gh-actions-documenter.yml",
    "wiki-page-maintenance.yml",
    "gh-actions-auto-docs.yml",
    "dependfix-security-auto-fix.yml",
    "dependafix-ai-remediation.yml",
    "patchbot-scanner.yml",
    "python-lint-sarif.yml",
    "verified-bot-commit.yml",
    "issue-bot.yml",
    "no-free-usage.yml",
    "setup-github-actions-bot.yml",
    "auto-issue-bot.yml",
    "set-bot-github-user.yml",
    "github-ci-bot.yml",
    "google-chat-notification.yml",
    "codeowners-bot.yml",
    "github-bot-auto-answer.yml",
    "pr-triage-bot.yml",
    "ai-pr-opener-bot.yml",
    "fixed-issues-labeler.yml",
    "playwright-test-failure-triage-bot.yml",
    "git-as-github-actions-bot.yml",
    "bot-check-action.yml",
    "setup-github-app-as-bot.yml",
    "autoheal-ci.yml",
    "pull-request-code-review-bot.yml",
    "config-git-actions-bot.yml",
    "add-reviewers.yml",
    "dependency-review.yml",
    "npm-audit.yml",
    "github-code-review-assistant.yml",
    "playwright-ci-debugger.yml",
    "attest-build-provenance.yml",
    "reusable-artifact-attestation.yml",
    "reviewdog-suggester.yml",
    "actionlint-review.yml",
    "misspell-review.yml",
    "anchore-sbom.yml",
    "setup-agent-skills.yml",
    "copilot-cli.yml",
    "ci-doctor.yml",
    "workflow-doctor.yml",
    "agent-skills-doctor.yml",
    "auto-close-fixed-issues.yml",
    "npm-audit-fix.yml",
    "clean-engine.yml",
    "dependabot-risk-report.yml",
    "ai-pr-reviewer.yml",
    "dependencies-autoupdate.yml",
    "multi-lint-action.yml",
    "dependabot-lockfile-fixer.yml",
    "build.yml",
    "docker-sync-repos.yml",
]


def test_marketplace_workflows_have_concurrency() -> None:
    """Ensure all marketplace workflow files declare concurrency."""
    for filename in MARKETPLACE_WORKFLOW_FILES:
        workflow_path = WORKFLOWS_DIR / filename
        assert workflow_path.is_file(), f"{filename} does not exist"
        content = workflow_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        assert isinstance(data, dict), f"{filename} is not valid YAML"
        assert "concurrency" in data, f"{filename} is missing concurrency declaration"


def test_marketplace_workflow_permissions_remain_strict_mappings() -> None:
    """Ensure no scalar permissions exist across any workflow file."""
    findings = find_scalar_permissions(WORKFLOWS_DIR)
    assert findings == [], f"Found scalar permissions: {findings}"


def test_github_multi_deployments_integration() -> None:
    """Ensure maxgfr/github-multi-deployments is properly integrated and documented."""
    target_sha = PINNED_ACTIONS["maxgfr/github-multi-deployments"]

    # 1. reusable-deployment.yml integration
    reusable_dep = WORKFLOWS_DIR / "reusable-deployment.yml"
    assert reusable_dep.is_file()
    dep_content = reusable_dep.read_text(encoding="utf-8")
    assert f"maxgfr/github-multi-deployments@{target_sha}" in dep_content
    dep_data = yaml.safe_load(dep_content)
    assert dep_data["jobs"]["deploy-record"]["permissions"]["deployments"] == "write"

    # 2. reusable-pr-deploy.yml integration
    pr_dep = WORKFLOWS_DIR / "reusable-pr-deploy.yml"
    assert pr_dep.is_file()
    pr_content = pr_dep.read_text(encoding="utf-8")
    assert f"maxgfr/github-multi-deployments@{target_sha}" in pr_content
    pr_data = yaml.safe_load(pr_content)
    assert pr_data["jobs"]["deploy"]["permissions"]["deployments"] == "write"
    assert pr_data["jobs"]["teardown"]["permissions"]["deployments"] == "write"

    # 3. Documentation exists
    ref_doc = (
        REPO_ROOT
        / "personas"
        / "sakjules"
        / "skills"
        / "SakJules-github-pr-workflow"
        / "references"
        / "github-multi-deployments.md"
    )
    assert ref_doc.is_file()
    ref_text = ref_doc.read_text(encoding="utf-8")
    assert target_sha in ref_text


def test_actions_attest_integration() -> None:
    """Ensure actions/attest is properly integrated, pinned, and documented."""
    target_sha = PINNED_ACTIONS["actions/attest"]

    # 1. Workflow attest-build-provenance.yml integration
    attest_workflow = WORKFLOWS_DIR / "attest-build-provenance.yml"
    assert attest_workflow.is_file()
    attest_content = attest_workflow.read_text(encoding="utf-8")
    assert f"actions/attest@{target_sha}" in attest_content
    attest_data = yaml.safe_load(attest_content)
    job_perms = attest_data["jobs"]["attest-build-provenance"]["permissions"]
    assert job_perms["id-token"] == "write"
    assert job_perms["attestations"] == "write"
    assert job_perms["contents"] == "read"

    # 2. Reusable workflow reusable-artifact-attestation.yml integration
    reusable_attest = WORKFLOWS_DIR / "reusable-artifact-attestation.yml"
    assert reusable_attest.is_file()
    reusable_content = reusable_attest.read_text(encoding="utf-8")
    assert f"actions/attest@{target_sha}" in reusable_content
    reusable_data = yaml.safe_load(reusable_content)
    on_clause = reusable_data.get("on") or reusable_data.get(True)
    assert on_clause is not None
    assert "workflow_call" in on_clause
    reusable_job_perms = reusable_data["jobs"]["attest"]["permissions"]
    assert reusable_job_perms["id-token"] == "write"
    assert reusable_job_perms["attestations"] == "write"
    assert reusable_job_perms["contents"] == "read"

    # 3. Documentation exists
    ref_doc = (
        REPO_ROOT
        / "personas"
        / "sakjules"
        / "skills"
        / "SakJules-github-pr-workflow"
        / "references"
        / "artifact-attestations.md"
    )
    assert ref_doc.is_file()
    ref_text = ref_doc.read_text(encoding="utf-8")
    assert target_sha in ref_text


def test_docker_ecosystem_actions_integration() -> None:
    """Ensure Docker toolchain actions (Wave 26) are properly integrated and pinned."""
    build_path = WORKFLOWS_DIR / "build.yml"
    assert build_path.is_file()
    build_content = build_path.read_text(encoding="utf-8")
    build_data = yaml.safe_load(build_content)

    assert "concurrency" in build_data
    assert isinstance(build_data["permissions"], dict)
    assert build_data["permissions"]["contents"] == "read"

    assert f"docker/login-action@{PINNED_ACTIONS['docker/login-action']}" in build_content
    assert (
        f"docker/setup-buildx-action@{PINNED_ACTIONS['docker/setup-buildx-action']}"
        in build_content
    )
    assert f"docker/setup-qemu-action@{PINNED_ACTIONS['docker/setup-qemu-action']}" in build_content
    assert f"docker/build-push-action@{PINNED_ACTIONS['docker/build-push-action']}" in build_content
    assert f"docker/metadata-action@{PINNED_ACTIONS['docker/metadata-action']}" in build_content

    sync_path = WORKFLOWS_DIR / "docker-sync-repos.yml"
    assert sync_path.is_file()
    sync_content = sync_path.read_text(encoding="utf-8")
    sync_data = yaml.safe_load(sync_content)

    assert "concurrency" in sync_data
    assert isinstance(sync_data["permissions"], dict)
    assert (
        f"cloudposse/github-action-sync-docker-repos@{PINNED_ACTIONS['cloudposse/github-action-sync-docker-repos']}"
        in sync_content
    )
