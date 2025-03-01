#!/usr/bin/env python3
"""
Banner module for PQ Matrix Installer.
Displays the application banner and initial information.
"""

import platform
import os
from colorama import init, Fore, Style

# Initialize colorama
init()


def print_banner():
    """
    Print the PQ Matrix Installer banner.
    """
    banner = f"""
{Fore.BLUE}╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║  🛡️  PQ Matrix Installer - Post-Quantum Security for Matrix  🛡️  ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

A comprehensive installer for deploying secure Matrix servers
with post-quantum encryption, decentralized storage, and more.
"""
    print(banner)


def print_phase_header(phase_name, phase_number, total_phases):
    """
    Print a header for the current installation phase.
    
    Args:
        phase_name (str): Name of the current phase
        phase_number (int): Current phase number
        total_phases (int): Total number of phases
    """
    header = f"""
{Fore.CYAN}╔═════════════════════════════════════════════════════════════════╗
║  PHASE {phase_number}/{total_phases}: {phase_name.upper()}  
╚═════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(header)


def print_system_info():
    """
    Print information about the system.
    """
    info = f"""
{Fore.YELLOW}SYSTEM INFORMATION:{Style.RESET_ALL}
  • OS: {platform.system()} {platform.release()}
  • Python: {platform.python_version()}
  • Architecture: {platform.machine()}
"""
    print(info)


def print_completion():
    """
    Print completion message after successful installation.
    """
    message = f"""
{Fore.GREEN}╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║           🎉  PQ Matrix Server Successfully Installed  🎉       ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

Your secure, quantum-resistant Matrix server is now set up and ready to use.
"""
    print(message)
