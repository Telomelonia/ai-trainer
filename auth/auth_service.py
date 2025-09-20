"""
Core Authentication Service for CoreSense AI Platform
Industry-standard authentication with JWT tokens, secure password hashing, and session management
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import uuid
import re
from email_validator import validate_email, EmailNotValidError

class AuthConfig:
    """Authentication configuration with secure defaults"""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)  # Override with env var in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Configuration
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Session Configuration
    SESSION_EXPIRE_HOURS: int = 24
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_REFRESH_THRESHOLD_MINUTES: int = 15
    
    # Security Configuration
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    
    # Rate Limiting
    MAX_PASSWORD_RESET_REQUESTS_PER_HOUR: int = 3
    MAX_EMAIL_VERIFICATION_REQUESTS_PER_HOUR: int = 5

class SecurityService:
    """Core security service for password hashing, token generation, and validation"""
    
    def __init__(self):
        # Password hashing context with bcrypt
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Strong hashing rounds
        )
        
        # Token generation for secure random tokens
        self.token_bytes = 32
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt with salt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    def generate_secure_token(self) -> str:
        """
        Generate a cryptographically secure random token
        
        Returns:
            URL-safe base64 encoded token
        """
        return secrets.token_urlsafe(self.token_bytes)
    
    def hash_token(self, token: str) -> str:
        """
        Hash a token for secure storage
        
        Args:
            token: Token to hash
            
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def verify_token_hash(self, token: str, token_hash: str) -> bool:
        """
        Verify a token against its hash
        
        Args:
            token: Original token
            token_hash: Stored hash
            
        Returns:
            True if token matches hash, False otherwise
        """
        expected_hash = self.hash_token(token)
        return hmac.compare_digest(expected_hash, token_hash)
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())

class PasswordValidator:
    """Password validation with configurable rules"""
    
    @staticmethod
    def validate_password(password: str, config: AuthConfig = None) -> Tuple[bool, list]:
        """
        Validate password against security requirements
        
        Args:
            password: Password to validate
            config: Authentication configuration
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if config is None:
            config = AuthConfig()
        
        errors = []
        
        # Check minimum length
        if len(password) < config.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters long")
        
        # Check for uppercase letters
        if config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for numbers
        if config.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check for special characters
        if config.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak patterns
        weak_patterns = [
            r'12345', r'password', r'qwerty', r'abc', r'admin',
            r'(.)\1{3,}',  # Repeated characters (aaaa)
            r'012|123|234|345|456|567|678|789',  # Sequential numbers
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append("Password contains common weak patterns")
                break
        
        return len(errors) == 0, errors

class EmailValidator:
    """Email validation and normalization"""
    
    @staticmethod
    def validate_email_address(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize email address
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, normalized_email, error_message)
        """
        try:
            # Validate email using email-validator library
            validated_email = validate_email(
                email,
                check_deliverability=False  # Set to True in production with proper DNS
            )
            
            # Return normalized email (lowercase, etc.)
            return True, validated_email.email, None
            
        except EmailNotValidError as e:
            return False, None, str(e)

class JWTService:
    """JWT token management service"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
    
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = user_data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token
        
        Args:
            user_data: User data to encode in token
            
        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.now(timezone.utc) + timedelta(days=self.config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = user_data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without full validation
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
            return True
        except:
            return True

class AuthenticationService:
    """Main authentication service combining all security components"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        self.security = SecurityService()
        self.jwt_service = JWTService(self.config)
        self.password_validator = PasswordValidator()
        self.email_validator = EmailValidator()
    
    def create_user_tokens(self, user_id: int, email: str, role: str) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        user_data = {
            "user_id": user_id,
            "email": email,
            "role": role
        }
        
        access_token = self.jwt_service.create_access_token(user_data)
        refresh_token = self.jwt_service.create_refresh_token(user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an access token and return user data"""
        return self.jwt_service.verify_token(token, "access")
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a refresh token and return user data"""
        return self.jwt_service.verify_token(token, "refresh")
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.security.hash_password(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return self.security.verify_password(password, hashed_password)
    
    def validate_password(self, password: str) -> Tuple[bool, list]:
        """Validate a password"""
        return self.password_validator.validate_password(password, self.config)
    
    def validate_email(self, email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate an email"""
        return self.email_validator.validate_email_address(email)
    
    def generate_secure_token(self) -> str:
        """Generate a secure token"""
        return self.security.generate_secure_token()
    
    def hash_token(self, token: str) -> str:
        """Hash a token"""
        return self.security.hash_token(token)
    
    def verify_token_hash(self, token: str, token_hash: str) -> bool:
        """Verify a token hash"""
        return self.security.verify_token_hash(token, token_hash)

# Global authentication service instance
auth_service = AuthenticationService()

# Export classes and service
__all__ = [
    'AuthConfig',
    'SecurityService', 
    'PasswordValidator',
    'EmailValidator',
    'JWTService',
    'AuthenticationService',
    'auth_service'
]