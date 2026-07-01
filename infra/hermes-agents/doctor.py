#!/usr/bin/env python3
import json
import os
import shutil
import subprocess

import yaml


GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


def check_git_status(repo_path):
    try:
        res = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, capture_output=True, text=True, check=True)
        changes = res.stdout.strip()
        if not changes:
            return {"status": "PASS", "details": "Git working tree is clean."}
        else:
            return {"status": "PASS", "details": f"Untracked/modified files present:\n{changes}"}
    except Exception as e:
        return {"status": "FAIL", "details": f"Failed to check git status: {e}", "remediation": "Check if git is installed and if this is a valid git repository."}

def check_omp_files(repo_path):
    omp_state_dir = os.path.join(repo_path, '.omp', 'state')
    required_files = ['mode.json', 'approval.json', 'reasoning.json', 'rules.json', 'taskboard.md']
    required_dirs = ['checkpoints', 'decisions']

    findings = []
    failed = False

    if not os.path.exists(omp_state_dir):
        return {"status": "FAIL", "details": ".omp/state/ directory does not exist.", "remediation": "Run '/oh-my-product:launch' to initialize state directory."}

    for f in required_files:
        path = os.path.join(omp_state_dir, f)
        if not os.path.exists(path):
            findings.append(f"Missing required OMP file: {f}")
            failed = True
        else:
            # Check writeability
            if not os.access(path, os.W_OK):
                findings.append(f"OMP file is not writeable: {f}")
                failed = True

    for d in required_dirs:
        path = os.path.join(omp_state_dir, d)
        if not os.path.exists(path):
            findings.append(f"Missing required OMP directory: {d}")
            failed = True
        else:
            # Check writeability
            if not os.access(path, os.W_OK):
                findings.append(f"OMP directory is not writeable: {d}")
                failed = True

    if failed:
        return {"status": "FAIL", "details": "; ".join(findings), "remediation": "Re-run /oh-my-product:launch to fix missing or unwritable state files."}
    else:
        return {"status": "PASS", "details": "All OMP state files and directories exist and are writeable."}

def check_yaml_integrity(repo_path):
    configs = [
        ('default/config.yaml', os.path.join(repo_path, 'default', 'config.yaml')),
        ('saksee/config.yaml', os.path.join(repo_path, 'profiles', 'saksee', 'config.yaml')),
        ('sakthai/config.yaml', os.path.join(repo_path, 'profiles', 'sakthai', 'config.yaml')),
        ('saksit/config.yaml', os.path.join(repo_path, 'profiles', 'saksit', 'config.yaml'))
    ]

    findings = []
    failed = False
    for name, path in configs:
        if not os.path.exists(path):
            findings.append(f"Missing configuration file: {name}")
            failed = True
            continue
        try:
            with open(path, encoding='utf-8') as f:
                yaml.safe_load(f)
        except Exception as e:
            findings.append(f"YAML syntax error in {name}: {e}")
            failed = True

    if failed:
        return {"status": "FAIL", "details": "; ".join(findings), "remediation": "Restore the config file from backup or fix the YAML syntax error manually."}
    else:
        return {"status": "PASS", "details": "All configuration YAML files are valid and structurally sound."}


