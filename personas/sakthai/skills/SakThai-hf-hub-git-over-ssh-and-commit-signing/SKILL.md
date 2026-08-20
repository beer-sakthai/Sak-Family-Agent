---
name: SakThai-hf-hub-git-over-ssh-and-commit-signing
description: Complete reference for authenticating Git operations on the Hugging Face Hub via SSH
  and cryptographically signing commits with GPG
...
---

# HF Hub: Git over SSH & Commit Signing

## Summary
Complete reference for authenticating Git operations on the Hugging Face Hub via SSH, and cryptographically signing commits with GPG to prove authorship. Covers key generation, key upload, git configuration, testing, and troubleshooting.

## Core Concepts

### Git over SSH
- Uses SSH key pairs (public + private) instead of HTTPS tokens or passwords
- SSH public key uploaded to HF account; private key stays on local machine
- Repository URL format: `git@hf.co:<namespace>/<repo-name>.git`
- No password prompt when configured correctly

### GPG Commit Signing
- Git authenticates *who can push* but not *who authored* the commit
- GPG signing cryptographically proves commit authorship
- Signed commits show "Verified" badge on the Hub
- Requires matching email address between GPG key and HF account

## SSH Key Management

### Checking for existing keys
```bash
ls -la ~/.ssh/
# Look for id_rsa.pub, id_ecdsa.pub, id_ed25519.pub
```

### Generating new key
```bash
ssh-keygen -t ed25519 -C "your.email@example.co"
# Recommended: use a passphrase
# Adds key to agent: ssh-add ~/.ssh/id_ed25519
```

### Adding key to HF account
1. Copy public key: `cat ~/.ssh/id_ed25519.pub`
2. Go to https://huggingface.co/settings/keys
3. Click "Add SSH key", paste, name it, save

### Testing connection
```bash
ssh -T git@hf.co
# Expected: "Hi <username>! You've successfully authenticated..."
# If "Hi anonymous": SSH key not being used — check ssh-agent
```

## HuggingFace SSH Key Fingerprints
Add to `~/.ssh/known_hosts` for trust-on-first-use:

- **ECDSA:** `SHA256:aBG5R7IomF4BSsx/h6tNAUVLhEkkaNGB8Sluyh/Q/qY`
- **ED25519:** `SHA256:dVjzGIdV7d6cwKIeZiCoRMa2gMvSKfGZAvHf4gMiMao`
- **RSA:** `SHA256:uqjYymysBGCXXiMVebB8L8RIuWbPSKGBxQQNhcT5a3Q`

Full known_hosts entries available in the [HF docs](https://huggingface.co/docs/hub/en/security-git-ssh).

## GPG Commit Signing

### Key generation
```bash
gpg --gen-key
# Email MUST match verified email on HF account
```

### Export public key
```bash
gpg --armor --export <YOUR KEY ID>
```

### Upload to HF
1. Copy armored public key output
2. Go to https://huggingface.co/settings/keys
3. Click "Add GPG Key", paste, save

### Configure git for signing
```bash
git config user.signingkey <Your GPG Key ID>
git config user.email <Your email on hf.co>

# Sign a commit
git commit -S -m "My first signed commit"

# Sign all commits by default
git config --global commit.gpgsign true
```

### Verified statuses
| Status | Meaning |
|--------|---------|
| **Verified** | Commit signed, signature cryptographically verified |
| **Unverified** | Commit signed but public key not found on HF |
| **(none)** | Commit not signed |

## Key Differences

| Feature | SSH | GPG |
|---------|-----|-----|
| **Purpose** | Authentication (who can push) | Verification (who authored) |
| **Key type** | RSA/ECDSA/Ed25519 | RSA/Ed25519 |
| **Where stored** | `~/.ssh/` | GPG keyring |
| **Upload to HF** | Settings > SSH Keys | Settings > GPG Keys |
| **Effect on commits** | Enables push without password | Shows "Verified" badge |

## Best Practices
- Use separate SSH keys per machine (like separate API tokens)
- Always use passphrase on SSH private keys
- GPG email must exactly match HF account's verified email
- For CI/CD workflows, prefer Trusted Publishers (OIDC) over storing SSH keys
- Rotate keys periodically; remove old keys from HF settings
