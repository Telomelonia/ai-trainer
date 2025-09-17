#!/bin/bash
# Core Training AI Ecosystem - Startup Script
# Phase 1 Implementation

echo "🏋️ Starting Core Training AI Ecosystem"
echo "======================================="

# Check if virtual environment exists
if [ ! -d "hackathon_env" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source hackathon_env/bin/activate

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📥 Installing Streamlit..."
    pip install streamlit
fi

# Show system info
echo "🔧 System Information:"
echo "   Python: $(python --version)"
echo "   Streamlit: $(streamlit version)"
echo "   Working Directory: $(pwd)"

# Start the application
echo ""
echo "🚀 Starting Streamlit application..."
echo "   URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Run with optimized settings for development
streamlit run app/main.py \
    --server.port 8501 \
    --server.address localhost \
    --server.runOnSave true \
    --browser.gatherUsageStats false