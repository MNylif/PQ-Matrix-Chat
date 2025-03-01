#!/usr/bin/env python3
"""
Configuration manager for the PQ Matrix Installer.
Handles loading, storing, and validating configuration options.
"""

import os
import json
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv
import questionary
from schema import Schema, And, Use, Optional, Or, SchemaError

# Local imports
from src.utils.logger import get_logger


class ConfigManager:
    """Configuration manager for PQ Matrix Installer."""
    
    def __init__(self, args, logger=None):
        """
        Initialize the configuration manager.
        
        Args:
            args: Command line arguments
            logger: Logger instance
        """
        self.logger = logger or get_logger()
        self.args = args
        self.config = {}
        self.config_dir = Path.home() / ".pq-matrix"
        self.config_file = self.config_dir / "config.yml"
        self.env_file = self.config_dir / ".env"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or initialize new one
        self._load_config()
        
        # Validate the configuration
        if not self._validate_config():
            if not args.non_interactive:
                self._prompt_for_config()
            else:
                self.logger.error("Configuration is invalid and non-interactive mode is enabled")
                self.logger.error("Please provide a valid config file with --config")
                raise ValueError("Invalid configuration in non-interactive mode")
    
    def _load_config(self):
        """
        Load configuration from file, environment, or command line arguments.
        """
        # Try to load from config file
        if self.args.config and os.path.exists(self.args.config):
            self.logger.info(f"Loading configuration from {self.args.config}")
            with open(self.args.config, 'r') as f:
                if self.args.config.endswith('.json'):
                    self.config = json.load(f)
                elif self.args.config.endswith(('.yaml', '.yml')):
                    self.config = yaml.safe_load(f)
                else:
                    self.logger.error(f"Unsupported config file format: {self.args.config}")
        
        # Check if default config file exists
        elif self.config_file.exists():
            self.logger.info(f"Loading configuration from {self.config_file}")
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        
        # Load environment variables
        if self.env_file.exists():
            self.logger.info(f"Loading environment variables from {self.env_file}")
            load_dotenv(self.env_file)
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_env(self):
        """
        Load configuration from environment variables.
        """
        # Matrix server configuration
        if os.environ.get('MATRIX_SERVER_NAME'):
            self.config['matrix_server_name'] = os.environ.get('MATRIX_SERVER_NAME')
        
        if os.environ.get('MATRIX_DOMAIN'):
            self.config['matrix_domain'] = os.environ.get('MATRIX_DOMAIN')
        
        # Cloudflare configuration
        if os.environ.get('CLOUDFLARE_API_TOKEN'):
            if 'cloudflare' not in self.config:
                self.config['cloudflare'] = {}
            self.config['cloudflare']['api_token'] = os.environ.get('CLOUDFLARE_API_TOKEN')
        
        if os.environ.get('CLOUDFLARE_EMAIL'):
            if 'cloudflare' not in self.config:
                self.config['cloudflare'] = {}
            self.config['cloudflare']['email'] = os.environ.get('CLOUDFLARE_EMAIL')
        
        # Rclone configuration
        if os.environ.get('RCLONE_REMOTE'):
            if 'rclone' not in self.config:
                self.config['rclone'] = {}
            self.config['rclone']['remote'] = os.environ.get('RCLONE_REMOTE')
        
        if os.environ.get('RCLONE_PATH'):
            if 'rclone' not in self.config:
                self.config['rclone'] = {}
            self.config['rclone']['path'] = os.environ.get('RCLONE_PATH')
        
        # TURN server configuration
        if os.environ.get('TURN_SECRET'):
            if 'turn' not in self.config:
                self.config['turn'] = {}
            self.config['turn']['secret'] = os.environ.get('TURN_SECRET')
    
    def _validate_config(self):
        """
        Validate the configuration against a schema.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Define the schema for validation
        schema = Schema({
            Optional('matrix_server_name'): And(str, len),
            Optional('matrix_domain'): And(str, len),
            Optional('admin_email'): And(str, len),
            Optional('cloudflare'): {
                Optional('api_token'): And(str, len),
                Optional('email'): And(str, len)
            },
            Optional('rclone'): {
                Optional('remote'): And(str, len),
                Optional('path'): And(str, len)
            },
            Optional('turn'): {
                Optional('secret'): And(str, len)
            },
            Optional('optimization_level'): And(str, lambda s: s in ['low', 'standard', 'high'])
        })
        
        try:
            schema.validate(self.config)
            return True
        except SchemaError as e:
            self.logger.warning(f"Configuration validation error: {str(e)}")
            return False
    
    def _prompt_for_config(self):
        """
        Prompt the user for configuration values.
        """
        self.logger.info("Please provide the following configuration values:")
        
        # Matrix server configuration
        self.config['matrix_server_name'] = questionary.text(
            "Matrix server name:",
            default=self.config.get('matrix_server_name', 'matrix.example.com')
        ).ask()
        
        self.config['matrix_domain'] = questionary.text(
            "Matrix domain (usually the same as server name):",
            default=self.config.get('matrix_domain', self.config['matrix_server_name'])
        ).ask()
        
        self.config['admin_email'] = questionary.text(
            "Admin email address (for Let's Encrypt certificates):",
            default=self.config.get('admin_email', 'admin@example.com')
        ).ask()
        
        # Cloudflare integration
        use_cloudflare = questionary.confirm(
            "Do you want to use Cloudflare for DNS and proxy?",
            default=bool(self.config.get('cloudflare'))
        ).ask()
        
        if use_cloudflare:
            if 'cloudflare' not in self.config:
                self.config['cloudflare'] = {}
            
            self.config['cloudflare']['api_token'] = questionary.password(
                "Cloudflare API Token:",
                default=self.config.get('cloudflare', {}).get('api_token', '')
            ).ask()
            
            self.config['cloudflare']['email'] = questionary.text(
                "Cloudflare Email:",
                default=self.config.get('cloudflare', {}).get('email', '')
            ).ask()
        
        # Rclone integration
        use_rclone = questionary.confirm(
            "Do you want to use rclone for backups?",
            default=bool(self.config.get('rclone'))
        ).ask()
        
        if use_rclone:
            if 'rclone' not in self.config:
                self.config['rclone'] = {}
            
            self.config['rclone']['remote'] = questionary.text(
                "Rclone remote name:",
                default=self.config.get('rclone', {}).get('remote', 'pqmatrix')
            ).ask()
            
            self.config['rclone']['path'] = questionary.text(
                "Rclone backup path:",
                default=self.config.get('rclone', {}).get('path', 'backups/pqmatrix')
            ).ask()
        
        # TURN server configuration
        import secrets
        default_turn_secret = self.config.get('turn', {}).get('secret', '')
        if not default_turn_secret:
            default_turn_secret = secrets.token_hex(16)
        
        if 'turn' not in self.config:
            self.config['turn'] = {}
        
        self.config['turn']['secret'] = questionary.password(
            "TURN server secret (leave empty to generate random):",
            default=default_turn_secret
        ).ask()
        
        # Optimization level
        self.config['optimization_level'] = questionary.select(
            "Select optimization level:",
            choices=[
                {
                    'name': 'Low - Uses Kyber-512, minimal resources',
                    'value': 'low'
                },
                {
                    'name': 'Standard - Uses Kyber-768, balanced resources',
                    'value': 'standard'
                },
                {
                    'name': 'High - Uses Kyber-1024, maximum resources',
                    'value': 'high'
                }
            ],
            default=self.config.get('optimization_level', 'standard')
        ).ask()
        
        # Save the configuration
        self._save_config()
    
    def _save_config(self):
        """
        Save the configuration to a file.
        """
        # Save configuration to YAML file
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        # Save sensitive values to .env file
        with open(self.env_file, 'w') as f:
            f.write(f"MATRIX_SERVER_NAME={self.config.get('matrix_server_name', '')}\n")
            f.write(f"MATRIX_DOMAIN={self.config.get('matrix_domain', '')}\n")
            
            if 'cloudflare' in self.config:
                f.write(f"CLOUDFLARE_API_TOKEN={self.config['cloudflare'].get('api_token', '')}\n")
                f.write(f"CLOUDFLARE_EMAIL={self.config['cloudflare'].get('email', '')}\n")
            
            if 'rclone' in self.config:
                f.write(f"RCLONE_REMOTE={self.config['rclone'].get('remote', '')}\n")
                f.write(f"RCLONE_PATH={self.config['rclone'].get('path', '')}\n")
            
            if 'turn' in self.config:
                f.write(f"TURN_SECRET={self.config['turn'].get('secret', '')}\n")
        
        # Set restrictive permissions on .env file to protect sensitive data
        os.chmod(self.env_file, 0o600)
        
        self.logger.info(f"Configuration saved to {self.config_file} and {self.env_file}")
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        if '.' in key:
            # Handle nested keys
            parts = key.split('.')
            value = self.config
            for part in parts:
                if part not in value:
                    return default
                value = value[part]
            return value
        else:
            return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key
            value: Value to set
        """
        if '.' in key:
            # Handle nested keys
            parts = key.split('.')
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.config[key] = value
        
        # Save the updated configuration
        self._save_config()
