#!/usr/bin/env python3
"""
Network Phase for PQ Matrix Installer.
Configures networking, DNS, and Cloudflare integration.
"""

import os
import sys
import subprocess
import socket
import requests
import logging
from pathlib import Path

# Local imports
from src.phases.phase_manager import InstallationPhase
from src.utils.logger import get_logger, AuditLogger
from src.cloudflare.cloudflare_api import CloudflareManager


class NetworkPhase(InstallationPhase):
    """
    Phase for configuring network settings, DNS, and Cloudflare integration.
    """
    
    def __init__(self, config_manager, logger=None):
        """
        Initialize the network configuration phase.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        super().__init__(config_manager, logger)
        self.name = "Network Setup"
        self.description = "Configure network, DNS, and Cloudflare integration"
        self.required = True
        self.audit_logger = AuditLogger()
        self.server_ip = None
    
    def check_prerequisites(self):
        """
        Check if prerequisites for this phase are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # Check if domain is set in config
        if not self.config.get('matrix_domain'):
            self.logger.error("Matrix domain not set in configuration")
            return False
        
        # Check if server_name is set in config
        if not self.config.get('matrix_server_name'):
            self.logger.error("Matrix server name not set in configuration")
            return False
        
        # Check internet connectivity
        try:
            requests.get('https://google.com', timeout=5)
            self.logger.info("Internet connectivity verified")
            return True
        except requests.RequestException:
            self.logger.error("No internet connection available")
            return False
    
    def execute(self):
        """
        Execute the network configuration phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Configuring network...")
        
        # Get server IP
        if not self._get_server_ip():
            return False
        
        # Configure Cloudflare if enabled
        if self.config.get('cloudflare'):
            if not self._configure_cloudflare():
                self.logger.warning("Cloudflare configuration failed, continuing without it")
        
        # Configure local network settings
        if not self._configure_network_settings():
            return False
        
        return True
    
    def _get_server_ip(self):
        """
        Get the server's public IP address.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Detecting server IP address...")
        
        try:
            # Try multiple services to get IP
            ip_services = [
                'https://api.ipify.org',
                'https://ifconfig.me/ip',
                'https://icanhazip.com'
            ]
            
            for service in ip_services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if self._validate_ip(ip):
                            self.server_ip = ip
                            self.logger.info(f"Detected server IP address: {self.server_ip}")
                            
                            # Store IP in config
                            self.config.set('server_ip', self.server_ip)
                            self.audit_logger.log(f"Detected server IP: {self.server_ip}")
                            
                            return True
                except requests.RequestException:
                    continue
            
            self.logger.error("Failed to detect server IP address automatically")
            
            # Ask user to manually input IP
            import questionary
            self.server_ip = questionary.text(
                "Please enter your server's public IP address:",
                validate=self._validate_ip
            ).ask()
            
            if self.server_ip:
                self.logger.info(f"Using manually entered IP address: {self.server_ip}")
                self.config.set('server_ip', self.server_ip)
                self.audit_logger.log(f"Manually entered server IP: {self.server_ip}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error detecting server IP address: {str(e)}")
            return False
    
    def _validate_ip(self, ip):
        """
        Validate an IP address.
        
        Args:
            ip (str): IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            parts = ip.split('.')
            
            # Check if IPv4 format (4 parts)
            if len(parts) != 4:
                return False
            
            # Check each octet is a number between 0-255
            for part in parts:
                if not part.isdigit() or int(part) < 0 or int(part) > 255:
                    return False
            
            return True
        except Exception:
            return False
    
    def _configure_cloudflare(self):
        """
        Configure Cloudflare DNS and proxy settings.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Configuring Cloudflare integration...")
        
        try:
            # Initialize Cloudflare manager
            cf_manager = CloudflareManager(self.config, self.logger)
            
            # Set up DNS records for Matrix server
            if not cf_manager.setup_matrix_dns(self.server_ip):
                self.logger.error("Failed to set up Cloudflare DNS records")
                return False
            
            # Configure page rules
            if not cf_manager.configure_page_rules():
                self.logger.warning("Failed to configure Cloudflare page rules, continuing anyway")
            
            # Configure firewall rules
            if not cf_manager.configure_firewall_rules():
                self.logger.warning("Failed to configure Cloudflare firewall rules, continuing anyway")
            
            self.logger.info("Cloudflare configuration completed successfully")
            self.audit_logger.log("Configured Cloudflare DNS and proxy for Matrix server")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring Cloudflare: {str(e)}")
            return False
    
    def _configure_network_settings(self):
        """
        Configure local network settings.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Configuring local network settings...")
        
        try:
            # Create local hostname entry
            matrix_domain = self.config.get('matrix_domain')
            matrix_server = self.config.get('matrix_server_name')
            
            # Check if domain is in hosts file
            hosts_file = "/etc/hosts"
            if os.path.exists(hosts_file):
                with open(hosts_file, 'r') as f:
                    hosts_content = f.read()
                
                # Check if domain is already in hosts file
                if matrix_domain in hosts_content and matrix_server in hosts_content:
                    self.logger.info(f"Domain {matrix_domain} already in hosts file")
                else:
                    # Add domain to hosts file
                    self.logger.info(f"Adding {matrix_domain} to hosts file")
                    
                    hosts_entry = f"\n# PQ Matrix Server domains\n127.0.0.1 {matrix_domain} {matrix_server}\n"
                    
                    # Write to temp file
                    with open('/tmp/hosts.new', 'w') as f:
                        f.write(hosts_content + hosts_entry)
                    
                    # Move to hosts file
                    try:
                        subprocess.run(['sudo', 'mv', '/tmp/hosts.new', hosts_file], check=True)
                        self.logger.info(f"Added {matrix_domain} to hosts file")
                    except subprocess.CalledProcessError:
                        self.logger.warning("Failed to update hosts file, continuing anyway")
            
            # Test connectivity to domain
            self.logger.info(f"Testing connectivity to {matrix_domain}...")
            try:
                # Check if DNS resolves (try multiple times because DNS propagation takes time)
                import time
                resolved = False
                for i in range(3):
                    try:
                        ip = socket.gethostbyname(matrix_domain)
                        self.logger.info(f"Domain {matrix_domain} resolves to {ip}")
                        resolved = True
                        break
                    except socket.gaierror:
                        self.logger.info(f"Domain {matrix_domain} not yet resolving, retrying in 5 seconds...")
                        time.sleep(5)
                
                if not resolved:
                    self.logger.warning(f"Domain {matrix_domain} does not resolve to an IP address")
                    self.logger.warning("DNS propagation may take some time, continuing anyway")
            
            except Exception as e:
                self.logger.warning(f"Error testing connectivity: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring network settings: {str(e)}")
            return False
    
    def rollback(self):
        """
        Rollback network configuration if failed.
        """
        self.logger.warning("Rolling back network configuration...")
        
        try:
            # If Cloudflare was configured, try to remove DNS records
            if self.config.get('cloudflare'):
                self.logger.info("Removing Cloudflare DNS records...")
                
                try:
                    cf_manager = CloudflareManager(self.config, self.logger)
                    
                    # Get DNS records for the domain
                    records = cf_manager.get_dns_records()
                    
                    # Delete records created for Matrix
                    matrix_domain = self.config.get('matrix_domain')
                    matrix_server = self.config.get('matrix_server_name')
                    
                    for record in records:
                        name = record.get('name', '')
                        if name == matrix_domain or name == matrix_server or \
                           name.startswith(f"element.{matrix_domain}") or \
                           name.startswith(f"_matrix._tcp.{matrix_domain}"):
                            cf_manager.delete_dns_record(record['id'])
                            self.logger.info(f"Deleted DNS record: {name}")
                    
                except Exception as e:
                    self.logger.error(f"Error removing Cloudflare DNS records: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error rolling back network configuration: {str(e)}")
