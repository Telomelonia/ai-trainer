"""
CoreSense AI Platform - Utility Functions
Shared utility functions for import handling, validation, etc.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from core.logging import get_logger
from core.exceptions import ValidationError, ConfigurationError

logger = get_logger(__name__)


def import_module_safely(module_path: str, module_name: str = None) -> Optional[Any]:
    """
    Safely import a module from a file path with proper error handling
    
    Args:
        module_path: Path to the module file
        module_name: Optional module name (defaults to filename)
        
    Returns:
        Imported module or None if import fails
    """
    try:
        if not os.path.exists(module_path):
            logger.warning(f"Module file not found: {module_path}")
            return None
        
        if module_name is None:
            module_name = Path(module_path).stem
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            logger.error(f"Could not create module spec for {module_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules before execution
        sys.modules[module_name] = module
        
        spec.loader.exec_module(module)
        
        logger.debug(f"Successfully imported module: {module_name}")
        return module
        
    except Exception as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        return None


def add_path_to_sys(path: Union[str, Path]) -> None:
    """
    Add a path to sys.path if not already present
    
    Args:
        path: Path to add to sys.path
    """
    path_str = str(Path(path).resolve())
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
        logger.debug(f"Added path to sys.path: {path_str}")


def setup_import_paths(base_dir: Path) -> None:
    """
    Setup all necessary import paths for the application
    
    Args:
        base_dir: Base directory of the application
    """
    paths_to_add = [
        base_dir,
        base_dir / 'agents',
        base_dir / 'sensors', 
        base_dir / 'config',
        base_dir / 'auth',
        base_dir / 'services',
        base_dir / 'core'
    ]
    
    for path in paths_to_add:
        if path.exists():
            add_path_to_sys(path)


def validate_env_vars(required_vars: List[str]) -> None:
    """
    Validate that required environment variables are set
    
    Args:
        required_vars: List of required environment variable names
        
    Raises:
        ConfigurationError: If any required variables are missing
    """
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


def get_project_root() -> Path:
    """
    Get the project root directory
    
    Returns:
        Path to project root
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove any remaining non-printable characters
    filename = ''.join(char for char in filename if char.isprintable())
    # Limit length
    return filename[:255]


def format_bytes(size: int) -> str:
    """
    Format bytes as human readable string
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string with default fallback
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON string: {json_str[:100]}...")
        return default


def retry_operation(func, max_retries: int = 3, delay: float = 1.0):
    """
    Retry an operation with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {sleep_time}s: {e}")
                time.sleep(sleep_time)
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
    
    raise last_exception


def is_valid_email(email: str) -> bool:
    """
    Simple email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email appears valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        logger.debug(f"Starting: {self.description}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.debug(f"Completed: {self.description} in {duration:.2f}s")
    
    @property
    def duration(self) -> float:
        """Get the duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0