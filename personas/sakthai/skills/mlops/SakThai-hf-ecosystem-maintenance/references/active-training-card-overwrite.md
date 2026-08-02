# HF Jobs Active Training — Card Overwrite Pitfall

Captured 2026-07-30 during Cron #034: enriched `sakthai-context-1.5b-tools-v7` card (pipeline_tag, family table, growing ecosystem) was overwritten by training step commit 3 seconds later.

## The Problem

When a model is trained via `hf jobs` (HF Jobs managed compute), the training process periodically generates commits that update the README with auto-generated content:

```
Training in progress, step 50
Training in progress, step 100
Training in progress, step 150
...
```

**Each of these commits completely replaces the README.md** with a fresh auto-generated card containing only TRL/SFT metadata, framework versions, and a generic usage example. Any manual card enrichment pushed between steps is silently overwritten.

## Detection

**Before pushing a card enrichment, check for active training:**

```bash
# Check recent commits for "Training in progress" pattern
curl -s "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-tools-v7/commits/main?limit=5" | python3 -c "
import json, sys
commits = json.load(sys.stdin)
for c in commits:
    msg = c.get('title', '')
    if 'Training in progress' in msg:
        print(f'⚠️  Active training detected: \"{msg}\" at {c.get(\"date\", \"?\")}')
    else:
        print(f'✓ Last commit: \"{msg}\"')
"
```

**Signs of active training:**
- Recent commits (within the last hour) containing "Training in progress"
- Commit interval is regular (~5-10 minutes between steps)
- Auto-generated README with `generated_from_trainer`, `trl`, `sft` tags only

## What Happens

| Time | Event | README Content |
|:----:|-------|----------------|
| T+0 | Training publishes step N | Auto-generated stub card |
| T+5min | You push enriched card | Full card with badges, family table, cross-links |
| T+10min | Training publishes step N+1 | **Auto-generated stub card again** (your changes gone) |

Your enriched card is **gone** — not merged, not rebased — completely replaced. The training process does a force-like push of the auto-generated file.

## Solution

### If training IS active: Wait

1. **Do not push a card enrichment.** It will be wasted effort.
2. **Check expected training duration.** If `--max_steps 1000` and step 250 just ran, expect ~2.5 more hours at 10min/50 steps.
3. **Prepare the card locally** and push it only after the last "Training in progress" commit is followed by a non-training commit (or no new commits for 30+ minutes).

### If training has FINISHED: Push immediately

After the final step, the card stays as the last auto-generated stub. Enrich it normally:

```bash
# Clone, replace README, commit, push
git clone https://$USER:$HF_TOKEN@huggingface.co/$AUTHOR/$REPO /tmp/enrich-$REPO
cp /path/to/enriched/README.md /tmp/enrich-$REPO/README.md
cd /tmp/enrich-$REPO
git config user.email "sakthai@agent"
git config user.name "SakThai Agent"
git add README.md
git commit -m "Overhaul model card: pipeline_tag, ecosystem cross-links, growing the ecosystem section"
git push
```

### Edge case: Competition with automatic training pushes

If two independent processes push to the same repo (your card enrichment + training job), the **last push wins** — no merge, no conflict resolution. Git's fast-forward rules apply: if your commit was pushed after the training commit but the training process pushes again before your commit is noticed, your commit is orphaned.

**Rule:** An `hf jobs` training process has write access to the repo. Never assume a push from outside the training process will survive. Always verify by re-fetching the README after 2× the training interval.

## Real Example (Cron #034, 2026-07-30)

```
Step 200: 2026-07-30 00:14:13
My push:  2026-07-30 00:23:32  ← enriched card with pipeline_tag, 14-model family table
Step 250: 2026-07-30 00:23:35  ← 3 seconds later, my card was wiped
```

**Lesson:** Always check `git log` or the commits API before pushing a card enrichment. A single `curl` + `grep` for "Training in progress" saves 30+ minutes of wasted work.

## Verification after training completes

Once you've confirmed no "Training in progress" commits for 30+ minutes, then push:

1. **Fetch the current stub**: `curl -s "https://huggingface.co/$AUTHOR/$REPO/raw/main/README.md"`
2. **Check it's a stub**: should be 40-80 lines with `generated_from_trainer` in YAML
3. **Replace with enriched card**: full family table, pipeline_tag, datasets, badges, growing ecosystem
4. **Verify**: Re-fetch after push and confirm `pipeline_tag: text-generation` is present
5. **Check again after 10 minutes**: if no "Training in progress" commits appear, the enrichment is stable
