import os
import asyncio
import subprocess

SKILLS_DIR = "skills"

def get_available_workflows():
    """
    Returns a list of available workflows (skills).
    """
    return [d for d in os.listdir(SKILLS_DIR) if os.path.isdir(os.path.join(SKILLS_DIR, d))]

async def run_workflow(workflow_name: str) -> str:
    """
    Executes a workflow by looking for a matching skill in the skills directory,
    and then running it using the `sakthai` CLI.
    """
    print(f"Attempting to execute workflow: {workflow_name}")

    available_skills = get_available_workflows()

    if workflow_name in available_skills:
        print(f"Executing skill: {workflow_name}")
        command = [
            "python",
            "-m",
            "sakthai",
            "run",
            f"execute the {workflow_name} skill",
            "--with-skills",
            workflow_name,
            "--fast",
            "--stateless"
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return f"Skill '{workflow_name}' executed successfully:\n{stdout.decode()}"
        else:
            return f"Error executing skill '{workflow_name}':\n{stderr.decode()}"
    else:
        return f"Workflow '{workflow_name}' not found. Available skills are: {', '.join(available_skills)}"