def _load_yaml_config(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _load_env_file(path):
    values = {}
    if not os.path.exists(path):
        return values

    with open(path, encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[len('export '):].lstrip()
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if value and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
    return values


def _resolve_github_token(repo_path):
    token = os.environ.get('GITHUB_TOKEN', '').strip()
    if token:
        return token, "environment"

    env_path = os.path.join(repo_path, '.env')
    token = _load_env_file(env_path).get('GITHUB_TOKEN', '').strip()
    if token:
        return token, "local .env"

    return '', "missing"


def _probe_hermes_mcp(server_name):
    if shutil.which('hermes') is None:
        return {
            "status": "WARN",
            "details": f"Hermes CLI is not available, so `hermes mcp test {server_name}` was skipped.",
            "remediation": f"Install Hermes CLI and run `hermes mcp test {server_name}` to verify the live MCP endpoint."
        }

    try:
        res = subprocess.run(
            ['hermes', 'mcp', 'test', server_name],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as e:
        return {
            "status": "WARN",
            "details": f"Could not execute `hermes mcp test {server_name}`: {e}",
            "remediation": f"Install Hermes CLI and rerun `hermes mcp test {server_name}`."
        }

    output = "\n".join(part for part in [res.stdout.strip(), res.stderr.strip()] if part)
    if res.returncode == 0:
        details = f"`hermes mcp test {server_name}` passed."
        if output:
            details = f"{details} {output}"
        return {"status": "PASS", "details": details}

    details = f"`hermes mcp test {server_name}` failed with exit code {res.returncode}."
    if output:
        details = f"{details}\n{output}"
    return {
        "status": "FAIL",
        "details": details,
        "remediation": f"Refresh the GitHub MCP token and rerun `hermes mcp test {server_name}`."
    }


def check_github_mcp(repo_path):
    config_path = os.path.join(repo_path, 'default', 'config.yaml')
    if not os.path.exists(config_path):
        return {
            "status": "FAIL",
            "details": "default/config.yaml is missing, so the GitHub MCP configuration cannot be validated.",
            "remediation": "Restore infra/hermes-agents/default/config.yaml from the repo."
        }

    try:
        config = _load_yaml_config(config_path)
    except Exception as e:
        return {
            "status": "FAIL",
            "details": f"Failed to parse default/config.yaml: {e}",
            "remediation": "Fix the YAML syntax in infra/hermes-agents/default/config.yaml."
        }

    github = (config.get('mcp_servers') or {}).get('github')
    if not isinstance(github, dict):
        return {
            "status": "FAIL",
            "details": "default/config.yaml does not define mcp_servers.github.",
            "remediation": "Add the GitHub MCP server entry under mcp_servers.github."
        }

    if github.get('url') != GITHUB_MCP_URL:
        return {
            "status": "FAIL",
            "details": f"GitHub MCP URL is {github.get('url')!r}, expected {GITHUB_MCP_URL!r}.",
            "remediation": "Set mcp_servers.github.url to the GitHub Copilot MCP endpoint."
        }

    headers = github.get('headers') or {}
    auth_header = headers.get('Authorization')
    if auth_header != 'Bearer ${GITHUB_TOKEN}':
        return {
            "status": "FAIL",
            "details": "default/config.yaml does not reference the GitHub token in mcp_servers.github.headers.Authorization.",
            "remediation": "Set mcp_servers.github.headers.Authorization to `Bearer ${GITHUB_TOKEN}`."
        }

    token, token_source = _resolve_github_token(repo_path)
    if not token:
        return {
            "status": "WARN",
            "details": "GitHub MCP config is present, but GITHUB_TOKEN is not set in the environment or local .env.",
            "remediation": "Export GITHUB_TOKEN or add it to infra/hermes-agents/.env, then rerun doctor."
        }

    probe = _probe_hermes_mcp('github')
    if probe['status'] == 'PASS':
        return {
            "status": "PASS",
            "details": f"GitHub MCP config is present, GITHUB_TOKEN is available from {token_source}, and the live probe passed."
        }
    if probe['status'] == 'WARN':
        return {
            "status": "WARN",
            "details": f"GitHub MCP config is present and GITHUB_TOKEN is available from {token_source}, but the live probe was skipped.\n{probe['details']}",
            "remediation": probe['remediation']
        }
    return probe


def check_deployment_script(repo_path):
    deploy_path = os.path.join(repo_path, 'deploy.py')
    if not os.path.exists(deploy_path):
        return {"status": "FAIL", "details": "deploy.py script is missing.", "remediation": "Re-run the previous agent step to generate deploy.py."}
    if not os.access(deploy_path, os.X_OK):
        return {"status": "FAIL", "details": "deploy.py is not executable.", "remediation": "Run 'chmod +x deploy.py' to make it executable."}
    return {"status": "PASS", "details": "deploy.py exists and is executable."}

def check_systemd_files(repo_path):
    systemd_src = os.path.join(repo_path, 'systemd')
    required_services = [
        'hermes-gateway.service',
        'hermes-gateway-saksee.service',
        'hermes-gateway-sakthai.service',
        'hermes-gateway-saksit.service'
    ]

    findings = []
    failed = False
    if not os.path.exists(systemd_src):
        return {"status": "FAIL", "details": "systemd directory is missing in the repository.", "remediation": "Restore systemd directory."}

    for s in required_services:
        path = os.path.join(systemd_src, s)
        if not os.path.exists(path):
            findings.append(f"Missing systemd service file: {s}")
            failed = True

    if failed:
        return {"status": "FAIL", "details": "; ".join(findings), "remediation": "Restore the missing systemd service files in the systemd directory."}
    else:
        return {"status": "PASS", "details": "All required systemd service definitions exist in the repository."}

def main():
    # Validate the config tree this script lives in (infra/hermes-agents/),
    # not a hardcoded external clone path. The former standalone
    # ~/sakthai-hermes-agents repo was consolidated here and deleted.
    repo_path = os.path.dirname(os.path.abspath(__file__))

    results = {}
    results["git_health"] = check_git_status(repo_path)
    results["omp_state"] = check_omp_files(repo_path)
    results["yaml_integrity"] = check_yaml_integrity(repo_path)
    results["github_mcp"] = check_github_mcp(repo_path)
    results["deployment_script"] = check_deployment_script(repo_path)
    results["systemd_services"] = check_systemd_files(repo_path)

    overall_health = "PASS"
    seen_warn = False
    for check in results.values():
        if check["status"] == "FAIL":
            overall_health = "FAIL"
            break
        if check["status"] == "WARN":
            seen_warn = True

    if overall_health != "FAIL" and seen_warn:
        overall_health = "WARN"

    output = {
        "overall_health": overall_health,
        "diagnostics": results
    }

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
