#!/usr/bin/env python3
import json
import os
import subprocess

import yaml


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
    results["deployment_script"] = check_deployment_script(repo_path)
    results["systemd_services"] = check_systemd_files(repo_path)

    overall_health = "PASS"
    for check in results.values():
        if check["status"] == "FAIL":
            overall_health = "FAIL"
            break

    output = {
        "overall_health": overall_health,
        "diagnostics": results
    }

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
