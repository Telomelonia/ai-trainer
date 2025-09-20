"""
CoreSense AI Platform - Configuration Management
Centralized configuration with environment variable handling and validation
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = "sqlite:///./coresense.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    session_expire_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    password_min_length: int = 8


@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = "noreply@coresense.ai"
    from_name: str = "CoreSense AI"


@dataclass
class AppConfig:
    """Main application configuration"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8501
    
    # Application paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    
    # Feature flags
    enable_auth: bool = True
    enable_sensors: bool = True
    enable_agents: bool = True
    enable_metrics: bool = False
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    
    # External services
    openai_api_key: str = ""
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables"""
        
        # Load .env file if it exists
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        # Database config
        database = DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'sqlite:///./coresense.db'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )
        
        # Security config
        security = SecurityConfig(
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', 'change-me-in-production'),
            jwt_access_token_expire_minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            jwt_refresh_token_expire_days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7')),
            session_expire_hours=int(os.getenv('SESSION_EXPIRE_HOURS', '24')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', '30')),
            password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
        )
        
        # Email config
        email = EmailConfig(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            from_email=os.getenv('FROM_EMAIL', 'noreply@coresense.ai'),
            from_name=os.getenv('FROM_NAME', 'CoreSense AI')
        )
        
        return cls(
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '8501')),
            enable_auth=os.getenv('ENABLE_AUTH', 'true').lower() == 'true',
            enable_sensors=os.getenv('ENABLE_SENSORS', 'true').lower() == 'true',
            enable_agents=os.getenv('ENABLE_AGENTS', 'true').lower() == 'true',
            enable_metrics=os.getenv('ENABLE_METRICS', 'false').lower() == 'true',
            database=database,
            security=security,
            email=email,
            openai_api_key=os.getenv('OPENAI_API_KEY', '')
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if self.environment == 'production':
            if self.security.jwt_secret_key == 'change-me-in-production':
                errors.append("JWT_SECRET_KEY must be changed in production")
            
            if self.debug:
                errors.append("DEBUG should be False in production")
            
            if self.email.smtp_username and not self.email.smtp_password:
                errors.append("SMTP_PASSWORD required when SMTP_USERNAME is set")
        
        if self.security.password_min_length < 8:
            errors.append("PASSWORD_MIN_LENGTH should be at least 8")
        
        return errors
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == 'development'


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment"""
    global _config
    _config = AppConfig.from_env()
    return _config


def validate_config() -> None:
    """Validate current configuration and raise if invalid"""
    config = get_config()
    errors = config.validate()
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)