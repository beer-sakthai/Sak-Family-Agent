# hf-hub-cli-rebuilt

**author:** SakThai
**license:** MIT

**Area:** Hugging Face Hub / CLI
**Tags:** `huggingface-hub`, `cli`, `sandbox`, `jobs`, `spaces-templates`, `v1.22`, `v1.23`, `v1.24`

## Purpose

This skill covers the rebuilt `hf` CLI introduced in huggingface_hub v1.22.0+ and the new features shipped in v1.22, v1.23, and v1.24: Sandboxes, faster tree-cached downloads, Space templates, Job naming, CLI extensions, and the Click-based CLI framework.

## When to Use

- User asks about the `hf` CLI, new commands, or CLI changes
- User wants to spin up Sandboxes (`Sandbox.create`, `SandboxPool`)
- User wants to create Spaces from official templates
- User wants to name Jobs or use scheduled Jobs
- User asks about "what's new" in huggingface_hub v1.22–v1.24

## Key References

- **CLI Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/cli
- **CLI Reference:** https://huggingface.co/docs/huggingface_hub/en/package_reference/cli
- **Sandboxes Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/sandbox
- **Jobs Guide:** https://huggingface.co/docs/huggingface_hub/en/guides/jobs
- **Space Templates:** `hf spaces templates` CLI or `list_space_templates()` API
- **Learnings:** `references/hf-learnings.md`

## Dependencies

- huggingface_hub >= 1.22.0
- For standalone `hf` CLI: `curl -fsSL https://huggingface.co/hf/install | bash`
