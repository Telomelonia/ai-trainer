#!/usr/bin/env python3
"""
Production Fitness Data MCP Server
Core Training AI Ecosystem - Production Implementation

Handles sensor data collection, real-time analysis, and exercise session management.
Provides stability metrics, movement analysis, and performance tracking with database integration.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
import random
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, desc, func, text

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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

# Import our database models and services
from auth.models import User, TrainingSession
from auth.fitness_models import (
    FitnessSession, ExerciseType, SensorData, UserPreferences, 
    RealTimeEvent, AnalyticsCache
)
from auth.database_service import get_db_session, init_database
from services.openai_service import openai_service, analyze_exercise_form

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fitness-data-server")

class RealTimeSensorManager:
    """Manages real-time sensor data collection and streaming"""
    
    def __init__(self):
        self.active_sessions = {}  # session_id -> session_info
        self.sensor_connections = {}  # sensor_id -> connection_info
        self.data_streams = {}  # session_id -> data_buffer
        self.is_collecting = False
        
    async def start_session(self, user_id: int, exercise_type: str, session_config: Dict[str, Any]) -> str:
        """Start a new fitness session with real-time data collection"""
        try:
            with get_db_session() as db:
                # Get or create exercise type
                exercise_type_obj = db.query(ExerciseType).filter(
                    ExerciseType.name == exercise_type
                ).first()
                
                if not exercise_type_obj:
                    # Create basic exercise type if not exists
                    exercise_type_obj = ExerciseType(
                        name=exercise_type,
                        category="stability",
                        difficulty_level="intermediate",
                        description=f"Stability training exercise: {exercise_type}",
                        duration_range_min=30,
                        duration_range_max=300,
                        required_sensors=["emg", "imu", "pressure"],
                        is_active=True
                    )
                    db.add(exercise_type_obj)
                    db.commit()
                    db.refresh(exercise_type_obj)
                
                # Create fitness session
                session = FitnessSession(
                    user_id=user_id,
                    exercise_type_id=exercise_type_obj.id,
                    session_uuid=str(uuid.uuid4()),
                    planned_duration=session_config.get('duration', 60),
                    session_mode=session_config.get('mode', 'guided'),
                    difficulty_level=session_config.get('difficulty', 'intermediate'),
                    completion_status='started',
                    started_at=datetime.now(timezone.utc)
                )
                
                db.add(session)
                db.commit()
                db.refresh(session)
                
                # Initialize session tracking
                self.active_sessions[session.session_uuid] = {
                    'session_id': session.id,
                    'user_id': user_id,
                    'exercise_type': exercise_type,
                    'started_at': session.started_at,
                    'config': session_config,
                    'data_points': 0,
                    'last_analysis': None
                }
                
                self.data_streams[session.session_uuid] = []
                
                logger.info(f"Started fitness session {session.session_uuid} for user {user_id}")
                return session.session_uuid
                
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise
    
    async def collect_sensor_data(self, session_uuid: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and process real-time sensor data"""
        try:
            if session_uuid not in self.active_sessions:
                raise ValueError(f"Session {session_uuid} not found")
            
            session_info = self.active_sessions[session_uuid]
            
            with get_db_session() as db:
                # Store sensor data
                timestamp = datetime.now(timezone.utc)
                
                # Process different sensor types
                for sensor_type, data in sensor_data.items():
                    if sensor_type != 'timestamp':
                        sensor_record = SensorData(
                            session_id=session_info['session_id'],
                            sensor_type=sensor_type,
                            sensor_id=f"{sensor_type}_001",
                            timestamp=timestamp,
                            raw_data=data,
                            processed_data=self._process_sensor_data(sensor_type, data),
                            signal_quality=self._calculate_signal_quality(sensor_type, data),
                            sequence_number=session_info['data_points']
                        )
                        db.add(sensor_record)
                
                # Update session data counter
                session_info['data_points'] += 1
                
                # Add to streaming buffer
                self.data_streams[session_uuid].append({
                    'timestamp': timestamp.isoformat(),
                    'data': sensor_data,
                    'sequence': session_info['data_points']
                })
                
                # Keep buffer size manageable
                if len(self.data_streams[session_uuid]) > 1000:
                    self.data_streams[session_uuid] = self.data_streams[session_uuid][-500:]
                
                # Calculate real-time metrics
                metrics = await self._calculate_real_time_metrics(session_uuid, sensor_data)
                
                # Check for real-time events (form corrections, warnings, etc.)
                events = await self._detect_real_time_events(session_uuid, sensor_data, metrics)
                
                if events:
                    for event in events:
                        event_record = RealTimeEvent(
                            session_id=session_info['session_id'],
                            event_type=event['type'],
                            event_subtype=event.get('subtype', 'general'),
                            severity=event.get('severity', 'info'),
                            event_data=event['data'],
                            message=event['message'],
                            session_timestamp=(timestamp - session_info['started_at']).total_seconds(),
                            action_required=event.get('action_required', False)
                        )
                        db.add(event_record)
                
                db.commit()
                
                return {
                    'session_uuid': session_uuid,
                    'timestamp': timestamp.isoformat(),
                    'metrics': metrics,
                    'events': events,
                    'data_points_collected': session_info['data_points'],
                    'session_duration': (timestamp - session_info['started_at']).total_seconds()
                }
                
        except Exception as e:
            logger.error(f"Error collecting sensor data: {e}")
            return {'error': str(e)}
    
    def _process_sensor_data(self, sensor_type: str, raw_data: Any) -> Dict[str, Any]:
        """Process raw sensor data based on sensor type"""
        if sensor_type == 'emg':
            return {
                'filtered_signal': raw_data,
                'rms_value': math.sqrt(sum(x**2 for x in raw_data) / len(raw_data)) if isinstance(raw_data, list) else raw_data,
                'peak_detection': self._detect_peaks(raw_data) if isinstance(raw_data, list) else []
            }
        elif sensor_type == 'imu':
            return {
                'magnitude': math.sqrt(sum(x**2 for x in raw_data.values())) if isinstance(raw_data, dict) else 0,
                'stability_metric': self._calculate_stability_metric(raw_data) if isinstance(raw_data, dict) else 0
            }
        elif sensor_type == 'pressure':
            return {
                'total_pressure': sum(raw_data.values()) if isinstance(raw_data, dict) else 0,
                'balance_ratio': self._calculate_balance_ratio(raw_data) if isinstance(raw_data, dict) else 0
            }
        else:
            return {'processed': raw_data}
    
    def _calculate_signal_quality(self, sensor_type: str, data: Any) -> float:
        """Calculate signal quality for sensor data"""
        # Simple signal quality assessment
        if isinstance(data, dict):
            values = list(data.values())
            if values and all(isinstance(v, (int, float)) for v in values):
                # Check for reasonable ranges and consistency
                variance = sum((x - sum(values)/len(values))**2 for x in values) / len(values)
                quality = max(0, min(100, 100 - variance * 10))
                return quality
        elif isinstance(data, (int, float)):
            # For single values, assume good quality if in reasonable range
            return 95.0 if 0 <= data <= 100 else 70.0
        
        return 85.0  # Default quality
    
    def _detect_peaks(self, signal: List[float]) -> List[int]:
        """Simple peak detection for EMG signals"""
        if len(signal) < 3:
            return []
        
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                peaks.append(i)
        return peaks
    
    def _calculate_stability_metric(self, imu_data: Dict[str, float]) -> float:
        """Calculate stability metric from IMU data"""
        if not imu_data:
            return 0.0
        
        # Simple stability calculation based on acceleration variance
        acc_magnitude = math.sqrt(
            imu_data.get('acceleration_x', 0)**2 + 
            imu_data.get('acceleration_y', 0)**2 + 
            imu_data.get('acceleration_z', 0)**2
        )
        
        # Lower variance = higher stability
        stability = max(0, 100 - abs(acc_magnitude - 9.81) * 10)
        return min(100, stability)
    
    def _calculate_balance_ratio(self, pressure_data: Dict[str, float]) -> float:
        """Calculate balance ratio from pressure sensors"""
        if not pressure_data:
            return 0.0
        
        total = sum(pressure_data.values())
        if total == 0:
            return 0.0
        
        # Calculate how evenly distributed the pressure is
        expected = total / len(pressure_data)
        variance = sum((v - expected)**2 for v in pressure_data.values()) / len(pressure_data)
        balance = max(0, 100 - variance)
        return min(100, balance)
    
    async def _calculate_real_time_metrics(self, session_uuid: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate real-time performance metrics"""
        if session_uuid not in self.data_streams:
            return {}
        
        recent_data = self.data_streams[session_uuid][-10:]  # Last 10 data points
        
        if not recent_data:
            return {}
        
        # Calculate moving averages and trends
        stability_scores = []
        for data_point in recent_data:
            if 'stability_score' in data_point['data']:
                stability_scores.append(data_point['data']['stability_score'])
        
        if stability_scores:
            current_stability = stability_scores[-1]
            avg_stability = sum(stability_scores) / len(stability_scores)
            stability_trend = "improving" if len(stability_scores) > 1 and stability_scores[-1] > stability_scores[0] else "stable"
        else:
            current_stability = 0
            avg_stability = 0
            stability_trend = "unknown"
        
        return {
            'current_stability': current_stability,
            'average_stability': round(avg_stability, 1),
            'stability_trend': stability_trend,
            'data_points': len(recent_data),
            'session_duration': len(self.data_streams[session_uuid]) * 2  # Assuming 2-second intervals
        }
    
    async def _detect_real_time_events(self, session_uuid: str, sensor_data: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect real-time events requiring user feedback"""
        events = []
        
        current_stability = metrics.get('current_stability', 0)
        
        # Form correction events
        if current_stability < 60:
            events.append({
                'type': 'form_correction',
                'subtype': 'stability_warning',
                'severity': 'warning',
                'message': 'Try to maintain better stability - focus on core engagement',
                'data': {'current_stability': current_stability},
                'action_required': True
            })
        
        # Achievement events
        if current_stability > 90:
            events.append({
                'type': 'achievement',
                'subtype': 'high_performance',
                'severity': 'info',
                'message': 'Excellent form! Keep it up!',
                'data': {'current_stability': current_stability},
                'action_required': False
            })
        
        # Milestone events
        session_duration = metrics.get('session_duration', 0)
        if session_duration > 0 and session_duration % 30 == 0:  # Every 30 seconds
            events.append({
                'type': 'milestone',
                'subtype': 'time_milestone',
                'severity': 'info',
                'message': f'Great progress! {session_duration} seconds completed',
                'data': {'duration': session_duration},
                'action_required': False
            })
        
        return events

# Initialize sensor manager
sensor_manager = RealTimeSensorManager()

# Create MCP server
server = Server("fitness-data-server")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Define available tools for the fitness data server"""
    return [
        Tool(
            name="start_fitness_session",
            description="Start a new fitness session with real-time sensor data collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User identifier"
                    },
                    "exercise_type": {
                        "type": "string",
                        "description": "Type of exercise (plank, side_plank, dead_bug, etc.)"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Planned duration in seconds (default: 60)",
                        "default": 60
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Difficulty level (beginner, intermediate, advanced)",
                        "default": "intermediate"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Session mode (guided, free_training, assessment)",
                        "default": "guided"
                    }
                },
                "required": ["user_id", "exercise_type"]
            }
        ),
        Tool(
            name="collect_sensor_data",
            description="Collect real-time sensor data during an active session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_uuid": {
                        "type": "string",
                        "description": "Session UUID from start_fitness_session"
                    },
                    "sensor_data": {
                        "type": "object",
                        "description": "Sensor data payload",
                        "properties": {
                            "stability_score": {"type": "number"},
                            "emg_data": {"type": "object"},
                            "imu_data": {"type": "object"},
                            "pressure_data": {"type": "object"}
                        }
                    }
                },
                "required": ["session_uuid", "sensor_data"]
            }
        ),
        Tool(
            name="get_user_session_history",
            description="Get user's exercise session history with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User identifier"
                    },
                    "exercise_type": {
                        "type": "string",
                        "description": "Filter by exercise type (optional)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of sessions to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_live_sensor_data",
            description="Get current live sensor readings (for testing/calibration)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sensor_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of sensors to read (emg, imu, pressure, all)",
                        "default": ["all"]
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls from agents"""
    
    try:
        if name == "start_fitness_session":
            user_id = arguments["user_id"]
            exercise_type = arguments["exercise_type"]
            
            session_config = {
                'duration': arguments.get('duration', 60),
                'difficulty': arguments.get('difficulty', 'intermediate'),
                'mode': arguments.get('mode', 'guided')
            }
            
            session_uuid = await sensor_manager.start_session(user_id, exercise_type, session_config)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "session_started",
                    "session_uuid": session_uuid,
                    "user_id": user_id,
                    "exercise_type": exercise_type,
                    "config": session_config,
                    "message": f"Started {exercise_type} session for user {user_id}"
                })
            )]
        
        elif name == "collect_sensor_data":
            session_uuid = arguments["session_uuid"]
            sensor_data = arguments["sensor_data"]
            
            result = await sensor_manager.collect_sensor_data(session_uuid, sensor_data)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, default=str)
            )]
        
        elif name == "get_user_session_history":
            user_id = arguments["user_id"]
            exercise_type = arguments.get("exercise_type")
            days = arguments.get("days", 30)
            limit = arguments.get("limit", 50)
            
            with get_db_session() as db:
                # Build query
                query = db.query(FitnessSession).filter(
                    FitnessSession.user_id == user_id
                )
                
                if exercise_type:
                    exercise_type_obj = db.query(ExerciseType).filter(
                        ExerciseType.name == exercise_type
                    ).first()
                    if exercise_type_obj:
                        query = query.filter(FitnessSession.exercise_type_id == exercise_type_obj.id)
                
                if days:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                    query = query.filter(FitnessSession.started_at >= cutoff_date)
                
                # Get sessions with exercise type info
                sessions = query.options(selectinload(FitnessSession.exercise_type))\
                              .order_by(desc(FitnessSession.started_at))\
                              .limit(limit).all()
                
                session_data = []
                for session in sessions:
                    session_data.append({
                        "session_id": session.id,
                        "session_uuid": session.session_uuid,
                        "exercise_type": session.exercise_type.name if session.exercise_type else "unknown",
                        "started_at": session.started_at.isoformat(),
                        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                        "duration_minutes": session.duration_minutes,
                        "completion_status": session.completion_status,
                        "overall_performance": session.overall_performance,
                        "stability_score": session.stability_score,
                        "form_quality_score": session.form_quality_score,
                        "personal_best": session.personal_best,
                        "improvement_from_last": session.improvement_from_last
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "user_id": user_id,
                        "sessions_found": len(session_data),
                        "sessions": session_data,
                        "filter_applied": {
                            "exercise_type": exercise_type,
                            "days": days,
                            "limit": limit
                        }
                    })
                )]
        
        elif name == "get_live_sensor_data":
            sensor_types = arguments.get("sensor_types", ["all"])
            
            # Simulate current sensor readings
            live_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "collecting",
                "sensors": {}
            }
            
            if "all" in sensor_types or "emg" in sensor_types:
                live_data["sensors"]["emg"] = {
                    "core_activation": random.uniform(40, 80),
                    "back_activation": random.uniform(30, 70),
                    "signal_quality": random.uniform(85, 100)
                }
            
            if "all" in sensor_types or "imu" in sensor_types:
                live_data["sensors"]["imu"] = {
                    "stability_index": random.uniform(70, 95),
                    "movement_variance": random.uniform(0.1, 2.0),
                    "orientation_drift": random.uniform(-5, 5)
                }
            
            if "all" in sensor_types or "pressure" in sensor_types:
                live_data["sensors"]["pressure"] = {
                    "total_pressure": random.uniform(100, 200),
                    "balance_ratio": random.uniform(45, 55),
                    "pressure_variance": random.uniform(0.5, 3.0)
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(live_data)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "start_fitness_session",
                        "collect_sensor_data", 
                        "get_user_session_history",
                        "get_live_sensor_data"
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
    logger.info("Starting Production Fitness Data MCP Server...")
    
    try:
        # Initialize database connection
        await init_database()
        logger.info("Database connection initialized")
        
        # Initialize OpenAI service
        logger.info("OpenAI service ready for AI-powered insights")
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="fitness-data-server",
                    server_version="2.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={
                            "real_time_streaming": True,
                            "ai_analysis": True,
                            "concurrent_sessions": True
                        },
                    )
                )
            )
            
    except Exception as e:
        logger.error(f"Server initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())