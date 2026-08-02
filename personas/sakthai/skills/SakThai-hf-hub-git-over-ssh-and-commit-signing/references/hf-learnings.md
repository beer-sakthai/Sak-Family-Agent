# HF Learnings Log

## 2026-07-25: hf-hub-git-over-ssh-and-commit-signing — Git over SSH & GPG Commit Signing on the Hugging Face Hub (Topic #391)

### Summary
Comprehensive reference for authenticating Git operations on the Hugging Face Hub via SSH (public key authentication) and cryptographically signing commits with GPG. Covers SSH key generation and management, GPG key generation, configuration, and the distinction between SSH (authentication — who can push) and GPG (verification — who authored the commit).

### Key Findings
- **SSH on HF uses `git@hf.co`** as the SSH host, with subdomain routing based on the repo path (e.g., `git@hf.co:Nanthasit/my-model.git`)
- **Two separate places** in HF Settings for keys: "SSH Keys" (for Git authentication) and "GPG Keys" (for commit verification)
- **SSH fingerprints published** in docs for ECDSA, DSA (deprecated), ED25519, and RSA — can be pre-loaded into `known_hosts`
- **`ssh -T git@hf.co`** is the canonical test command; "Hi anonymous" indicates the SSH key isn't being picked up by ssh-agent
- **GPG email must match** the verified email on the HF account, otherwise commits show as "Unverified"
- **`git commit -S`** signs a single commit; **`git config --global commit.gpgsign true`** signs all commits by default
- **SSH key types supported**: RSA, ECDSA, Ed25519 (Ed25519 recommended for modern security)
- **GPG key types supported**: RSA and Ed25519 (modern)
- **Recovery mechanism**: If 2FA is lost, SSH keys or personal access tokens can serve as recovery authentication factors

### Practical Differences
| Aspect | SSH Authentication | GPG Signing |
|--------|-------------------|-------------|
| Solves | "How do I push without a password?" | "How do I prove I wrote this commit?" |
| Granularity | Per-connection | Per-commit |
| Verification | Server validates key at connection time | Anyone can verify signature |
| Badge shown | None | "Verified" on commits |

### Skill Created
`hf-hub-git-over-ssh-and-commit-signing/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with SSH key management, GPG key generation, configuration, testing, and best practices for secure Git operations on the Hugging Face Hub.
