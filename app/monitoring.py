"""
CoreSense AI Platform - Production Error Handling and Monitoring
Comprehensive error handling, logging, and monitoring for production deployment
"""

import logging
import sys
import traceback
import functools
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import streamlit as st
import json
import os

# Configure production logging
def setup_production_logging():
    """Configure production-grade logging"""
    
    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # Create handlers
    handlers = [
        logging.StreamHandler(sys.stdout),  # Console output
        logging.FileHandler(f"{log_dir}/coresense.log"),  # Application log
        logging.FileHandler(f"{log_dir}/error.log", level=logging.ERROR)  # Error log
    ]
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )
    
    # Create specialized loggers
    loggers = {
        'auth': logging.getLogger('coresense.auth'),
        'database': logging.getLogger('coresense.database'),
        'api': logging.getLogger('coresense.api'),
        'ui': logging.getLogger('coresense.ui'),
        'performance': logging.getLogger('coresense.performance')
    }
    
    return loggers

# Initialize loggers
loggers = setup_production_logging()

class ErrorHandler:
    """Centralized error handling for the CoreSense platform"""
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None, user_id: str = None):
        """Log error with context information"""
        
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'user_id': user_id,
            'context': context or {}
        }
        
        # Add session state context if available
        if hasattr(st, 'session_state'):
            error_data['session_context'] = {
                'page': st.session_state.get('current_page'),
                'user_agent': st.session_state.get('user_agent'),
                'session_id': st.session_state.get('session_id')
            }
        
        loggers['api'].error(
            f"Error occurred: {error_data['error_type']} - {error_data['error_message']}",
            extra={'error_data': error_data}
        )
        
        return error_data
    
    @staticmethod
    def handle_auth_error(error: Exception, operation: str = "authentication"):
        """Handle authentication-related errors"""
        
        error_data = ErrorHandler.log_error(
            error, 
            context={'operation': operation, 'component': 'authentication'}
        )
        
        # Show user-friendly error message
        if "password" in str(error).lower():
            st.error("🔐 Invalid password. Please try again.")
        elif "email" in str(error).lower():
            st.error("📧 Email not found. Please check your email address.")
        elif "token" in str(error).lower():
            st.error("🔑 Session expired. Please log in again.")
        else:
            st.error("🚫 Authentication failed. Please try again.")
        
        return error_data
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str = "database_operation"):
        """Handle database-related errors"""
        
        error_data = ErrorHandler.log_error(
            error,
            context={'operation': operation, 'component': 'database'}
        )
        
        # Show user-friendly error message
        if "connection" in str(error).lower():
            st.error("🔌 Database connection issue. Please try again later.")
        elif "timeout" in str(error).lower():
            st.error("⏰ Request timed out. Please try again.")
        else:
            st.error("💾 Data operation failed. Please try again.")
        
        return error_data
    
    @staticmethod
    def handle_api_error(error: Exception, endpoint: str = "unknown"):
        """Handle API-related errors"""
        
        error_data = ErrorHandler.log_error(
            error,
            context={'endpoint': endpoint, 'component': 'api'}
        )
        
        # Show user-friendly error message
        st.error("🌐 Service temporarily unavailable. Please try again later.")
        
        return error_data

def error_boundary(component_name: str = "component"):
    """Decorator for error boundary around functions"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_data = ErrorHandler.log_error(
                    e,
                    context={'component': component_name, 'function': func.__name__}
                )
                
                # Show error in UI
                st.error(f"❌ Error in {component_name}. Please refresh the page.")
                
                # Show error details in development
                if os.getenv('ENVIRONMENT') == 'development':
                    st.exception(e)
                
                return None
                
        return wrapper
    return decorator

class PerformanceMonitor:
    """Monitor application performance"""
    
    @staticmethod
    def log_performance(operation: str, duration: float, context: Dict[str, Any] = None):
        """Log performance metrics"""
        
        perf_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'context': context or {}
        }
        
        # Log slow operations
        if duration > 2.0:  # Operations taking more than 2 seconds
            loggers['performance'].warning(
                f"Slow operation detected: {operation} took {duration:.2f}s",
                extra={'performance_data': perf_data}
            )
        else:
            loggers['performance'].info(
                f"Operation completed: {operation} in {duration:.2f}s",
                extra={'performance_data': perf_data}
            )
    
    @staticmethod
    def monitor_function(operation_name: str = None):
        """Decorator to monitor function performance"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    PerformanceMonitor.log_performance(
                        operation_name or func.__name__,
                        duration,
                        context={'status': 'success'}
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    PerformanceMonitor.log_performance(
                        operation_name or func.__name__,
                        duration,
                        context={'status': 'error', 'error': str(e)}
                    )
                    raise
                    
            return wrapper
        return decorator

