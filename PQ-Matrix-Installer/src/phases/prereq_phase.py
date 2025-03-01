#!/usr/bin/env python3
"""
Prerequisites Phase for PQ Matrix Installer.
Handles the installation of system prerequisites.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Local imports
from src.phases.phase_manager import InstallationPhase
from src.utils.logger import get_logger


class PrerequisitesPhase(InstallationPhase):
    """
    Phase for checking and installing system prerequisites.
    """
    
    def __init__(self, config_manager, logger=None):
        """
        Initialize the prerequisites phase.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        super().__init__(config_manager, logger)
        self.name = "Prerequisites"
        self.description = "Check and install system prerequisites"
        self.required = True
    
    def check_prerequisites(self):
        """
        Check if prerequisites for this phase are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # Basic system checks already performed in SystemChecker
        return True
    
    def execute(self):
        """
        Execute the prerequisites installation phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Checking and installing prerequisites...")
        
        # Create installation directory
        install_dir = Path.home() / ".pq-matrix"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Install system packages
        if not self._install_system_packages():
            return False
        
        # Setup Python virtual environment
        if not self._setup_python_venv():
            return False
        
        # Install Python dependencies
        if not self._install_python_deps():
            return False
        
        # Check and configure firewall
        if not self._configure_firewall():
            self.logger.warning("Firewall configuration failed. Continuing anyway.")
        
        return True
    
    def _install_system_packages(self):
        """
        Install required system packages.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Installing required system packages...")
        
        # Define packages based on distribution
        os_type = platform.system()
        if os_type == "Linux":
            try:
                distro_info = platform.freedesktop_os_release()
                distro_id = distro_info.get('ID', '').lower()
                
                if distro_id in ['ubuntu', 'debian']:
                    packages = [
                        'curl', 'gnupg', 'apt-transport-https', 'ca-certificates',
                        'lsb-release', 'python3-pip', 'python3-venv', 'git'
                    ]
                    
                    # Update package list
                    self.logger.info("Updating package list...")
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    
                    # Install packages
                    self.logger.info(f"Installing packages: {', '.join(packages)}")
                    subprocess.run(['sudo', 'apt-get', 'install', '-y'] + packages, check=True)
                    
                    return True
                    
                elif distro_id in ['fedora', 'rhel', 'centos']:
                    packages = [
                        'curl', 'gnupg', 'ca-certificates', 'python3-pip',
                        'python3-virtualenv', 'git'
                    ]
                    
                    # Install packages
                    self.logger.info(f"Installing packages: {', '.join(packages)}")
                    subprocess.run(['sudo', 'dnf', 'install', '-y'] + packages, check=True)
                    
                    return True
                    
                else:
                    self.logger.warning(f"Unsupported Linux distribution: {distro_id}")
                    self.logger.warning("You may need to install required packages manually")
                    return True  # Continue anyway
                    
            except Exception as e:
                self.logger.error(f"Error installing system packages: {str(e)}")
                return False
                
        elif os_type == "Darwin":  # macOS
            try:
                # Check if Homebrew is installed
                if not shutil.which('brew'):
                    self.logger.info("Installing Homebrew...")
                    script_url = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
                    subprocess.run(['/bin/bash', '-c', f'curl -fsSL {script_url} | bash'], check=True)
                
                # Install packages
                packages = ['python@3.10', 'git']
                
                self.logger.info(f"Installing packages with Homebrew: {', '.join(packages)}")
                subprocess.run(['brew', 'install'] + packages, check=True)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error installing system packages on macOS: {str(e)}")
                return False
                
        else:
            self.logger.warning(f"Unsupported operating system: {os_type}")
            self.logger.warning("You may need to install required packages manually")
            return True  # Continue anyway
    
    def _setup_python_venv(self):
        """
        Set up Python virtual environment.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Setting up Python virtual environment...")
        
        try:
            venv_dir = Path.home() / ".pq-matrix" / "venv"
            
            # Create virtual environment if it doesn't exist
            if not venv_dir.exists():
                self.logger.info(f"Creating virtual environment at {venv_dir}")
                subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
            
            # Store venv path in config
            self.config.set('venv_path', str(venv_dir))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up Python virtual environment: {str(e)}")
            return False
    
    def _install_python_deps(self):
        """
        Install Python dependencies.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Installing Python dependencies...")
        
        try:
            venv_dir = Path(self.config.get('venv_path'))
            
            # Determine pip path
            if platform.system() == "Windows":
                pip_path = venv_dir / "Scripts" / "pip"
            else:
                pip_path = venv_dir / "bin" / "pip"
            
            # Upgrade pip
            self.logger.info("Upgrading pip...")
            subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'], check=True)
            
            # Install dependencies from requirements.txt
            script_dir = Path(__file__).resolve().parent.parent.parent
            requirements_file = script_dir / "requirements.txt"
            
            if requirements_file.exists():
                self.logger.info(f"Installing dependencies from {requirements_file}")
                subprocess.run([str(pip_path), 'install', '-r', str(requirements_file)], check=True)
            else:
                # Fallback to installing core dependencies
                self.logger.info("Installing core dependencies...")
                dependencies = [
                    'psutil>=5.9.0',
                    'python-dotenv>=1.0.0',
                    'requests>=2.28.0',
                    'cryptography>=41.0.0',
                    'colorama>=0.4.6',
                    'cloudflare>=2.14.0',
                    'questionary>=2.0.0',
                    'tqdm>=4.66.0',
                    'PyYAML>=6.0.0',
                    'aiohttp>=3.8.0',
                    'schema>=0.7.5'
                ]
                subprocess.run([str(pip_path), 'install'] + dependencies, check=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing Python dependencies: {str(e)}")
            return False
    
    def _configure_firewall(self):
        """
        Configure firewall to allow necessary ports.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Configuring firewall...")
        
        ports = [80, 443, 8448, 3478, 5349]
        
        os_type = platform.system()
        if os_type == "Linux":
            try:
                # Check if ufw is available (Ubuntu/Debian)
                if shutil.which('ufw'):
                    self.logger.info("Configuring UFW firewall...")
                    
                    # Enable UFW if not already enabled
                    status = subprocess.run(['sudo', 'ufw', 'status'], 
                                             capture_output=True, text=True).stdout
                    if 'inactive' in status:
                        self.logger.info("Enabling UFW firewall...")
                        subprocess.run(['sudo', 'ufw', '--force', 'enable'], check=True)
                    
                    # Allow required ports
                    for port in ports:
                        self.logger.info(f"Allowing port {port}...")
                        subprocess.run(['sudo', 'ufw', 'allow', str(port)], check=True)
                    
                    return True
                
                # Check if firewalld is available (Fedora/RHEL/CentOS)
                elif shutil.which('firewall-cmd'):
                    self.logger.info("Configuring firewalld...")
                    
                    # Allow required ports
                    for port in ports:
                        self.logger.info(f"Allowing port {port}...")
                        subprocess.run([
                            'sudo', 'firewall-cmd', '--add-port', f'{port}/tcp', '--permanent'
                        ], check=True)
                    
                    # Reload firewall
                    subprocess.run(['sudo', 'firewall-cmd', '--reload'], check=True)
                    
                    return True
                
                else:
                    self.logger.warning("No supported firewall found. Ports may need to be opened manually.")
                    return True  # Continue anyway
                
            except Exception as e:
                self.logger.error(f"Error configuring firewall: {str(e)}")
                return False
        
        elif os_type == "Darwin":  # macOS
            self.logger.info("Firewall configuration not implemented for macOS.")
            self.logger.info("Please ensure ports 80, 443, 8448, 3478, and 5349 are open.")
            return True
        
        else:
            self.logger.warning(f"Firewall configuration not implemented for {os_type}.")
            return True
    
    def rollback(self):
        """
        Rollback changes made by this phase in case of failure.
        """
        self.logger.warning("Rolling back prerequisite installation...")
        
        # Nothing to rollback for now as we don't want to remove system packages
        # that might be used by other applications
        pass
