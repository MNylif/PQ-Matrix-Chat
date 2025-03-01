#!/usr/bin/env python3
"""
Cloudflare API integration for PQ Matrix Installer.
Handles DNS record management and proxy configuration.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union

import CloudFlare

# Local imports
from src.utils.logger import get_logger


class CloudflareManager:
    """Manages Cloudflare API interactions for DNS and proxy configuration."""
    
    def __init__(self, config_manager, logger=None):
        """
        Initialize the Cloudflare manager.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config = config_manager
        self.logger = logger or get_logger()
        self.cf = None
        self.zone_id = None
        self.domain = self.config.get('matrix_domain', '')
        
        # Initialize Cloudflare API client
        self._init_cloudflare()
    
    def _init_cloudflare(self):
        """
        Initialize the Cloudflare API client.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get Cloudflare credentials
            api_token = self.config.get('cloudflare.api_token', '')
            email = self.config.get('cloudflare.email', '')
            
            if not api_token:
                self.logger.error("Cloudflare API token not found in configuration")
                return False
            
            # Initialize Cloudflare client
            if email:
                self.cf = CloudFlare.CloudFlare(email=email, token=api_token)
            else:
                self.cf = CloudFlare.CloudFlare(token=api_token)
            
            # Get zone ID for the domain
            if self.domain:
                self._get_zone_id()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Cloudflare API client: {str(e)}")
            return False
    
    def _get_zone_id(self):
        """
        Get the zone ID for the configured domain.
        
        Returns:
            str: Zone ID or None if not found
        """
        try:
            zones = self.cf.zones.get(params={'name': self.domain})
            
            if not zones:
                # Try with parent domain
                parent_domain = '.'.join(self.domain.split('.')[-2:])
                zones = self.cf.zones.get(params={'name': parent_domain})
            
            if zones:
                self.zone_id = zones[0]['id']
                self.logger.info(f"Found Cloudflare zone ID: {self.zone_id}")
                return self.zone_id
            else:
                self.logger.error(f"No Cloudflare zone found for domain: {self.domain}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting Cloudflare zone ID: {str(e)}")
            return None
    
    def get_dns_records(self, record_type=None, name=None) -> List[Dict[str, Any]]:
        """
        Get DNS records for the configured domain.
        
        Args:
            record_type (str, optional): Record type to filter by (e.g., 'A', 'CNAME')
            name (str, optional): Record name to filter by
            
        Returns:
            list: List of DNS records
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return []
        
        try:
            params = {}
            if record_type:
                params['type'] = record_type
            if name:
                params['name'] = name
            
            records = self.cf.zones.dns_records.get(self.zone_id, params=params)
            return records
            
        except Exception as e:
            self.logger.error(f"Error getting DNS records: {str(e)}")
            return []
    
    def create_dns_record(self, record_type: str, name: str, content: str, 
                          ttl: int = 1, proxied: bool = False) -> Optional[Dict[str, Any]]:
        """
        Create a DNS record.
        
        Args:
            record_type (str): Record type (e.g., 'A', 'CNAME')
            name (str): Record name
            content (str): Record content (e.g., IP address for A records)
            ttl (int): Time to live in seconds (1 = automatic)
            proxied (bool): Whether to proxy the record through Cloudflare
            
        Returns:
            dict: Created record or None if failed
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return None
        
        try:
            # Check if record already exists
            existing_records = self.get_dns_records(record_type, name)
            if existing_records:
                self.logger.info(f"DNS record {name} already exists, updating instead")
                return self.update_dns_record(
                    existing_records[0]['id'], record_type, name, content, ttl, proxied
                )
            
            # Create new record
            record = {
                'type': record_type,
                'name': name,
                'content': content,
                'ttl': ttl,
                'proxied': proxied
            }
            
            self.logger.info(f"Creating DNS record: {name} ({record_type})")
            result = self.cf.zones.dns_records.post(self.zone_id, data=record)
            
            if result:
                self.logger.info(f"DNS record created successfully: {name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating DNS record: {str(e)}")
            return None
    
    def update_dns_record(self, record_id: str, record_type: str, name: str, 
                          content: str, ttl: int = 1, proxied: bool = False) -> Optional[Dict[str, Any]]:
        """
        Update a DNS record.
        
        Args:
            record_id (str): Record ID
            record_type (str): Record type (e.g., 'A', 'CNAME')
            name (str): Record name
            content (str): Record content (e.g., IP address for A records)
            ttl (int): Time to live in seconds (1 = automatic)
            proxied (bool): Whether to proxy the record through Cloudflare
            
        Returns:
            dict: Updated record or None if failed
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return None
        
        try:
            record = {
                'type': record_type,
                'name': name,
                'content': content,
                'ttl': ttl,
                'proxied': proxied
            }
            
            self.logger.info(f"Updating DNS record: {name} ({record_type})")
            result = self.cf.zones.dns_records.put(self.zone_id, record_id, data=record)
            
            if result:
                self.logger.info(f"DNS record updated successfully: {name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating DNS record: {str(e)}")
            return None
    
    def delete_dns_record(self, record_id: str) -> bool:
        """
        Delete a DNS record.
        
        Args:
            record_id (str): Record ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return False
        
        try:
            self.logger.info(f"Deleting DNS record: {record_id}")
            self.cf.zones.dns_records.delete(self.zone_id, record_id)
            self.logger.info("DNS record deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting DNS record: {str(e)}")
            return False
    
    def setup_matrix_dns(self, server_ip: str) -> bool:
        """
        Set up DNS records for a Matrix server.
        
        Args:
            server_ip (str): Server IP address
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return False
        
        try:
            # Main domain A record
            main_domain = self.domain
            self.create_dns_record('A', main_domain, server_ip, proxied=True)
            
            # Matrix server domain (if different from main domain)
            matrix_server = self.config.get('matrix_server_name', self.domain)
            if matrix_server != main_domain:
                self.create_dns_record('A', matrix_server, server_ip, proxied=True)
            
            # Element client subdomain
            element_domain = f"element.{main_domain}"
            self.create_dns_record('A', element_domain, server_ip, proxied=True)
            
            # SRV records for Matrix federation
            srv_content = f"0 10 8448 {matrix_server}"
            self.create_dns_record('SRV', f"_matrix._tcp.{main_domain}", srv_content, proxied=False)
            
            # TXT record for server delegation
            if matrix_server != main_domain:
                self.create_dns_record('TXT', f"_matrix.{main_domain}", f"v=matrix;server={matrix_server}", proxied=False)
            
            self.logger.info("Matrix DNS setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up Matrix DNS: {str(e)}")
            return False
    
    def configure_page_rules(self) -> bool:
        """
        Configure Cloudflare page rules for Matrix server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return False
        
        try:
            matrix_server = self.config.get('matrix_server_name', self.domain)
            
            # Create page rule for /.well-known paths (no caching)
            well_known_rule = {
                'targets': [
                    {
                        'target': 'url',
                        'constraint': {
                            'operator': 'matches',
                            'value': f"*{matrix_server}/.well-known/*"
                        }
                    }
                ],
                'actions': [
                    {
                        'id': 'cache_level',
                        'value': 'bypass'
                    },
                    {
                        'id': 'browser_cache_ttl',
                        'value': '0'
                    }
                ],
                'status': 'active',
                'priority': 1
            }
            
            self.logger.info("Creating page rule for /.well-known paths")
            self.cf.zones.pagerules.post(self.zone_id, data=well_known_rule)
            
            # Create page rule for /_matrix paths (no caching)
            matrix_rule = {
                'targets': [
                    {
                        'target': 'url',
                        'constraint': {
                            'operator': 'matches',
                            'value': f"*{matrix_server}/_matrix/*"
                        }
                    }
                ],
                'actions': [
                    {
                        'id': 'cache_level',
                        'value': 'bypass'
                    },
                    {
                        'id': 'browser_cache_ttl',
                        'value': '0'
                    }
                ],
                'status': 'active',
                'priority': 2
            }
            
            self.logger.info("Creating page rule for /_matrix paths")
            self.cf.zones.pagerules.post(self.zone_id, data=matrix_rule)
            
            self.logger.info("Cloudflare page rules configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring page rules: {str(e)}")
            return False
    
    def configure_firewall_rules(self) -> bool:
        """
        Configure Cloudflare firewall rules for Matrix server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cf or not self.zone_id:
            self.logger.error("Cloudflare client not initialized or zone ID not found")
            return False
        
        try:
            # Block high-risk countries (optional)
            if self.config.get('cloudflare.block_high_risk_countries', False):
                high_risk_rule = {
                    'filter': {
                        'expression': "ip.geoip.country in {\"CN\" \"RU\" \"KP\" \"IR\"}",
                        'paused': False
                    },
                    'action': 'block',
                    'description': 'Block high-risk countries'
                }
                
                self.logger.info("Creating firewall rule to block high-risk countries")
                self.cf.zones.firewall.rules.post(self.zone_id, data=high_risk_rule)
            
            # Rate limiting rule for _matrix endpoints
            matrix_rate_limit = {
                'description': 'Rate limit Matrix API',
                'expression': "starts_with(http.request.uri.path, \"/_matrix\")",
                'mitigation_timeout': 600,
                'period': 60,
                'requests_per_period': 300,
                'mitigation_expression': "true"
            }
            
            self.logger.info("Creating rate limiting rule for Matrix API")
            self.cf.zones.rate_limits.post(self.zone_id, data=matrix_rate_limit)
            
            self.logger.info("Cloudflare firewall rules configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring firewall rules: {str(e)}")
            return False
