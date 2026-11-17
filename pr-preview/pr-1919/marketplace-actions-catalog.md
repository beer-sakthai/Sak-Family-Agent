# GitHub Marketplace Actions Catalog & Security Standards

**Status:** Adopted  
**Standard:** OpenSSF Scorecard Immutable Commit SHA Pinning  
**Enforcement:** Automated tests (`tests/test_marketplace_actions.py`) & workflow permissions linter

---

## 1. Overview & Security Mandate

To prevent supply-chain attacks (such as tag mutation, compromised upstream accounts, or unexpected breaking changes), all third-party GitHub Actions utilized in the House of Sak repository must adhere to the following invariants:
1. **Commit SHA Pinning:** Every `uses:` reference must target a full 40-character commit SHA accompanied by a human-readable tag comment (e.g., `owner/repo@<sha> # <tag>`).
2. **Explicit Permissions Mapping:** Top-level and job-level permissions must be declared as explicit YAML mappings (e.g., `contents: read`). Broad scalar declarations (`read-all`, `write-all`) are rejected by repository linting.
3. **StepSecurity Harden-Runner:** Every runner instance executing third-party actions must initialize StepSecurity's `harden-runner` as its first step to enforce outbound network and file integrity.
4. **Deterministic Concurrency:** Every active workflow must declare a `concurrency:` group to avoid race conditions.

---

### 2. Seventy-Four Verified Marketplace Actions

