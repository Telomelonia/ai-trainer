"""
Authentication System Initialization for CoreSense
Main module to initialize and configure the authentication system
"""

import os
import logging
from typing import Optional
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthInitializer:
    """Initialize and configure the authentication system"""
    
    def __init__(self):
        self.initialized = False
        self._db_service = None
        self._session_manager = None
        self._auth_ui = None
    
    def initialize(self, force_reinit: bool = False) -> bool:
        """
        Initialize the authentication system
        
        Args:
            force_reinit: Force reinitialization even if already initialized
            
        Returns:
            True if initialization successful, False otherwise
        """
        if self.initialized and not force_reinit:
            return True
        
        try:
            logger.info("Initializing CoreSense authentication system...")
            
            # Initialize database
            if not self._initialize_database():
                logger.error("Failed to initialize database")
                return False
            
            # Initialize session manager
            if not self._initialize_session_manager():
                logger.error("Failed to initialize session manager")
                return False
            
            # Initialize UI components
            if not self._initialize_ui():
                logger.error("Failed to initialize UI components")
                return False
            
            self.initialized = True
            logger.info("CoreSense authentication system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Authentication system initialization failed: {e}")
            return False
    
    def _initialize_database(self) -> bool:
        """Initialize database connection and tables"""
        try:
            from .database import db_service
            
            # Initialize database
            if not db_service.initialize():
                return False
            
            self._db_service = db_service
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _initialize_session_manager(self) -> bool:
        """Initialize session manager"""
        try:
            from .session_manager import session_manager
            
            # Initialize session manager
            if not session_manager.initialize_session():
                return False
            
            self._session_manager = session_manager
            logger.info("Session manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Session manager initialization failed: {e}")
            return False
    
    def _initialize_ui(self) -> bool:
        """Initialize UI components"""
        try:
            from .streamlit_ui import auth_ui
            
            self._auth_ui = auth_ui
            logger.info("UI components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"UI initialization failed: {e}")
            return False
    
    def get_db_service(self):
        """Get database service instance"""
        if not self.initialized:
            raise RuntimeError("Authentication system not initialized")
        return self._db_service
    
    def get_session_manager(self):
        """Get session manager instance"""
        if not self.initialized:
            raise RuntimeError("Authentication system not initialized")
        return self._session_manager
    
    def get_auth_ui(self):
        """Get authentication UI instance"""
        if not self.initialized:
            raise RuntimeError("Authentication system not initialized")
        return self._auth_ui
    
    def cleanup(self):
        """Cleanup authentication system resources"""
        try:
            if self._db_service:
                self._db_service.db_manager.close()
            
            self.initialized = False
            logger.info("Authentication system cleanup completed")
            
        except Exception as e:
            logger.error(f"Authentication system cleanup failed: {e}")

# Global initializer instance
auth_initializer = AuthInitializer()

def init_auth_system(force_reinit: bool = False) -> bool:
    """
    Initialize the authentication system
    
    Args:
        force_reinit: Force reinitialization
        
    Returns:
        True if successful, False otherwise
    """
    return auth_initializer.initialize(force_reinit)

def require_auth_init():
    """Decorator to ensure auth system is initialized"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not auth_initializer.initialized:
                if not init_auth_system():
                    st.error("❌ Failed to initialize authentication system")
                    st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Streamlit app integration helpers
def setup_auth_page_config():
    """Setup Streamlit page configuration for authentication"""
    st.set_page_config(
        page_title="CoreSense AI Platform",
        page_icon="💫",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get help': 'https://coresense.ai/help',
            'Report a bug': 'https://coresense.ai/support',
            'About': """
            # CoreSense AI Platform
            
            **Intelligent Core Training System**
            
            Build stronger, more stable core muscles with AI-powered coaching 
            and real-time feedback.
            
            - 🤖 Advanced AI coaching
            - 📊 Real-time stability analysis  
            - 🎯 Personalized workout plans
            - 📈 Detailed progress tracking
            
            Version 1.0.0
            """
        }
    )

def add_auth_styles():
    """Add custom CSS styles for authentication"""
    st.markdown("""
    <style>
        /* Authentication form styles */
        .auth-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .auth-header {
            background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%);
            padding: 30px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .auth-form {
            background: #f9f9f9;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        
        .auth-button {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .auth-button-primary {
            background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%);
            color: white;
        }
        
        .auth-button-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
        }
        
        .auth-button-secondary {
            background: transparent;
            color: #6C63FF;
            border: 2px solid #6C63FF;
        }
        
        .auth-button-secondary:hover {
            background: #6C63FF;
            color: white;
        }
        
        /* User profile styles */
        .user-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        
        .premium-badge {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .verified-badge {
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .unverified-badge {
            background: #ffc107;
            color: black;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .auth-container {
                max-width: 100%;
                padding: 10px;
            }
            
            .auth-header {
                padding: 20px;
            }
            
            .auth-form {
                padding: 20px;
            }
        }
        
        /* Success and error message styles */
        .stSuccess > div {
            background-color: #d4edda !important;
            border-color: #c3e6cb !important;
            color: #155724 !important;
        }
        
        .stError > div {
            background-color: #f8d7da !important;
            border-color: #f5c6cb !important;
            color: #721c24 !important;
        }
        
        .stWarning > div {
            background-color: #fff3cd !important;
            border-color: #ffeaa7 !important;
            color: #856404 !important;
        }
        
        .stInfo > div {
            background-color: #d1ecf1 !important;
            border-color: #bee5eb !important;
            color: #0c5460 !important;
        }
        
        /* Custom metric styles */
        .metric-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #6C63FF;
            margin-bottom: 10px;
        }
        
        /* Navigation styles */
        .nav-link {
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 5px;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background-color: #f0f2f6;
            color: #6C63FF;
        }
        
        .nav-link-active {
            background-color: #6C63FF;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

# Export main components
__all__ = [
    'AuthInitializer',
    'auth_initializer',
    'init_auth_system',
    'require_auth_init',
    'setup_auth_page_config',
    'add_auth_styles'
]