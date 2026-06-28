---
name: sak-tts-voices
description: >
  Registry of the canonical Edge-TTS voices assigned to each Sak Family Agent.
  Reference this skill before modifying any tts.edge.voice field in config files
  to avoid assigning the wrong voice or gender to an agent.
---

## Canonical Voice Assignments

| Agent   | Profile   | Bot handle              | Gender | Edge-TTS Voice          |
|---------|-----------|-------------------------|--------|-------------------------|
| SakKing | `default` | `@sakthai_agent_v2_bot` | Male   | `en-US-BrianNeural`     |
| SakSee  | `saksee`  | `@saksee_bot`           | Female | `en-US-AriaNeural`      |
| SakThai | `sakthai` | `@sakthai_v1_bot`       | Male   | `en-US-AndrewNeural`    |
| SakSit  | `saksit`  | `@saksit_agent_bot`     | Male   | `en-US-ChristopherNeural` |

## Config fields (repository)

Each profile's `tts` block must look like:

```yaml
tts:
  provider: edge        # MUST be 'edge', not 'openai' or any other value
  edge:
    voice: <voice>      # See table above
```

## Invariants

1. ALL four profiles MUST have `tts.provider: edge`. Previously three profiles had
   `provider: openai`, which caused TTS to bypass Edge-TTS entirely.
2. Voices are intentionally **distinct** — never set two agents to the same voice.
3. SakSee is intentionally **female** (`AriaNeural`). The other three are male.

## Config file paths (repo)

| Agent   | Repo config path |
|---------|-----------------|
| SakKing | `default/config.yaml` |
| SakSee  | `profiles/saksee/config.yaml` |
| SakThai | `profiles/sakthai/config.yaml` |
| SakSit  | `profiles/saksit/config.yaml` |

## Workflow when modifying a voice

1. Edit the `tts.edge.voice` field in the repo config file
2. Run `./deploy.py` to sync to live `~/.hermes/` (see `hermes-deploy` skill)
3. Instruct user to restart the relevant service in their host terminal:
   ```bash
   systemctl --user restart hermes-gateway.service          # SakKing (default)
   systemctl --user restart hermes-gateway-saksee.service   # SakSee
   systemctl --user restart hermes-gateway-sakthai.service  # SakThai
   systemctl --user restart hermes-gateway-saksit.service   # SakSit
   ```

## Smoke-test verification

After restarting, verify live configs match the table above:

```python
import yaml
live = {
    "default": "/home/beerthai/.hermes/config.yaml",
    "saksee":  "/home/beerthai/.hermes/profiles/saksee/config.yaml",
    "sakthai": "/home/beerthai/.hermes/profiles/sakthai/config.yaml",
    "saksit":  "/home/beerthai/.hermes/profiles/saksit/config.yaml",
}
for name, path in live.items():
    cfg = yaml.safe_load(open(path))
    tts = cfg.get("tts", {})
    print(name, tts.get("provider"), tts.get("edge", {}).get("voice"))
```
