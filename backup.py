"""
@author: Vuong Van Duy
backup.py
data: 14.10.2025

This script creates a backup of the running .py file with name = MD5(file) at backup_dir,
then deletes the original file. It returns True if successful, False if failed.
"""


from pathlib import Path
import shutil
import hashlib
import os
from typing import Optional

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

if __name__ == "__main__":
    #self_backup_and_delete()
    path = Path(__file__).resolve()
    print(get_file_name(path))
