## 2025-05-14 - [Caching Skill Discovery]
**Learning:** The agent loop was spending ~140-160ms on every iteration just to discover and parse skills, even when they didn't change. This was due to repeated recursive directory scanning and YAML parsing of ~100 SKILL.md files.
**Action:** Implement `lru_cache` for skill parsing and discovery, while making `SkillInfo` a frozen dataclass to ensure cache safety. This reduces overhead to near-zero (<0.1ms) for subsequent iterations.
