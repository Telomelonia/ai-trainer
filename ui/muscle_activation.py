"""
CoreSense AI Platform - Muscle Activation UI
Real-time muscle activation monitoring interface
"""

import streamlit as st
import time
from typing import Dict, Any
from core.services import ServiceManager
from core.logging import get_logger
from ui.common import render_header

logger = get_logger(__name__)


def render_muscle_activation(service_manager: ServiceManager):
    """
    Render the muscle activation monitoring page
    
    Args:
        service_manager: Service manager instance
    """
    render_header("💫 CoreSense Muscle Activation", "Real-time Fabric Sensor Analysis")
    
    # Initialize session state
    if 'fabric_monitoring_active' not in st.session_state:
        st.session_state.fabric_monitoring_active = False
        st.session_state.exercise_type = "plank"
    
    # Exercise selection and controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.session_state.exercise_type = st.selectbox(
            "Select Exercise",
            ["plank", "side_plank", "dead_bug", "bird_dog"],
            format_func=lambda x: x.replace("_", " ").title()
        )
    
    with col2:
        if st.button("🚀 Start Monitoring", disabled=st.session_state.fabric_monitoring_active):
            if _start_muscle_monitoring(service_manager):
                st.session_state.fabric_monitoring_active = True
                st.success("CoreSense monitoring started!")
            else:
                st.error("Failed to start monitoring")
    
    with col3:
        if st.button("⏹️ Stop Monitoring", disabled=not st.session_state.fabric_monitoring_active):
            if _stop_muscle_monitoring(service_manager):
                st.session_state.fabric_monitoring_active = False
                st.success("Monitoring stopped!")
    
    # Display muscle activation data
    if st.session_state.fabric_monitoring_active:
        _render_active_monitoring(service_manager)
    else:
        _render_monitoring_info()


def _start_muscle_monitoring(service_manager: ServiceManager) -> bool:
    """
    Start muscle activation monitoring
    
    Args:
        service_manager: Service manager instance
        
    Returns:
        True if monitoring started successfully
    """
    fabric_agent = service_manager.get_service('fabric_sensor_agent')
    if fabric_agent:
        try:
            # Start monitoring session
            result = fabric_agent.start_monitoring_session(
                user_id="demo_user",
                exercise=st.session_state.exercise_type
            )
            return not result.get('error')
        except Exception as e:
            logger.error(f"Failed to start muscle monitoring: {e}")
            return False
    
    logger.warning("Fabric sensor agent not available")
    return False


def _stop_muscle_monitoring(service_manager: ServiceManager) -> bool:
    """
    Stop muscle activation monitoring
    
    Args:
        service_manager: Service manager instance
        
    Returns:
        True if monitoring stopped successfully
    """
    fabric_agent = service_manager.get_service('fabric_sensor_agent')
    if fabric_agent:
        try:
            result = fabric_agent.stop_monitoring_session("demo_user")
            return not result.get('error')
        except Exception as e:
            logger.error(f"Failed to stop muscle monitoring: {e}")
            return False
    
    return False


def _render_active_monitoring(service_manager: ServiceManager):
    """
    Render active muscle monitoring interface
    
    Args:
        service_manager: Service manager instance
    """
    fabric_agent = service_manager.get_service('fabric_sensor_agent')
    
    if fabric_agent:
        try:
            # Get real-time muscle data
            muscle_data = fabric_agent.get_current_activation("demo_user")
            
            if muscle_data and not muscle_data.get('error'):
                _render_muscle_metrics(muscle_data)
                _render_coaching_insights(muscle_data)
                
                # Auto-refresh for real-time updates
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error getting muscle data")
                
        except Exception as e:
            st.error(f"Error in muscle monitoring: {e}")
    else:
        st.error("Fabric sensor agent not available")