| Action Name | Upstream Repository | Tag | Immutable Commit SHA | Required Permissions | Purpose |
|---|---|---|---|---|---|
| **Create Pull Request** | [`devops-infra/action-pull-request`](https://github.com/devops-infra/action-pull-request) | `v0.5.5` | `e66e2ba93519dc63b9884a26e620e2fd0cffab2c` | `contents: write`, `pull-requests: write`, `issues: write` | Automated PR creation with template replacement & diffs |
| **Commit & Push** | [`devops-infra/action-commit-push`](https://github.com/devops-infra/action-commit-push) | `v0.9.2` | `be5ba37125c79eb0016cbd8cc385f0aa160538c5` | `contents: write` | Staging, signing, committing & pushing file changes |
| **Wiki Sync** | [`Andrew-Chen-Wang/github-wiki-action`](https://github.com/Andrew-Chen-Wang/github-wiki-action) | `v5` | `1bbb4280446f9630e8e21a18012cbacf3b0f992e` | `contents: write` | Syncs in-repo Markdown (`docs/`) to GitHub Wiki (`.wiki.git`) |
| **Branch Sync** | [`connor-baer/action-sync-branch`](https://github.com/connor-baer/action-sync-branch) | `v2` | `f5d20b6a6944c70909c187b558313dfc1d8daa48` | `contents: write`, `pull-requests: write` | Auto-syncs branches / opens catch-up PRs on merge |
| **Markdown Autodocs** | [`dineshsonachalam/markdown-autodocs`](https://github.com/dineshsonachalam/markdown-autodocs) | `v1.0.7` | `6596b4a049f087c7abe84cc7457e2c53652df810` | `contents: read` / `write` | Injects code blocks, JSON tables, and workflow artifacts into Markdown |
| **PR Comment Trigger** | [`Khan/pull-request-comment-trigger`](https://github.com/Khan/pull-request-comment-trigger) | `v1.1.0` | `edab8d9ba7759221187ef7120592a6fbfada0d18` | `pull-requests: read`, `issues: write` | Detects slash commands or keyword triggers in PR comments |
| **Deployment Action** | [`chrnorm/deployment-action`](https://github.com/chrnorm/deployment-action) | `v2.0.7` | `55729fcebec3d284f60f5bcabbd8376437d696b1` | `deployments: write` | Creates GitHub Deployments and tracks environment URLs |
| **Git PR Release** | [`bakunyo/git-pr-release-action`](https://github.com/bakunyo/git-pr-release-action) | `v1.4` | `035b7151a53745c03b85c6274ab1ae4bc734eccd` | `contents: write`, `pull-requests: write`, `issues: write` | Automated release PR aggregating merged PR summaries |
| **PR Deploy** | [`hngprojects/pr-deploy`](https://github.com/hngprojects/pr-deploy) | `V2.0.1` | `2f8b3e0dce07f0c6f7e6e80018dc52081a61b63b` | `contents: read`, `pull-requests: write` | Ephemeral containerized deployments for pull requests |
| **Continuous Benchmark** | [`benchmark-action/github-action-benchmark`](https://github.com/benchmark-action/github-action-benchmark) | `v1.22.2` | `4322e5726e6334590d251fc4f92bec0efafc45dc` | `contents: write`, `pull-requests: write` | Continuous performance metric tracking and regression alerts |
| **GitHub Release from Tag** | [`ghalactic/github-release-from-tag`](https://github.com/ghalactic/github-release-from-tag) | `v6` | `30770b91acccc8e1e2f14562d813cb30af08f1c6` | `contents: write`, `issues: write` | Automatic GitHub release creation sourced from git tags |
| **GitHub Activity Readme** | [`jamesgeorge007/github-activity-readme`](https://github.com/jamesgeorge007/github-activity-readme) | `v0.5.0` | `4aefbfa1c222d70537dc6a02f0519266aab2b1ea` | `contents: write` | Daily repository and contributor activity sync in README |
| **Renovate Bot Action** | [`renovatebot/github-action`](https://github.com/renovatebot/github-action) | `v46.3.14` | `acdd6bda8b035c99ce59d5675816af2aa65a1774` | `contents: read` | Automated self-hosted dependency upgrade automation |
| **Lint Action** | [`wearerequired/lint-action`](https://github.com/wearerequired/lint-action) | `v3.0.2` | `124229c6e2974984ba137c67a499ba28bfc33e33` | `contents: read`, `checks: write` | Automated multi-linter check and auto-fixing |
| **Create GitHub App Token** | [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token) | `v3.3.0` | `64ab729a6294000f5aa4a4bc0b73d1f32bc45510` | `contents: read` | Generates short-lived installation tokens for bot automation |
| **Dependabot Auto-Merge** | [`fastify/github-action-merge-dependabot`](https://github.com/fastify/github-action-merge-dependabot) | `v3.15.0` | `73ec4cbb5e56df5591eae286972d5b2201ffe90f` | `contents: write`, `pull-requests: write` | Automated approval and merging for Dependabot PRs |
| **PR Lint Action** | [`seferov/pr-lint-action`](https://github.com/seferov/pr-lint-action) | `v2.0.0` | `cbef81c153f36262fbcd92fe97d6c6b8736d891d` | `contents: read`, `pull-requests: read` | Conventional Commits regex validation on pull request titles |
| **PR Label Checker** | [`Optimal-AI/PR-Label-Checker`](https://github.com/Optimal-AI/PR-Label-Checker) | `1.0.3` | `48d46fe6336aedcbb836ca580e86f195f9d14b01` | `contents: read`, `pull-requests: read` | Verifies required category labels on pull requests |
| **Manual Workflow Approval** | [`trstringer/manual-approval`](https://github.com/trstringer/manual-approval) | `v1.13.1` | `fa642940caf8412403569b28b2db4a1df08a83a3` | `issues: write` | Halts execution until approved by designated reviewers |
| **Step CI Action** | [`stepci/stepci`](https://github.com/stepci/stepci) | `2.8.2` | `570a42a52dcb9c7864031da79b047ffbaa268847` | `contents: read` | Automated API testing and performance verification |
| **Workflow Dispatch** | [`benc-uk/workflow-dispatch`](https://github.com/benc-uk/workflow-dispatch) | `v1.3.3` | `d004979be141727c7a17c28f603e2facc40d0855` | `actions: write`, `contents: read` | Dispatches secondary workflows programmatically |
| **Repo File Sync** | [`BetaHuhn/repo-file-sync-action`](https://github.com/BetaHuhn/repo-file-sync-action) | `v1.21.1` | `8b92be3375cf1d1b0cd579af488a9255572e4619` | `contents: write`, `pull-requests: write` | Synchronizes config/governance files across multiple repositories |
| **Trigger Workflow and Wait** | [`convictional/trigger-workflow-and-wait`](https://github.com/convictional/trigger-workflow-and-wait) | `v1.6.5` | `f69fa9eedd3c62a599220f4d5745230e237904be` | `actions: write`, `contents: read` | Triggers a workflow and blocks until completion status |
| **Workflow Conclusion** | [`technote-space/workflow-conclusion-action`](https://github.com/technote-space/workflow-conclusion-action) | `v3.0.3` | `45ce8e0eb155657ab8ccf346ade734257fd196a5` | `actions: read`, `contents: read` | Aggregates and determines conclusions of upstream jobs |
| **Actions Version Updater** | [`saadmk11/github-actions-version-updater`](https://github.com/saadmk11/github-actions-version-updater) | `v1.0.3` | `764bee6cd2905c6c91624f35332f1472fa736c23` | `contents: write`, `pull-requests: write` | Automated scanner updating action versions across workflows |
| **Runner Disk Cleaner** | [`rokibhasansagar/slimhub_actions`](https://github.com/rokibhasansagar/slimhub_actions) | `v25.42.5` | `5560c2d964bc240edfc5a0855b4b2c8261a29f29` | `contents: read` | Strips unnecessary runner software to maximize build disk headroom |
| **Workflow Dispatch & Wait** | [`the-actions-org/workflow-dispatch`](https://github.com/the-actions-org/workflow-dispatch) | `v4.0.0` | `3133c5d135c7dbe4be4f9793872b6ef331b53bc7` | `actions: write`, `contents: read` | Dispatches workflows with input payload and waits for conclusion |
| **Workflow Queue** | [`ahmadnassri/action-workflow-queue`](https://github.com/ahmadnassri/action-workflow-queue) | `v1.2.0` | `542658b3a8270cac81ae15d401b0d974732808ac` | `actions: read`, `contents: read` | Serializes and queues concurrent workflow executions |
| **Workflow Sync** | [`varunsridharan/action-github-workflow-sync`](https://github.com/varunsridharan/action-github-workflow-sync) | `3.5` | `3c60cce5ee8e615a7c68ac75fc14893dcac62d49` | `contents: write`, `pull-requests: write` | Synchronizes reusable workflows across ecosystem repositories |
| **Auto Cancel Redundant** | [`technote-space/auto-cancel-redundant-workflow`](https://github.com/technote-space/auto-cancel-redundant-workflow) | `v1.7.5` | `7d35aba30420fc2368f8aeed50371e99e7fa3239` | `actions: write`, `contents: read` | Automatically cancels redundant prior workflow runs |
| **Workflow Run Wait** | [`ahmadnassri/action-workflow-run-wait`](https://github.com/ahmadnassri/action-workflow-run-wait) | `v1.4.4` | `2aa3d9e1a12ecaaa9908e368eaf2123bb084323e` | `actions: read`, `contents: read` | Waits for concurrent or preceding workflow runs to complete |
| **GitFlow Lifecycle** | [`hoangvvo/gitflow-workflow-action`](https://github.com/hoangvvo/gitflow-workflow-action) | `0.3.8` | `a8dcd721fe5390b7f837873d5af2497980890a7e` | `contents: write`, `pull-requests: write` | Automates GitFlow branching, releases, and hotfix merges |
| **Setup GitHub Licensed** | [`github/setup-licensed`](https://github.com/github/setup-licensed) | `v1.3.1` | `be11bcbb82e3140b6cf260e647c3efeeca8fcefd` | `contents: read` | Installs and configures official licensed cache and tooling |
| **Workflow Immortality** | [`PhrozenByte/gh-workflow-immortality`](https://github.com/PhrozenByte/gh-workflow-immortality) | `v1` | `39378c27dcacbc17e6fbf83057d1fc40c574000d` | `contents: write` | Prevents automated scheduled workflow disabling from repository inactivity |
| **Actions Usage Audit** | [`fergusmacd/github-actions-usage`](https://github.com/fergusmacd/github-actions-usage) | `v0.9.2` | `86eef42173b5fe9778e33326468f51cc5a34348c` | `actions: read`, `contents: read` | Audits billable GitHub Actions runner minutes across the organization |
| **Workflow Status Indicator** | [`martialonline/workflow-status`](https://github.com/martialonline/workflow-status) | `v4.2` | `326830cacf79872efe767e15031f58d1ea0508c4` | `contents: read` | Generates dynamic status summaries and workflow badges |
| **Dispatch Workflow Method** | [`lasith-kg/dispatch-workflow`](https://github.com/lasith-kg/dispatch-workflow) | `v3.0.0` | `2597e9a3d222d7959052dea1c009560bbeb495e4` | `actions: write`, `contents: read` | Flexible repository_dispatch and workflow_dispatch cross-repo dispatcher |
| **Checkbox Workflow Action** | [`wadackel/checkbox-workflow-action`](https://github.com/wadackel/checkbox-workflow-action) | `v1.1.0` | `39a84e680429bb174302beed9f222e06972cecf9` | `issues: read`, `pull-requests: read` | Triggers CI steps upon checking checkboxes in PR bodies or comments |
| **Simple Comment PR** | [`NejcZdovc/comment-pr`](https://github.com/NejcZdovc/comment-pr) | `v2.1.0` | `a423635d183a8259308e80593c96fecf31539c26` | `pull-requests: write`, `contents: read` | Publishes formatted markdown updates directly to pull requests |
| **Wait for Workflow** | [`ArcticLampyrid/action-wait-for-workflow`](https://github.com/ArcticLampyrid/action-wait-for-workflow) | `v1.3.0` | `ff297b23789206858260877c4b83026d90c6db8c` | `actions: read`, `contents: read` | Polls and halts until target named workflow run reaches completion |
| **Git Flow Action** | [`kvendingoldo/git-flow-action`](https://github.com/kvendingoldo/git-flow-action) | `v2.16.0` | `ca756ba150c376eb9bf35e3ff3ed591913bb7f11` | `contents: write` | Automates GitFlow release branches, tags, and GitHub releases |
| **Gemini Actions** | [`dortort/gemini-actions`](https://github.com/dortort/gemini-actions) | `v0.1.0` | `c7ce09711c46a567055a16a762c0c99fdf181aeb` | `contents: read` | Meta-package and dispatcher for Google Gemini AI repository automation |
| **CI Dokumentor** | [`hoverkraft-tech/ci-dokumentor`](https://github.com/hoverkraft-tech/ci-dokumentor) | `0.6.1` | `93a10eb9c637d6b06ef394f12d60189b192b87c2` | `contents: read` | Automated generation of comprehensive CI/CD workflow documentation |
| **Code Review by Gemini AI** | [`rubensflinco/gemini-code-review-action`](https://github.com/rubensflinco/gemini-code-review-action) | `1.0.6` | `eff35325520e8afcd9ed86618920a4804925c05f` | `contents: read`, `pull-requests: write` | Automated pull request code reviews and diff chunk analysis via Gemini API |
| **Gemini Review Bot** | [`jgunnink/gemini-review-bot`](https://github.com/jgunnink/gemini-review-bot) | `v1.5.0` | `a1912666a1c394f0f7b51cb0910d02d54c1a93f7` | `contents: read`, `pull-requests: write` | Interactive PR code reviews, inline thread commentary, and diff analysis |
| **Git Auto Commit** | [`stefanzweifel/git-auto-commit-action`](https://github.com/stefanzweifel/git-auto-commit-action) | `v7.2.1` | `d0b01107b5db882071f96de5dd4b54961ea93f4c` | `contents: write` | Automatically commits and pushes changed files back to the repository |
| **Dependabot Auto Merge CLI** | [`ahmadnassri/action-dependabot-auto-merge`](https://github.com/ahmadnassri/action-dependabot-auto-merge) | `v2.6.6` | `45fc124d949b19b6b8bf6645b6c9d55f4f9ac61a` | `contents: write`, `pull-requests: write` | Automatically comments and approves Dependabot PRs based on target semver rules |
| **Autofix CI** | [`autofix-ci/action`](https://github.com/autofix-ci/action) | `v1.3.4` | `c5b2d67aa2274e7b5a18224e8171550871fc7e4a` | `contents: read` | Seamlessly fixes lint and formatting violations in pull requests |
| **Auto Request Review** | [`necojackarc/auto-request-review`](https://github.com/necojackarc/auto-request-review) | `v0.14.0` | `9a4b11888f2d60c79120c5413f13eb63febc2b68` | `pull-requests: write`, `contents: read` | Automatically requests reviews from designated owners or teams on PR creation |
| **Auto Assign Issues & PRs** | [`wow-actions/auto-assign`](https://github.com/wow-actions/auto-assign) | `v3.0.2` | `67fafa03df61d7e5f201734a2fa60d1ab111880d` | `issues: write`, `pull-requests: write`, `contents: read` | Automatically assigns reviewers and assignees to new issues and pull requests |
| **Auto Close Issues** | [`lucasbento/auto-close-issues`](https://github.com/lucasbento/auto-close-issues) | `v1.0.2` | `667e4f3cd71f2760a3869680944b8df55325b005` | `issues: write`, `contents: read` | Automatically closes inactive or answered issues according to timeline rules |
| **Auto Merge Pull Request** | [`reitermarkus/automerge`](https://github.com/reitermarkus/automerge) | `v2.8.0` | `634d0a4b51134c163eee182ac9aa79133eb33e8d` | `contents: write`, `pull-requests: write` | Automatically merges pull requests when labels, reviews, and status checks pass |
| **Auto Label Merge Conflicts** | [`mschilde/auto-label-merge-conflicts`](https://github.com/mschilde/auto-label-merge-conflicts) | `v2.0` | `3fdaf1c8b3f8e5b0f88753d9cb3c9c779370b3ef` | `pull-requests: write`, `contents: read` | Automatically identifies and labels pull requests containing merge conflicts |
| **Pipeline Healer** | [`JAI0705/DevOps_Pipeline_healer_agent`](https://github.com/JAI0705/DevOps_Pipeline_healer_agent) | `v1` | `a23105b6783cdd78c9a1417f1d20d66d5cb7598d` | `contents: read`, `pull-requests: write` | Automated AI agent diagnosing and healing broken CI pipelines |
| **The Auditor PR Reviewer** | [`Shawnchee/the-auditor`](https://github.com/Shawnchee/the-auditor) | `v1.0.0` | `fdc6bdd022bbe244c9134d14b8241f04e4537142` | `contents: read`, `pull-requests: write` | Comprehensive automated PR auditor powered by Google Gemini |
| **Auto Reviewer Assign** | [`johnmanjiro13/auto-reviewer-assign`](https://github.com/johnmanjiro13/auto-reviewer-assign) | `v0.2.0` | `cac72d552c3f3163adfb7bc4a3f676163911d0ef` | `pull-requests: write`, `contents: read` | Automatically assigns code reviewers to newly created pull requests |
| **GH Actions Docs** | [`3lvia/gh-actions-docs`](https://github.com/3lvia/gh-actions-docs) | `v1.2.5` | `2db29362f0d6d92052f6fa49b71743af5f0c11f8` | `contents: read` | Automatically documents GitHub Actions inputs, outputs, and usage |
| **Merge Dependency PRs** | [`desbo/merge-pr-action`](https://github.com/desbo/merge-pr-action) | `v0.3.2` | `1accf075c170137f89b939d6f5d7b2600d0dc344` | `contents: write`, `pull-requests: write` | Automated approval and merging of dependency update PRs |
| **Auto Merge Bot** | [`casassg/auto-merge-bot`](https://github.com/casassg/auto-merge-bot) | `v0.3.6` | `5d2a038b1b9ac48a0ac698519001d3e6cd299747` | `contents: write`, `pull-requests: write` | Automated merge bot for pull requests satisfying merge criteria |
| **Automatically Merge PRs** | [`BaharaJr/merge-pr`](https://github.com/BaharaJr/merge-pr) | `0.0.3` | `28444c475789780e15b5b4f5e67a5309a7f48d6a` | `contents: write`, `pull-requests: write` | Automatically merges pull requests upon passing CI tests |
| **PR Automation** | [`devjoes/pr-automation`](https://github.com/devjoes/pr-automation) | `v0.1.0` | `b9f61eef9e676ad2253aa4a08a2313468e7e57b7` | `contents: read`, `pull-requests: write` | Automated branch filtering, validation, and PR lifecycle handling |
| **Self Approve Action** | [`nicklegan/github-repo-self-approve-action`](https://github.com/nicklegan/github-repo-self-approve-action) | `v1.0.1` | `bea11671222460fbc41ad06797a0de470985f602` | `pull-requests: write`, `contents: read` | Automated self-approval gate for repository administrative workflows |
| **Autolabeler CODEOWNERS** | [`pratikmallya/autolabeler-codeowners`](https://github.com/pratikmallya/autolabeler-codeowners) | `0.1` | `cca9694441f25116fcb5d5f16757a6e43e5c4375` | `pull-requests: write`, `contents: read` | Automatically labels pull requests based on matching CODEOWNERS patterns |
| **Update PR Reminder** | [`Bhupesh-V/update-pr-reminder-action`](https://github.com/Bhupesh-V/update-pr-reminder-action) | `v1` | `9ccd3478ba932042624093b7153300ce63a68b66` | `pull-requests: write`, `contents: read` | Automated reminder notifications on stale or pending pull requests |
| **AI Code Guard** | [`salehhashemi1992/ai-code-guard`](https://github.com/salehhashemi1992/ai-code-guard) | `v1.1.0` | `769ff29bf912ecf13a432773cb8bbd076b850207` | `pull-requests: write`, `contents: read` | Automated AI security and code quality review guardrail |
| **Add Badges** | [`wow-actions/add-badges`](https://github.com/wow-actions/add-badges) | `v1.1.0` | `43f2c1eaecfb2596b89a8136a3fbda4f18d1d188` | `contents: write` | Automatically generates and inserts dynamic status badges into README |
| **Sync Branch Action** | [`LucasRuy/sync-branch-action`](https://github.com/LucasRuy/sync-branch-action) | `v1.2.0` | `2208081dfed383bf8e9c13ce862061a3e7a58239` | `contents: write` | Synchronizes and merges source branches into target destination branches |
| **Generate Documentation** | [`vargiuscuola/genshdoc`](https://github.com/vargiuscuola/genshdoc) | `v1.0` | `0f2a1895670c474de679631a33eae9369743af5f` | `contents: read` | Automated documentation generation for shell scripts using shdoc |
| **Safe Dependabot** | [`DiogoRibeiro7/safe-dependabot`](https://github.com/DiogoRibeiro7/safe-dependabot) | `v1.1.1` | `6108108e756497ce9c7b4e9e38d76fea453c1181` | `contents: read` | Validates Dependabot configuration against conservative dependency-update policies |
| **Dependabot Helper** | [`onebalaban/DependabotHelper`](https://github.com/onebalaban/DependabotHelper) | `v1` | `9455093e7f3d2338e9eeb42984865e29660e3ad8` | `contents: read` | Records execution time and greets automated dependency maintainers |
| **Dependabot Automerge** | [`invi5H/dependabot-automerge`](https://github.com/invi5H/dependabot-automerge) | `v1.0.0` | `aea0b2bd7e72af2f06118ce377821568046589f6` | `contents: write`, `pull-requests: write` | Automatically approves and merges Dependabot PRs based on update type |
| **Dependabot Workflow Action** | [`GavinMeierSonos/dependabot-action`](https://github.com/GavinMeierSonos/dependabot-action) | `v1.10-beta` | `a0789e7b36fd4cf0ba2906e77568ae5deae85f95` | `contents: write`, `pull-requests: write` | Runs containerized Dependabot version updates within custom runner workflows |
| **Dependabot Fetch Metadata** | [`dependabot/fetch-metadata`](https://github.com/dependabot/fetch-metadata) | `v3.1.0` | `25dd0e34f4fe68f24cc83900b1fe3fe149efef98` | `pull-requests: read` | Extracts structured metadata (semver, ecosystems, alerts) from Dependabot PRs |
| **Dependabot Issue for PRs** | [`goatandsheep/dependabot-issue-action`](https://github.com/goatandsheep/dependabot-issue-action) | `v1.0.1` | `085384c6fc7247bf455bcd86178c6fc8a5ffc1d5` | `issues: write`, `pull-requests: read` | Automatically creates triage and tracking issues for incoming Dependabot PRs |


---

## 3. Workflow Implementations & Usage

```mermaid
graph TD
    Trigger[PR / Issue / Push / Tag / Schedule / Dispatch] --> Runner[StepSecurity Harden-Runner]
    Runner --> Checkout[Actions Checkout @ SHA]
    Checkout --> ActionChoice{Trigger Type}
    ActionChoice -->|Push to main| WikiSync[Andrew-Chen-Wang/github-wiki-action]
    ActionChoice -->|PR Comment| CommentTrigger[Khan/pull-request-comment-trigger]
    ActionChoice -->|Doc Sync| Autodocs[dineshsonachalam/markdown-autodocs]
    ActionChoice -->|Branch Sync| BranchSync[connor-baer/action-sync-branch]
    ActionChoice -->|Deploy Event| DeployAction[chrnorm/deployment-action]
    ActionChoice -->|Scheduled Hygiene| MaintenancePR[devops-infra/action-commit-push + action-pull-request]
    ActionChoice -->|Release PR| GitPRRelease[bakunyo/git-pr-release-action]
    ActionChoice -->|Container Deploy| PRDeploy[hngprojects/pr-deploy]
    ActionChoice -->|Benchmark Run| Benchmark[benchmark-action/github-action-benchmark]
    ActionChoice -->|Tag Push v*| TagRelease[ghalactic/github-release-from-tag]
    ActionChoice -->|Daily Schedule| ActivityReadme[jamesgeorge007/github-activity-readme]
    ActionChoice -->|Nightly Dependency| RenovateBot[renovatebot/github-action]
    ActionChoice -->|Quality Lint| MultiLint[wearerequired/lint-action]
    ActionChoice -->|Bot Authentication| AppToken[actions/create-github-app-token]
    ActionChoice -->|Dependabot PR| DependabotMerge[fastify/github-action-merge-dependabot]
    ActionChoice -->|PR Title Lint| PRLint[seferov/pr-lint-action]
    ActionChoice -->|Label Verification| PRLabelChecker[Optimal-AI/PR-Label-Checker]
    ActionChoice -->|Manual Approval Gate| ApprovalGate[trstringer/manual-approval]
    ActionChoice -->|API Testing| StepCI[stepci/stepci]
    ActionChoice -->|Dispatch Workflow| DispatchAction[benc-uk/workflow-dispatch]
    ActionChoice -->|Repo File Sync| FileSync[BetaHuhn/repo-file-sync-action]
    ActionChoice -->|Trigger & Wait| TriggerWait[convictional/trigger-workflow-and-wait]
    ActionChoice -->|Job Conclusion| ConclusionAction[technote-space/workflow-conclusion-action]
    ActionChoice -->|Actions Updater| ActionsUpdater[saadmk11/github-actions-version-updater]
    ActionChoice -->|Disk Space Cleaning| SlimHub[rokibhasansagar/slimhub_actions]
    ActionChoice -->|Dispatch & Wait| DispatchWait[the-actions-org/workflow-dispatch]
    ActionChoice -->|Workflow Queue| QueueAction[ahmadnassri/action-workflow-queue]
    ActionChoice -->|Workflow Sync| WfSync[varunsridharan/action-github-workflow-sync]
    ActionChoice -->|Cancel Redundant| AutoCancel[technote-space/auto-cancel-redundant-workflow]
    ActionChoice -->|Wait for Run| RunWait[ahmadnassri/action-workflow-run-wait]
    ActionChoice -->|GitFlow Lifecycle| GitFlow[hoangvvo/gitflow-workflow-action]
    ActionChoice -->|License Audit| Licensed[github/setup-licensed]
    ActionChoice -->|Keepalive Immortality| Immortality[PhrozenByte/gh-workflow-immortality]
    ActionChoice -->|Usage Audit| UsageAudit[fergusmacd/github-actions-usage]
    ActionChoice -->|Status Indicator| StatusIndicator[martialonline/workflow-status]
    ActionChoice -->|Custom Dispatch| CustomDispatch[lasith-kg/dispatch-workflow]
    ActionChoice -->|Checkbox Gate| CheckboxGate[wadackel/checkbox-workflow-action]
    ActionChoice -->|Comment on PR| CommentPR[NejcZdovc/comment-pr]
    ActionChoice -->|Wait for Workflow| WaitForWf[ArcticLampyrid/action-wait-for-workflow]
    ActionChoice -->|Git Flow Runner| GitFlowRunner[kvendingoldo/git-flow-action]
    ActionChoice -->|Gemini Actions| GeminiActions[dortort/gemini-actions]
    ActionChoice -->|CI Dokumentor| CIDokumentor[hoverkraft-tech/ci-dokumentor]
    ActionChoice -->|Gemini AI Review| GeminiAICodeReview[rubensflinco/gemini-code-review-action]
    ActionChoice -->|Gemini Review Bot| GeminiReviewBot[jgunnink/gemini-review-bot]
    ActionChoice -->|Git Auto Commit| GitAutoCommit[stefanzweifel/git-auto-commit-action]
    ActionChoice -->|Dependabot Merge CLI| DepMergeCLI[ahmadnassri/action-dependabot-auto-merge]
    ActionChoice -->|Autofix CI| AutofixCI[autofix-ci/action]
    ActionChoice -->|Auto Request Review| AutoReqReview[necojackarc/auto-request-review]
    ActionChoice -->|Auto Assign| AutoAssign[wow-actions/auto-assign]
    ActionChoice -->|Auto Close Issues| AutoCloseIssues[lucasbento/auto-close-issues]
    ActionChoice -->|Automerge PR| AutomergePR[reitermarkus/automerge]
    ActionChoice -->|Label Conflicts| LabelConflicts[mschilde/auto-label-merge-conflicts]
    ActionChoice -->|Pipeline Healer| PipeHealer[JAI0705/DevOps_Pipeline_healer_agent]
    ActionChoice -->|PR Auditor| PRAuditor[Shawnchee/the-auditor]
    ActionChoice -->|Reviewer Assign| AutoRevAssign[johnmanjiro13/auto-reviewer-assign]
    ActionChoice -->|Actions Docs| GHActionsDocs[3lvia/gh-actions-docs]
    ActionChoice -->|Merge Dep PRs| MergeDepPRs[desbo/merge-pr-action]
    ActionChoice -->|Auto Merge Bot| AutoMergeBot[casassg/auto-merge-bot]
    ActionChoice -->|Merge PRs| MergePRs[BaharaJr/merge-pr]
    ActionChoice -->|PR Automation| PRAutomation[devjoes/pr-automation]
    ActionChoice -->|Self Approve| SelfApprove[nicklegan/github-repo-self-approve-action]
    ActionChoice -->|Codeowners Labels| CodeownersLabel[pratikmallya/autolabeler-codeowners]
    ActionChoice -->|PR Reminder| PRReminder[Bhupesh-V/update-pr-reminder-action]
    ActionChoice -->|AI Code Guard| AICodeGuard[salehhashemi1992/ai-code-guard]
    ActionChoice -->|Add Badges| AddBadges[wow-actions/add-badges]
    ActionChoice -->|Branch Sync Action| SyncBranchAct[LucasRuy/sync-branch-action]
    ActionChoice -->|Gen Shdoc| GenShdoc[vargiuscuola/genshdoc]
    ActionChoice -->|Safe Dependabot| SafeDep[DiogoRibeiro7/safe-dependabot]
    ActionChoice -->|Dependabot Helper| DepHelper[onebalaban/DependabotHelper]
    ActionChoice -->|Dep Automerge| DepAutomerge[invi5H/dependabot-automerge]
    ActionChoice -->|Dependabot Workflow| DepWorkflow[GavinMeierSonos/dependabot-action]
    ActionChoice -->|Fetch Metadata| FetchMetadata[dependabot/fetch-metadata]
    ActionChoice -->|Dependabot Issue| DepIssue[goatandsheep/dependabot-issue-action]
```

### 3.1 Wiki Sync Workflow ([`.github/workflows/wiki-sync.yml`](../.github/workflows/wiki-sync.yml))
Synchronizes documentation from `docs/` to GitHub Wiki on push to `main`:

```yaml
- name: Deploy Documentation to Wiki
  uses: Andrew-Chen-Wang/github-wiki-action@1bbb4280446f9630e8e21a18012cbacf3b0f992e # v5
  with:
    path: docs
    strategy: clone
```

### 3.2 PR Comment Trigger Workflow ([`.github/workflows/pr-comment-trigger.yml`](../.github/workflows/pr-comment-trigger.yml))
Detects slash commands (e.g., `@deploy`, `/benchmark`, `/preview`, `/test`) on pull requests:

```yaml
- name: Check for deploy trigger
  uses: Khan/pull-request-comment-trigger@edab8d9ba7759221187ef7120592a6fbfada0d18 # v1.1.0
  id: check-deploy
  with:
    trigger: '@deploy'
    reaction: rocket
  env:
    GITHUB_TOKEN: ${{ github.token }}
```

### 3.3 Markdown Autodocs Workflow ([`.github/workflows/autodocs.yml`](../.github/workflows/autodocs.yml))
Updates documentation tables and code blocks automatically:

```yaml
- name: Markdown Autodocs
  uses: dineshsonachalam/markdown-autodocs@6596b4a049f087c7abe84cc7457e2c53652df810 # v1.0.7
  with:
    output_file_paths: '["README.md"]'
```

### 3.4 Reusable Deployment Workflow ([`.github/workflows/reusable-deployment.yml`](../.github/workflows/reusable-deployment.yml))
Creates GitHub environment deployments and connects status tracking:

```yaml
- name: Create Deployment Record
  uses: chrnorm/deployment-action@55729fcebec3d284f60f5bcabbd8376437d696b1 # v2.0.7
  id: deployment
  with:
    token: ${{ github.token }}
    environment: ${{ inputs.environment }}
    environment-url: ${{ inputs.environment_url }}
```

### 3.5 Branch Sync Workflow ([`.github/workflows/branch-sync.yml`](../.github/workflows/branch-sync.yml))
Synchronizes branches across staging or downstream environments:

```yaml
- name: Synchronize Branch
  uses: connor-baer/action-sync-branch@f5d20b6a6944c70909c187b558313dfc1d8daa48 # v2
  with:
    branch: ${{ inputs.target_branch }}
    token: ${{ github.token }}
    force: false
```

### 3.6 Automated Maintenance PR Workflow ([`.github/workflows/automated-pr-maintenance.yml`](../.github/workflows/automated-pr-maintenance.yml))
Performs automated hygiene commits and opens structured Pull Requests:

```yaml
- name: Commit and push changes
  uses: devops-infra/action-commit-push@be5ba37125c79eb0016cbd8cc385f0aa160538c5 # v0.9.2
  with:
    github_token: ${{ github.token }}
    commit_prefix: "[automation]"
    commit_message: ${{ inputs.commit_message }}
    target_branch: ${{ inputs.branch_name }}

- name: Open Pull Request
  uses: devops-infra/action-pull-request@e66e2ba93519dc63b9884a26e620e2fd0cffab2c # v0.5.5
  with:
    github_token: ${{ github.token }}
    source_branch: ${{ inputs.branch_name }}
    target_branch: main
    title: ${{ inputs.pr_title }}
    template: .github/PULL_REQUEST_TEMPLATE.md
    label: automation,maintenance
```

### 3.7 Git PR Release Workflow ([`.github/workflows/git-pr-release.yml`](../.github/workflows/git-pr-release.yml))
Aggregates merged pull requests into a release candidate pull request:

```yaml
- name: Generate Release Pull Request
  uses: bakunyo/git-pr-release-action@035b7151a53745c03b85c6274ab1ae4bc734eccd # v1.4
  env:
    GITHUB_TOKEN: ${{ github.token }}
    GIT_PR_RELEASE_BRANCH_PRODUCTION: ${{ inputs.base_branch }}
    GIT_PR_RELEASE_BRANCH_STAGING: ${{ inputs.head_branch }}
```

### 3.8 Reusable PR Deploy Workflow ([`.github/workflows/reusable-pr-deploy.yml`](../.github/workflows/reusable-pr-deploy.yml))
Spins up containerized PR preview environments on remote Docker hosts:

```yaml
- name: Deploy Pull Request Container
  uses: hngprojects/pr-deploy@2f8b3e0dce07f0c6f7e6e80018dc52081a61b63b # V2.0.1
  with:
    context: ${{ inputs.docker_context }}
    server_port: ${{ inputs.server_port }}
  env:
    SERVER_HOST: ${{ secrets.SERVER_HOST }}
    SERVER_USERNAME: ${{ secrets.SERVER_USERNAME }}
    SERVER_PASSWORD: ${{ secrets.SERVER_PASSWORD }}
```

### 3.9 Continuous Benchmark Workflow ([`.github/workflows/continuous-benchmark.yml`](../.github/workflows/continuous-benchmark.yml))
Monitors execution performance and tracks metrics across commits:

```yaml
- name: Store and track benchmark results
  uses: benchmark-action/github-action-benchmark@4322e5726e6334590d251fc4f92bec0efafc45dc # v1.22.2
  with:
    name: SakThai Core Benchmarks
    tool: 'pytest'
    output-file-path: output.json
    github-token: ${{ github.token }}
    auto-push: false
    comment-on-alert: true
    fail-on-alert: false
```

### 3.10 Release from Tag Workflow ([`.github/workflows/release-from-tag.yml`](../.github/workflows/release-from-tag.yml))
Creates GitHub Releases automatically upon pushing SemVer `v*` tags:

```yaml
- name: Create GitHub Release
  uses: ghalactic/github-release-from-tag@30770b91acccc8e1e2f14562d813cb30af08f1c6 # v6
  with:
    generateReleaseNotes: true
  env:
    GITHUB_TOKEN: ${{ github.token }}
```

### 3.11 Activity in Readme Workflow ([`.github/workflows/activity-readme.yml`](../.github/workflows/activity-readme.yml))
Periodically synchronizes recent public repository activity into the README:

```yaml
- name: Update Activity Section
  uses: jamesgeorge007/github-activity-readme@4aefbfa1c222d70537dc6a02f0519266aab2b1ea # v0.5.0
  env:
    GITHUB_TOKEN: ${{ github.token }}
  with:
    COMMIT_MSG: "chore(docs): update recent activity section [skip ci]"
    MAX_LINES: 5
```

### 3.12 Renovate Bot Workflow ([`.github/workflows/renovate.yml`](../.github/workflows/renovate.yml))
Self-hosted Renovate runner checking dependencies with dry-run support:

```yaml
- name: Run Renovate
  uses: renovatebot/github-action@acdd6bda8b035c99ce59d5675816af2aa65a1774 # v46.3.14
  with:
    configurationFile: .github/renovate.json5
    token: ${{ secrets.RENOVATE_TOKEN || github.token }}
  env:
    LOG_LEVEL: info
    RENOVATE_DRY_RUN: ${{ inputs.dry_run || 'full' }}
```

### 3.13 Multi-Linter Action Workflow ([`.github/workflows/lint-check.yml`](../.github/workflows/lint-check.yml))
Runs linters and formatters with automatic annotations and optional fixes:

```yaml
- name: Run Lint Action
  uses: wearerequired/lint-action@124229c6e2974984ba137c67a499ba28bfc33e33 # v3.0.2
  with:
    github_token: ${{ github.token }}
    ruff: true
    auto_fix: ${{ inputs.auto_fix || false }}
```

### 3.14 Reusable GitHub App Token Generator ([`.github/workflows/reusable-app-token.yml`](../.github/workflows/reusable-app-token.yml))
Exchanges app credentials for short-lived bot installation access tokens:

```yaml
- name: Generate GitHub App Token
  uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510 # v3.3.0
  id: app-token
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.PRIVATE_KEY }}
    owner: ${{ inputs.owner || github.repository_owner }}
```

### 3.15 Dependabot Auto-Merge Workflow ([`.github/workflows/dependabot-auto-merge.yml`](../.github/workflows/dependabot-auto-merge.yml))
Automatically evaluates, approves, and merges eligible Dependabot pull requests based on SemVer policies and un-spoofable actor verification:

```yaml
- name: Auto-Merge Dependabot PR
  uses: fastify/github-action-merge-dependabot@73ec4cbb5e56df5591eae286972d5b2201ffe90f # v3.15.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    target: ${{ inputs.target || 'any' }}
    pr-number: ${{ inputs.pr_number || '' }}
    merge-method: squash
```

### 3.16 PR Lint Action Workflow ([`.github/workflows/pr-lint.yml`](../.github/workflows/pr-lint.yml))
Enforces Conventional Commits title structure on incoming pull requests:

```yaml
- name: Verify PR Title Conventional Commits
  uses: seferov/pr-lint-action@cbef81c153f36262fbcd92fe97d6c6b8736d891d # v2.0.0
  with:
    title-regex: '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|init)(\([a-zA-Z0-9_\-\/]+\))?: .+'
    error-message: 'PR title must follow Conventional Commits format (e.g., "feat: add feature", "fix(core): fix issue").'
```

### 3.17 PR Label Checker Workflow ([`.github/workflows/pr-label-checker.yml`](../.github/workflows/pr-label-checker.yml))
Automated workflow checking for mandatory classification labels on pull requests:

```yaml
- name: Check PR Labels
  uses: Optimal-AI/PR-Label-Checker@48d46fe6336aedcbb836ca580e86f195f9d14b01 # 1.0.3
```

### 3.18 Manual Workflow Approval Gate ([`.github/workflows/reusable-manual-approval-gate.yml`](../.github/workflows/reusable-manual-approval-gate.yml))
Enforces human-in-the-loop verification on critical pipelines:

```yaml
- name: Wait for manual approval
  uses: trstringer/manual-approval@fa642940caf8412403569b28b2db4a1df08a83a3 # v1.13.1
  with:
    secret: ${{ secrets.GITHUB_TOKEN }}
    approvers: ${{ inputs.approvers }}
    minimum-approvals: 1
```

### 3.19 Step CI API Testing ([`.github/workflows/step-ci.yml`](../.github/workflows/step-ci.yml))
Performs declarative HTTP/REST integration testing with Step CI:

```yaml
- name: Run Step CI
  uses: stepci/stepci@570a42a52dcb9c7864031da79b047ffbaa268847 # 2.8.2
  with:
    workflow: .stepci/smoke-test.yml
```

### 3.20 Reusable Workflow Dispatch ([`.github/workflows/reusable-workflow-dispatch.yml`](../.github/workflows/reusable-workflow-dispatch.yml))
Dispatches dependent downstream workflows programmatically:

```yaml
- name: Dispatch target workflow
  uses: benc-uk/workflow-dispatch@d004979be141727c7a17c28f603e2facc40d0855 # v1.3.3
  with:
    workflow: ${{ inputs.target_workflow }}
    token: ${{ github.token }}
```

### 3.21 Repo File Sync Workflow ([`.github/workflows/repo-file-sync.yml`](../.github/workflows/repo-file-sync.yml))
Synchronizes configuration and governance templates across repositories:

```yaml
- name: Run Repo File Sync
  uses: BetaHuhn/repo-file-sync-action@8b92be3375cf1d1b0cd579af488a9255572e4619 # v1.21.1
  with:
    GH_PAT: ${{ github.token }}
```

### 3.22 Reusable Trigger Workflow and Wait ([`.github/workflows/reusable-trigger-workflow-wait.yml`](../.github/workflows/reusable-trigger-workflow-wait.yml))
Triggers workflows and polls for final status conclusion:

```yaml
- name: Trigger remote workflow
  uses: convictional/trigger-workflow-and-wait@f69fa9eedd3c62a599220f4d5745230e237904be # v1.6.5
  with:
    owner: beer-sakthai
    repo: Sak-Family-Agent
    github_token: ${{ github.token }}
    workflow_file_name: ${{ inputs.workflow_file }}
```

### 3.23 Workflow Conclusion Evaluator ([`.github/workflows/workflow-conclusion.yml`](../.github/workflows/workflow-conclusion.yml))
Aggregates predecessor status outcomes across multiple asynchronous matrix jobs:

```yaml
- name: Evaluate conclusions
  uses: technote-space/workflow-conclusion-action@45ce8e0eb155657ab8ccf346ade734257fd196a5 # v3.0.3
```

### 3.24 Actions Version Updater ([`.github/workflows/actions-version-updater.yml`](../.github/workflows/actions-version-updater.yml))
Automated periodic scanner to discover and propose action updates:

```yaml
- name: Run GitHub Actions Version Updater
  uses: saadmk11/github-actions-version-updater@764bee6cd2905c6c91624f35332f1472fa736c23 # v1.0.3
  with:
    token: ${{ github.token }}
```

### 3.25 Runner Disk Space Cleaner ([`.github/workflows/runner-disk-cleaner.yml`](../.github/workflows/runner-disk-cleaner.yml))
Reclaims ephemeral disk space before executing large ML, model, or container builds:

```yaml
- name: Clean runner environment
  uses: rokibhasansagar/slimhub_actions@5560c2d964bc240edfc5a0855b4b2c8261a29f29 # v25.42.5
```

### 3.26 Reusable Workflow Dispatch & Wait ([`.github/workflows/reusable-workflow-dispatch-wait.yml`](../.github/workflows/reusable-workflow-dispatch-wait.yml))
Triggers a workflow dispatch event and waits for conclusion:

```yaml
- name: Trigger and wait
  uses: the-actions-org/workflow-dispatch@3133c5d135c7dbe4be4f9793872b6ef331b53bc7 # v4.0.0
  with:
    workflow: ${{ inputs.target_workflow }}
    token: ${{ github.token }}
```

### 3.27 Workflow Queue Serializer ([`.github/workflows/workflow-queue.yml`](../.github/workflows/workflow-queue.yml))
Guarantees strictly serialized execution across concurrent workflow dispatch events:

```yaml
- name: Queue Execution
  uses: ahmadnassri/action-workflow-queue@542658b3a8270cac81ae15d401b0d974732808ac # v1.2.0
  with:
    queue-name: global-deploy-queue
    timeout: 600
```

### 3.28 GitHub Workflow Sync ([`.github/workflows/github-workflow-sync.yml`](../.github/workflows/github-workflow-sync.yml))
Synchronizes GitHub Actions workflow files across repositories:

```yaml
- name: Sync workflows
  uses: varunsridharan/action-github-workflow-sync@3c60cce5ee8e615a7c68ac75fc14893dcac62d49 # 3.5
  with:
    GITHUB_TOKEN: ${{ github.token }}
    REPOSITORIES: beer-sakthai/Sak-Family-Agent
    WORKFLOW_FILES: lint-check.yml
```

### 3.29 Auto Cancel Redundant Workflows ([`.github/workflows/auto-cancel-redundant.yml`](../.github/workflows/auto-cancel-redundant.yml))
Automatically cancels outdated in-flight runs when newer commits arrive:

```yaml
- name: Cancel redundant workflow runs
  uses: technote-space/auto-cancel-redundant-workflow@7d35aba30420fc2368f8aeed50371e99e7fa3239 # v1.7.5
  with:
    GITHUB_TOKEN: ${{ github.token }}
```

### 3.30 Workflow Run Wait ([`.github/workflows/workflow-run-wait.yml`](../.github/workflows/workflow-run-wait.yml))
Waits for previous in-flight workflow runs to complete:

```yaml
- name: Wait for in-flight runs
  uses: ahmadnassri/action-workflow-run-wait@2aa3d9e1a12ecaaa9908e368eaf2123bb084323e # v1.4.4
  with:
    delay: 10
    timeout: 600
```

### 3.31 GitFlow Lifecycle Automation ([`.github/workflows/gitflow-lifecycle.yml`](../.github/workflows/gitflow-lifecycle.yml))
Automates GitFlow branching, release tags, and hotfix merges:

```yaml
- name: Run GitFlow Workflow Action
  uses: hoangvvo/gitflow-workflow-action@a8dcd721fe5390b7f837873d5af2497980890a7e # 0.3.8
  with:
    develop_branch: main
    main_branch: main
```

### 3.32 Setup GitHub Licensed ([`.github/workflows/licensed-audit.yml`](../.github/workflows/licensed-audit.yml))
Installs and configures official GitHub Licensed dependency audit tools:

```yaml
- name: Setup GitHub Licensed
  uses: github/setup-licensed@be11bcbb82e3140b6cf260e647c3efeeca8fcefd # v1.3.1
  with:
    version: '4.4.1'
```

### 3.33 Workflow Immortality Keepalive ([`.github/workflows/workflow-immortality.yml`](../.github/workflows/workflow-immortality.yml))
Prevents scheduled GitHub Actions from being disabled due to 60 days of inactivity:

```yaml
- name: Keep Workflows Active
  uses: PhrozenByte/gh-workflow-immortality@39378c27dcacbc17e6fbf83057d1fc40c574000d # v1
  with:
    secret: ${{ github.token }}
```

### 3.34 Actions Usage Audit ([`.github/workflows/actions-usage-audit.yml`](../.github/workflows/actions-usage-audit.yml))
Audits billable GitHub Actions runner minutes across the organization:

```yaml
- name: Audit Workflow Usage
  uses: fergusmacd/github-actions-usage@86eef42173b5fe9778e33326468f51cc5a34348c # v0.9.2
  with:
    organisation: beer-sakthai
    gitHubAPIKey: ${{ github.token }}
```

### 3.35 Workflow Status Indicator ([`.github/workflows/workflow-status-indicator.yml`](../.github/workflows/workflow-status-indicator.yml))
Generates dynamic status summaries and workflow conclusion indicators:

```yaml
- name: Output Status Indicator
  uses: martialonline/workflow-status@326830cacf79872efe767e15031f58d1ea0508c4 # v4.2
```

### 3.36 Reusable Dispatch Method ([`.github/workflows/reusable-dispatch-method.yml`](../.github/workflows/reusable-dispatch-method.yml))
Dispatches cross-repository workflows using configurable dispatch methods:

```yaml
- name: Trigger Dispatch
  uses: lasith-kg/dispatch-workflow@2597e9a3d222d7959052dea1c009560bbeb495e4 # v3.0.0
  with:
    dispatch-method: workflow_dispatch
    owner: beer-sakthai
    repo: ${{ inputs.target_repo }}
    token: ${{ github.token }}
    workflow: lint-check.yml
```

### 3.37 Checkbox Workflow Trigger ([`.github/workflows/checkbox-trigger.yml`](../.github/workflows/checkbox-trigger.yml))
Triggers steps based on checkbox states in issues or pull requests:

```yaml
- name: Checkbox Action
  uses: wadackel/checkbox-workflow-action@39a84e680429bb174302beed9f222e06972cecf9 # v1.1.0
  with:
    id: test-checkbox
    number: 1
```

### 3.38 Reusable Comment PR Helper ([`.github/workflows/reusable-comment-pr.yml`](../.github/workflows/reusable-comment-pr.yml))
Publishes formatted markdown updates directly to pull requests:

```yaml
- name: Comment on PR
  uses: NejcZdovc/comment-pr@a423635d183a8259308e80593c96fecf31539c26 # v2.1.0
  with:
    file: ''
    message: ${{ inputs.comment_body }}
```

### 3.39 Wait for Workflow ([`.github/workflows/wait-for-workflow.yml`](../.github/workflows/wait-for-workflow.yml))
Polls and halts until the target named workflow completes:

```yaml
- name: Wait for target workflow
  uses: ArcticLampyrid/action-wait-for-workflow@ff297b23789206858260877c4b83026d90c6db8c # v1.3.0
  with:
    workflow: lint-check.yml
    token: ${{ github.token }}
```

### 3.40 Git Flow Action ([`.github/workflows/git-flow-action.yml`](../.github/workflows/git-flow-action.yml))
Executes GitFlow release branching and tagging operations:

```yaml
- name: Run Git Flow Action
  uses: kvendingoldo/git-flow-action@ca756ba150c376eb9bf35e3ff3ed591913bb7f11 # v2.16.0
  with:
    enable_git_push: ${{ inputs.enable_git_push || 'false' }}
    log_level: ${{ inputs.log_level || 'INFO' }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.41 Gemini Actions Dispatcher ([`.github/workflows/gemini-actions.yml`](../.github/workflows/gemini-actions.yml))
Meta-package and dispatcher for repository tasks automated by Google Gemini AI:

```yaml
- name: Execute Gemini Actions Dispatcher
  uses: dortort/gemini-actions@c7ce09711c46a567055a16a762c0c99fdf181aeb # v0.1.0
  with:
    action: ${{ inputs.action_mode || 'info' }}
```

### 3.42 CI Dokumentor Workflow ([`.github/workflows/ci-dokumentor.yml`](../.github/workflows/ci-dokumentor.yml))
Generates comprehensive documentation for CI/CD workflow manifests:

```yaml
- name: Document CI Workflows
  uses: hoverkraft-tech/ci-dokumentor@93a10eb9c637d6b06ef394f12d60189b192b87c2 # 0.6.1
  with:
    source: ${{ inputs.source_workflow || '.github/workflows/ci.yml' }}
    dry-run: ${{ inputs.dry_run || 'true' }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.43 Code Review by Gemini AI ([`.github/workflows/gemini-code-review-action.yml`](../.github/workflows/gemini-code-review-action.yml))
Reviews pull requests and provides automated diff chunk analysis using the Gemini API:

```yaml
- name: Run Gemini AI Code Review
  if: steps.check_secret.outputs.has_key == 'true'
  uses: rubensflinco/gemini-code-review-action@eff35325520e8afcd9ed86618920a4804925c05f # 1.0.6
  with:
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    github_repository: ${{ github.repository }}
    github_pull_request_number: ${{ inputs.pull_request_number || '1' }}
    git_commit_hash: ${{ github.sha }}
    model: "gemini-3.8-flash"
    pull_request_diff: "dry-run-diff"
```

### 3.44 Gemini Review Bot ([`.github/workflows/gemini-review-bot.yml`](../.github/workflows/gemini-review-bot.yml))
Provides interactive PR code reviews, inline thread commentary, and diff analysis:

```yaml
- name: Execute Gemini Review Bot
  if: steps.check_secret.outputs.has_key == 'true'
  uses: jgunnink/gemini-review-bot@a1912666a1c394f0f7b51cb0910d02d54c1a93f7 # v1.5.0
  with:
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    instructions: ${{ inputs.instructions || '' }}
```

### 3.45 Git Auto Commit ([`.github/workflows/git-auto-commit.yml`](../.github/workflows/git-auto-commit.yml))
Automatically commits changed files during workflow execution back to the repository:

```yaml
- name: Auto-commit changed files
  uses: stefanzweifel/git-auto-commit-action@d0b01107b5db882071f96de5dd4b54961ea93f4c # v7.2.1
  with:
    commit_message: "${{ inputs.commit_message || 'chore: automated file update' }}"
    file_pattern: ${{ inputs.file_pattern || '.' }}
```

### 3.46 Dependabot Auto Merge CLI ([`.github/workflows/dependabot-auto-merge-cli.yml`](../.github/workflows/dependabot-auto-merge-cli.yml))
Automates approval and merge commands for Dependabot pull requests based on target semantic versioning:

```yaml
- name: Run Dependabot Auto Merge CLI
  uses: ahmadnassri/action-dependabot-auto-merge@45fc124d949b19b6b8bf6645b6c9d55f4f9ac61a # v2.6.6
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    command: ${{ inputs.command || 'squash and merge' }}
    target: ${{ inputs.target || 'patch' }}
```

### 3.47 Autofix CI ([`.github/workflows/autofix.yml`](../.github/workflows/autofix.yml))
Automatically applies fixes for lint and formatting violations in pull requests:

```yaml
- name: Run autofix.ci
  uses: autofix-ci/action@c5b2d67aa2274e7b5a18224e8171550871fc7e4a # v1.3.4
  with:
    fail-fast: false
```

### 3.48 Auto Request Review ([`.github/workflows/auto-request-review.yml`](../.github/workflows/auto-request-review.yml))
Automatically requests reviews from designated reviewers and teams upon pull request creation:

```yaml
- name: Auto-request review
  uses: necojackarc/auto-request-review@9a4b11888f2d60c79120c5413f13eb63febc2b68 # v0.14.0
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.49 Auto Assign Issues & PRs ([`.github/workflows/auto-assign.yml`](../.github/workflows/auto-assign.yml))
Automatically assigns reviewers and assignees to new issues and pull requests:

```yaml
- name: Auto Assign Reviewers and Assignees
  uses: wow-actions/auto-assign@67fafa03df61d7e5f201734a2fa60d1ab111880d # v3.0.2
  with:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    addReviewers: true
    addAssignees: true
```

### 3.50 Auto Close Issues ([`.github/workflows/auto-close-issues.yml`](../.github/workflows/auto-close-issues.yml))
Automatically identifies and closes stale or inactive issues according to repository timeline criteria:

```yaml
- name: Auto-close inactive issues
  uses: lucasbento/auto-close-issues@667e4f3cd71f2760a3869680944b8df55325b005 # v1.0.2
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.51 Auto Merge Pull Request ([`.github/workflows/automerge-pr.yml`](../.github/workflows/automerge-pr.yml))
Automatically merges approved pull requests when required labels, reviews, and status checks pass:

```yaml
- name: Auto-merge pull request
  uses: reitermarkus/automerge@634d0a4b51134c163eee182ac9aa79133eb33e8d # v2.8.0
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    dry-run: true
```

### 3.52 Auto Label Merge Conflicts ([`.github/workflows/auto-label-merge-conflicts.yml`](../.github/workflows/auto-label-merge-conflicts.yml))
Scans pull requests and automatically applies conflict labels when head branches diverge:

```yaml
- name: Auto-label merge conflicts
  uses: mschilde/auto-label-merge-conflicts@3fdaf1c8b3f8e5b0f88753d9cb3c9c779370b3ef # master (node:22-alpine)
  with:
    CONFLICT_LABEL_NAME: "has-conflicts"
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3.53 Pipeline Healer ([`.github/workflows/pipeline-healer.yml`](../.github/workflows/pipeline-healer.yml))
AI-powered agent to diagnose and suggest remediation steps for failed pipeline steps:

```yaml
- name: Run Pipeline Healer
  uses: JAI0705/DevOps_Pipeline_healer_agent@a23105b6783cdd78c9a1417f1d20d66d5cb7598d # v1
  with:
    groq-api-key: ${{ secrets.GROQ_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.54 The Auditor PR Reviewer ([`.github/workflows/the-auditor.yml`](../.github/workflows/the-auditor.yml))
Gemini-powered automated pull request reviewer and code quality auditor:

```yaml
- name: Run The Auditor
  uses: Shawnchee/the-auditor@fdc6bdd022bbe244c9134d14b8241f04e4537142 # v1.0.0
  with:
    gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.55 Auto Reviewer Assign ([`.github/workflows/auto-reviewer-assign.yml`](../.github/workflows/auto-reviewer-assign.yml))
Automatically assigns reviewers to pull requests based on configurable rules:

```yaml
- name: Auto Assign Reviewers
  uses: johnmanjiro13/auto-reviewer-assign@cac72d552c3f3163adfb7bc4a3f676163911d0ef # v0.2.0
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.56 GH Actions Docs ([`.github/workflows/gh-actions-docs.yml`](../.github/workflows/gh-actions-docs.yml))
Generates documentation tables for composite actions and workflow interfaces:

```yaml
- name: Run gh-actions-docs
  uses: 3lvia/gh-actions-docs@2db29362f0d6d92052f6fa49b71743af5f0c11f8 # v1.2.5
```

### 3.57 Merge Dependency Update PRs ([`.github/workflows/merge-pr-action.yml`](../.github/workflows/merge-pr-action.yml))
Automatically reviews and merges automated dependency update pull requests:

```yaml
- name: Merge Dependency Update PRs
  uses: desbo/merge-pr-action@1accf075c170137f89b939d6f5d7b2600d0dc344 # v0.3.2
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.58 Auto Merge Bot ([`.github/workflows/auto-merge-bot.yml`](../.github/workflows/auto-merge-bot.yml))
Merges pull requests matching target prefixes or labels when checks succeed:

```yaml
- name: Run Auto Merge Bot
  uses: casassg/auto-merge-bot@5d2a038b1b9ac48a0ac698519001d3e6cd299747 # v0.3.6
  with:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    TAG: "automerge"
```

### 3.59 Automatically Merge Pull Requests ([`.github/workflows/merge-pr.yml`](../.github/workflows/merge-pr.yml))
Merges pull requests on demand or schedule based on target branch and merge method:

```yaml
- name: Auto Merge PR
  uses: BaharaJr/merge-pr@28444c475789780e15b5b4f5e67a5309a7f48d6a # 0.0.3
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    method: "squash"
```

### 3.60 PR Automation ([`.github/workflows/pr-automation.yml`](../.github/workflows/pr-automation.yml))
Automates pull request management and validation with branch blacklisting:

```yaml
- name: Run PR Automation
  uses: devjoes/pr-automation@b9f61eef9e676ad2253aa4a08a2313468e7e57b7 # v0.1.0
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    branchBlackList: "main"
```

### 3.61 GitHub Repository Self Approve Action ([`.github/workflows/self-approve.yml`](../.github/workflows/self-approve.yml))
Self-approves internal automation pull requests via GitHub App installation authentication:

```yaml
- name: Self Approve PR
  uses: nicklegan/github-repo-self-approve-action@bea11671222460fbc41ad06797a0de470985f602 # v1.0.1
  with:
    appid: ${{ secrets.APP_ID }}
    privatekey: ${{ secrets.APP_PRIVATE_KEY }}
    installationid: ${{ secrets.APP_INSTALLATION_ID }}
```

### 3.62 Autolabeler CODEOWNERS ([`.github/workflows/autolabeler-codeowners.yml`](../.github/workflows/autolabeler-codeowners.yml))
Labels pull requests based on path ownership mappings defined in `CODEOWNERS`:

```yaml
- name: Run Autolabeler CODEOWNERS
  uses: pratikmallya/autolabeler-codeowners@cca9694441f25116fcb5d5f16757a6e43e5c4375 # 0.1
  with:
    githubToken: ${{ secrets.GITHUB_TOKEN }}
```

### 3.63 Update PR Reminder ([`.github/workflows/update-pr-reminder.yml`](../.github/workflows/update-pr-reminder.yml))
Reminds contributors to keep PR descriptions up to date when new commits are pushed:

```yaml
- name: Run Update PR Reminder
  uses: Bhupesh-V/update-pr-reminder-action@9ccd3478ba932042624093b7153300ce63a68b66 # v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.64 AI Code Guard ([`.github/workflows/ai-code-guard.yml`](../.github/workflows/ai-code-guard.yml))
Automated AI-assisted code review guardrail for pull requests:

```yaml
- name: Run AI Code Guard
  uses: salehhashemi1992/ai-code-guard@769ff29bf912ecf13a432773cb8bbd076b850207 # v1.1.0
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.65 Add Badges ([`.github/workflows/add-badges.yml`](../.github/workflows/add-badges.yml))
Appends CI status and coverage badges to markdown files or README documentation:

```yaml
- name: Add Badges
  uses: wow-actions/add-badges@43f2c1eaecfb2596b89a8136a3fbda4f18d1d188 # v1.1.0
  with:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3.66 Sync Branch Action ([`.github/workflows/sync-branch-action.yml`](../.github/workflows/sync-branch-action.yml))
Keeps downstream staging or feature branches synchronized with base branches:

```yaml
- name: Sync Branch Action
  uses: LucasRuy/sync-branch-action@2208081dfed383bf8e9c13ce862061a3e7a58239 # v1.2.0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SOURCE_BRANCH: "main"
    DESTINATION_BRANCH: "staging"
```

### 3.67 Generate Documentation ([`.github/workflows/genshdoc.yml`](../.github/workflows/genshdoc.yml))
Generates documentation from annotated shell scripts using `genshdoc`:

```yaml
- name: Run genshdoc
  uses: vargiuscuola/genshdoc@0f2a1895670c474de679631a33eae9369743af5f # v1.0
  with:
    source: "scripts"
```

### 3.68 Safe Dependabot Policy ([`.github/workflows/safe-dependabot.yml`](../.github/workflows/safe-dependabot.yml))
Validates `.github/dependabot.yml` against conservative update policies and ecosystem directory coverage:

```yaml
- name: Run Safe Dependabot Policy Check
  uses: DiogoRibeiro7/safe-dependabot@6108108e756497ce9c7b4e9e38d76fea453c1181 # v1.1.1
  with:
    config-path: ".github/dependabot.yml"
    max-open-prs: "10"
    require-major-ignore: "false"
    detect-ecosystems: "false"
```

### 3.69 Dependabot Helper ([`.github/workflows/dependabot-helper.yml`](../.github/workflows/dependabot-helper.yml))
Records execution timestamps and greets automated dependency maintainers:

```yaml
- name: Run Dependabot Helper
  uses: onebalaban/DependabotHelper@9455093e7f3d2338e9eeb42984865e29660e3ad8 # v1
  with:
    who-to-greet: "Dependabot"
```

### 3.70 Dependabot Automerge ([`.github/workflows/dependabot-automerge.yml`](../.github/workflows/dependabot-automerge.yml))
Automatically reviews, approves, and merges eligible patch and minor Dependabot pull requests:

```yaml
- name: Automatically Merge Dependabot PRs
  uses: invi5H/dependabot-automerge@aea0b2bd7e72af2f06118ce377821568046589f6 # v1.0.0
```

### 3.71 Dependabot Workflow Action ([`.github/workflows/dependabot-workflow.yml`](../.github/workflows/dependabot-workflow.yml))
Runs containerized Dependabot version update passes directly inside custom GitHub Actions workflows:

```yaml
- name: Run Dependabot Action
  uses: GavinMeierSonos/dependabot-action@a0789e7b36fd4cf0ba2906e77568ae5deae85f95 # v1.10-beta
  with:
    repo-name: ${{ github.repository }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
    registry-token: ${{ secrets.GITHUB_TOKEN }}
```

### 3.72 Dependabot Fetch Metadata ([`.github/workflows/dependabot-fetch-metadata.yml`](../.github/workflows/dependabot-fetch-metadata.yml))
Extracts structured metadata (semver delta, ecosystems, alert CVSS, compatibility scores) from Dependabot pull requests:

```yaml
- name: Fetch Dependabot metadata
  uses: dependabot/fetch-metadata@25dd0e34f4fe68f24cc83900b1fe3fe149efef98 # v3.1.0
  with:
    github-token: ${{ github.token }}
    skip-verification: true
```

### 3.73 Dependabot Issue for PRs ([`.github/workflows/dependabot-issue.yml`](../.github/workflows/dependabot-issue.yml))
Automatically creates triage and tracking issues for incoming Dependabot pull requests:

```yaml
- name: Create Dependabot Issue
  uses: goatandsheep/dependabot-issue-action@085384c6fc7247bf455bcd86178c6fc8a5ffc1d5 # v1.0.1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. Threat Modeling & Supply Chain Defense

1. **Tag Mutation Resistance:** Even if an upstream author re-tags or an attacker force-pushes a malicious payload to an existing release tag, the pinned 40-character SHA prevents execution of altered code.
2. **Least Privilege Enforcement:** Every workflow declares minimal permissions per job. No workflow uses repository-wide `write-all` permissions.
3. **Egress Network Policy:** StepSecurity Harden-Runner restricts runner DNS and IP outbound traffic, preventing token exfiltration.
4. **CI Invariant Guardrails:** The test suite in `tests/test_marketplace_actions.py` validates on every build that all action references match their approved commit SHAs and follow concurrency policies.
