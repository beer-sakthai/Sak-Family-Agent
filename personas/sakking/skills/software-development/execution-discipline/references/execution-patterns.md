# Execution Pattern References

## Prompt verification sequence

In this session, after creating skills, the agent realized the skill
registry did not reflect the new skills. The correct sequence was:

1. Inspect the target skill path.
2. Read the skill file for verification.
3. Confirm via `skills_list`.
4. Continue with the task instead of rerunning creation behavior.

## Evidence-first rule

Before any command is run to install or fix dependency state, confirm:
- authoritative docs URL and exact command
- installed version from which the script is being run
- shebang/proxy/symlink state if packages or binaries are involved

Missing any of the above counts as insufficient evidence to act.

## Empty-output trap

When a tool call returns no content, treat that as a state change and
use explicit read/inspect calls to verify progress. Do not reissue the
same intent without inspection.
