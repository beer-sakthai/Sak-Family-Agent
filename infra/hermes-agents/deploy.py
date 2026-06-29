#!/usr/bin/env python3
import os
import shutil
import subprocess


def replace_paths(content, target_home):
    return content.replace('/home/sakthai', target_home)

def copy_with_replacement(src, dst, target_home):
    with open(src, encoding='utf-8', errors='ignore') as f:
        content = f.read()

    modified_content = replace_paths(content, target_home)

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    # Backup existing file if it exists
    if os.path.exists(dst):
        bak_path = dst + '.bak'
        shutil.copy2(dst, bak_path)
        print(f"Backed up existing {dst} to {bak_path}")

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print(f"Copied and updated: {src} -> {dst}")

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    home_dir = os.path.expanduser('~')
    hermes_home = os.path.join(home_dir, '.hermes')
    systemd_home = os.path.join(home_dir, '.config', 'systemd', 'user')

    print("Deploying configurations...")
    print(f"Repository root: {repo_root}")
    print(f"Target HOME: {home_dir}")
    print(f"Hermes path: {hermes_home}")
    print(f"Systemd path: {systemd_home}")

    # 1. Sync default profile
    default_src = os.path.join(repo_root, 'default')
    for filename in ['config.yaml', 'SOUL.md']:
        src_file = os.path.join(default_src, filename)
        if os.path.exists(src_file):
            dst_file = os.path.join(hermes_home, filename)
            copy_with_replacement(src_file, dst_file, home_dir)

    # 2. Sync shared directory
    shared_src = os.path.join(repo_root, 'shared')
    for filename in ['agents-roster.md']:
        src_file = os.path.join(shared_src, filename)
        if os.path.exists(src_file):
            dst_file = os.path.join(hermes_home, 'shared', filename)
            copy_with_replacement(src_file, dst_file, home_dir)

    # 3. Sync profiles
    profiles_src = os.path.join(repo_root, 'profiles')
    if os.path.exists(profiles_src):
        for profile in os.listdir(profiles_src):
            profile_dir = os.path.join(profiles_src, profile)
            if not os.path.isdir(profile_dir):
                continue

            print(f"\nProcessing profile: {profile}")
            target_profile_dir = os.path.join(hermes_home, 'profiles', profile)
            os.makedirs(target_profile_dir, exist_ok=True)

            # Copy config.yaml and SOUL.md
            for filename in ['config.yaml', 'SOUL.md']:
                src_file = os.path.join(profile_dir, filename)
                if os.path.exists(src_file):
                    dst_file = os.path.join(target_profile_dir, filename)
                    copy_with_replacement(src_file, dst_file, home_dir)

            # Copy cron jobs if exists
            cron_src = os.path.join(profile_dir, 'cron', 'jobs.json')
            if os.path.exists(cron_src):
                cron_dst = os.path.join(target_profile_dir, 'cron', 'jobs.json')
                copy_with_replacement(cron_src, cron_dst, home_dir)

            # Create symlink AGENTS.md -> ../../shared/agents-roster.md
            symlink_path = os.path.join(target_profile_dir, 'AGENTS.md')
            if os.path.exists(symlink_path) or os.path.islink(symlink_path):
                try:
                    os.remove(symlink_path)
                except Exception as e:
                    print(f"Warning: could not remove existing symlink/file at {symlink_path}: {e}")
            try:
                os.symlink('../../shared/agents-roster.md', symlink_path)
                print(f"Created symlink: {symlink_path} -> ../../shared/agents-roster.md")
            except Exception as e:
                print(f"Failed to create symlink: {e}")

    # 4. Sync systemd files
    systemd_src = os.path.join(repo_root, 'systemd')
    if os.path.exists(systemd_src):
        print("\nProcessing systemd services...")
        for root, _dirs, files in os.walk(systemd_src):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, systemd_src)
                dst_file = os.path.join(systemd_home, rel_path)
                copy_with_replacement(src_file, dst_file, home_dir)

    print("\nFile sync complete.")

    # 5. Reload systemd and try restarting services
    print("\nAttempting to reload systemd and restart services...")
    try:
        # We try to run daemon-reload
        subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True, text=True, check=True)
        print("Systemd user daemon reloaded successfully.")

        # Identify the services to restart
        services = ['hermes-gateway.service']
        for profile in os.listdir(profiles_src):
            if os.path.isdir(os.path.join(profiles_src, profile)):
                services.append(f"hermes-gateway-{profile}.service")

        print(f"Restarting services: {', '.join(services)}")
        subprocess.run(['systemctl', '--user', 'restart'] + services, check=True)
        print("Services restarted successfully!")
    except Exception:
        print("\nCould not reload/restart services automatically (this is expected if running in a sandbox).")
        print("Please run the following commands manually in your host terminal to apply changes:")
        print("  systemctl --user daemon-reload")
        services = ['hermes-gateway.service']
        if os.path.exists(profiles_src):
            for profile in os.listdir(profiles_src):
                if os.path.isdir(os.path.join(profiles_src, profile)):
                    services.append(f"hermes-gateway-{profile}.service")
        print(f"  systemctl --user restart {' '.join(services)}")

if __name__ == '__main__':
    main()
