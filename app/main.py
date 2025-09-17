import streamlit as st
import json
import random
from datetime import datetime
import time
import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
try:
    from arduino_connector import ArduinoConnector
    ARDUINO_AVAILABLE = True
except ImportError as e:
    st.warning(f"Arduino connector not available: {e}")
    ARDUINO_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Core Training AI Ecosystem",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-danger { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Navigation sidebar
st.sidebar.title("🏋️ Core Training AI")
page = st.sidebar.selectbox("Navigate", [
    "Live Dashboard", 
    "User Profile", 
    "AI Coach Chat", 
    "Progress Analytics"
])

# Initialize Arduino connector in session state
if 'arduino_connector' not in st.session_state:
    if ARDUINO_AVAILABLE:
        st.session_state.arduino_connector = ArduinoConnector(simulation_mode=True)
    else:
        st.session_state.arduino_connector = None

# Get Arduino connector
arduino = st.session_state.arduino_connector

# Simulation data function (fallback if Arduino connector fails)
def simulate_stability_data():
    """Generate realistic stability data for testing"""
    base_score = 85
    variation = random.uniform(-10, 10)
    score = max(50, min(100, base_score + variation))
    
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "stability_score": round(score, 1),
        "movement_variance": round(random.uniform(0.1, 0.8), 2),
        "form_quality": "Excellent" if score > 90 else "Good" if score > 75 else "Needs Improvement",
        "session_duration": f"{random.randint(1, 5)}:{random.randint(10, 59):02d}"
    }

# Get current data from Arduino or simulation
def get_current_data():
    """Get current stability data"""
    if arduino and ARDUINO_AVAILABLE:
        try:
            return arduino.get_current_stability_data()
        except Exception as e:
            st.error(f"Arduino error: {e}")
            return simulate_stability_data()
    else:
        return simulate_stability_data()

# Page routing
if page == "Live Dashboard":
    st.title("🏋️ Core Stability Monitor")
    st.markdown("### Real-time Training Analytics")
    
    # Get simulated data
    data = get_current_data()
    
    # Real-time metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Stability Score", 
            value=f"{data['stability_score']}%", 
            delta="↗️ +5%" if data['stability_score'] > 80 else "↘️ -2%"
        )
    
    with col2:
        quality_color = "status-good" if data['form_quality'] == "Excellent" else "status-warning" if data['form_quality'] == "Good" else "status-danger"
        st.metric(
            label="Form Quality", 
            value=data['form_quality']
        )
    
    with col3:
        st.metric(
            label="Session Duration", 
            value=data['session_duration'], 
            delta="⏱️"
        )
    
    with col4:
        st.metric(
            label="Movement Variance", 
            value=f"{data['movement_variance']}", 
            delta="📊"
        )
    
    # Live data section
    st.markdown("---")
    col_chart, col_feedback = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📈 Real-time Stability Chart")
        
        # Placeholder for live chart (will implement with real data)
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
        
        # Display simple chart
        chart_data = {
            'Time': [point['time'] for point in st.session_state.stability_history],
            'Stability Score': [point['score'] for point in st.session_state.stability_history]
        }
        st.line_chart(chart_data, x='Time', y='Stability Score')
    
    with col_feedback:
        st.subheader("🤖 AI Coaching")
        
        # Generate coaching feedback based on score
        if data['stability_score'] > 90:
            feedback = "🎉 Excellent form! Try increasing hold duration to 45 seconds."
            feedback_type = "success"
        elif data['stability_score'] > 75:
            feedback = "✅ Good stability. Focus on controlled breathing and core engagement."
            feedback_type = "info"
        else:
            feedback = "⚠️ Engage core muscles more. Reduce unnecessary movement and focus on your center."
            feedback_type = "warning"
        
        st.markdown(f"**Current Advice:**")
        if feedback_type == "success":
            st.success(feedback)
        elif feedback_type == "info":
            st.info(feedback)
        else:
            st.warning(feedback)
        
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
    
    # Auto-refresh button
    if st.button("🔄 Refresh Data", type="primary"):
        st.rerun()
    
    # Auto-refresh every 2 seconds (for demo purposes)
    time.sleep(2)
    st.rerun()

