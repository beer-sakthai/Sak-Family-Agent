import asyncio
import sys
from pathlib import Path

from ..config import SKILLS_DIR, persona_skills_dir, sakthai_persona


def _skills_dir() -> Path:
    """The skills directory this gateway process browses/executes workflows from.

    Persona-scoped via ``SAKTHAI_PERSONA`` when set (see
    ``infra/vm-agents/env-templates/*.env.example``); falls back to
    ``SKILLS_DIR`` (SakThai's own overlay) unchanged for any deployment that
    doesn't set it yet.
    """
    persona = sakthai_persona()
    return persona_skills_dir(persona) if persona else SKILLS_DIR


def _workflow_command(workflow_name: str) -> list[str]:
    """Build the command used to execute one workflow skill."""
    # The task text is placed last, after a ``--`` separator, so it can never be
    # parsed as an option by the inner CLI even if it were to start with ``-``.
    return [
        sys.executable,
        "-m",
        "sakthai",
        "run",
        "--with-skills",
        workflow_name,
        "--fast",
        "--stateless",
        "--",
        f"execute the {workflow_name} skill",
    ]


def get_available_workflows():
    """
    Returns a list of available workflows (skills).
    """
    skills_dir = _skills_dir()
    if not skills_dir.is_dir():
        return []
    return sorted(d.name for d in skills_dir.iterdir() if d.is_dir())


async def run_workflow(workflow_name: str) -> str:
    """
    Executes a workflow by looking for a matching skill in the skills directory,
    and then running it using the `sakthai` CLI.
    """
    print(f"Attempting to execute workflow: {workflow_name}")

    available_skills = get_available_workflows()

    if workflow_name in available_skills:
        print(f"Executing skill: {workflow_name}")
        command = _workflow_command(workflow_name)
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return f"Skill '{workflow_name}' executed successfully:\n{stdout.decode()}"
        else:
            return f"Error executing skill '{workflow_name}':\n{stderr.decode()}"
    else:
        return f"Workflow '{workflow_name}' not found. Available skills are: {', '.join(available_skills)}"
