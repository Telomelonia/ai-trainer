"""
CoreSense AI Platform - Common UI Components
Shared UI components and utilities
"""

import streamlit as st
from typing import Dict, Any, Optional
import random
from datetime import datetime
from core.services import ServiceManager
from core.logging import get_logger

logger = get_logger(__name__)


def setup_page_config():
    """Setup Streamlit page configuration"""
    st.set_page_config(
        page_title="CoreSense AI Platform",
        page_icon="💫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
        .metric-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #6C63FF;
        }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-danger { color: #dc3545; }
        .coresense-header {
            background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        .muscle-activation-chart {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #6C63FF;
        }
    </style>
    """, unsafe_allow_html=True)


def setup_sidebar(service_manager: ServiceManager) -> str:
    """
    Setup sidebar with navigation and system status
    
    Args:
        service_manager: Service manager instance
        
    Returns:
        Selected page name
    """
    st.sidebar.title("💫 CoreSense AI")
    
    # System status display
    st.sidebar.markdown("### 🔧 System Status")
    
    # Check service statuses
    services_status = {
        'sensor_manager': 'Multi-Sensor Platform',
        'agent_orchestrator': 'AI Agent System',
        'fabric_sensor_agent': 'Fabric Sensors',
        'auth': 'Authentication',
        'database': 'Database'
    }
    
    for service_key, display_name in services_status.items():
        status = service_manager.get_service_status(service_key)
        if status and status.available:
            icon = "🟢" if status.initialized else "🟡"
            status_text = "Ready" if status.initialized else "Available"
        else:
            icon = "🔴"
            status_text = "Unavailable"
        
        st.sidebar.markdown(f"**{display_name}:** {icon} {status_text}")
    
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.selectbox("Navigate", [
        "Live Dashboard", 
        "Muscle Activation", 
        "Coral Orchestration",
        "User Profile", 
        "AI Coach Chat", 
        "Progress Analytics"
    ])
    
    return page


def get_current_data(service_manager: ServiceManager) -> Dict[str, Any]:
    """
    Get current sensor/stability data
    
    Args:
        service_manager: Service manager instance
        
    Returns:
        Current data dictionary
    """
    # Try to get data from sensor manager
    sensor_manager = service_manager.get_service('sensor_manager')
    if sensor_manager:
        try:
            # Get primary sensor data
            return sensor_manager.get_current_data()
        except Exception as e:
            logger.warning(f"Failed to get sensor data: {e}")
    
    # Fallback to simulation
    return simulate_stability_data()


def simulate_stability_data() -> Dict[str, Any]:
    """Generate realistic stability data for testing"""
    base_score = 85
    variation = random.uniform(-10, 10)
    score = max(50, min(100, base_score + variation))
    
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "stability_score": round(score, 1),
        "movement_variance": round(random.uniform(0.1, 0.8), 2),
        "form_quality": "Excellent" if score > 90 else "Good" if score > 75 else "Needs Improvement",
        "session_duration": f"{random.randint(1, 5)}:{random.randint(10, 59):02d}",
        "source": "simulation"
    }


def render_header(title: str, subtitle: str = None):
    """
    Render CoreSense header
    
    Args:
        title: Page title
        subtitle: Optional subtitle
    """
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
    <div class="coresense-header">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_service_status(service_manager: ServiceManager):
    """
    Render detailed service status information
    
    Args:
        service_manager: Service manager instance
    """
    st.subheader("🔧 System Services")
    
    services = service_manager.get_all_services()
    
    if not services:
        st.warning("No services registered")
        return
    
    for name, status in services.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{name.replace('_', ' ').title()}**")
        
        with col2:
            if status.available:
                if status.initialized:
                    st.success("✅ Ready")
                else:
                    st.warning("🟡 Available")
            else:
                st.error("❌ Unavailable")
        
        with col3:
            if status.error:
                st.error(f"Error: {status.error[:50]}...")


def show_loading(message: str = "Loading..."):
    """Show loading spinner with message"""
    return st.spinner(message)


def render_metric_card(label: str, value: str, delta: str = None, help_text: str = None):
    """
    Render a metric card
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        help_text: Optional help text
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help_text
    )