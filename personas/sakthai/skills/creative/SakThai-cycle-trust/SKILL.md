---
name: SakThai-cycle-trust
description: "Stage 5: Verify the work is safe, correct, and truly done."
version: 1.0.0
author: Beer Sakthai (@beer-sakthai) & Gemini Code Assist
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [core, cycle, trust, verification, testing]
    category: core
    owner: SakKing
---

# Cycle: Trust

This is the fifth and most critical stage. It is where we establish **Truth**.

Truth is not just about correctness; it is about fidelity to the original `Dream`. It is the security that what we built is what we *meant* to build. It is the guarantee that our actions were safe, effective, and beneficial to Beer.

We never celebrate before the work is green. Trust is earned through rigorous, auditable verification.

## Your Task

To establish Truth, you will build a "Chain of Trust" by performing and documenting these checks in order.

1. **Automated Verification (`CI/CD Check`):**
    - Check the results of any CI pipeline. Did all tests pass? Did the deployment succeed?
    - Record the status and a link to the results.

2. **Manual Verification (`Functional Check`):**
    - If automation is not possible, perform a direct functional test.
    - For `SakSee`, this means visiting the webpage and using `browser_vision` to confirm it looks correct.
    - For `SakSit`, this means reviewing the generated image or video.
    - For `SakKing`, this means running the code or viewing the artifact.
    - Record the outcome of the manual check.

3. **Fidelity Verification (`Dream Check`):**
    - Recall the original `Vision Document` from the `Dream` stage.
    - Compare the final artifact against the "What does 'done' look like?" and "Why are we doing this?" sections.
    - Answer plainly: "Does this work achieve the original goal?"
    - Record the fidelity assessment.

4. **User Confirmation (`Final Check`):**
    - Present the final result and a summary of the verification steps to the user.
    - Ask for final confirmation: "Does this meet the goal and is it safe to proceed to the Growth stage?"

## Output

Produce a "Verification Report" containing the full Chain of Trust. The final line of the report must be either `Status: Verification Passed` or `Status: Verification Failed`.

If verification fails at any step, you must halt the cycle and create a plan to fix the issue. Do not proceed to the `Growth` stage until Trust is fully established.
