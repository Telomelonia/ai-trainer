"""
CoreSense AI Platform - Remaining UI Components
Minimal implementations for complete application
"""

import streamlit as st
from core.services import ServiceManager
from ui.common import render_header


def render_user_profile(service_manager: ServiceManager):
    """Render user profile page"""
    render_header("👤 User Profile", "Manage your training preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        user_name = st.text_input("Name", value="Training Enthusiast")
        user_age = st.number_input("Age", min_value=18, max_value=100, value=28)
        fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])
        
        st.subheader("Training Goals")
        goals = st.multiselect(
            "Select your goals:",
            ["Core Strength", "Balance", "Stability", "Injury Prevention"],
            default=["Core Strength", "Stability"]
        )
    
    with col2:
        st.subheader("Training Preferences")
        session_duration = st.slider("Session Duration (minutes)", 10, 60, 30)
        difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")
        
        if st.button("Save Profile", type="primary"):
            st.success("Profile saved successfully!")


def render_ai_coach(service_manager: ServiceManager):
    """Render AI coach chat page"""
    render_header("🤖 AI Coach", "Your intelligent training assistant")
    
    # Check if AI agent is available
    core_agent = service_manager.get_service('core_training_agent')
    
    if core_agent:
        st.success("🟢 AI Agent Active")
    else:
        st.warning("🟡 Basic Mode - AI agent not available")
    
    # Simple chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm your CoreSense AI coach. How can I help you today?"}
        ]
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your training..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simple response logic
        with st.chat_message("assistant"):
            if "form" in prompt.lower():
                response = "Focus on proper alignment and controlled breathing for better form."
            elif "exercise" in prompt.lower():
                response = "I recommend starting with planks, dead bugs, and bird dogs."
            else:
                response = "That's a great question! For core training, consistency is key."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


def render_progress_analytics(service_manager: ServiceManager):
    """Render progress analytics page"""
    render_header("📊 Progress Analytics", "Track your training progress")
    
    # Mock data for demo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", "23", "↗️ +3")
    with col2:
        st.metric("Avg Stability", "84.2%", "↗️ +2.1%")
    with col3:
        st.metric("Training Hours", "15.5h", "↗️ +2.3h")
    with col4:
        st.metric("Current Streak", "7 days", "🔥")
    
    # Simple progress visualization
    st.subheader("Weekly Progress")
    
    progress_data = {
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Score': [78, 81, 85, 82, 87, 89, 84]
    }
    
    st.line_chart(progress_data, x='Day', y='Score')
    
    # Insights
    st.subheader("🎯 Insights")
    insights = [
        "🎉 You've improved by 12% this week!",
        "💪 7 consecutive training days - excellent consistency!",
        "🎯 Focus on longer holds to reach 90% stability goal"
    ]
    
    for insight in insights:
        st.info(insight)


def render_auth_ui():
    """Render authentication UI"""
    render_header("🔐 CoreSense Login", "Access your personalized training")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to CoreSense")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            if username and password:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Please enter username and password")
    
    with tab2:
        st.subheader("Create Account")
        new_username = st.text_input("Choose Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Choose Password", type="password")
        
        if st.button("Sign Up", type="primary"):
            if new_username and new_email and new_password:
                st.success("Account created! Please login.")
            else:
                st.error("Please fill all fields")