elif page == "User Profile":
    st.title("👤 User Profile & Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        user_name = st.text_input("Name", value="Training Enthusiast")
        user_age = st.number_input("Age", min_value=18, max_value=100, value=28)
        fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])
        
        st.subheader("Training Goals")
        goals = st.multiselect(
            "Select your goals:",
            ["Core Strength", "Balance", "Stability", "Injury Prevention", "Athletic Performance"],
            default=["Core Strength", "Stability"]
        )
    
    with col2:
        st.subheader("Training Preferences")
        session_duration = st.slider("Preferred Session Duration (minutes)", 10, 60, 30)
        difficulty = st.select_slider("Difficulty Level", options=["Easy", "Medium", "Hard"], value="Medium")
        
        st.subheader("Health Considerations")
        injuries = st.text_area("Any injuries or limitations?", placeholder="e.g., Lower back issues, knee problems...")
        
        if st.button("Save Profile", type="primary"):
            st.success("Profile saved successfully!")
            st.balloons()

elif page == "AI Coach Chat":
    st.title("🤖 AI Personal Trainer Chat")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm your AI Core Training Coach. How can I help you improve your training today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your training..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response (simplified for demo)
        with st.chat_message("assistant"):
            if "stability" in prompt.lower():
                response = "Based on your current stability score, I recommend focusing on static holds and breathing control. Try maintaining a plank position while focusing on slow, controlled breaths."
            elif "exercise" in prompt.lower():
                response = "Here are some core exercises tailored to your current level: 1) Modified plank (30s), 2) Dead bug (10 reps), 3) Side plank (15s each side). Focus on quality over quantity!"
            elif "form" in prompt.lower():
                response = "Great question about form! Keep your core engaged, maintain neutral spine alignment, and avoid holding your breath. Quality movement is more important than speed."
            else:
                response = f"That's a great question about '{prompt}'. Based on your training data, I suggest focusing on consistent practice and gradual progression. Would you like specific exercise recommendations?"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

elif page == "Progress Analytics":
    st.title("📊 Progress Analytics & Reports")
    
    # Time period selector
    col1, col2 = st.columns([1, 3])
    with col1:
        time_period = st.selectbox("Time Period", ["Last 7 Days", "Last 30 Days", "Last 3 Months"])
    
    # Mock analytics data
    st.subheader("Training Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", "23", "↗️ +3")
    with col2:
        st.metric("Avg Stability Score", "84.2%", "↗️ +2.1%")
    with col3:
        st.metric("Training Hours", "15.5h", "↗️ +2.3h")
    with col4:
        st.metric("Streak", "7 days", "🔥")
    
    # Progress charts
    st.subheader("Progress Over Time")
    
    # Mock data for progress chart (simplified without pandas)
    dates = ["Sep 10", "Sep 11", "Sep 12", "Sep 13", "Sep 14", "Sep 15", "Sep 16", "Sep 17"]
    stability_scores = [78, 79, 81, 83, 82, 85, 87, 84]
    session_durations = [25, 28, 30, 32, 30, 35, 38, 35]
    
    # Create chart data
    progress_data = {
        'Date': dates,
        'Stability Score': stability_scores
    }
    
    duration_data = {
        'Date': dates, 
        'Session Duration': session_durations
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.line_chart(progress_data, x='Date', y='Stability Score')
        st.caption("Stability Score Trend")
    
    with col2:
        st.bar_chart(duration_data, x='Date', y='Session Duration')
        st.caption("Session Duration (minutes)")
    
    # Insights
    st.subheader("🎯 Training Insights")
    insights = [
        "🎉 You've improved your stability score by 12% this week!",
        "💪 Your consistency has been excellent with 7 consecutive training days",
        "⏰ Consider increasing session duration to 40+ minutes for better results",
        "🎯 Focus on balance exercises to reach your 90% stability goal"
    ]
    
    for insight in insights:
        st.info(insight)

# Footer
st.markdown("---")
st.markdown("**Core Training AI Ecosystem** | Built for Internet of Agents Hackathon 2025")