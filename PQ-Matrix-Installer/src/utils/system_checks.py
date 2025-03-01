#!/usr/bin/env python3
"""
System checks module for PQ Matrix Installer.
Performs pre-flight checks to ensure the system meets requirements.
"""

import os
import sys
import platform
import shutil
import subprocess
import logging
import tempfile
from pathlib import Path

import psutil

# Local imports
from src.utils.logger import get_logger


class SystemChecker:
    """System requirements checker for PQ Matrix Installer."""
    
    def __init__(self, logger=None):
        """
        Initialize the system checker.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger()
        
        # Minimum requirements
        self.min_cpu_cores = 2
        self.min_ram_gb = 2
        self.min_disk_space_gb = 20
        self.required_ports = [80, 443, 3478, 5349]
        
        # Optimization level requirements
        self.optimization_requirements = {
            'low': {
                'ram_gb': 2,  # 2GB RAM
                'cpu_cores': 2,
                'disk_space_gb': 20
            },
            'standard': {
                'ram_gb': 4,  # 4GB RAM
                'cpu_cores': 4,
                'disk_space_gb': 30
            },
            'high': {
                'ram_gb': 8,  # 8GB RAM
                'cpu_cores': 8,
                'disk_space_gb': 50
            }
        }
    
    def check_system_requirements(self):
        """
        Perform all system requirement checks.
        
        Returns:
            bool: True if all checks pass, False otherwise
        """
        self.logger.info("Performing system requirement checks...")
        
        checks = [
            self._check_os_compatibility(),
            self._check_cpu(),
            self._check_memory(),
            self._check_disk_space(),
            self._check_python_version(),
            self._check_internet_connection(),
            self._check_docker(),
            self._check_port_availability()
        ]
        
        if all(checks):
            self.logger.info("✅ All system requirement checks passed!")
            return True
        else:
            self.logger.warning("❌ Some system requirement checks failed.")
            return False
    
    def determine_optimization_level(self):
        """
        Determine the appropriate optimization level based on system resources.
        
        Returns:
            str: Optimization level ('low', 'standard', or 'high')
        """
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
        
        if ram_gb >= self.optimization_requirements['high']['ram_gb'] and \
           cpu_cores >= self.optimization_requirements['high']['cpu_cores']:
            return 'high'
        elif ram_gb >= self.optimization_requirements['standard']['ram_gb'] and \
             cpu_cores >= self.optimization_requirements['standard']['cpu_cores']:
            return 'standard'
        else:
            return 'low'
    
    def _check_os_compatibility(self):
        """
        Check if the current OS is compatible.
        
        Returns:
            bool: True if compatible, False otherwise
        """
        os_type = platform.system()
        
        if os_type == "Linux":
            self.logger.info("✅ Operating System: Linux detected")
            
            # Check if it's a supported distribution
            try:
                distro_info = platform.freedesktop_os_release()
                distro_name = distro_info.get('NAME', '')
                distro_version = distro_info.get('VERSION_ID', '')
                
                supported_distros = [
                    ('Ubuntu', '20.04'),
                    ('Ubuntu', '22.04'),
                    ('Debian', '11'),
                    ('Debian', '12')
                ]
                
                for supported_name, supported_version in supported_distros:
                    if supported_name in distro_name and distro_version >= supported_version:
                        self.logger.info(f"✅ Distribution: {distro_name} {distro_version} is supported")
                        return True
                
                self.logger.warning(f"⚠️ Distribution: {distro_name} {distro_version} is not officially supported")
                return True  # Still return True as it might work
                
            except Exception:
                self.logger.warning("⚠️ Could not determine Linux distribution")
                return True  # Assume it's compatible
                
        elif os_type == "Darwin":  # macOS
            self.logger.warning("⚠️ Operating System: macOS detected. This is supported for development only.")
            return True
            
        elif os_type == "Windows":
            self.logger.error("❌ Operating System: Windows is not supported for production use")
            return False
            
        else:
            self.logger.error(f"❌ Operating System: Unknown OS {os_type}")
            return False
    
    def _check_cpu(self):
        """
        Check if the CPU meets requirements.
        
        Returns:
            bool: True if requirements are met, False otherwise
        """
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
        
        if cpu_cores >= self.min_cpu_cores:
            self.logger.info(f"✅ CPU: {cpu_cores} cores available (minimum: {self.min_cpu_cores})")
            return True
        else:
            self.logger.error(f"❌ CPU: Only {cpu_cores} cores available. {self.min_cpu_cores}+ cores required.")
            return False
    
    def _check_memory(self):
        """
        Check if the system has enough memory.
        
        Returns:
            bool: True if requirements are met, False otherwise
        """
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        
        if ram_gb >= self.min_ram_gb:
            self.logger.info(f"✅ Memory: {ram_gb:.1f} GB available (minimum: {self.min_ram_gb} GB)")
            return True
        else:
            self.logger.error(f"❌ Memory: Only {ram_gb:.1f} GB available. {self.min_ram_gb}+ GB required.")
            return False
    
    def _check_disk_space(self):
        """
        Check if there's enough disk space available.
        
        Returns:
            bool: True if requirements are met, False otherwise
        """
        # Check space in home directory or current directory
        home_dir = str(Path.home())
        disk_usage = psutil.disk_usage(home_dir)
        free_space_gb = disk_usage.free / (1024 ** 3)
        
        if free_space_gb >= self.min_disk_space_gb:
            self.logger.info(f"✅ Disk: {free_space_gb:.1f} GB free (minimum: {self.min_disk_space_gb} GB)")
            return True
        else:
            self.logger.error(f"❌ Disk: Only {free_space_gb:.1f} GB free. {self.min_disk_space_gb}+ GB required.")
            return False
    
    def _check_python_version(self):
        """
        Check if the Python version is adequate.
        
        Returns:
            bool: True if requirements are met, False otherwise
        """
        major, minor, _ = sys.version_info[:3]
        
        if major >= 3 and minor >= 8:
            self.logger.info(f"✅ Python: {sys.version.split()[0]} (minimum: 3.8)")
            return True
        else:
            self.logger.error(f"❌ Python: {sys.version.split()[0]} is too old. Python 3.8+ required.")
            return False
    
    def _check_internet_connection(self):
        """
        Check if there's an internet connection.
        
        Returns:
            bool: True if internet connection exists, False otherwise
        """
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self.logger.info("✅ Network: Internet connection available")
            return True
        except (socket.timeout, socket.error):
            self.logger.error("❌ Network: No internet connection")
            return False
    
    def _check_docker(self):
        """
        Check if Docker is installed or can be installed.
        
        Returns:
            bool: True if Docker is available or can be installed, False otherwise
        """
        if shutil.which("docker"):
            self.logger.info("✅ Docker: Already installed")
            
            # Check if current user can run docker without sudo
            try:
                subprocess.check_call(
                    ["docker", "info"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.logger.info("✅ Docker: User has permission to run Docker")
            except subprocess.CalledProcessError:
                self.logger.warning("⚠️ Docker: User may not have permission to run Docker")
                self.logger.warning("You may need to add your user to the docker group:")
                self.logger.warning("    sudo usermod -aG docker $USER")
                self.logger.warning("Then log out and log back in")
            
            return True
        else:
            self.logger.warning("⚠️ Docker: Not installed")
            self.logger.warning("Docker will be installed during the installation process")
            
            # Check if we can install Docker
            if platform.system() == "Linux":
                # Check if apt-get is available (Debian-based)
                if shutil.which("apt-get"):
                    return True
                # Check if yum is available (Red Hat-based)
                elif shutil.which("yum"):
                    return True
                else:
                    self.logger.error("❌ Docker: Cannot automatically install Docker on this system")
                    self.logger.error("Please install Docker manually before continuing")
                    return False
            else:
                self.logger.error("❌ Docker: Cannot automatically install Docker on this system")
                self.logger.error("Please install Docker manually before continuing")
                return False
    
    def _check_port_availability(self):
        """
        Check if required ports are available.
        
        Returns:
            bool: True if all required ports are available, False otherwise
        """
        unavailable_ports = []
        
        for port in self.required_ports:
            if self._is_port_in_use(port):
                unavailable_ports.append(port)
        
        if not unavailable_ports:
            self.logger.info(f"✅ Ports: All required ports are available: {self.required_ports}")
            return True
        else:
            self.logger.error(f"❌ Ports: Some required ports are in use: {unavailable_ports}")
            return False
    
    def _is_port_in_use(self, port):
        """
        Check if a port is in use.
        
        Args:
            port (int): Port number to check
            
        Returns:
            bool: True if port is in use, False otherwise
        """
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
