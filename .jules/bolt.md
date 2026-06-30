## 2025-05-14 - [Caching Skill Discovery]
**Learning:** The agent loop was spending ~140-160ms on every iteration just to discover and parse skills, even when they didn't change. This was due to repeated recursive directory scanning and YAML parsing of ~100 SKILL.md files.
**Action:** Implement `lru_cache` for skill parsing and discovery, while making `SkillInfo` a frozen dataclass to ensure cache safety. This reduces overhead to near-zero (<0.1ms) for subsequent iterations.

## 2025-05-15 - [Error Observability in Health Checks]
**Learning:** Swallowing exceptions in cleanup/cancellation logic within health checks masks transient network issues or API failures. While it's correct to allow the overall check to proceed, logging the failure is critical for debugging why "smoke tests" might be leaking resources or failing to clean up.
**Action:** Replaced a silent 'pass' with a logged warning using the shared 'log' utility in 'health_check.py'. This ensures failures are visible in stderr without breaking the tool's machine-readable JSON stdout.
