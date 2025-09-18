#!/usr/bin/env python3
"""
Fitness Data MCP Server
Core Training AI Ecosystem - Phase 2

Exposes fitness and stability data to agents through MCP protocol.
Provides real-time stability monitoring, session logging, and exercise history.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Import our Arduino connector
try:
    from app.arduino_connector import ArduinoConnector
    ARDUINO_AVAILABLE = True
except ImportError:
    print("Warning: Arduino connector not available, using simulation only")
    ARDUINO_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness-data-server")

# In-memory data storage (in production, use a proper database)
exercise_sessions = []
user_data = {}

# Initialize Arduino connector
arduino = None
if ARDUINO_AVAILABLE:
    arduino = ArduinoConnector(simulation_mode=True)

# Create MCP server
server = Server("fitness-data-server")

def get_current_stability_data():
    """Get current stability data from Arduino or simulation"""
    if arduino:
        return arduino.get_current_stability_data()
    else:
        # Fallback simulation
        import random
        from datetime import datetime
        
        score = random.uniform(70, 95)
        return {
            "timestamp": datetime.now().isoformat(),
            "stability_score": round(score, 1),
            "movement_variance": round(random.uniform(0.1, 0.8), 2),
            "form_quality": "Excellent" if score > 90 else "Good" if score > 75 else "Fair",
            "session_duration": "2:34",
            "source": "simulation"
        }

def log_session_data(user_id: str, exercise_type: str, duration: float, avg_stability: float, notes: str = ""):
    """Log exercise session data"""
    session = {
        "session_id": f"session_{len(exercise_sessions) + 1}",
        "user_id": user_id,
        "exercise_type": exercise_type,
        "duration_minutes": duration,
        "avg_stability_score": avg_stability,
        "timestamp": datetime.now().isoformat(),
        "notes": notes,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    exercise_sessions.append(session)
    logger.info(f"Logged session for user {user_id}: {exercise_type}")
    return session

def get_user_exercise_history(user_id: str, days: int = 30) -> List[Dict]:
    """Get exercise history for a user"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    user_sessions = [
        session for session in exercise_sessions 
        if session["user_id"] == user_id and 
        datetime.fromisoformat(session["timestamp"]) >= cutoff_date
    ]
    
    return sorted(user_sessions, key=lambda x: x["timestamp"], reverse=True)

