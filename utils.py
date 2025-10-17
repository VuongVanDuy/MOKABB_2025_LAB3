"""
@author: Vuong Van Duy
utils.py
data: 14.10.2025

This module provides utility functions for user resolution, file ownership management,
file name retrieval, MD5 checksum calculation, and self-backup and deletion of files.
"""


import os
import pwd
import subprocess
import hashlib
import shutil
from typing import Optional, Union, List
from pathlib import Path
from config import UNIT_DIR, BACKUP_DIR, SAVE_VIRUS_DIR, CRON_DIR, WRAPPER_DIR, LIST_NEW_FILES


def check_root() -> bool:
    return os.geteuid() == 0

def resolve_invoking_user() -> str:
    """
    Trả về tên user đã 'gọi' lệnh khi process đang chạy dưới root.
    Ưu tiên: sudo -> pkexec -> doas. Nếu không root, trả về user hiện tại theo UID.
    """
    euid = os.geteuid()
    if euid == 0:
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            return sudo_user

        pk_uid = os.environ.get("PKEXEC_UID")
        if pk_uid and pk_uid.isdigit():
            try:
                return pwd.getpwuid(int(pk_uid)).pw_name
            except KeyError:
                pass

        doas_user = os.environ.get("DOAS_USER")
        if doas_user:
            return doas_user

        # không xác định được
        raise RuntimeError(
            "Root user unknown (SUDO_USER/PKEXEC_UID/DOAS_USER does not exist). "
            "Please pass the user parameter to the function or set the TARGET_USER "
            "environment variable."
        )
    else:

        return pwd.getpwuid(os.getuid()).pw_name

def remove_roots_ownership(listPath: List[Union[str, Path]]) -> None:
    if not check_root():
        return
    try:
        user = resolve_invoking_user()

        for path in listPath:
            path = Path(path).resolve()
            if path.exists():
                subprocess.run(["sudo", "chown", f"{user}:{user}", str(path)], check=True)
                print(f"✅ Changed ownership to {user}:{user} for {path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running chown: {e}")

def create_dirs_if_not_exists():
    list_dirs = [UNIT_DIR, BACKUP_DIR, SAVE_VIRUS_DIR, CRON_DIR, WRAPPER_DIR]
    for dir_path in list_dirs:
        expanded_path = os.path.expanduser(dir_path)
        try:
            os.makedirs(expanded_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {expanded_path}: {e}")

    remove_roots_ownership(list_dirs)

def get_file_name(p: Path) -> str:
    return p.name

def _md5_of_file(p: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def self_backup_and_delete(backup_dir: Optional[str], pathFileName: Path) -> bool:
    """
    Create a backup of the running .py file with name = MD5(file) at backup_dir,
    then delete the original file. Return True if successful, False if failed.
    """
    if pathFileName is None:
        return False

    me = pathFileName

    if not me.exists():
        print("Source file not found:", me)
        return False

    digest = _md5_of_file(me)
    bdir = Path(os.path.expanduser(backup_dir)).resolve()
    try:
        bdir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print("Unable to create backup folder:", bdir, "-", e)
        return False

    digest_ = digest + ".bak"
    backup_path = bdir / digest_

    try:
        shutil.copy2(str(me), str(backup_path))
        LIST_NEW_FILES.append(backup_path)
        # if check_root():
        #     remove_root_ownership(backup_path)

        if _md5_of_file(backup_path) != digest:
            print("MD5 copy does not match, cancel deletion of original file.")
            try:
                backup_path.unlink()
            except Exception:
                pass
            return False

        os.remove(str(me))
        print("✅ Backup:", backup_path)
        print("🗑️ Deleted:", me)
        return True

    except Exception as e:
        print("❌ Error while backup/delete:", e)
        return False
