"""
CoreSense AI Platform - Dashboard UI
Live monitoring dashboard with real-time data
"""

import streamlit as st
import time
from typing import Dict, Any
from core.services import ServiceManager
from core.logging import get_logger
from ui.common import render_header, get_current_data, render_metric_card

logger = get_logger(__name__)


def render_dashboard(service_manager: ServiceManager):
    """
    Render the live dashboard page
    
    Args:
        service_manager: Service manager instance
    """
    render_header("💫 CoreSense Live Dashboard", "Real-time Core Stability Intelligence")
    
    # Get current data
    data = get_current_data(service_manager)
    
    # Real-time metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = "↗️ +5%" if data['stability_score'] > 80 else "↘️ -2%"
        render_metric_card(
            "Stability Score", 
            f"{data['stability_score']}%", 
            delta
        )
    
    with col2:
        render_metric_card(
            "Form Quality", 
            data['form_quality']
        )
    
    with col3:
        render_metric_card(
            "Session Duration", 
            data['session_duration'], 
            "⏱️"
        )
    
    with col4:
        render_metric_card(
            "Movement Variance", 
            f"{data['movement_variance']}", 
            "📊"
        )
    
    # Live data section
    st.markdown("---")
    col_chart, col_feedback = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📈 Real-time Stability Chart")
        
        # Initialize stability history in session state
        if 'stability_history' not in st.session_state:
            st.session_state.stability_history = []
        
        # Add current data point
        st.session_state.stability_history.append({
            'time': data['timestamp'],
            'score': data['stability_score']
        })
        
        # Keep only last 20 data points
        if len(st.session_state.stability_history) > 20:
            st.session_state.stability_history.pop(0)
        
        # Display chart
        if st.session_state.stability_history:
            chart_data = {
                'Time': [point['time'] for point in st.session_state.stability_history],
                'Stability Score': [point['score'] for point in st.session_state.stability_history]
            }
            st.line_chart(chart_data, x='Time', y='Stability Score')
    
    with col_feedback:
        st.subheader("🤖 AI Coaching")
        
        # Get AI coaching feedback
        feedback = _generate_coaching_feedback(data, service_manager)
        
        st.markdown("**Current Advice:**")
        if feedback['type'] == "success":
            st.success(feedback['message'])
        elif feedback['type'] == "info":
            st.info(feedback['message'])
        else:
            st.warning(feedback['message'])
        
        # Exercise recommendations
        st.markdown("**Recommended Exercises:**")
        exercises = [
            "Plank Hold - 30s",
            "Dead Bug - 10 reps",
            "Bird Dog - 8 reps each side",
            "Pallof Press - 12 reps"
        ]
        for exercise in exercises:
            st.markdown(f"• {exercise}")
    
    # Service status
    with st.expander("🔧 System Status"):
        from ui.common import render_service_status
        render_service_status(service_manager)
    
    # Auto-refresh controls
    col1, col2 = st.columns([1, 3])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=True)
    with col2:
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(2)
        st.rerun()


def _generate_coaching_feedback(data: Dict[str, Any], service_manager: ServiceManager) -> Dict[str, str]:
    """
    Generate coaching feedback based on current data
    
    Args:
        data: Current stability data
        service_manager: Service manager instance
        
    Returns:
        Feedback dictionary with type and message
    """
    score = data['stability_score']
    
    # Try to get AI coaching from agents
    core_agent = service_manager.get_service('core_training_agent')
    if core_agent:
        try:
            # Get AI-generated coaching
            coaching = core_agent.get_coaching_feedback(data)
            return {
                'type': coaching.get('type', 'info'),
                'message': coaching.get('message', 'Keep up the good work!')
            }
        except Exception as e:
            logger.warning(f"AI coaching not available: {e}")
    
    # Fallback to rule-based feedback
    if score > 90:
        return {
            'type': 'success',
            'message': '🎉 Excellent form! Try increasing hold duration to 45 seconds.'
        }
    elif score > 75:
        return {
            'type': 'info', 
            'message': '✅ Good stability. Focus on controlled breathing and core engagement.'
        }
    else:
        return {
            'type': 'warning',
            'message': '⚠️ Engage core muscles more. Reduce unnecessary movement and focus on your center.'
        }