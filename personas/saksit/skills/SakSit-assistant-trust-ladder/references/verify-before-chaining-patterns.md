# VAC — Verify Before Chaining: Patterns & Examples

> Supporting reference for the Technical Trust section in saksit-assistant-trust-ladder

## Quick VAC Checklist (execute before every dependent call)

- [ ] Last tool that wrote/patched/created — did I read it back?
- [ ] If terminal: exit code 0? stderr empty? Output as expected shape?
- [ ] If API: response status 2xx+? Required fields present?
- [ ] If file: exists? Non-empty? Correct first/last lines?

## Cascade Failure Examples

### Multi-platform content (Beer's common pattern)

```
write_file("ig-post.md")
  → terminal("instagram publish ig-post.md")   ← Returns 200, but image URL is broken
    → terminal("linkedin publish ig-post.md")   ← FAILS — image URL is wrong
```

**VAC fix:** After Instagram publish, verify response has valid `permalink` field before cross-posting.

### File-edit chain

```
write_file("config.yaml")                         # Has a YAML typo
  → write_file("worker.py")                       # Reads config.yaml at import
    → terminal("python worker.py")                # FAILS — yaml.parse error
```

**VAC fix:** After writing `config.yaml`, run `python -c "import yaml; yaml.safe_load(open('config.yaml'))"` before writing worker.py.

### Multi-patch chain

```
patch(path="auth.py", old="v1", new="v2")          # Patch 1 applies
  → patch(path="auth.py", old="v2", new="v3")      # FAILS — context shifted
```

**VAC fix:** After patch 1, read the modified lines back before composing patch 2. The in-memory model and the on-disk file can diverge.

### Social content cascade

```
# Step 1: Create post content
write_file("post-content.json")       ✓ Returns success

# Step 2: Post to Instagram (depends on Step 1)
terminal("composio instagram post post-content.json")  ← Silent failure — wrong credential

# Step 3: Post to LinkedIn (depends on Step 1, not Step 2)
terminal("composio linkedin post post-content.json")   ← This would work! But Step 2 failed

# What happens without VAC:
#   → LinkedIn posts successfully
#   → Instagram silently failed
#   → Beer notices missing Instagram post
#   → Have to recreate and repost from scratch
```

**VAC fix:** After Step 2, check the response includes `"id"` or `"status": "published"` before assuming success. If Step 2 failed but Step 3 succeeded, tell Beer the full picture: "LinkedIn is live; Instagram failed due to credential error. Fixing now."

## Use in Conjunction with the Trust Ladder

The VAC pattern supports every rung of the trust ladder:

| Ladder Rung | VAC Application |
|-------------|----------------|
| **Read** | Before suggesting, verify you actually read the file correctly (re-read key sections) |
| **Suggest** | Before proposing, verify the context you're basing the suggestion on |
| **Draft** | After drafting, read the draft back before presenting it |
| **Confirm** | Before the final "ready?" check, verify all dependent outputs are green |
| **Autonomous** | During autonomous execution, VAC is your guardrail — every step self-verifies |

## When to Skip VAC

VAC costs ~2 seconds per check. Skip when:
- The call has no side effects and the output isn't used by the next step
- You just wrote a file and immediately read it in the same step (terminal one-liner that both writes and validates)
- The call's failure is self-evident from its own output (e.g., a failed test command whose output you're already capturing)
