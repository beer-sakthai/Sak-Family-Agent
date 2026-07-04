"""Example main application loop for the Sak-Family-Agent.

This script demonstrates how the value-driven 6-stage cycle is used to drive
the agent's behavior over time. It initializes a memory store, then enters a
loop where it:
1. Retrieves the current stage (e.g., DREAM).
2. Executes a simulated "skill" corresponding to that stage.
3. Advances the state to the next stage in the cycle (e.g., HOPE).

This directly implements the core architectural concept described in the
`value_driven_architecture.tex` paper.
"""

import logging
import time
from typing import Callable

from sakthai.cycle import Stage, advance_stage, get_current_stage, stage_info
from sakthai.memory.store import MemoryStore

# Configure basic logging to see the output from the cycle module.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Simulate Modular Skills ---
# In a real application, these would be complex functions or separate modules
# that perform actions aligned with each stage's value.


def dream_skill() -> None:
    """Skill for the DREAM stage."""
    print("DREAM: Defining the ideal future. What is our ultimate goal?")
    time.sleep(2)  # Simulate work
    print("DREAM: Goal set: Achieve financial independence and creative freedom.")


def hope_skill() -> None:
    """Skill for the HOPE stage."""
    print("HOPE: Identifying pathways to the dream. How can we get there?")
    time.sleep(2)
    print("HOPE: Pathway identified: Build and launch the Sak-Family-Agent project.")


def care_skill() -> None:
    """Skill for the CARE stage."""
    print("CARE: Acting with empathy and ensuring well-being. Is the system secure?")
    time.sleep(2)
    print("CARE: System check complete. All safeguards are active.")


def joy_skill() -> None:
    """Skill for the JOY stage."""
    print("JOY: Finding moments of happiness. Let's celebrate a small win.")
    time.sleep(2)
    print("JOY: Milestone reached! The state machine is cycling correctly.")


def trust_skill() -> None:
    """Skill for the TRUST stage."""
    print("TRUST: Building reliability through consistent action. Backing up memory.")
    time.sleep(2)
    print("TRUST: Memory backup successful.")


def growth_skill() -> None:
    """Skill for the GROWTH stage."""
    print("GROWTH: Learning from experience. What did we learn in this cycle?")
    time.sleep(2)
    print("GROWTH: Insight gained: A clean architecture makes development faster.")


def main() -> None:
    """Runs the main agent loop."""
    print("Initializing Sak-Family-Agent...")
    store = MemoryStore("sakthai-agent.db")

    # Map each stage to its corresponding skill.
    skill_map: dict[Stage, Callable[[], None]] = {
        Stage.DREAM: dream_skill,
        Stage.HOPE: hope_skill,
        Stage.CARE: care_skill,
        Stage.JOY: joy_skill,
        Stage.TRUST: trust_skill,
        Stage.GROWTH: growth_skill,
    }

    try:
        while True:
            current_stage = get_current_stage(store)
            info = stage_info(current_stage)
            print(f"\n--- Entering Stage {info.number}: {info.stage.name} ---")
            print(f"Description: {info.description}")

            # Execute the skill for the current stage.
            skill_to_run = skill_map[current_stage]
            skill_to_run()

            # Advance to the next stage for the next iteration.
            advance_stage(store)
            time.sleep(3)  # Pause between stages.

    except KeyboardInterrupt:
        print("\nShutting down agent.")
    finally:
        store.close()
        print("Agent shutdown complete.")


if __name__ == "__main__":
    main()