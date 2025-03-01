#!/usr/bin/env python3
"""
Docker Phase for PQ Matrix Installer.
Handles Docker installation and setup.
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


class DockerPhase(InstallationPhase):
    """
    Phase for installing and configuring Docker and Docker Compose.
    """
    
    def __init__(self, config_manager, logger=None):
        """
        Initialize the Docker installation phase.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        super().__init__(config_manager, logger)
        self.name = "Docker Setup"
        self.description = "Install and configure Docker and Docker Compose"
        self.required = True
        self.installed_docker = False
    
    def check_prerequisites(self):
        """
        Check if prerequisites for this phase are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # Check if Docker is already installed
        if shutil.which("docker"):
            self.logger.info("Docker is already installed")
            
            # Check if Docker is running
            try:
                subprocess.run(
                    ["docker", "info"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                self.logger.info("Docker daemon is running")
                return True
            except subprocess.CalledProcessError:
                self.logger.warning("Docker is installed but the daemon might not be running")
                return True
        else:
            self.logger.info("Docker is not installed")
            return True  # We'll install it
    
    def execute(self):
        """
        Execute the Docker installation phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Setting up Docker...")
        
        # Install Docker if not already installed
        if not shutil.which("docker"):
            if not self._install_docker():
                return False
            self.installed_docker = True
        
        # Setup Docker Compose
        if not self._setup_docker_compose():
            return False
        
        # Configure Docker for Matrix
        if not self._configure_docker():
            return False
        
        return True
    
    def _install_docker(self):
        """
        Install Docker.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Installing Docker...")
        
        os_type = platform.system()
        if os_type == "Linux":
            try:
                distro_info = platform.freedesktop_os_release()
                distro_id = distro_info.get('ID', '').lower()
                
                if distro_id in ['ubuntu', 'debian']:
                    # Update package list
                    self.logger.info("Updating package list...")
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    
                    # Install dependencies
                    self.logger.info("Installing dependencies...")
                    deps = [
                        'apt-transport-https', 'ca-certificates', 'curl',
                        'gnupg', 'lsb-release'
                    ]
                    subprocess.run(['sudo', 'apt-get', 'install', '-y'] + deps, check=True)
                    
                    # Add Docker's official GPG key
                    self.logger.info("Adding Docker GPG key...")
                    keyring_path = "/etc/apt/keyrings"
                    subprocess.run(['sudo', 'mkdir', '-p', keyring_path], check=True)
                    
                    # Download and add GPG key
                    cmd = 'curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg'
                    if distro_id == 'ubuntu':
                        cmd = 'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg'
                    
                    subprocess.run(cmd, shell=True, check=True)
                    subprocess.run(['sudo', 'chmod', 'a+r', '/etc/apt/keyrings/docker.gpg'], check=True)
                    
                    # Add the repository to sources
                    self.logger.info("Adding Docker repository...")
                    arch = subprocess.check_output(['dpkg', '--print-architecture']).decode('utf-8').strip()
                    
                    repo_content = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/{distro_id} {distro_info.get('VERSION_CODENAME')} stable"
                    with open('/tmp/docker.list', 'w') as f:
                        f.write(repo_content)
                    
                    subprocess.run(['sudo', 'mv', '/tmp/docker.list', '/etc/apt/sources.list.d/docker.list'], check=True)
                    
                    # Update package list again
                    self.logger.info("Updating package list...")
                    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                    
                    # Install Docker
                    self.logger.info("Installing Docker...")
                    docker_pkgs = [
                        'docker-ce', 'docker-ce-cli', 'containerd.io',
                        'docker-buildx-plugin', 'docker-compose-plugin'
                    ]
                    subprocess.run(['sudo', 'apt-get', 'install', '-y'] + docker_pkgs, check=True)
                    
                    # Add current user to the docker group
                    self.logger.info("Adding current user to docker group...")
                    username = os.environ.get('USER', os.environ.get('USERNAME'))
                    subprocess.run(['sudo', 'usermod', '-aG', 'docker', username], check=True)
                    
                elif distro_id in ['fedora', 'rhel', 'centos']:
                    # Install dependencies
                    self.logger.info("Installing dependencies...")
                    subprocess.run(['sudo', 'dnf', 'install', '-y', 'dnf-plugins-core'], check=True)
                    
                    # Add Docker repository
                    self.logger.info("Adding Docker repository...")
                    repo_url = 'https://download.docker.com/linux/fedora/docker-ce.repo'
                    if distro_id in ['rhel', 'centos']:
                        repo_url = 'https://download.docker.com/linux/centos/docker-ce.repo'
                    
                    subprocess.run(['sudo', 'dnf', 'config-manager', '--add-repo', repo_url], check=True)
                    
                    # Install Docker
                    self.logger.info("Installing Docker...")
                    docker_pkgs = ['docker-ce', 'docker-ce-cli', 'containerd.io']
                    subprocess.run(['sudo', 'dnf', 'install', '-y'] + docker_pkgs, check=True)
                    
                    # Add current user to the docker group
                    self.logger.info("Adding current user to docker group...")
                    username = os.environ.get('USER', os.environ.get('USERNAME'))
                    subprocess.run(['sudo', 'usermod', '-aG', 'docker', username], check=True)
                    
                    # Start Docker
                    self.logger.info("Starting Docker service...")
                    subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                    subprocess.run(['sudo', 'systemctl', 'enable', 'docker'], check=True)
                    
                else:
                    self.logger.error(f"Unsupported Linux distribution: {distro_id}")
                    self.logger.error("Please install Docker manually: https://docs.docker.com/engine/install/")
                    return False
                
                # Verify Docker installation
                self.logger.info("Verifying Docker installation...")
                subprocess.run(['docker', '--version'], check=True)
                
                self.logger.info("""
