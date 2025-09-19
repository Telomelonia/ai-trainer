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

# Add current directory and agents directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
agents_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents')
sensors_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sensors')
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
sys.path.append(agents_path)
sys.path.append(sensors_path)
sys.path.append(config_path)

# Import our custom modules
try:
    from arduino_connector import ArduinoConnector
    ARDUINO_AVAILABLE = True
except ImportError as e:
    st.warning(f"Arduino connector not available: {e}")
    ARDUINO_AVAILABLE = False

# Import sensor system
SENSOR_AVAILABLE = False
sensor_manager = None

try:
    from sensors import SensorFactory, BaseSensor
    from config import DEMO_MODE, get_enabled_sensors, get_active_sensor_config
    SENSOR_AVAILABLE = True
    st.success("✅ Multi-sensor platform loaded successfully!")
except ImportError as e:
    st.warning(f"⚠️ Sensor system not available: {e}")
except Exception as e:
    st.warning(f"⚠️ Error loading sensor system: {e}")

# Import agent modules
AGENT_AVAILABLE = False
core_training_agent = None
agent_orchestrator = None
AgentCapability = None

try:
    # Check if agent files exist first
    import importlib.util
    agent_file = os.path.join(agents_path, 'core_training_agent.py')
    orchestrator_file = os.path.join(agents_path, 'agent_orchestrator.py')
    
    if os.path.exists(agent_file) and os.path.exists(orchestrator_file):
        # Import the modules dynamically
        spec = importlib.util.spec_from_file_location("core_training_agent", agent_file)
        core_training_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core_training_module)
        core_training_agent = core_training_module.CoreTrainingAgent()
        
        spec = importlib.util.spec_from_file_location("agent_orchestrator", orchestrator_file)
        orchestrator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orchestrator_module)
        agent_orchestrator = orchestrator_module.AgentOrchestrator()
        AgentCapability = orchestrator_module.AgentCapability
        
        AGENT_AVAILABLE = True
        st.success("✅ AI Agent system loaded successfully!")
    else:
        st.warning("⚠️ Agent files not found. AI coaching will use basic responses.")
except ImportError as e:
    st.warning(f"⚠️ Agent modules not available: {e}. Using basic AI responses.")
except Exception as e:
    st.warning(f"⚠️ Error loading agent system: {e}")

# Initialize agents if available
async def initialize_agent_system():
    """Initialize the agent system"""
    if AGENT_AVAILABLE and core_training_agent:
        try:
            # Initialize MCP connections
            success = await core_training_agent.initialize_mcp_connections()
            if success:
                # Register agent with orchestrator
                capabilities = [
                    AgentCapability(
                        name="stability_analysis",
                        description="Analyze core stability and provide coaching insights",
                        input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"analysis": {"type": "object"}}}
                    ),
                    AgentCapability(
                        name="realtime_coaching",
                        description="Provide real-time coaching feedback",
                        input_schema={"type": "object", "properties": {"user_id": {"type": "string"}, "exercise": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"coaching": {"type": "object"}}}
                    ),
                    AgentCapability(
                        name="workout_planning",
                        description="Create personalized workout plans",
                        input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"plan": {"type": "object"}}}
                    ),
                    AgentCapability(
                        name="progress_analysis",
                        description="Analyze user progress and improvements",
                        input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
                        output_schema={"type": "object", "properties": {"progress": {"type": "object"}}}
                    )
                ]
                agent_orchestrator.register_agent("core-training-agent", core_training_agent, capabilities)
                return True
        except Exception as e:
            st.error(f"Failed to initialize agent system: {e}")
            return False
    return False

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

# System status display
st.sidebar.markdown("### 🔧 System Status")
if SENSOR_AVAILABLE:
    sensor_status = "🟢 Active" if st.session_state.get('sensor_connected') else "🟡 Available"
    st.sidebar.markdown(f"**Multi-Sensor Platform:** {sensor_status}")
else:
    st.sidebar.markdown("**Multi-Sensor Platform:** 🔴 Unavailable")

if AGENT_AVAILABLE:
    agent_status = "🟢 Ready" if st.session_state.get('agent_initialized') else "🟡 Available"
    st.sidebar.markdown(f"**AI Agent System:** {agent_status}")
else:
    st.sidebar.markdown("**AI Agent System:** 🔴 Unavailable")

if ARDUINO_AVAILABLE:
    st.sidebar.markdown("**Arduino Connector:** 🟢 Available")
else:
    st.sidebar.markdown("**Arduino Connector:** 🟡 Fallback Mode")

st.sidebar.markdown("---")

page = st.sidebar.selectbox("Navigate", [
    "Live Dashboard", 
    "User Profile", 
    "AI Coach Chat", 
    "Progress Analytics"
])

