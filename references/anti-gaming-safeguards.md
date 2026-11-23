# Anti-Gaming & Holdout Isolation Safeguards

1. **Three-Way Dataset Split:** Partition `BaseEvalDataPoint` cases into `dev` (prompt/schema drafting), `validation` (automated loop hill-climbing), and `holdout` (locked until final release gate).
2. **Paired Blind Judging:** Present Baseline and Candidate traces in randomized A/B order to `assets/eval-judge.prompt` so verbosity bias or position bias does not inflate candidate scores.
3. **Description Token Ceiling:** Reject candidate tool edits that achieve marginal accuracy gains by stuffing few-shot examples into tool `.describe()` fields beyond the token threshold.
4. **Human Approval Gate:** Pause and confirm with the user before deleting existing MCP tools, making breaking schema changes, or broadening `allowed-tools`.
5. **Snapshot Rollback:** Persist session/evaluation checkpoints with `FileSessionStore` or `FirestoreSessionStore` and revert to the last passing `snapshotId` on any regression.