Docker has been installed successfully, but you need to log out and log back in
for the group membership to take effect. If you don't want to log out, run:
    
    newgrp docker
    
to update your current shell session.
""")
                
                return True
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error installing Docker: {str(e)}")
                return False
                
        elif os_type == "Darwin":  # macOS
            self.logger.info("""
On macOS, Docker should be installed using Docker Desktop:
1. Visit https://docs.docker.com/desktop/install/mac-install/
2. Download and install Docker Desktop for Mac
3. Once installed, start Docker Desktop and wait for it to finish starting up
4. Run this installer again
""")
            return False
            
        else:
            self.logger.error(f"Unsupported operating system: {os_type}")
            return False
    
    def _setup_docker_compose(self):
        """
        Set up Docker Compose.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Setting up Docker Compose...")
        
        try:
            # Check if Docker Compose is already installed
            result = subprocess.run(
                ["docker", "compose", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                self.logger.info(f"Docker Compose is already installed: {result.stdout.decode('utf-8').strip()}")
                return True
            
            # Check if docker-compose (v1) is installed
            docker_compose_v1 = shutil.which("docker-compose")
            if docker_compose_v1:
                self.logger.info("Docker Compose v1 is installed. Recommending upgrade to v2...")
                
            # For Linux, install Docker Compose plugin
            os_type = platform.system()
            if os_type == "Linux":
                # Docker Compose comes with Docker CE installation now
                # Check if it's available as a plugin
                subprocess.run(["docker", "compose", "version"], check=True)
                self.logger.info("Docker Compose plugin is installed")
                return True
                
            elif os_type == "Darwin":  # macOS
                # Docker Compose comes with Docker Desktop for Mac
                self.logger.info("Docker Compose should be installed with Docker Desktop for Mac")
                self.logger.info("Please make sure Docker Desktop is installed and running")
                
                # Check if docker command is available before proceeding
                if not shutil.which("docker"):
                    self.logger.error("Docker command not found. Please install Docker Desktop for Mac")
                    return False
                
                # Try running docker compose to see if it's available
                try:
                    subprocess.run(["docker", "compose", "version"], check=True)
                    self.logger.info("Docker Compose is installed")
                    return True
                except subprocess.CalledProcessError:
                    self.logger.error("Docker Compose is not available. Please install Docker Desktop for Mac")
                    return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error setting up Docker Compose: {str(e)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error setting up Docker Compose: {str(e)}")
            return False
    
    def _configure_docker(self):
        """
        Configure Docker for Matrix server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Configuring Docker for Matrix server...")
        
        try:
            # Create Docker network for Matrix
            self.logger.info("Creating Docker network for Matrix...")
            network_name = "matrix-network"
            
            # Check if network already exists
            networks = subprocess.check_output(["docker", "network", "ls", "--format", "{{.Name}}"]).decode('utf-8').splitlines()
            
            if network_name not in networks:
                subprocess.run(["docker", "network", "create", network_name], check=True)
                self.logger.info(f"Created Docker network: {network_name}")
            else:
                self.logger.info(f"Docker network {network_name} already exists")
            
            # Create Docker volumes for Matrix data
            self.logger.info("Creating Docker volumes for Matrix data...")
            volumes = [
                "matrix-conduit-data",
                "matrix-postgres-data",
                "matrix-keys",
                "matrix-media"
            ]
            
            existing_volumes = subprocess.check_output(["docker", "volume", "ls", "--format", "{{.Name}}"]).decode('utf-8').splitlines()
            
            for volume in volumes:
                if volume not in existing_volumes:
                    subprocess.run(["docker", "volume", "create", volume], check=True)
                    self.logger.info(f"Created Docker volume: {volume}")
                else:
                    self.logger.info(f"Docker volume {volume} already exists")
            
            # Set Docker daemon configuration for security
            os_type = platform.system()
            if os_type == "Linux":
                daemon_config = {
                    "live-restore": True,
                    "log-driver": "json-file",
                    "log-opts": {
                        "max-size": "10m",
                        "max-file": "3"
                    },
                    "userns-remap": "default"
                }
                
                import json
                daemon_json = json.dumps(daemon_config, indent=2)
                
                # Write to temporary file
                with open('/tmp/daemon.json', 'w') as f:
                    f.write(daemon_json)
                
                try:
                    # Check if /etc/docker exists
                    subprocess.run(['sudo', 'mkdir', '-p', '/etc/docker'], check=True)
                    
                    # Move the file to /etc/docker/daemon.json
                    subprocess.run(['sudo', 'mv', '/tmp/daemon.json', '/etc/docker/daemon.json'], check=True)
                    
                    # Restart Docker daemon
                    self.logger.info("Restarting Docker daemon...")
                    subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], check=True)
                    
                    # Wait for Docker to be available again
                    import time
                    max_attempts = 10
                    attempts = 0
                    while attempts < max_attempts:
                        try:
                            subprocess.run(["docker", "info"], 
                                          stdout=subprocess.DEVNULL, 
                                          stderr=subprocess.DEVNULL, 
                                          check=True)
                            break
                        except subprocess.CalledProcessError:
                            attempts += 1
                            self.logger.info(f"Waiting for Docker daemon to restart... ({attempts}/{max_attempts})")
                            time.sleep(2)
                    
                    if attempts == max_attempts:
                        self.logger.warning("Docker daemon did not restart properly")
                        return False
                    
                except Exception as e:
                    self.logger.warning(f"Could not configure Docker daemon: {str(e)}")
                    self.logger.warning("This is non-critical, continuing with installation")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error configuring Docker: {str(e)}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error configuring Docker: {str(e)}")
            return False
    
    def rollback(self):
        """
        Rollback Docker installation if failed.
        """
        # We don't want to remove Docker if it was already installed
        if not self.installed_docker:
            self.logger.info("Nothing to rollback for Docker phase (Docker was already installed)")
            return
        
        self.logger.warning("Rolling back Docker installation...")
        
        try:
            os_type = platform.system()
            if os_type == "Linux":
                distro_info = platform.freedesktop_os_release()
                distro_id = distro_info.get('ID', '').lower()
                
                if distro_id in ['ubuntu', 'debian']:
                    self.logger.info("Removing Docker packages...")
                    docker_pkgs = [
                        'docker-ce', 'docker-ce-cli', 'containerd.io',
                        'docker-buildx-plugin', 'docker-compose-plugin'
                    ]
                    subprocess.run(['sudo', 'apt-get', 'remove', '-y'] + docker_pkgs)
                    
                    # Remove Docker repository
                    self.logger.info("Removing Docker repository...")
                    subprocess.run(['sudo', 'rm', '-f', '/etc/apt/sources.list.d/docker.list'])
                    
                elif distro_id in ['fedora', 'rhel', 'centos']:
                    self.logger.info("Removing Docker packages...")
                    docker_pkgs = ['docker-ce', 'docker-ce-cli', 'containerd.io']
                    subprocess.run(['sudo', 'dnf', 'remove', '-y'] + docker_pkgs)
            
        except Exception as e:
            self.logger.error(f"Error rolling back Docker installation: {str(e)}")
