"""
User Management System for CoreSense Authentication
Complete user registration, login, profile management, and role-based access control
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

from .models import User, UserSession, UserRole
from .auth_service import auth_service, AuthConfig
from .database import db_service

logger = logging.getLogger(__name__)

@dataclass
class UserRegistrationData:
    """Data structure for user registration"""
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    fitness_level: Optional[str] = None
    training_goals: Optional[List[str]] = None
    preferred_session_duration: int = 30
    health_considerations: Optional[str] = None

@dataclass
class UserLoginData:
    """Data structure for user login"""
    email_or_username: str
    password: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class UserProfileUpdate:
    """Data structure for user profile updates"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    fitness_level: Optional[str] = None
    training_goals: Optional[List[str]] = None
    preferred_session_duration: Optional[int] = None
    health_considerations: Optional[str] = None

@dataclass
class AuthResult:
    """Result of authentication operations"""
    success: bool
    message: str
    user: Optional[User] = None
    tokens: Optional[Dict[str, str]] = None
    errors: Optional[List[str]] = None

class UserManagementService:
    """Service for managing user registration, login, and profile operations"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        self.auth_service = auth_service
        self.db_service = db_service
    
    def register_user(self, registration_data: UserRegistrationData) -> AuthResult:
        """
        Register a new user
        
        Args:
            registration_data: User registration information
            
        Returns:
            AuthResult with registration outcome
        """
        try:
            # Validate email
            is_valid_email, normalized_email, email_error = self.auth_service.validate_email(registration_data.email)
            if not is_valid_email:
                return AuthResult(
                    success=False,
                    message="Invalid email address",
                    errors=[email_error or "Invalid email format"]
                )
            
            # Validate password
            is_valid_password, password_errors = self.auth_service.validate_password(registration_data.password)
            if not is_valid_password:
                return AuthResult(
                    success=False,
                    message="Password does not meet security requirements",
                    errors=password_errors
                )
            
            # Check if email already exists
            existing_user = self.db_service.get_user_by_email(normalized_email)
            if existing_user:
                return AuthResult(
                    success=False,
                    message="An account with this email already exists",
                    errors=["Email already registered"]
                )
            
            # Check if username already exists
            existing_username = self.db_service.get_user_by_username(registration_data.username)
            if existing_username:
                return AuthResult(
                    success=False,
                    message="This username is already taken",
                    errors=["Username already exists"]
                )
            
            # Hash password
            hashed_password = self.auth_service.hash_password(registration_data.password)
            
            # Prepare training goals as JSON
            training_goals_json = None
            if registration_data.training_goals:
                training_goals_json = json.dumps(registration_data.training_goals)
            
            # Create user
            user = self.db_service.create_user(
                email=normalized_email,
                username=registration_data.username,
                hashed_password=hashed_password,
                first_name=registration_data.first_name,
                last_name=registration_data.last_name,
                age=registration_data.age,
                fitness_level=registration_data.fitness_level,
                training_goals=training_goals_json,
                preferred_session_duration=registration_data.preferred_session_duration,
                health_considerations=registration_data.health_considerations,
                role=UserRole.FREE  # Default role
            )
            
            if not user:
                return AuthResult(
                    success=False,
                    message="Failed to create user account",
                    errors=["Database error during registration"]
                )
            
            logger.info(f"User registered successfully: {user.email}")
            
            return AuthResult(
                success=True,
                message="Account created successfully! Please verify your email to continue.",
                user=user
            )
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return AuthResult(
                success=False,
                message="Registration failed due to a system error",
                errors=[str(e)]
            )
    
    def login_user(self, login_data: UserLoginData) -> AuthResult:
        """
        Authenticate user login
        
        Args:
            login_data: User login information
            
        Returns:
            AuthResult with login outcome and tokens
        """
        try:
            # Find user by email or username
            user = None
            if "@" in login_data.email_or_username:
                # Looks like an email
                user = self.db_service.get_user_by_email(login_data.email_or_username)
            else:
                # Treat as username
                user = self.db_service.get_user_by_username(login_data.email_or_username)
            
            if not user:
                return AuthResult(
                    success=False,
                    message="Invalid email/username or password",
                    errors=["User not found"]
                )
            
            # Verify password
            if not self.auth_service.verify_password(login_data.password, user.hashed_password):
                return AuthResult(
                    success=False,
                    message="Invalid email/username or password",
                    errors=["Invalid password"]
                )
            
            # Check if user is active
            if not user.is_active:
                return AuthResult(
                    success=False,
                    message="Your account has been deactivated. Please contact support.",
                    errors=["Account deactivated"]
                )
            
            # Create tokens
            tokens = self.auth_service.create_user_tokens(
                user_id=user.id,
                email=user.email,
                role=user.role.value
            )
            
            # Create session record
            session_expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.SESSION_EXPIRE_HOURS)
            
            user_session = self.db_service.create_user_session(
                user_id=user.id,
                session_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=session_expires_at,
                device_info=login_data.device_info,
                ip_address=login_data.ip_address,
                user_agent=login_data.user_agent
            )
            
            if not user_session:
                logger.warning(f"Failed to create session for user {user.id}")
            
            # Update last login
            self.db_service.update_user(user.id, last_login=datetime.now(timezone.utc))
            
            logger.info(f"User logged in successfully: {user.email}")
            
            return AuthResult(
                success=True,
                message="Login successful",
                user=user,
                tokens=tokens
            )
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return AuthResult(
                success=False,
                message="Login failed due to a system error",
                errors=[str(e)]
            )
    
    def logout_user(self, session_token: str) -> bool:
        """
        Logout user by invalidating session
        
        Args:
            session_token: User's session token
            
        Returns:
            True if logout successful, False otherwise
        """
        try:
            success = self.db_service.invalidate_session(session_token)
            if success:
                logger.info("User logged out successfully")
            return success
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile information
        
        Args:
            user_id: User ID
            
        Returns:
            User profile dictionary or None
        """
        try:
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return None
            
            # Parse training goals from JSON
            training_goals = []
            if user.training_goals:
                try:
                    training_goals = json.loads(user.training_goals)
                except json.JSONDecodeError:
                    training_goals = []
            
            profile = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "age": user.age,
                "fitness_level": user.fitness_level,
                "training_goals": training_goals,
                "preferred_session_duration": user.preferred_session_duration,
                "health_considerations": user.health_considerations,
                "role": user.role.value,
                "is_premium": user.is_premium,
                "subscription_status": user.subscription_status,
                "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: int, profile_update: UserProfileUpdate) -> AuthResult:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_update: Profile update data
            
        Returns:
            AuthResult with update outcome
        """
        try:
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    message="User not found",
                    errors=["User does not exist"]
                )
            
            # Prepare update data
            updates = {}
            
            if profile_update.first_name is not None:
                updates["first_name"] = profile_update.first_name
            
            if profile_update.last_name is not None:
                updates["last_name"] = profile_update.last_name
            
            if profile_update.age is not None:
                if profile_update.age < 13 or profile_update.age > 120:
                    return AuthResult(
                        success=False,
                        message="Invalid age provided",
                        errors=["Age must be between 13 and 120"]
                    )
                updates["age"] = profile_update.age
            
            if profile_update.fitness_level is not None:
                valid_levels = ["beginner", "intermediate", "advanced"]
                if profile_update.fitness_level.lower() not in valid_levels:
                    return AuthResult(
                        success=False,
                        message="Invalid fitness level",
                        errors=[f"Fitness level must be one of: {', '.join(valid_levels)}"]
                    )
                updates["fitness_level"] = profile_update.fitness_level.lower()
            
            if profile_update.training_goals is not None:
                updates["training_goals"] = json.dumps(profile_update.training_goals)
            
            if profile_update.preferred_session_duration is not None:
                if profile_update.preferred_session_duration < 10 or profile_update.preferred_session_duration > 120:
                    return AuthResult(
                        success=False,
                        message="Invalid session duration",
                        errors=["Session duration must be between 10 and 120 minutes"]
                    )
                updates["preferred_session_duration"] = profile_update.preferred_session_duration
            
            if profile_update.health_considerations is not None:
                updates["health_considerations"] = profile_update.health_considerations
            
            # Update user
            updated_user = self.db_service.update_user(user_id, **updates)
            
            if not updated_user:
                return AuthResult(
                    success=False,
                    message="Failed to update profile",
                    errors=["Database error during update"]
                )
            
            logger.info(f"User profile updated: {user.email}")
            
            return AuthResult(
                success=True,
                message="Profile updated successfully",
                user=updated_user
            )
            
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            return AuthResult(
                success=False,
                message="Profile update failed due to a system error",
                errors=[str(e)]
            )
    
    def change_user_password(self, user_id: int, current_password: str, new_password: str) -> AuthResult:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            AuthResult with password change outcome
        """
        try:
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    message="User not found",
                    errors=["User does not exist"]
                )
            
            # Verify current password
            if not self.auth_service.verify_password(current_password, user.hashed_password):
                return AuthResult(
                    success=False,
                    message="Current password is incorrect",
                    errors=["Invalid current password"]
                )
            
            # Validate new password
            is_valid_password, password_errors = self.auth_service.validate_password(new_password)
            if not is_valid_password:
                return AuthResult(
                    success=False,
                    message="New password does not meet security requirements",
                    errors=password_errors
                )
            
            # Hash new password
            new_hashed_password = self.auth_service.hash_password(new_password)
            
            # Update password
            updated_user = self.db_service.update_user(user_id, hashed_password=new_hashed_password)
            
            if not updated_user:
                return AuthResult(
                    success=False,
                    message="Failed to change password",
                    errors=["Database error during password change"]
                )
            
            logger.info(f"Password changed for user: {user.email}")
            
            return AuthResult(
                success=True,
                message="Password changed successfully"
            )
            
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return AuthResult(
                success=False,
                message="Password change failed due to a system error",
                errors=[str(e)]
            )
    
    def upgrade_to_premium(self, user_id: int, duration_months: int = 1) -> AuthResult:
        """
        Upgrade user to premium
        
        Args:
            user_id: User ID
            duration_months: Premium duration in months
            
        Returns:
            AuthResult with upgrade outcome
        """
        try:
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    message="User not found",
                    errors=["User does not exist"]
                )
            
            # Calculate premium expiration
            premium_expires_at = datetime.now(timezone.utc) + timedelta(days=duration_months * 30)
            
            # Update user role and premium status
            updated_user = self.db_service.update_user(
                user_id,
                role=UserRole.PREMIUM,
                premium_expires_at=premium_expires_at,
                subscription_status="active"
            )
            
            if not updated_user:
                return AuthResult(
                    success=False,
                    message="Failed to upgrade to premium",
                    errors=["Database error during upgrade"]
                )
            
            logger.info(f"User upgraded to premium: {user.email}")
            
            return AuthResult(
                success=True,
                message=f"Successfully upgraded to premium for {duration_months} months",
                user=updated_user
            )
            
        except Exception as e:
            logger.error(f"Premium upgrade failed: {e}")
            return AuthResult(
                success=False,
                message="Premium upgrade failed due to a system error",
                errors=[str(e)]
            )
    
    def deactivate_user(self, user_id: int) -> AuthResult:
        """
        Deactivate user account
        
        Args:
            user_id: User ID
            
        Returns:
            AuthResult with deactivation outcome
        """
        try:
            updated_user = self.db_service.update_user(user_id, is_active=False)
            
            if not updated_user:
                return AuthResult(
                    success=False,
                    message="Failed to deactivate account",
                    errors=["User not found or database error"]
                )
            
            logger.info(f"User account deactivated: {updated_user.email}")
            
            return AuthResult(
                success=True,
                message="Account deactivated successfully"
            )
            
        except Exception as e:
            logger.error(f"Account deactivation failed: {e}")
            return AuthResult(
                success=False,
                message="Account deactivation failed due to a system error",
                errors=[str(e)]
            )

# Global user management service instance
user_service = UserManagementService()

# Export classes and service
__all__ = [
    'UserRegistrationData',
    'UserLoginData',
    'UserProfileUpdate',
    'AuthResult',
    'UserManagementService',
    'user_service'
]