class HealthCheck:
    """Application health monitoring"""
    
    @staticmethod
    def check_database_health():
        """Check database connectivity"""
        try:
            from auth.database import db_service
            
            # Simple query to test connection
            result = db_service.health_check()
            
            return {
                'status': 'healthy' if result else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': 'Database connection successful' if result else 'Database connection failed'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': f'Database error: {str(e)}'
            }
    
    @staticmethod
    def check_auth_health():
        """Check authentication system health"""
        try:
            from auth.auth_service import auth_service
            
            # Test auth service initialization
            result = hasattr(auth_service, 'security_service')
            
            return {
                'status': 'healthy' if result else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': 'Authentication service operational' if result else 'Authentication service not available'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': f'Authentication error: {str(e)}'
            }
    
    @staticmethod
    def check_email_health():
        """Check email service health"""
        try:
            from auth.email_service import email_service
            
            # Test email service configuration
            result = email_service.smtp_server is not None
            
            return {
                'status': 'healthy' if result else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': 'Email service configured' if result else 'Email service not configured'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': f'Email service error: {str(e)}'
            }
    
    @staticmethod
    def get_system_health():
        """Get overall system health status"""
        
        checks = {
            'database': HealthCheck.check_database_health(),
            'authentication': HealthCheck.check_auth_health(),
            'email': HealthCheck.check_email_health()
        }
        
        # Determine overall status
        all_healthy = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'components': checks,
            'version': '1.0.0'
        }

class MetricsCollector:
    """Collect application metrics"""
    
    @staticmethod
    def log_user_action(action: str, user_id: str = None, details: Dict[str, Any] = None):
        """Log user actions for analytics"""
        
        action_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user_id': user_id,
            'details': details or {},
            'session_id': st.session_state.get('session_id')
        }
        
        loggers['ui'].info(
            f"User action: {action}",
            extra={'action_data': action_data}
        )
    
    @staticmethod
    def log_page_view(page: str, user_id: str = None):
        """Log page views"""
        
        MetricsCollector.log_user_action(
            'page_view',
            user_id=user_id,
            details={'page': page}
        )
    
    @staticmethod
    def log_feature_usage(feature: str, user_id: str = None, success: bool = True):
        """Log feature usage"""
        
        MetricsCollector.log_user_action(
            'feature_usage',
            user_id=user_id,
            details={'feature': feature, 'success': success}
        )

# Streamlit-specific error handling
def streamlit_error_handler():
    """Set up Streamlit-specific error handling"""
    
    # Custom exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        ErrorHandler.log_error(
            exc_value,
            context={
                'exc_type': exc_type.__name__,
                'component': 'streamlit_global'
            }
        )
    
    sys.excepthook = handle_exception

# Initialize error handling
def init_error_handling():
    """Initialize all error handling systems"""
    
    # Set up Streamlit error handling
    streamlit_error_handler()
    
    # Log application startup
    loggers['api'].info("CoreSense application starting up")
    
    # Log system health on startup
    health_status = HealthCheck.get_system_health()
    loggers['api'].info(f"System health check: {health_status['status']}")

# Context manager for error boundaries
class ErrorBoundary:
    """Context manager for error boundaries"""
    
    def __init__(self, component_name: str, show_error: bool = True):
        self.component_name = component_name
        self.show_error = show_error
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            ErrorHandler.log_error(
                exc_value,
                context={'component': self.component_name}
            )
            
            if self.show_error:
                st.error(f"❌ Error in {self.component_name}. Please try again.")
            
            # Suppress the exception in production
            if os.getenv('ENVIRONMENT') != 'development':
                return True
        
        return False

# Usage examples and decorators
@error_boundary("authentication")
@PerformanceMonitor.monitor_function("user_login")
def example_login_function(email: str, password: str):
    """Example of how to use error handling decorators"""
    # Function implementation
    pass

# Export all utilities
__all__ = [
    'ErrorHandler',
    'PerformanceMonitor', 
    'HealthCheck',
    'MetricsCollector',
    'ErrorBoundary',
    'error_boundary',
    'init_error_handling',
    'loggers'
]