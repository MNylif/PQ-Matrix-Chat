#!/usr/bin/env python3
"""
Phase Manager for PQ Matrix Installer.
Manages the execution of installation phases.
"""

import importlib
import logging
import sys
import time
from pathlib import Path

# Local imports
from src.utils.logger import get_logger
from src.utils.banner import print_phase_header
from src.utils.system_checks import SystemChecker


class InstallationPhase:
    """Base class for installation phases."""
    
    def __init__(self, config_manager, logger=None):
        """
        Initialize the installation phase.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config = config_manager
        self.logger = logger or get_logger()
        self.name = "Base Phase"
        self.description = "Base installation phase"
        self.required = True
    
    def check_prerequisites(self):
        """
        Check if prerequisites for this phase are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        return True
    
    def execute(self):
        """
        Execute the installation phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def rollback(self):
        """
        Rollback changes made by this phase in case of failure.
        """
        self.logger.warning(f"Rollback not implemented for phase: {self.name}")
    
    def cleanup(self):
        """
        Perform cleanup after phase execution.
        """
        pass


class PhaseManager:
    """Manager for installation phases."""
    
    def __init__(self, config_manager, optimization_level='standard', logger=None):
        """
        Initialize the phase manager.
        
        Args:
            config_manager: Configuration manager instance
            optimization_level (str): Resource optimization level
            logger: Logger instance
        """
        self.config = config_manager
        self.optimization_level = optimization_level
        self.logger = logger or get_logger()
        self.phases = []
        self.current_phase = None
        
        # Register phases
        self._register_phases()
    
    def _register_phases(self):
        """Register all installation phases."""
        from src.phases.prereq_phase import PrerequisitesPhase
        from src.phases.docker_phase import DockerPhase
        from src.phases.network_phase import NetworkPhase
        from src.phases.matrix_phase import MatrixPhase
        from src.phases.security_phase import SecurityPhase
        from src.phases.backup_phase import BackupPhase
        from src.phases.finalize_phase import FinalizePhase
        
        # Add phases in execution order
        self.phases = [
            PrerequisitesPhase(self.config, self.logger),
            DockerPhase(self.config, self.logger),
            NetworkPhase(self.config, self.logger),
            MatrixPhase(self.config, self.logger),
            SecurityPhase(self.config, self.logger),
            BackupPhase(self.config, self.logger),
            FinalizePhase(self.config, self.logger)
        ]
        
        # Adjust phases based on optimization level
        self._adjust_phases_for_optimization()
    
    def _adjust_phases_for_optimization(self):
        """Adjust phases based on optimization level."""
        system_checker = SystemChecker(self.logger)
        detected_level = system_checker.determine_optimization_level()
        
        # If requested level is higher than what system can support, downgrade
        if (self.optimization_level == 'high' and detected_level != 'high') or \
           (self.optimization_level == 'standard' and detected_level == 'low'):
            self.logger.warning(
                f"Requested optimization level '{self.optimization_level}' is too high "
                f"for this system. Downgrading to '{detected_level}'."
            )
            self.optimization_level = detected_level
        
        # Update config with actual optimization level
        self.config.set('optimization_level', self.optimization_level)
        
        self.logger.info(f"Using optimization level: {self.optimization_level}")
    
    def run_all_phases(self, skip_phases=None):
        """
        Run all installation phases.
        
        Args:
            skip_phases (list): List of phase names to skip
            
        Returns:
            bool: True if all phases completed successfully, False otherwise
        """
        if skip_phases is None:
            skip_phases = []
        
        total_phases = len([p for p in self.phases if p.name not in skip_phases])
        current_phase_num = 1
        
        for phase in self.phases:
            if phase.name in skip_phases:
                self.logger.info(f"Skipping phase: {phase.name}")
                continue
            
            self.current_phase = phase
            print_phase_header(phase.name, current_phase_num, total_phases)
            self.logger.info(f"Starting phase: {phase.name} - {phase.description}")
            
            # Check prerequisites
            if not phase.check_prerequisites():
                if phase.required:
                    self.logger.error(f"Prerequisites not met for required phase: {phase.name}")
                    return False
                else:
                    self.logger.warning(f"Prerequisites not met for optional phase: {phase.name}. Skipping.")
                    continue
            
            # Execute phase
            start_time = time.time()
            try:
                success = phase.execute()
                if not success:
                    if phase.required:
                        self.logger.error(f"Required phase failed: {phase.name}")
                        phase.rollback()
                        return False
                    else:
                        self.logger.warning(f"Optional phase failed: {phase.name}. Continuing.")
            except Exception as e:
                self.logger.error(f"Error in phase {phase.name}: {str(e)}", exc_info=True)
                phase.rollback()
                if phase.required:
                    return False
            finally:
                phase.cleanup()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Completed phase: {phase.name} in {elapsed_time:.1f} seconds")
            
            current_phase_num += 1
        
        self.logger.info("All phases completed successfully!")
        return True
    
    def run_single_phase(self, phase_name):
        """
        Run a single installation phase by name.
        
        Args:
            phase_name (str): Name of the phase to run
            
        Returns:
            bool: True if phase completed successfully, False otherwise
        """
        for phase in self.phases:
            if phase.name.lower() == phase_name.lower():
                self.current_phase = phase
                print_phase_header(phase.name, 1, 1)
                self.logger.info(f"Running single phase: {phase.name} - {phase.description}")
                
                # Check prerequisites
                if not phase.check_prerequisites():
                    self.logger.error(f"Prerequisites not met for phase: {phase.name}")
                    return False
                
                # Execute phase
                try:
                    success = phase.execute()
                    if not success:
                        self.logger.error(f"Phase failed: {phase.name}")
                        phase.rollback()
                        return False
                except Exception as e:
                    self.logger.error(f"Error in phase {phase.name}: {str(e)}", exc_info=True)
                    phase.rollback()
                    return False
                finally:
                    phase.cleanup()
                
                self.logger.info(f"Phase completed successfully: {phase.name}")
                return True
        
        self.logger.error(f"Phase not found: {phase_name}")
        return False
