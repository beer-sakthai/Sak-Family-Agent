import asyncio
import sys

from ..config import SKILLS_DIR


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
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir())


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
