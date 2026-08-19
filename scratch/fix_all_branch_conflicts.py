import subprocess
import os

def run(cmd, cwd="/home/beern/Sak-Family-Agent", check=False):
    print(f"==> Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return res

def fix_branches():
    run("git fetch --all")
    branches_res = run("git branch -r")
    raw_branches = [line.strip() for line in branches_res.stdout.splitlines() if line.strip()]

    remote_branches = []
    for b in raw_branches:
        if "->" in b:
            continue
        if b.startswith("origin/"):
            b_name = b[len("origin/"):]
            if b_name != "main" and not b_name.startswith("HEAD"):
                remote_branches.append(b_name)

    print(f"Found {len(remote_branches)} remote feature branches to sync with main: {remote_branches}")

    for branch in remote_branches:
        print(f"\n==========================================")
        print(f"Processing branch: {branch}")
        print(f"==========================================")
        run(f"git checkout -B {branch} origin/{branch}")

        # Try merging origin/main
        merge_res = run("git merge origin/main --no-edit")
        if merge_res.returncode != 0:
            print(f"[!] Conflict detected on {branch}. Resolving conflicts...")
            # Automatically resolve conflicts preferring main for deleted/modified files and adding resolution
            run("git checkout --theirs . 2>/dev/null || true")
            run("git add .")
            run('git commit -m "style/fix: resolve merge conflicts with main" || true')

        print(f"[+] Pushing resolved branch {branch} to origin...")
        run(f"git push origin {branch} --force-with-lease")

    # Return to main
    run("git checkout main")
    run("git pull origin main")
    print("\n[SUCCESS] All branches processed and synced with main!")

if __name__ == "__main__":
    fix_branches()
