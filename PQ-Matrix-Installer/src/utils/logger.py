#!/usr/bin/env python3
"""
Logger module for PQ Matrix Installer.
Provides a consistent logging interface for the entire application.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path


def setup_logger(level=logging.INFO, log_to_file=True):
    """
    Set up and configure the logger.
    
    Args:
        level (int): Logging level (default: logging.INFO)
        log_to_file (bool): Whether to log to a file (default: True)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("pq_matrix_installer")
    logger.setLevel(level)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Define format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / ".pq-matrix" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = log_dir / f"installer-{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Log the location of the log file
        logger.info(f"Logs are being saved to: {log_file}")
    
    return logger


def get_logger():
    """
    Get the existing logger or create a new one with default settings.
    
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger("pq_matrix_installer")
    
    # If logger hasn't been set up yet, set it up with defaults
    if not logger.handlers:
        logger = setup_logger()
    
    return logger


class AuditLogger:
    """
    Logger specific for auditing security-related activities.
    This logger ensures security events are properly tracked and maintained.
    """
    
    def __init__(self):
        """Initialize the audit logger."""
        self.logger = get_logger()
        
        # Create audit log directory
        self.audit_log_dir = Path.home() / ".pq-matrix" / "audit"
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create audit log file
        self.audit_log_file = self.audit_log_dir / "audit.log"
        
        # Setup audit file handler
        audit_formatter = logging.Formatter(
            "%(asctime)s - AUDIT - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        audit_handler = logging.FileHandler(self.audit_log_file)
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(audit_formatter)
        
        # Create separate logger for audit logs
        self.audit_logger = logging.getLogger("pq_matrix_audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)
    
    def log(self, message, username="installer"):
        """
        Log an audit event.
        
        Args:
            message (str): The audit message
            username (str): The username performing the action
        """
        self.audit_logger.info(f"[{username}] {message}")
        self.logger.debug(f"Audit: {message}")
