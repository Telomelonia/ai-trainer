"""
CoreSense AI Platform - Simplified Main Application
Clean, maintainable Streamlit app with centralized service management
"""

import streamlit as st
from typing import Dict, Any
import asyncio

# Core imports
from core.config import get_config, validate_config
from core.logging import setup_logging, get_logger
from core.services import initialize_core_services, get_service_manager
from core.exceptions import CoreSenseError

# UI components
from ui.dashboard import render_dashboard
from ui.muscle_activation import render_muscle_activation
from ui.auth import render_user_profile, render_ai_coach, render_progress_analytics, render_auth_ui
from ui.coral_orchestration import render_coral_orchestration
from ui.common import setup_page_config, setup_sidebar, get_current_data

logger = get_logger(__name__)


class CoreSenseApp:
    """Main CoreSense application class"""
    
    def __init__(self):
        self.config = get_config()
        self.service_manager = None
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the application"""
        try:
            # Validate configuration
            validate_config()
            
            # Setup logging
            setup_logging(
                level=self.config.log_level,
                log_file="logs/coresense.log" if not self.config.is_development else None
            )
            
            logger.info("🚀 Starting CoreSense AI Platform")
            
            # Initialize services
            self.service_manager = initialize_core_services()
            
            # Setup Streamlit page
            setup_page_config()
            
            logger.info("✅ CoreSense application initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CoreSense application: {e}")
            st.error(f"Failed to initialize application: {e}")
            st.stop()
    
    def run(self):
        """Run the main application"""
        try:
            # Handle authentication if enabled
            if self.config.enable_auth:
                auth_service = self.service_manager.get_service('auth')
                if auth_service and not self._is_authenticated():
                    render_auth_ui()
                    return
            
            # Setup sidebar and navigation
            page = setup_sidebar(self.service_manager)
            
            # Route to appropriate page
            self._route_page(page)
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"An error occurred: {e}")
    
    def _is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        # Simplified authentication check
        return st.session_state.get('authenticated', False)
    
    def _route_page(self, page: str):
        """Route to the appropriate page"""
        page_handlers = {
            'Live Dashboard': render_dashboard,
            'Muscle Activation': render_muscle_activation,
            'Coral Orchestration': render_coral_orchestration,
            'User Profile': render_user_profile,
            'AI Coach Chat': render_ai_coach,
            'Progress Analytics': render_progress_analytics
        }
        
        handler = page_handlers.get(page)
        if handler:
            handler(self.service_manager)
        else:
            st.error(f"Unknown page: {page}")


def main():
    """Main application entry point"""
    app = CoreSenseApp()
    app.run()


if __name__ == "__main__":
    main()