def _render_muscle_metrics(muscle_data: Dict[str, Any]):
    """
    Render muscle activation metrics
    
    Args:
        muscle_data: Muscle activation data
    """
    st.markdown('<div class="muscle-activation-chart">', unsafe_allow_html=True)
    st.subheader("💪 Real-time Muscle Activation")
    
    activation = muscle_data.get("activation_map", {})
    
    # Display muscle activation in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Upper Rectus", f"{activation.get('upper_rectus', 0):.2f}", "Core Upper")
        st.metric("Lower Rectus", f"{activation.get('lower_rectus', 0):.2f}", "Core Lower")
    
    with col2:
        st.metric("Right Oblique", f"{activation.get('right_oblique', 0):.2f}", "Side Right")
        st.metric("Left Oblique", f"{activation.get('left_oblique', 0):.2f}", "Side Left")
    
    with col3:
        st.metric("Transverse", f"{activation.get('transverse', 0):.2f}", "Deep Core")
        st.metric("Erector Spinae", f"{activation.get('erector_spinae', 0):.2f}", "Lower Back")
    
    # Overall quality metrics
    col1, col2 = st.columns(2)
    
    with col1:
        quality_score = muscle_data.get("quality_score", 0)
        delta = "↗️ Excellent" if quality_score > 85 else "→ Good" if quality_score > 70 else "↘️ Needs Work"
        st.metric("Quality Score", f"{quality_score}%", delta)
    
    with col2:
        compensation = muscle_data.get("compensation_detected", False)
        compensation_text = "❌ Detected" if compensation else "✅ None"
        st.metric("Compensation", compensation_text)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_coaching_insights(muscle_data: Dict[str, Any]):
    """
    Render AI coaching insights
    
    Args:
        muscle_data: Muscle activation data
    """
    st.subheader("🤖 AI Coaching Insights")
    
    compensation = muscle_data.get("compensation_detected", False)
    coaching_priority = muscle_data.get("coaching_priority", "")
    primary_muscles = muscle_data.get("primary_muscles", [])
    
    if compensation:
        compensation_type = muscle_data.get("compensation_type", "Unknown")
        st.error(f"⚠️ **Compensation Detected**: {compensation_type}")
        st.warning(f"💡 **AI Coaching**: {coaching_priority}")
    else:
        st.success("✅ Optimal muscle activation pattern!")
        st.info(f"💡 {coaching_priority}")
    
    # Primary activated muscles
    if primary_muscles:
        st.markdown("**Primary Activated Muscles:**")
        for muscle in primary_muscles:
            st.markdown(f"• {muscle.replace('_', ' ').title()}")
    
    # Sensor status
    st.markdown("---")
    st.markdown("### 📡 Sensor Status")
    st.info("🔬 **Mode**: Fabric Sensor Simulation")
    st.caption("Hardware compression band: Phase 2 development")


def _render_monitoring_info():
    """Render information when monitoring is not active"""
    st.info("👆 Click 'Start Monitoring' to begin CoreSense muscle activation analysis")
    
    # Show example data or instructions
    st.subheader("💡 About Muscle Activation Monitoring")
    
    st.markdown("""
    **CoreSense Fabric Sensor Technology:**
    
    - **6-Zone Sensor Array**: Monitors all major core muscle groups
    - **Real-time Analysis**: Instant feedback on muscle activation patterns
    - **Compensation Detection**: Identifies when you're using the wrong muscles
    - **AI Coaching**: Personalized guidance for optimal form
    
    **Monitored Muscle Groups:**
    - Upper & Lower Rectus Abdominis (front core)
    - Left & Right Obliques (side core)
    - Transverse Abdominis (deep core)
    - Erector Spinae (lower back)
    """)
    
    # Exercise selection guide
    st.subheader("🎯 Exercise Guide")
    
    exercise_guide = {
        "Plank": "Full core engagement, focus on stability",
        "Side Plank": "Lateral core strength and balance", 
        "Dead Bug": "Core control and coordination",
        "Bird Dog": "Core stability with limb movement"
    }
    
    for exercise, description in exercise_guide.items():
        st.markdown(f"**{exercise}**: {description}")