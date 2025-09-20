# CoreSense AI Platform
## First AI System to Simulate Direct Muscle Activation Measurement

### 🎯 Innovation
CoreSense uses intelligent hardware simulation to predict which core muscles you're using during training - not just IF you're stable, but WHICH muscles are activating.

### 🏗️ Architecture
- **Fabric Sensor Agent**: Simulates 6-zone compression band
- **Muscle Activation AI**: Detects compensation patterns
- **Real-time Coaching**: Guides proper muscle engagement
- **MCP Integration**: Scalable agent coordination

### 📊 Features
- ✅ 6-zone muscle activation mapping
- ✅ Compensation pattern detection
- ✅ AI-powered coaching
- ✅ Real-time feedback
- ✅ Progress analytics

### 🚀 Quick Start

#### Installation
```bash
# Clone and install
git clone <repository-url>
cd ai-trainer
pip install -r requirements.txt
```

#### Run CoreSense Platform
```bash
# Launch the platform
streamlit run app/main.py

# Test the system
python test_coresense.py
```

Access the platform at `localhost:8501` to explore:
- **Live Dashboard**: Real-time stability monitoring
- **Muscle Activation**: 6-zone fabric sensor visualization
- **AI Coach Chat**: Intelligent coaching and feedback
- **Progress Analytics**: Performance tracking and insights

### 🏗️ System Architecture
```
CoreSense Platform/
├── app/main.py              # Streamlit UI application
├── agents/                  # AI agent system
│   ├── fabric_sensor_agent.py    # Hardware simulation
│   ├── core_training_agent.py    # Training intelligence
│   └── agent_orchestrator.py     # Agent coordination
├── mcp_servers/             # MCP server infrastructure
│   ├── fitness_data_server.py    # Fitness data management
│   ├── user_profile_server.py    # User profile service
│   └── progress_analytics_server.py  # Analytics engine
├── config/                  # Configuration files
│   ├── coresense_config.py       # Platform configuration
│   └── sensor_config.py          # Sensor settings
├── sensors/                 # Multi-sensor abstraction
└── test_coresense.py        # Comprehensive test suite
```

### 💡 Technical Innovation
- **Intelligent Hardware Simulation**: Advanced fabric sensor modeling
- **Muscle Activation Prediction**: AI-powered muscle engagement analysis
- **Compensation Pattern Detection**: Real-time form correction
- **MCP Agent Architecture**: Scalable AI service coordination
- **Real-time Coaching**: Context-aware fitness guidance

### 🧪 Testing & Validation
```bash
# Run comprehensive test suite
python test_coresense.py

# Test individual components
python -m pytest tests/
```

### 🎯 Current Status
**Phase 2 Complete**: CoreSense platform fully operational with:
- ✅ Fabric sensor simulation engine
- ✅ Real-time muscle activation UI
- ✅ AI coaching integration
- ✅ Comprehensive test coverage
- ✅ Production-ready architecture

---
**CoreSense AI Platform** | *Internet of Agents Hackathon 2025*