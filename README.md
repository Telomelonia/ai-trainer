# Core Training AI Ecosystem
## Internet of Agents Hackathon - Phase 1 Implementation

### 🏋️ Project Overview
A real-time core stability training system with AI coaching, built for the Internet of Agents hackathon. This is Phase 1 of a 4-phase development plan.

### ✅ Phase 1 Completed Features
- **Streamlit Web Application** with multi-page navigation
- **Live Dashboard** with real-time stability metrics
- **Arduino Connector** with simulation mode fallback
- **User Profile Management** 
- **AI Coach Chat Interface**
- **Progress Analytics & Reporting**

### 🚀 Quick Start

#### 1. Environment Setup
```bash
# Clone and navigate to project
cd ai-trainer

# Activate virtual environment (already created)
source hackathon_env/bin/activate

# Install dependencies (streamlit already installed)
pip install -r requirements.txt
```

#### 2. Run the Application
```bash
# Start the Streamlit app
streamlit run app/main.py --server.port 8501

# Or use the startup script
chmod +x run_app.sh
./run_app.sh
```

#### 3. Access the Application
- Open browser to: http://localhost:8501
- Navigate through the 4 main pages:
  - **Live Dashboard**: Real-time stability monitoring
  - **User Profile**: Personal settings and goals
  - **AI Coach Chat**: Interactive training assistant
  - **Progress Analytics**: Historical data and insights

### 📁 Project Structure
```
ai-trainer/
├── app/
│   ├── main.py                 # Main Streamlit application
│   ├── arduino_connector.py    # Arduino/sensor integration
│   └── websocket_server.py     # Real-time data broadcasting
├── mcp_servers/               # MCP servers (Phase 2)
├── agents/                    # AI agents (Phase 3)
├── static/                    # Static assets
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── hackathon_env/            # Virtual environment
```

### 🔧 Technical Details

#### Arduino Integration
- **Simulation Mode**: Generates realistic stability data for testing
- **Hardware Mode**: Ready for real Arduino sensor integration
- **Real-time Updates**: 1 Hz data sampling with trend analysis

#### Data Simulation
The Arduino connector generates realistic training data including:
- Stability scores (50-100%)
- Movement variance (accelerometer simulation)
- Form quality assessment
- Session timing and trends

### 🎯 Phase 1 Success Metrics
✅ **Working Streamlit app with live data**  
✅ **Arduino connector with simulation fallback**  
✅ **4-page navigation system**  
✅ **Real-time metrics display**  
✅ **AI coaching feedback system**  
✅ **Progress tracking and analytics**  

### 🚀 Next Phases
- **Phase 2**: MCP servers for data exposure to agents
- **Phase 3**: Core Training Agent development
- **Phase 4**: Coral Protocol integration

### 🛠️ Development Notes
- Built with Python 3.12 and Streamlit 1.49+
- Designed for rapid hackathon development
- Modular architecture for easy Phase 2-4 integration
- Simulation mode allows development without hardware

### 📊 Demo Features
1. **Real-time Dashboard**: Live stability monitoring with charts
2. **AI Coaching**: Context-aware training advice
3. **User Profiles**: Personalized fitness goals and preferences
4. **Analytics**: Progress tracking with visual reports

---
**Built for Internet of Agents Hackathon 2025**  
**Phase 1 Complete - Ready for MCP Integration**