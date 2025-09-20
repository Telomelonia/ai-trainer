"""
Session Management Service for CoreSense Authentication
Secure session persistence, token refresh, and session lifecycle management
"""

import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import logging
import json

from .models import User, UserSession
from .auth_service import auth_service, AuthConfig
from .database import db_service
from .user_service import AuthResult

logger = logging.getLogger(__name__)

class SessionManager:
    """Session manager for Streamlit with secure token handling"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        self.auth_service = auth_service
        self.db_service = db_service
        
        # Session keys for Streamlit
        self.USER_KEY = "coresense_user"
        self.TOKEN_KEY = "coresense_access_token"
        self.REFRESH_TOKEN_KEY = "coresense_refresh_token"
        self.SESSION_ID_KEY = "coresense_session_id"
        self.LOGIN_TIME_KEY = "coresense_login_time"
    
    def initialize_session(self) -> bool:
        """
        Initialize session state for authentication
        
        Returns:
            True if session initialized successfully, False otherwise
        """
        try:
            # Initialize session state keys if not present
            if self.USER_KEY not in st.session_state:
                st.session_state[self.USER_KEY] = None
            
            if self.TOKEN_KEY not in st.session_state:
                st.session_state[self.TOKEN_KEY] = None
            
            if self.REFRESH_TOKEN_KEY not in st.session_state:
                st.session_state[self.REFRESH_TOKEN_KEY] = None
            
            if self.SESSION_ID_KEY not in st.session_state:
                st.session_state[self.SESSION_ID_KEY] = None
            
            if self.LOGIN_TIME_KEY not in st.session_state:
                st.session_state[self.LOGIN_TIME_KEY] = None
            
            # Check if we have an existing valid session
            if self.is_logged_in():
                # Refresh token if needed
                self._refresh_token_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            return False
    
    def login_user(self, user: User, tokens: Dict[str, str], device_info: str = None) -> bool:
        """
        Log in user and establish session
        
        Args:
            user: User object
            tokens: Authentication tokens
            device_info: Device information
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Store user data in session
            user_data = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_premium": user.is_premium,
                "is_verified": user.is_verified
            }
            
            st.session_state[self.USER_KEY] = user_data
            st.session_state[self.TOKEN_KEY] = tokens["access_token"]
            st.session_state[self.REFRESH_TOKEN_KEY] = tokens["refresh_token"]
            st.session_state[self.LOGIN_TIME_KEY] = datetime.now(timezone.utc).isoformat()
            
            # Generate session ID for tracking
            session_id = self.auth_service.security.generate_session_id()
            st.session_state[self.SESSION_ID_KEY] = session_id
            
            logger.info(f"User logged in via session manager: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to login user via session manager: {e}")
            return False
    
    def logout_user(self) -> bool:
        """
        Log out user and clear session
        
        Returns:
            True if logout successful, False otherwise
        """
        try:
            # Invalidate database session if we have a token
            access_token = st.session_state.get(self.TOKEN_KEY)
            if access_token:
                self.db_service.invalidate_session(access_token)
            
            # Clear session state
            st.session_state[self.USER_KEY] = None
            st.session_state[self.TOKEN_KEY] = None
            st.session_state[self.REFRESH_TOKEN_KEY] = None
            st.session_state[self.SESSION_ID_KEY] = None
            st.session_state[self.LOGIN_TIME_KEY] = None
            
            logger.info("User logged out via session manager")
            return True
            
        except Exception as e:
            logger.error(f"Failed to logout user: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """
        Check if user is logged in with valid session
        
        Returns:
            True if user is logged in, False otherwise
        """
        try:
            # Check if we have user data and tokens
            user_data = st.session_state.get(self.USER_KEY)
            access_token = st.session_state.get(self.TOKEN_KEY)
            
            if not user_data or not access_token:
                return False
            
            # Verify access token
            token_data = self.auth_service.verify_access_token(access_token)
            if not token_data:
                # Try to refresh token
                if self._refresh_access_token():
                    return True
                else:
                    # Clear invalid session
                    self.logout_user()
                    return False
            
            # Validate token data matches session
            if token_data.get("user_id") != user_data.get("id"):
                self.logout_user()
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current logged-in user data
        
        Returns:
            User data dictionary or None if not logged in
        """
        if self.is_logged_in():
            return st.session_state.get(self.USER_KEY)
        return None
    
    def get_current_user_id(self) -> Optional[int]:
        """
        Get current user ID
        
        Returns:
            User ID or None if not logged in
        """
        user_data = self.get_current_user()
        return user_data.get("id") if user_data else None
    
    def has_role(self, required_role: str) -> bool:
        """
        Check if current user has required role
        
        Args:
            required_role: Required role (free, premium, admin)
            
        Returns:
            True if user has required role, False otherwise
        """
        user_data = self.get_current_user()
        if not user_data:
            return False
        
        user_role = user_data.get("role", "free")
        
        # Role hierarchy: admin > premium > free
        role_hierarchy = {"admin": 3, "premium": 2, "free": 1}
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def is_premium_user(self) -> bool:
        """Check if current user is premium"""
        user_data = self.get_current_user()
        return user_data.get("is_premium", False) if user_data else False
    
    def is_verified_user(self) -> bool:
        """Check if current user is verified"""
        user_data = self.get_current_user()
        return user_data.get("is_verified", False) if user_data else False
    
    def get_session_duration(self) -> Optional[timedelta]:
        """
        Get current session duration
        
        Returns:
            Session duration or None if not logged in
        """
        login_time_str = st.session_state.get(self.LOGIN_TIME_KEY)
        if not login_time_str:
            return None
        
        try:
            login_time = datetime.fromisoformat(login_time_str)
            return datetime.now(timezone.utc) - login_time
        except Exception:
            return None
    
    def _refresh_token_if_needed(self) -> bool:
        """
        Refresh access token if it's close to expiring
        
        Returns:
            True if token refreshed or not needed, False if failed
        """
        try:
            access_token = st.session_state.get(self.TOKEN_KEY)
            if not access_token:
                return False
            
            # Check if token is close to expiring (within refresh threshold)
            token_data = self.auth_service.verify_access_token(access_token)
            if token_data:
                # Token is still valid, check if it's close to expiring
                exp_timestamp = token_data.get("exp")
                if exp_timestamp:
                    exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    time_until_expiry = exp_time - datetime.now(timezone.utc)
                    
                    # Refresh if less than threshold minutes remaining
                    if time_until_expiry.total_seconds() < (self.config.SESSION_REFRESH_THRESHOLD_MINUTES * 60):
                        return self._refresh_access_token()
            else:
                # Token is invalid, try to refresh
                return self._refresh_access_token()
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking token refresh: {e}")
            return False
    
    def _refresh_access_token(self) -> bool:
        """
        Refresh access token using refresh token
        
        Returns:
            True if token refreshed successfully, False otherwise
        """
        try:
            refresh_token = st.session_state.get(self.REFRESH_TOKEN_KEY)
            if not refresh_token:
                return False
            
            # Verify refresh token
            token_data = self.auth_service.verify_refresh_token(refresh_token)
            if not token_data:
                return False
            
            # Get user data from database to ensure it's still valid
            user_id = token_data.get("user_id")
            user = self.db_service.get_user_by_id(user_id)
            if not user or not user.is_active:
                return False
            
            # Create new access token
            new_tokens = self.auth_service.create_user_tokens(
                user_id=user.id,
                email=user.email,
                role=user.role.value
            )
            
            # Update session with new tokens
            st.session_state[self.TOKEN_KEY] = new_tokens["access_token"]
            st.session_state[self.REFRESH_TOKEN_KEY] = new_tokens["refresh_token"]
            
            # Update user data in session
            user_data = st.session_state[self.USER_KEY]
            if user_data:
                user_data.update({
                    "role": user.role.value,
                    "is_premium": user.is_premium,
                    "is_verified": user.is_verified
                })
                st.session_state[self.USER_KEY] = user_data
            
            logger.info(f"Access token refreshed for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False
    
    def update_user_session_data(self, user_updates: Dict[str, Any]) -> bool:
        """
        Update user data in session
        
        Args:
            user_updates: Dictionary of user data updates
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            user_data = st.session_state.get(self.USER_KEY)
            if not user_data:
                return False
            
            user_data.update(user_updates)
            st.session_state[self.USER_KEY] = user_data
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user session data: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from database
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            return self.db_service.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

class AuthenticationMiddleware:
    """Middleware for protecting routes and checking authentication"""
    
    def __init__(self, session_manager: SessionManager = None):
        self.session_manager = session_manager or SessionManager()
    
    def require_auth(self, redirect_to_login: bool = True) -> bool:
        """
        Require authentication for current page
        
        Args:
            redirect_to_login: Whether to redirect to login page if not authenticated
            
        Returns:
            True if user is authenticated, False otherwise
        """
        if not self.session_manager.is_logged_in():
            if redirect_to_login:
                st.error("🔒 Please log in to access this page.")
                st.stop()
            return False
        return True
    
    def require_role(self, required_role: str, redirect_to_login: bool = True) -> bool:
        """
        Require specific role for current page
        
        Args:
            required_role: Required role (free, premium, admin)
            redirect_to_login: Whether to redirect to login page if insufficient role
            
        Returns:
            True if user has required role, False otherwise
        """
        if not self.require_auth(redirect_to_login):
            return False
        
        if not self.session_manager.has_role(required_role):
            if redirect_to_login:
                st.error(f"🚫 This feature requires {required_role} access.")
                st.stop()
            return False
        return True
    
    def require_premium(self, redirect_to_login: bool = True) -> bool:
        """Require premium access"""
        return self.require_role("premium", redirect_to_login)
    
    def require_verification(self, redirect_to_login: bool = True) -> bool:
        """
        Require email verification
        
        Args:
            redirect_to_login: Whether to redirect if not verified
            
        Returns:
            True if user is verified, False otherwise
        """
        if not self.require_auth(redirect_to_login):
            return False
        
        if not self.session_manager.is_verified_user():
            if redirect_to_login:
                st.warning("📧 Please verify your email address to access this feature.")
                st.stop()
            return False
        return True

# Global session manager and middleware instances
session_manager = SessionManager()
auth_middleware = AuthenticationMiddleware(session_manager)

# Convenience functions for common operations
def login_required(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        if not session_manager.is_logged_in():
            st.error("🔒 Please log in to access this feature.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def premium_required(func):
    """Decorator to require premium access for a function"""
    def wrapper(*args, **kwargs):
        if not session_manager.is_logged_in():
            st.error("🔒 Please log in to access this feature.")
            st.stop()
        if not session_manager.is_premium_user():
            st.error("🚫 This feature requires premium access.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def verification_required(func):
    """Decorator to require email verification for a function"""
    def wrapper(*args, **kwargs):
        if not session_manager.is_logged_in():
            st.error("🔒 Please log in to access this feature.")
            st.stop()
        if not session_manager.is_verified_user():
            st.warning("📧 Please verify your email address to access this feature.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

# Export classes and instances
__all__ = [
    'SessionManager',
    'AuthenticationMiddleware',
    'session_manager',
    'auth_middleware',
    'login_required',
    'premium_required',
    'verification_required'
]