"""
CoreSense AI Platform - Core Module
Centralized configuration, utilities, and shared components
"""

from .config import AppConfig, get_config
from .logging import setup_logging, get_logger
from .exceptions import CoreSenseError, ValidationError, AuthenticationError
from .utils import import_module_safely, validate_env_vars

__all__ = [
    'AppConfig',
    'get_config', 
    'setup_logging',
    'get_logger',
    'CoreSenseError',
    'ValidationError', 
    'AuthenticationError',
    'import_module_safely',
    'validate_env_vars'
]