def calculate_session_stats(user_id: str) -> Dict[str, Any]:
    """Calculate session statistics for a user"""
    user_sessions = get_user_exercise_history(user_id, days=7)  # Last 7 days
    
    if not user_sessions:
        return {
            "total_sessions": 0,
            "total_duration": 0,
            "avg_stability": 0,
            "improvement_trend": "no_data"
        }
    
    total_sessions = len(user_sessions)
    total_duration = sum(session["duration_minutes"] for session in user_sessions)
    avg_stability = sum(session["avg_stability_score"] for session in user_sessions) / total_sessions
    
    # Calculate improvement trend
    if len(user_sessions) >= 2:
        recent_avg = sum(s["avg_stability_score"] for s in user_sessions[:3]) / min(3, len(user_sessions))
        older_avg = sum(s["avg_stability_score"] for s in user_sessions[-3:]) / min(3, len(user_sessions))
        
        if recent_avg > older_avg + 2:
            improvement_trend = "improving"
        elif recent_avg < older_avg - 2:
            improvement_trend = "declining"
        else:
            improvement_trend = "stable"
    else:
        improvement_trend = "insufficient_data"
    
    return {
        "total_sessions": total_sessions,
        "total_duration": round(total_duration, 1),
        "avg_stability": round(avg_stability, 1),
        "improvement_trend": improvement_trend,
        "last_session": user_sessions[0]["timestamp"] if user_sessions else None
    }

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Define available tools for the fitness data server"""
    return [
        Tool(
            name="get_current_stability_score",
            description="Get real-time core stability score and form analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier for personalized data"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="log_exercise_session",
            description="Record a completed exercise session with performance metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "exercise_type": {
                        "type": "string",
                        "description": "Type of exercise performed (e.g., plank, dead_bug, bird_dog)"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Duration of exercise in minutes"
                    },
                    "avg_stability": {
                        "type": "number",
                        "description": "Average stability score during the session (0-100)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the session"
                    }
                },
                "required": ["user_id", "exercise_type", "duration", "avg_stability"]
            }
        ),
        Tool(
            name="get_exercise_history",
            description="Retrieve exercise history and performance trends for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days to look back (default: 30)",
                        "default": 30
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_session_statistics",
            description="Get comprehensive session statistics and performance analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_realtime_form_feedback",
            description="Get real-time form feedback and coaching suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "current_exercise": {
                        "type": "string",
                        "description": "Current exercise being performed"
                    }
                },
                "required": ["user_id", "current_exercise"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls from agents"""
    
    try:
        if name == "get_current_stability_score":
            user_id = arguments["user_id"]
            
            # Get current stability data
            stability_data = get_current_stability_data()
            
            # Add user context
            result = {
                "user_id": user_id,
                "current_data": stability_data,
                "timestamp": datetime.now().isoformat(),
                "server": "fitness-data-server"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "log_exercise_session":
            user_id = arguments["user_id"]
            exercise_type = arguments["exercise_type"]
            duration = arguments["duration"]
            avg_stability = arguments["avg_stability"]
            notes = arguments.get("notes", "")
            
            # Log the session
            session = log_session_data(user_id, exercise_type, duration, avg_stability, notes)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "session": session,
                    "message": f"Successfully logged {exercise_type} session for user {user_id}"
                }, indent=2)
            )]
        
        elif name == "get_exercise_history":
            user_id = arguments["user_id"]
            days = arguments.get("days", 30)
            
            # Get exercise history
            history = get_user_exercise_history(user_id, days)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "user_id": user_id,
                    "days_requested": days,
                    "total_sessions": len(history),
                    "sessions": history
                }, indent=2)
            )]
        
        elif name == "get_session_statistics":
            user_id = arguments["user_id"]
            
            # Calculate statistics
            stats = calculate_session_stats(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "user_id": user_id,
                    "statistics": stats,
                    "generated_at": datetime.now().isoformat()
                }, indent=2)
            )]
        
        elif name == "get_realtime_form_feedback":
            user_id = arguments["user_id"]
            current_exercise = arguments["current_exercise"]
            
            # Get current stability data
            stability_data = get_current_stability_data()
            score = stability_data["stability_score"]
            
            # Generate exercise-specific feedback
            if current_exercise.lower() in ["plank", "plank_hold"]:
                if score > 90:
                    feedback = "Excellent plank form! Try extending hold time or add leg lifts."
                elif score > 75:
                    feedback = "Good stability. Focus on keeping hips level and core engaged."
                else:
                    feedback = "Engage core more. Keep body in straight line from head to heels."
            
            elif current_exercise.lower() in ["dead_bug", "deadbug"]:
                if score > 90:
                    feedback = "Perfect dead bug execution! Control the movement slowly."
                elif score > 75:
                    feedback = "Good form. Ensure opposite arm and leg move together."
                else:
                    feedback = "Keep lower back pressed to floor. Move limbs slowly and controlled."
            
            else:
                if score > 90:
                    feedback = "Excellent form! You're maintaining great stability."
                elif score > 75:
                    feedback = "Good work! Focus on breathing and core engagement."
                else:
                    feedback = "Engage your core muscles more. Focus on stability over speed."
            
            result = {
                "user_id": user_id,
                "exercise": current_exercise,
                "current_score": score,
                "feedback": feedback,
                "form_quality": stability_data["form_quality"],
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "get_current_stability_score",
                        "log_exercise_session", 
                        "get_exercise_history",
                        "get_session_statistics",
                        "get_realtime_form_feedback"
                    ]
                })
            )]
    
    except Exception as e:
        logger.error(f"Error in tool call {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments
            })
        )]

async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Fitness Data MCP Server...")
    
    # Add some sample data for testing
    log_session_data("user_123", "plank", 2.5, 87.3, "Good session, felt strong")
    log_session_data("user_123", "dead_bug", 3.0, 84.7, "Need to focus on breathing")
    log_session_data("user_456", "bird_dog", 2.0, 91.2, "Excellent form today")
    
    logger.info("Sample data loaded. Server ready.")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fitness-data-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())