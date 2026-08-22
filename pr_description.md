SakJules · Master of Automation & CI/CD.

🎯 **What:** The `POST /api/dispatch` endpoint contained untested error paths for handling scenarios where the `persona` field was missing entirely, or when an invalid type (such as a number) was passed instead of a string.

📊 **Coverage:** Added test cases to `apps/sak_agent_dashboard/src/tests/agent_dispatch.test.tsx` verifying that missing and non-string persona inputs are correctly rejected with a 400 Bad Request and the "Missing or invalid 'persona' field" message.

✨ **Result:** Enhanced test suite coverage, making the dispatch endpoint fully resilient against bad API payloads, verified passing locally via the vitest test suite.