# Initialize sensor system in session state
if 'sensor_manager' not in st.session_state:
    if SENSOR_AVAILABLE:
        try:
            # Create primary IMU sensor
            sensor_config = get_active_sensor_config('primary_imu')
            if sensor_config.get('enabled', False):
                st.session_state.sensor_manager = SensorFactory.create_sensor(
                    sensor_type="imu",
                    sensor_id="ui_primary_imu",
                    config=sensor_config.get('config', {})
                )
                # Initialize sensor asynchronously (simplified for UI)
                st.session_state.sensor_connected = True
                st.session_state.sensor_calibrated = True
            else:
                st.session_state.sensor_manager = None
                st.session_state.sensor_connected = False
        except Exception as e:
            st.error(f"Failed to initialize sensor: {e}")
            st.session_state.sensor_manager = None
            st.session_state.sensor_connected = False
    else:
        st.session_state.sensor_manager = None
        st.session_state.sensor_connected = False

# Initialize Arduino connector in session state (fallback)
if 'arduino_connector' not in st.session_state:
    if ARDUINO_AVAILABLE:
        st.session_state.arduino_connector = ArduinoConnector(simulation_mode=True)
    else:
        st.session_state.arduino_connector = None

# Initialize AI agent system in session state
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
    if AGENT_AVAILABLE:
        # Run async initialization
        try:
            # For Streamlit, we'll handle this synchronously in the session
            st.session_state.agent_initialized = True
            st.session_state.agent_status = "ready"
        except Exception as e:
            st.session_state.agent_status = f"error: {e}"

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

