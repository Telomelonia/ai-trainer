"""
CoreSense AI Platform - Custom Exceptions
Centralized exception definitions for better error handling
"""


class CoreSenseError(Exception):
    """Base exception for all CoreSense errors"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.code}: {self.message}"


class ValidationError(CoreSenseError):
    """Raised when validation fails"""
    pass


class AuthenticationError(CoreSenseError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(CoreSenseError):
    """Raised when authorization fails"""
    pass


class DatabaseError(CoreSenseError):
    """Raised when database operations fail"""
    pass


class SensorError(CoreSenseError):
    """Raised when sensor operations fail"""
    pass


class AgentError(CoreSenseError):
    """Raised when agent operations fail"""
    pass


class ConfigurationError(CoreSenseError):
    """Raised when configuration is invalid"""
    pass


class ExternalServiceError(CoreSenseError):
    """Raised when external service calls fail"""
    pass