# Skill naming convention

Every skill's `name` now encodes **who owns it**, so a glance at the name (in
`sakthai skills list`, a prompt block, or a folder) tells you whether it is
shared across the whole Sak Family or authored by one persona.

## The rule

| Layer | Where it lives | `name:` prefix | Example |
|---|---|---|---|
| **Shared** | `personas/shared/skills/` | `Sak-` | `Sak-github-pr-workflow` |
| **SakKing** (lead, owns all) | `personas/sakking/skills/` | `SakKing-` | `SakKing-cron-watchdog-self-heal` |
| **SakThai** (Hugging Face) | `personas/sakthai/skills/` | `SakThai-` | `SakThai-hf-diffusers` |
| **SakSee** (Web) | `personas/saksee/skills/` | `SakSee-` | `SakSee-chrome-devtools` |
| **SakSit** (Social Media) | `personas/saksit/skills/` | `SakSit-` | `SakSit-ig-carousel-design` |
| **SakTan** (Daily Ops) | `personas/saktan/skills/` | `SakTan-` | `SakTan-daily-ops-helper` |
| **SakJules** (Automation & CI/CD) | `personas/sakjules/skills/` | `SakJules-` | `SakJules-github-actions-fix` |

Plus two structural rules, enforced by the validator:

- the skill's **leaf folder name must equal its `name`** field, and
- `name` must be **≤ 64 characters** (`SKILL_NAME_MAX`).

The single source of truth is `sakthai/skills.py`
(`SHARED_SKILL_PREFIX`, `PERSONA_SKILL_PREFIXES`, `naming_violations`,
`target_skill_name`).

## Tooling

```bash
# Audit every persona tree against the convention (exit 1 on any violation)
sakthai skills validate --naming

# Scaffold a new skill already carrying the right prefix
sakthai skills create my-skill --persona saksit   # -> SakSit-my-skill
sakthai skills create my-skill --persona shared   # -> Sak-my-skill

# Preview / apply the bulk rename for a layer (dry-run by default)
python scripts/rename_skills.py shared            # preview
python scripts/rename_skills.py saksit --apply    # rewrite name: + leaf folder
```

`sakthai skills sync-sakking` now imports SakKing-learned skills under the
`SakKing-` prefix (was the legacy `sakthai-`), via `target_skill_name`, which is
idempotent and strips any legacy/cross-layer prefix before applying the new one.

## Migration status (as of this change)

- **Mechanism landed:** convention constants, `--naming` validator, create-time
  enforcement, `sync-sakking` prefix, and `scripts/rename_skills.py`.
- **Deferred (run the script per layer):** `sakthai skills validate --naming`
  currently reports ~174 pre-convention skills (plain slugs or the legacy
  `sakthai-` prefix). Apply them layer-by-layer with `rename_skills.py --apply`
  once the identity/reassignment moves below are settled, then re-run
  `scripts/compose_persona.py <persona> --out …` to confirm composition still
  works.

## Recommended renames / reassignments

Beyond the mechanical prefixing, these skills are **mis-assigned** to their
persona after the identity changes (SakSit: Business → Social Media; SakSee:
Playwright → Web) and should move before being prefixed:

- **SakSit `business/` skills (~45: `saas-*`, `b2b-*`, `gtm-*`, pricing, unit
  economics, …)** — no longer fit "Master of Social Media". Reassign to
  **SakKing** (who owns all skills) under `SakKing-`, or promote to `shared/`
  under `Sak-` if any are broadly useful.
- **SakSit web skills** (`playwright-*`, `core-web-vitals-basics`,
  `view-transition-api`, `broadcast-channel-api`, `cookie-store-api`,
  `server-timing-header`, `css-content-visibility`) — these are **SakSee's**
  (Master of Web) domain. Move to `personas/saksee/skills/` and prefix
  `SakSee-`.
- **New SakSit skills to add** (Social Media / IG): image- and video-generation
  workflows that drive the Hugging Face Spaces wired in
  `personas/saksit/config/mcp.json` (e.g. `SakSit-ig-image-from-prompt`,
  `SakSit-shortform-video-storyboard`, `SakSit-caption-and-hashtag-pack`).
- **SakSee** keep `chrome-devtools` + `playwright`, prefixed `SakSee-`, and gain
  the web skills moved off SakSit.

Track the exact moves in the PR that applies `rename_skills.py --apply`.