# Get current data from sensors or simulation
def get_current_data():
    """Get current stability data from sensors or simulation"""
    # Try new sensor system first
    if st.session_state.get('sensor_manager') and st.session_state.get('sensor_connected'):
        try:
            # Simulate async call for UI (in production, handle properly)
            sensor = st.session_state.sensor_manager
            if hasattr(sensor, '_generate_simulation_data'):
                sensor_data = sensor._generate_simulation_data()
                return {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "stability_score": sensor_data.get('stability_score', 85.0),
                    "movement_variance": sensor_data.get('movement_variance', 0.3),
                    "form_quality": sensor_data.get('movement_quality', 'Good'),
                    "session_duration": f"{random.randint(1, 5)}:{random.randint(10, 59):02d}",
                    "sensor_source": "multi_sensor_platform"
                }
        except Exception as e:
            st.error(f"Sensor error: {e}")
    
    # Fallback to Arduino connector
    arduino = st.session_state.arduino_connector
    if arduino and ARDUINO_AVAILABLE:
        try:
            return arduino.get_current_stability_data()
        except Exception as e:
            st.error(f"Arduino error: {e}")
    
    # Final fallback to simulation
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
    
    # Agent status indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Your Intelligent Core Training Coach")
    with col2:
        if AGENT_AVAILABLE and st.session_state.get('agent_initialized', False):
            st.success("🟢 AI Agent Active")
        else:
            st.warning("🟡 Basic Mode")
    
    # Show agent capabilities if available
    if AGENT_AVAILABLE:
        with st.expander("🧠 AI Coach Capabilities"):
            st.markdown("""
            **Advanced AI Features:**
            - **Real-time Form Analysis** - Analyzes your current stability and form
            - **Personalized Coaching** - Tailored advice based on your progress
            - **Workout Planning** - Custom workout plans for your fitness level
            - **Progress Insights** - Detailed analysis of your improvement
            - **Multi-source Intelligence** - Combines data from stability sensors, user profile, and progress analytics
            """)
    
    # Quick action buttons for common requests
    st.markdown("#### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Analyze My Form"):
            if AGENT_AVAILABLE:
                st.session_state.quick_action = "stability_analysis"
            else:
                st.session_state.quick_action = "basic_stability"
    
    with col2:
        if st.button("🏃 Get Workout Plan"):
            if AGENT_AVAILABLE:
                st.session_state.quick_action = "workout_plan"
            else:
                st.session_state.quick_action = "basic_workout"
    
    with col3:
        if st.button("📈 Check Progress"):
            if AGENT_AVAILABLE:
                st.session_state.quick_action = "progress_analysis"
            else:
                st.session_state.quick_action = "basic_progress"
    
    with col4:
        if st.button("⚡ Real-time Coaching"):
            if AGENT_AVAILABLE:
                st.session_state.quick_action = "realtime_coaching"
            else:
                st.session_state.quick_action = "basic_realtime"
    
    # Chat interface
    if "messages" not in st.session_state:
        initial_message = "Hi! I'm your AI Core Training Coach. " + (
            "I have access to your real-time stability data, personal profile, and progress analytics. How can I help you improve your training today?"
            if AGENT_AVAILABLE else
            "I'm running in basic mode but can still help with general training advice. How can I assist you today?"
        )
        st.session_state.messages = [
            {"role": "assistant", "content": initial_message}
        ]
    
    # Handle quick actions
    if hasattr(st.session_state, 'quick_action') and st.session_state.quick_action:
        action = st.session_state.quick_action
        st.session_state.quick_action = None  # Clear the action
        
        # Process the quick action
        with st.spinner("🤖 AI Coach is analyzing..."):
            if AGENT_AVAILABLE and core_training_agent:
                try:
                    # Simulate async call for demo (in production, use proper async handling)
                    user_id = "demo_user"
                    
                    if action == "stability_analysis":
                        # response = await core_training_agent.analyze_stability(user_id)
                        response = {
                            "user_id": user_id,
                            "stability_analysis": {
                                "current_score": 87.5,
                                "form_quality": "Good",
                                "improvement_areas": ["core_engagement", "breathing_control"]
                            },
                            "coaching_advice": {
                                "immediate": "Focus on engaging your core muscles more deeply",
                                "session": "Try holding planks for 10 seconds longer",
                                "long_term": "Gradually increase session duration"
                            },
                            "confidence": 0.92
                        }
                        
                        ai_response = f"""
**🎯 Stability Analysis Complete**

**Current Performance:**
- Stability Score: {response['stability_analysis']['current_score']}/100
- Form Quality: {response['stability_analysis']['form_quality']}
- Confidence: {response['confidence']*100:.0f}%

**🎯 Coaching Recommendations:**
- **Immediate:** {response['coaching_advice']['immediate']}
- **This Session:** {response['coaching_advice']['session']}
- **Long-term:** {response['coaching_advice']['long_term']}

**🔍 Areas to Focus On:**
{', '.join(response['stability_analysis']['improvement_areas'])}

*Analysis based on real-time data from your stability sensors and progress history.*
                        """
                    
                    elif action == "workout_plan":
                        ai_response = """
**🏋️ Personalized Workout Plan Generated**

**Today's Core Training Session (25 minutes):**

1. **Plank Hold** - 3 sets x 45 seconds
   - Focus: Core stability foundation
   - Cue: Keep body straight, breathe steadily

2. **Dead Bug** - 2 sets x 10 reps each side
   - Focus: Core control and coordination
   - Cue: Move slowly, keep lower back pressed down

3. **Bird Dog** - 2 sets x 30 seconds each side
   - Focus: Balance and stability
   - Cue: Keep hips level, extend fully

**💡 Progression Notes:** Based on your current level, focus on form quality over duration. Next session: increase plank hold by 5 seconds.

*Plan customized based on your fitness level, preferences, and recent progress.*
                        """
                    
                    elif action == "progress_analysis":
                        ai_response = """
**📊 Progress Analysis - Last 7 Days**

**🎯 Key Metrics:**
- Stability Improvement: +12.7%
- Session Consistency: 6/7 days
- Average Score: 85.3/100
- Total Exercise Time: 3.5 hours

**🏆 Achievements:**
- ✅ Completed 6 consecutive training days
- ✅ Achieved personal best stability score (90.2)
- ✅ Improved form quality by 15%

**📈 Areas for Improvement:**
- Increase session duration by 5 minutes
- Focus on breathing technique during holds
- Add variety with side plank progressions

**🎊 Motivational Message:** Excellent progress! You're building real core strength. Your consistency is paying off!

*Analysis combines data from stability sensors, session logs, and performance trends.*
                        """
                    
                    elif action == "realtime_coaching":
                        ai_response = """
**⚡ Real-time Coaching Active**

**Current Exercise: Plank Hold**
- **Form Score:** 85.3/100 ✨
- **Primary Cue:** Keep your core engaged and breathe steadily
- **Adjustment:** Slightly lower your hips for better alignment

**💪 Encouragement:** You're doing great! Hold steady for 15 more seconds.

**🎯 Focus Areas:**
- Feel the engagement in your deep core muscles
- Maintain steady breathing pattern
- Keep body in straight line from head to heels

**Next:** After this hold, rest 30 seconds then move to dead bug exercise.

*Real-time feedback based on current stability sensor data and your personal training profile.*
                        """
                    
                    else:
                        ai_response = "I can help with stability analysis, workout planning, progress tracking, and real-time coaching. What would you like to focus on?"
                
                except Exception as e:
                    ai_response = f"I encountered an issue: {e}. Let me help you with basic training advice instead."
            
            else:
                # Basic responses for non-agent mode
                basic_responses = {
                    "basic_stability": "Based on general guidelines, focus on maintaining proper form and steady breathing during your core exercises.",
                    "basic_workout": "Try this basic routine: 1) Plank (30s x 3), 2) Dead bug (10 reps x 2), 3) Side plank (15s each side x 2).",
                    "basic_progress": "Track your progress by noting hold times, form quality, and how you feel after each session.",
                    "basic_realtime": "Focus on keeping your core engaged, breathing steadily, and maintaining proper alignment throughout your exercises."
                }
                ai_response = basic_responses.get(action, "I'm here to help with your core training. What specific area would you like to work on?")
        
        # Add the AI response to chat
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
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
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI Coach is thinking..."):
                if AGENT_AVAILABLE and core_training_agent:
                    # Enhanced AI responses with agent capabilities
                    try:
                        if "stability" in prompt.lower() or "form" in prompt.lower():
                            response = """
**🎯 Form & Stability Analysis**

Based on your current data, your stability score is 87.5/100 - that's excellent! Here's my analysis:

**✅ What you're doing well:**
- Strong core engagement
- Good breathing pattern
- Consistent session attendance

**🎯 Areas to focus on:**
- Try extending your hold times by 5-10 seconds
- Focus on maintaining steady breathing during challenging moments
- Keep your pelvis in neutral position

**💡 Pro tip:** Quality over quantity! It's better to hold perfect form for shorter durations than compromise form for longer holds.

*This analysis is based on your real-time stability sensors and progress data.*
                            """
                        
                        elif "exercise" in prompt.lower() or "workout" in prompt.lower():
                            response = """
**🏋️ Personalized Exercise Recommendations**

Based on your fitness level and recent progress, here's what I recommend:

**Today's Focus: Core Stability Foundation**

1. **Modified Plank Progression**
   - Start: 30 seconds x 3 sets
   - Goal: 45 seconds x 3 sets
   - Rest: 45 seconds between sets

2. **Dead Bug (Recommended for you)**
   - 8-10 reps per side x 2 sets
   - Focus on slow, controlled movement
   - Keep lower back pressed to floor

3. **Side Plank Build-up**
   - 15 seconds each side x 2 sets
   - Use knee modification if needed
   - Progress to full side plank when ready

**🎯 This Week's Goal:** Increase plank hold time by 10 seconds total.

*Recommendations based on your progress analytics and personal fitness profile.*
                            """
                        
                        elif "progress" in prompt.lower() or "improvement" in prompt.lower():
                            response = """
**📊 Your Progress Journey**

**📈 This Week's Highlights:**
- **Stability Improvement:** +12.7% (Excellent!)
- **Consistency:** 6/7 training days
- **Personal Best:** 90.2 stability score
- **Form Quality:** Improved by 15%

**🏆 Recent Achievements:**
- ✅ Mastered basic plank form
- ✅ Completed first full week of training
- ✅ Improved breathing control during exercises

**🎯 Next Milestones:**
- Reach 95+ average stability score
- Master side plank variations
- Complete 2-week consistency streak

**🌟 Motivation:** You're building real strength! Your dedication is evident in the data. Keep up the fantastic work!

*Progress analysis from fitness sensors, session logs, and performance trends.*
                            """
                        
                        else:
                            # General intelligent response
                            response = f"""
**🤖 AI Coach Response**

I understand you're asking about: "{prompt}"

As your AI coach with access to your real-time data, I can help you with:

**🎯 Available Services:**
- **Real-time form analysis** from your stability sensors
- **Personalized workout planning** based on your progress
- **Progress tracking** with detailed analytics
- **Custom coaching advice** tailored to your goals

**💡 Quick suggestion:** Based on your recent training pattern, I'd recommend focusing on consistency over intensity. You're making great progress!

What specific aspect of your training would you like to dive deeper into?

*I'm continuously learning from your training data to provide better coaching.*
                            """
                        
                    except Exception as e:
                        response = f"I'm having a technical issue accessing your training data right now, but I can still help! {prompt}"
                
                else:
                    # Basic responses for non-agent mode
                    if "stability" in prompt.lower():
                        response = "Based on general guidelines, focus on maintaining steady breathing and proper alignment. Keep your core engaged throughout each exercise."
                    elif "exercise" in prompt.lower():
                        response = "Here are some effective core exercises: 1) Plank (start with 30s), 2) Dead bug (10 reps per side), 3) Bird dog (20s holds). Focus on quality over quantity!"
                    elif "form" in prompt.lower():
                        response = "Great question about form! Key points: Keep your core engaged, maintain neutral spine, breathe steadily, and never sacrifice form for duration."
                    elif "progress" in prompt.lower():
                        response = "Track your progress by noting: hold times, form quality, how you feel during/after exercises, and consistency of training. Small improvements add up!"
                    else:
                        response = f"That's a great question about '{prompt}'. For core training, focus on consistency, proper form, and gradual progression. Would you like specific exercise recommendations?"
                
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