#!/usr/bin/env python3
"""
PQ Matrix Installer
==================

A comprehensive installer for the Post-Quantum-Resistant Matrix Server.
This tool automates the installation, configuration, and deployment
of a secure Matrix server with post-quantum encryption.

Usage:
    curl -sL https://raw.githubusercontent.com/your-org/pq-matrix-installer/main/install.sh | bash
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

# Local imports
from src.utils.logger import setup_logger
from src.utils.banner import print_banner
from src.phases.phase_manager import PhaseManager
from src.config.config_manager import ConfigManager
from src.utils.system_checks import SystemChecker


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PQ Matrix Installer - Automated secure Matrix server deployment'
    )
    
    parser.add_argument(
        '--optimization-level',
        choices=['low', 'standard', 'high'],
        default='standard',
        help='Resource optimization level for server configuration'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode using config file or environment variables'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file for non-interactive mode'
    )
    
    parser.add_argument(
        '--skip-phases',
        type=str,
        help='Comma-separated list of phases to skip'
    )
    
    parser.add_argument(
        '--only-phase',
        type=str,
        help='Run only a specific phase'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the installer."""
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    
    # Print banner
    print_banner()
    
    # Log startup information
    logger.info("Starting PQ Matrix Installer")
    logger.info(f"Optimization level: {args.optimization_level}")
    
    try:
        # Initialize system checker and perform pre-flight checks
        system_checker = SystemChecker(logger)
        if not system_checker.check_system_requirements():
            logger.error("System requirements not met. Exiting installation.")
            sys.exit(1)
        
        # Load or create configuration
        config_manager = ConfigManager(args, logger)
        
        # Initialize phase manager
        phase_manager = PhaseManager(config_manager, args.optimization_level, logger)
        
        # Run the installation phases
        if args.only_phase:
            phase_manager.run_single_phase(args.only_phase)
        else:
            skip_phases = args.skip_phases.split(',') if args.skip_phases else []
            phase_manager.run_all_phases(skip_phases)
        
        logger.info("Installation completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("\nInstallation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Installation failed: {str(e)}", exc_info=args.debug)
        sys.exit(1)


if __name__ == "__main__":
    main()
