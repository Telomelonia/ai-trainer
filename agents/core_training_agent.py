#!/usr/bin/env python3
"""
Core Training Agent
Core Training AI Ecosystem - Phase 3

AI agent that consumes MCP data and provides personalized core training coaching.
Integrates with fitness data, user profiles, and progress analytics to deliver
intelligent coaching recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCP client manager
from agents.mcp_client_manager import mcp_client_manager

# Import CoreSense fabric sensor agent
try:
    from agents.fabric_sensor_agent import CoreSenseFabricSensor
    FABRIC_SENSOR_AVAILABLE = True
except ImportError:
    FABRIC_SENSOR_AVAILABLE = False
    logger.warning("CoreSense fabric sensor not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core-training-agent")

class CoreTrainingAgent:
    """
    Intelligent core training agent that provides personalized coaching
    by analyzing data from multiple MCP servers.
    """
    
    def __init__(self):
        """Initialize the Core Training Agent"""
        self.agent_id = "core-training-agent"
        self.version = "2.0.0"  # Updated for CoreSense integration
        self.capabilities = [
            "stability_analysis",
            "form_feedback", 
            "progress_tracking",
            "personalized_coaching",
            "exercise_recommendation",
            "muscle_activation_analysis",  # New CoreSense capability
            "realtime_fabric_sensing"      # New CoreSense capability
        ]
        
        # MCP client manager for server communication
        self.mcp_client = mcp_client_manager
        self.is_connected = False
        
        # CoreSense fabric sensor integration
        self.fabric_sensor = None
        if FABRIC_SENSOR_AVAILABLE:
            self.fabric_sensor = CoreSenseFabricSensor()
            logger.info("CoreSense fabric sensor initialized")
        
        logger.info(f"CoreTrainingAgent initialized with capabilities: {self.capabilities}")
    
    async def initialize_mcp_connections(self):
        """Initialize connections to MCP servers"""
        try:
            success = await self.mcp_client.initialize_connections()
            if success:
                self.is_connected = True
                logger.info("MCP connections initialized successfully")
                return True
            else:
                logger.error("Failed to initialize MCP connections")
                return False
        except Exception as e:
            logger.error(f"Error initializing MCP connections: {str(e)}")
            return False
    
    async def analyze_stability(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze current stability data and provide coaching insights
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing stability analysis and coaching advice
        """
        try:
            if not self.is_connected:
                return {"error": "Agent not connected to MCP servers"}
            
            # Get current stability data from fitness server
            stability_data = await self.mcp_client.call_tool(
                "fitness_data",
                "get_current_stability_score",
                {"user_id": user_id}
            )
            
            # Get user preferences from profile server
            user_prefs = await self.mcp_client.call_tool(
                "user_profile",
                "get_user_preferences", 
                {"user_id": user_id}
            )
            
            # Get improvement rate from analytics
            improvement_data = await self.mcp_client.call_tool(
                "progress_analytics",
                "calculate_improvement_rate",
                {"user_id": user_id, "days": 7}
            )
            
            # Extract key metrics
            current_score = stability_data.get("current_data", {}).get("stability_score", 0)
            form_quality = stability_data.get("current_data", {}).get("form_quality", "Unknown")
            improvement_rate = improvement_data.get("improvement_rate", 0)
            user_level = user_prefs.get("personal_info", {}).get("fitness_level", "beginner")
            
            # Generate intelligent coaching advice based on data
            coaching_advice = self._generate_coaching_advice(
                current_score, form_quality, improvement_rate, user_level
            )
            
            analysis = {
                "user_id": user_id,
                "stability_analysis": {
                    "current_score": current_score,
                    "form_quality": form_quality,
                    "improvement_rate": improvement_rate,
                    "user_level": user_level,
                    "improvement_areas": coaching_advice["improvement_areas"]
                },
                "coaching_advice": coaching_advice["advice"],
                "confidence": coaching_advice["confidence"],
                "data_sources": {
                    "stability_data": "fitness_data_server",
                    "user_preferences": "user_profile_server", 
                    "improvement_rate": "progress_analytics_server"
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated stability analysis for user {user_id} with score {current_score}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stability for user {user_id}: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat()
            }
    
    async def provide_realtime_coaching(self, user_id: str, current_exercise: str) -> Dict[str, Any]:
        """
        Provide real-time coaching feedback during exercise
        
        Args:
            user_id: User identifier
            current_exercise: Exercise currently being performed
            
        Returns:
            Dict containing real-time coaching feedback
        """
        try:
            if not self.is_connected:
                return {"error": "Agent not connected to MCP servers"}
            
            # Get real-time form feedback from fitness server
            form_feedback = await self.mcp_client.call_tool(
                "fitness_data",
                "get_realtime_form_feedback",
                {"user_id": user_id, "current_exercise": current_exercise}
            )
            
            # Get user preferences for personalized coaching
            user_prefs = await self.mcp_client.call_tool(
                "user_profile",
                "get_user_preferences",
                {"user_id": user_id}
            )
            
            # Extract key data
            current_score = form_feedback.get("current_score", 0)
            feedback_text = form_feedback.get("feedback", "")
            form_quality = form_feedback.get("form_quality", "Unknown")
            user_level = user_prefs.get("personal_info", {}).get("fitness_level", "beginner")
            preferred_duration = user_prefs.get("preferences", {}).get("session_duration_minutes", 30)
            
            # Generate contextual coaching based on exercise and score
            coaching_cues = self._generate_exercise_cues(current_exercise, current_score, user_level)
            
            coaching = {
                "user_id": user_id,
                "exercise": current_exercise,
                "realtime_feedback": {
                    "form_score": current_score,
                    "form_quality": form_quality,
                    "primary_cue": coaching_cues["primary"],
                    "secondary_cue": coaching_cues["secondary"],
                    "encouragement": coaching_cues["encouragement"]
                },
                "adjustments": coaching_cues["adjustments"],
                "session_progress": {
                    "target_duration": f"{preferred_duration} minutes",
                    "current_quality": form_quality,
                    "improvement_focus": coaching_cues["focus_area"]
                },
                "mcp_feedback": feedback_text,
                "data_sources": {
                    "form_feedback": "fitness_data_server",
                    "user_preferences": "user_profile_server"
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated realtime coaching for user {user_id}, exercise {current_exercise}, score {current_score}")
            return coaching
            
        except Exception as e:
            logger.error(f"Error providing realtime coaching: {str(e)}")
            return {
                "error": f"Coaching failed: {str(e)}",
                "user_id": user_id,
                "exercise": current_exercise,
                "generated_at": datetime.now().isoformat()
            }
    
    async def create_workout_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Create a personalized workout plan based on user data and progress
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing personalized workout plan
        """
        try:
            if not self.is_connected:
                return {"error": "Agent not connected to MCP servers"}
            
            # Get user preferences and fitness goals
            user_prefs = await self.mcp_client.call_tool(
                "user_profile",
                "get_user_preferences",
                {"user_id": user_id}
            )
            
            # Get exercise recommendations based on user profile
            recommendations = await self.mcp_client.call_tool(
                "user_profile", 
                "get_exercise_recommendations",
                {"user_id": user_id}
            )
            
            # Get recent performance data
            history = await self.mcp_client.call_tool(
                "fitness_data",
                "get_exercise_history",
                {"user_id": user_id, "days": 7}
            )
            
            # Get progress analytics for intelligent planning
            improvement_data = await self.mcp_client.call_tool(
                "progress_analytics",
                "calculate_improvement_rate",
                {"user_id": user_id, "days": 7}
            )
            
            # Extract user data
            fitness_level = user_prefs.get("personal_info", {}).get("fitness_level", "beginner")
            session_duration = user_prefs.get("preferences", {}).get("session_duration_minutes", 20)
            preferred_exercises = user_prefs.get("preferences", {}).get("preferred_exercises", ["plank"])
            improvement_rate = improvement_data.get("improvement_rate", 0)
            
            # Generate personalized workout plan
            workout_plan = self._create_personalized_plan(
                user_id, fitness_level, session_duration, preferred_exercises, 
                improvement_rate, recommendations.get("recommendations", [])
            )
            
            logger.info(f"Generated personalized workout plan for user {user_id}, level {fitness_level}")
            return workout_plan
            
        except Exception as e:
            logger.error(f"Error creating workout plan for user {user_id}: {str(e)}")
            return {
                "error": f"Workout plan creation failed: {str(e)}",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat()
            }
    
    async def analyze_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user progress and provide insights
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing progress analysis and recommendations
        """
        try:
            if not self.is_connected:
                return {"error": "Agent not connected to MCP servers"}
            
            # Get comprehensive weekly report from analytics server
            weekly_report = await self.mcp_client.call_tool(
                "progress_analytics",
                "generate_weekly_report",
                {"user_id": user_id}
            )
            
            # Get improvement recommendations
            recommendations = await self.mcp_client.call_tool(
                "progress_analytics",
                "recommend_adjustments",
                {"user_id": user_id}
            )
            
            # Get recent session statistics
            session_stats = await self.mcp_client.call_tool(
                "fitness_data",
                "get_session_statistics",
                {"user_id": user_id}
            )
            
            # Extract key metrics
            summary = weekly_report.get("summary", {})
            achievements = weekly_report.get("achievements", [])
            areas_for_improvement = weekly_report.get("areas_for_improvement", [])
            next_week_goals = weekly_report.get("next_week_goals", [])
            
            # Generate motivational insights
            motivation = self._generate_motivational_insights(summary, achievements)
            
            progress_analysis = {
                "user_id": user_id,
                "time_period": "last_7_days",
                "progress_metrics": {
                    "stability_improvement": f"+{summary.get('improvement_percentage', 0)}%",
                    "session_consistency": f"{summary.get('total_sessions', 0)}/7 days",
                    "average_score": summary.get('average_stability_score', 0),
                    "total_exercise_time": f"{summary.get('total_duration_minutes', 0)} minutes",
                    "consistency_rating": summary.get('consistency_rating', 'Unknown')
                },
                "achievements": achievements,
                "areas_for_improvement": areas_for_improvement,
                "recommendations": {
                    "immediate": recommendations.get("recommendations", {}).get("immediate", []),
                    "weekly": recommendations.get("recommendations", {}).get("weekly", []),
                    "monthly": recommendations.get("recommendations", {}).get("monthly", [])
                },
                "motivational_message": motivation["message"],
                "celebration": motivation["celebration"],
                "next_goals": next_week_goals,
                "data_sources": {
                    "weekly_report": "progress_analytics_server",
                    "recommendations": "progress_analytics_server",
                    "session_stats": "fitness_data_server"
                },
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated comprehensive progress analysis for user {user_id}")
            return progress_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing progress for user {user_id}: {str(e)}")
            return {
                "error": f"Progress analysis failed: {str(e)}",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat()
            }
    
    async def handle_coaching_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main handler for coaching requests from the UI
        
        Args:
            request: Dict containing request type and parameters
            
        Returns:
            Dict containing coaching response
        """
        try:
            request_type = request.get("type", "general")
            user_id = request.get("user_id", "default_user")
            
            if request_type == "stability_analysis":
                return await self.analyze_stability(user_id)
            
            elif request_type == "realtime_coaching":
                current_exercise = request.get("current_exercise", "plank")
                return await self.provide_realtime_coaching(user_id, current_exercise)
            
            elif request_type == "workout_plan":
                return await self.create_workout_plan(user_id)
            
            elif request_type == "progress_analysis":
                return await self.analyze_progress(user_id)
            
            elif request_type == "general":
                # Handle general coaching questions
                question = request.get("question", "")
                return {
                    "user_id": user_id,
                    "question": question,
                    "response": "I'm your Core Training AI assistant! Ask me about form, exercises, or progress tracking.",
                    "suggestions": [
                        "How's my current form?",
                        "Create a workout plan for me",
                        "Show my progress this week",
                        "Give me real-time coaching"
                    ],
                    "generated_at": datetime.now().isoformat()
                }
            
            else:
                return {
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": ["stability_analysis", "realtime_coaching", "workout_plan", "progress_analysis", "general"],
                    "generated_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error handling coaching request: {str(e)}")
            return {
                "error": f"Request handling failed: {str(e)}",
                "request": request,
                "generated_at": datetime.now().isoformat()
            }
    
    def _generate_coaching_advice(self, score: float, form_quality: str, improvement_rate: float, user_level: str) -> Dict[str, Any]:
        """Generate intelligent coaching advice based on current data"""
        
        # Determine improvement areas based on score
        improvement_areas = []
        if score < 70:
            improvement_areas.extend(["core_engagement", "stability_foundation", "breathing_control"])
        elif score < 85:
            improvement_areas.extend(["core_control", "movement_precision", "endurance"])
        else:
            improvement_areas.extend(["advanced_variations", "hold_duration", "coordination"])
        
        # Generate advice based on score and user level
        advice = {}
        
        if score > 90:
            advice = {
                "immediate": "Excellent form! Focus on maintaining this quality while increasing challenge.",
                "session": f"Ready for advanced variations. Try adding {10 if user_level == 'advanced' else 5} seconds to holds.",
                "long_term": "Consider progressing to dynamic stability exercises and single-limb variations."
            }
            confidence = 0.95
        elif score > 80:
            advice = {
                "immediate": "Good stability! Focus on deeper core engagement and steady breathing.",
                "session": "Increase hold duration by 5-10 seconds or add 1-2 more sets.",
                "long_term": "Work toward mastering current exercises before progressing to variations."
            }
            confidence = 0.88
        elif score > 70:
            advice = {
                "immediate": "Building good foundation. Focus on form quality over duration.",
                "session": "Practice shorter holds with perfect form. Focus on breathing rhythm.",
                "long_term": "Gradually increase session frequency to build consistent strength."
            }
            confidence = 0.82
        else:
            advice = {
                "immediate": "Focus on basic stability. Engage core muscles and maintain alignment.",
                "session": "Start with modified positions. Hold for shorter durations with perfect form.",
                "long_term": "Build consistency with daily practice, even if sessions are brief."
            }
            confidence = 0.75
        
        # Adjust advice based on improvement rate
        if improvement_rate > 10:
            advice["encouragement"] = "Fantastic progress! You're improving rapidly."
        elif improvement_rate > 5:
            advice["encouragement"] = "Steady improvement! Keep up the consistent work."
        elif improvement_rate > 0:
            advice["encouragement"] = "Gradual progress is still progress. Stay consistent."
        else:
            advice["encouragement"] = "Focus on form quality. Progress will come with practice."
        
        return {
            "improvement_areas": improvement_areas,
            "advice": advice,
            "confidence": confidence
        }
    
    def _generate_exercise_cues(self, exercise: str, score: float, user_level: str) -> Dict[str, Any]:
        """Generate exercise-specific coaching cues based on current performance"""
        
        exercise_lower = exercise.lower()
        
        # Base cues for each exercise type
        exercise_cues = {
            "plank": {
                "primary": "Keep your body in a straight line from head to heels",
                "secondary": "Engage your core and breathe steadily",
                "focus_area": "core_stability",
                "adjustments": {
                    "immediate": "Tuck your pelvis slightly and engage glutes",
                    "breathing": "Breathe normally, don't hold your breath",
                    "focus": "Feel the engagement in your deep abdominal muscles"
                }
            },
            "dead_bug": {
                "primary": "Keep your lower back pressed to the floor",
                "secondary": "Move opposite arm and leg slowly and controlled",
                "focus_area": "core_control",
                "adjustments": {
                    "immediate": "Press lower back down, don't let it arch",
                    "breathing": "Exhale as you extend limbs",
                    "focus": "Control the movement, don't let momentum take over"
                }
            },
            "bird_dog": {
                "primary": "Keep your hips level and core engaged",
                "secondary": "Extend arm and leg fully, hold steady",
                "focus_area": "balance_stability",
                "adjustments": {
                    "immediate": "Don't let hips rotate or shift",
                    "breathing": "Maintain steady breathing throughout",
                    "focus": "Feel the line of energy from fingertips to toes"
                }
            },
            "side_plank": {
                "primary": "Keep your body straight, don't let hips sag",
                "secondary": "Stack your shoulders and engage your side core",
                "focus_area": "lateral_stability",
                "adjustments": {
                    "immediate": "Lift hips up, create straight line",
                    "breathing": "Breathe steadily, don't hold breath",
                    "focus": "Feel your side muscles working to hold position"
                }
            }
        }
        
        # Get base cues for the exercise
        base_cues = exercise_cues.get(exercise_lower, exercise_cues["plank"])  # Default to plank
        
        # Adjust encouragement based on score
        if score > 90:
            encouragement = "Excellent form! You're mastering this exercise."
        elif score > 85:
            encouragement = "Great work! You're holding strong form."
        elif score > 75:
            encouragement = "Good effort! Focus on the key cues."
        elif score > 65:
            encouragement = "Keep working! Form is more important than duration."
        else:
            encouragement = "Take your time. Focus on the basics first."
        
        # Adjust cues based on user level
        if user_level == "advanced" and score > 85:
            base_cues["secondary"] = f"Perfect! Try adding 5-10 seconds to your hold."
        elif user_level == "beginner" or score < 70:
            base_cues["primary"] = f"Start with modified position if needed. {base_cues['primary']}"
        
        return {
            "primary": base_cues["primary"],
            "secondary": base_cues["secondary"],
            "encouragement": encouragement,
            "adjustments": base_cues["adjustments"],
            "focus_area": base_cues["focus_area"]
        }
    
    def _create_personalized_plan(self, user_id: str, fitness_level: str, session_duration: int, 
                                 preferred_exercises: List[str], improvement_rate: float,
                                 recommendations: List[Dict]) -> Dict[str, Any]:
        """Create a personalized workout plan based on user data"""
        
        # Base exercise library with modifications based on fitness level
        exercise_library = {
            "plank": {
                "beginner": {"duration": 20, "sets": 2, "rest": 45},
                "intermediate": {"duration": 45, "sets": 3, "rest": 30},
                "advanced": {"duration": 60, "sets": 3, "rest": 20}
            },
            "dead_bug": {
                "beginner": {"repetitions": 6, "sets": 2, "rest": 60},
                "intermediate": {"repetitions": 10, "sets": 2, "rest": 45},
                "advanced": {"repetitions": 12, "sets": 3, "rest": 30}
            },
            "bird_dog": {
                "beginner": {"duration": 15, "sets": 2, "rest": 45},
                "intermediate": {"duration": 30, "sets": 2, "rest": 30},
                "advanced": {"duration": 45, "sets": 3, "rest": 20}
            },
            "side_plank": {
                "beginner": {"duration": 10, "sets": 1, "rest": 60},
                "intermediate": {"duration": 20, "sets": 2, "rest": 45},
                "advanced": {"duration": 30, "sets": 2, "rest": 30}
            }
        }
        
        # Select exercises based on preferences and recommendations
        selected_exercises = []
        
        # Start with preferred exercises
        for exercise in preferred_exercises:
            if exercise in exercise_library:
                params = exercise_library[exercise][fitness_level]
                
                # Adjust based on improvement rate
                if improvement_rate > 10:  # Rapid improvement
                    params = self._increase_difficulty(params, 0.15)
                elif improvement_rate > 5:  # Steady improvement
                    params = self._increase_difficulty(params, 0.10)
                
                selected_exercises.append({
                    "name": exercise,
                    **params,
                    "focus": self._get_exercise_focus(exercise),
                    "coaching_tips": self._get_exercise_tips(exercise)
                })
        
        # Add recommended exercises if we have space and they're not duplicates
        current_exercises = {ex["name"] for ex in selected_exercises}
        for rec in recommendations:
            if len(selected_exercises) >= 4:  # Limit workout size
                break
            exercise_name = rec.get("exercise", "").lower()
            if exercise_name in exercise_library and exercise_name not in current_exercises:
                params = exercise_library[exercise_name][fitness_level]
                selected_exercises.append({
                    "name": exercise_name,
                    **params,
                    "focus": self._get_exercise_focus(exercise_name),
                    "coaching_tips": self._get_exercise_tips(exercise_name),
                    "reason": rec.get("reason", "Recommended for your goals")
                })
        
        # Calculate total estimated duration
        estimated_duration = sum(
            (ex.get("duration", 0) + ex.get("rest", 0)) * ex.get("sets", 1) 
            + ex.get("repetitions", 0) * 3  # Estimate 3 seconds per rep
            for ex in selected_exercises
        ) // 60  # Convert to minutes
        
        return {
            "user_id": user_id,
            "plan_id": f"plan_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M')}",
            "difficulty_level": fitness_level,
            "estimated_duration": max(estimated_duration, session_duration),
            "exercises": selected_exercises,
            "progression_notes": self._get_progression_notes(fitness_level, improvement_rate),
            "next_session_adjustments": self._get_next_adjustments(improvement_rate),
            "personalization_factors": {
                "fitness_level": fitness_level,
                "preferred_exercises": preferred_exercises,
                "improvement_rate": improvement_rate,
                "target_duration": session_duration
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_motivational_insights(self, summary: Dict, achievements: List[str]) -> Dict[str, str]:
        """Generate motivational messaging based on progress data"""
        
        improvement = summary.get("improvement_percentage", 0)
        sessions = summary.get("total_sessions", 0)
        avg_score = summary.get("average_stability_score", 0)
        
        # Generate celebration message
        if len(achievements) >= 3:
            celebration = "🏆 Outstanding week! You're crushing your goals!"
        elif len(achievements) >= 2:
            celebration = "🎉 Great achievements this week!"
        elif len(achievements) >= 1:
            celebration = "✨ Nice progress! Keep building momentum!"
        else:
            celebration = "💪 Every session counts! You're building strength!"
        
        # Generate motivational message
        if improvement > 15:
            message = "Incredible improvement! Your dedication is paying off in a big way."
        elif improvement > 10:
            message = "Fantastic progress! You're consistently getting stronger."
        elif improvement > 5:
            message = "Steady improvement shows your commitment is working!"
        elif improvement > 0:
            message = "Small gains are still gains. Stay consistent!"
        else:
            message = "Progress isn't always linear. Focus on form and consistency."
        
        # Add session-specific encouragement
        if sessions >= 6:
            message += " Your consistency is exceptional!"
        elif sessions >= 4:
            message += " Great consistency this week!"
        elif sessions >= 2:
            message += " Keep building that habit!"
        
        return {
            "message": message,
            "celebration": celebration
        }
    
    def _increase_difficulty(self, params: Dict, factor: float) -> Dict:
        """Increase exercise difficulty by a factor"""
        new_params = params.copy()
        if "duration" in new_params:
            new_params["duration"] = int(new_params["duration"] * (1 + factor))
        if "repetitions" in new_params:
            new_params["repetitions"] = int(new_params["repetitions"] * (1 + factor))
        if "sets" in new_params and new_params["sets"] < 3:
            new_params["sets"] = min(3, new_params["sets"] + 1)
        return new_params
    
    def _get_exercise_focus(self, exercise: str) -> str:
        """Get the primary focus area for an exercise"""
        focus_map = {
            "plank": "core_stability",
            "dead_bug": "core_control", 
            "bird_dog": "balance_stability",
            "side_plank": "lateral_stability"
        }
        return focus_map.get(exercise, "core_strength")
    
    def _get_exercise_tips(self, exercise: str) -> List[str]:
        """Get coaching tips for an exercise"""
        tips_map = {
            "plank": ["Keep body straight", "Breathe steadily", "Engage glutes"],
            "dead_bug": ["Move slowly", "Keep lower back down", "Opposite arm and leg"],
            "bird_dog": ["Extend fully", "Keep hips level", "Hold steady"],
            "side_plank": ["Stack shoulders", "Keep body straight", "Engage side core"]
        }
        return tips_map.get(exercise, ["Focus on form", "Breathe steadily", "Stay controlled"])
    
    def _get_progression_notes(self, fitness_level: str, improvement_rate: float) -> str:
        """Get progression guidance based on level and improvement"""
        if fitness_level == "beginner":
            return "Focus on form quality over duration. Build consistency first."
        elif fitness_level == "intermediate":
            if improvement_rate > 10:
                return "Ready for increased challenge. Focus on advanced variations."
            else:
                return "Maintain current intensity. Perfect your form."
        else:  # advanced
            return "Challenge yourself with longer holds and dynamic variations."
    
    def _get_next_adjustments(self, improvement_rate: float) -> str:
        """Get next session adjustments based on improvement rate"""
        if improvement_rate > 15:
            return "Increase duration by 10-15 seconds or add advanced variations"
        elif improvement_rate > 10:
            return "Increase hold time by 5-10 seconds"
        elif improvement_rate > 5:
            return "Add 1 extra set or increase duration by 5 seconds"
        else:
            return "Focus on form quality. Small increases when ready."
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and capabilities"""
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "status": "active" if self.is_connected else "disconnected",
            "capabilities": self.capabilities,
            "mcp_connections": {
                "fitness_data": self.is_connected,
                "user_profile": self.is_connected,
                "progress_analytics": self.is_connected
            },
            "fabric_sensor_available": FABRIC_SENSOR_AVAILABLE,
            "last_updated": datetime.now().isoformat()
        }
    
    async def start_muscle_monitoring(self, user_id: str, exercise_type: str) -> Dict[str, Any]:
        """
        Start CoreSense fabric sensor monitoring for muscle activation
        
        Args:
            user_id: User identifier
            exercise_type: Type of exercise being performed
            
        Returns:
            Dict containing monitoring status and initial data
        """
        try:
            if not self.fabric_sensor:
                return {"error": "CoreSense fabric sensor not available"}
            
            # Start fabric sensor monitoring
            monitoring_result = await self.fabric_sensor.start_exercise(exercise_type)
            
            # Log to fitness data server
            if self.is_connected:
                await self.mcp_client.call_tool(
                    "fitness_data",
                    "log_exercise_start",
                    {
                        "user_id": user_id,
                        "exercise_type": exercise_type,
                        "sensor_type": "coresense_fabric",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Started CoreSense monitoring for user {user_id}, exercise: {exercise_type}")
            return {
                "status": "monitoring_started",
                "user_id": user_id,
                "exercise_type": exercise_type,
                "sensor_data": monitoring_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting muscle monitoring for user {user_id}: {str(e)}")
            return {
                "error": f"Failed to start monitoring: {str(e)}",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_realtime_muscle_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        Get real-time muscle activation analysis from CoreSense fabric sensors
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing muscle activation data and AI coaching insights
        """
        try:
            if not self.fabric_sensor:
                return {"error": "CoreSense fabric sensor not available"}
            
            # Get real-time muscle data
            muscle_data = await self.fabric_sensor.get_data()
            
            if "error" in muscle_data:
                return muscle_data
            
            # Get user preferences for personalized coaching
            user_prefs = {}
            if self.is_connected:
                user_prefs = await self.mcp_client.call_tool(
                    "user_profile",
                    "get_user_preferences",
                    {"user_id": user_id}
                )
            
            # Generate AI coaching based on muscle activation patterns
            coaching_insights = self._analyze_muscle_activation_patterns(
                muscle_data, user_prefs
            )
            
            # Combine data with coaching insights
            analysis = {
                "user_id": user_id,
                "muscle_activation": muscle_data["muscle_activation"],
                "stability_score": muscle_data["overall_stability"],
                "form_analysis": muscle_data["form_analysis"],
                "exercise_type": muscle_data["exercise"],
                "ai_coaching": coaching_insights,
                "timestamp": muscle_data["timestamp"]
            }
            
            # Log data to fitness server if connected
            if self.is_connected:
                await self.mcp_client.call_tool(
                    "fitness_data",
                    "log_stability_data",
                    {
                        "user_id": user_id,
                        "stability_score": muscle_data["overall_stability"],
                        "form_quality": muscle_data["form_analysis"]["form_score"],
                        "sensor_data": muscle_data["muscle_activation"],
                        "timestamp": muscle_data["timestamp"]
                    }
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting muscle analysis for user {user_id}: {str(e)}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_muscle_monitoring(self, user_id: str) -> Dict[str, Any]:
        """
        Stop CoreSense monitoring and get session summary
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing session summary and insights
        """
        try:
            if not self.fabric_sensor:
                return {"error": "CoreSense fabric sensor not available"}
            
            # Stop monitoring and get session summary
            session_result = await self.fabric_sensor.stop_exercise()
            
            # Generate comprehensive session insights
            session_insights = self._generate_session_insights(
                session_result["session_summary"]
            )
            
            # Log session to analytics server
            if self.is_connected:
                await self.mcp_client.call_tool(
                    "progress_analytics",
                    "log_session_data",
                    {
                        "user_id": user_id,
                        "session_summary": session_result["session_summary"],
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Stopped CoreSense monitoring for user {user_id}")
            return {
                "status": "monitoring_stopped",
                "user_id": user_id,
                "session_summary": session_result["session_summary"],
                "session_insights": session_insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping muscle monitoring for user {user_id}: {str(e)}")
            return {
                "error": f"Failed to stop monitoring: {str(e)}",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_muscle_activation_patterns(self, muscle_data: Dict[str, Any], user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze muscle activation patterns and provide AI coaching insights
        """
        activation = muscle_data.get("muscle_activation", {})
        form_analysis = muscle_data.get("form_analysis", {})
        exercise = muscle_data.get("exercise", "unknown")
        
        # Analyze activation patterns
        insights = {
            "primary_focus": [],
            "improvement_areas": [],
            "coaching_cues": [],
            "intensity_level": "moderate"
        }
        
        # Exercise-specific analysis
        if exercise == "plank":
            if activation.get("transverse", 0) > 0.8:
                insights["primary_focus"].append("Excellent deep core activation")
            else:
                insights["improvement_areas"].append("Increase deep core engagement")
                insights["coaching_cues"].append("Draw belly button toward spine")
            
            if activation.get("erector_spinae", 0) > 0.9:
                insights["improvement_areas"].append("Reduce back arch")
                insights["coaching_cues"].append("Slightly lower hips, engage glutes")
        
        elif exercise == "side_plank":
            dominant_oblique = max(activation.get("right_oblique", 0), activation.get("left_oblique", 0))
            if dominant_oblique > 0.8:
                insights["primary_focus"].append("Strong oblique activation")
            else:
                insights["improvement_areas"].append("Increase side core strength")
                insights["coaching_cues"].append("Push up through supporting arm")
        
        # Determine intensity level
        avg_activation = sum(activation.values()) / len(activation) if activation else 0
        if avg_activation > 0.7:
            insights["intensity_level"] = "high"
        elif avg_activation < 0.4:
            insights["intensity_level"] = "low"
        
        # Add form-based insights
        if form_analysis.get("form_score", 100) < 80:
            insights["improvement_areas"].extend(form_analysis.get("issues", []))
            insights["coaching_cues"].extend(form_analysis.get("recommendations", []))
        
        return insights
    
    def _generate_session_insights(self, session_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive insights from session data
        """
        avg_stability = session_summary.get("average_stability", 0)
        exercise_type = session_summary.get("exercise_type", "unknown")
        duration = session_summary.get("session_duration", 0)
        
        insights = {
            "performance_rating": "good",
            "key_achievements": [],
            "areas_for_improvement": [],
            "next_session_recommendations": []
        }
        
        # Performance rating
        if avg_stability >= 85:
            insights["performance_rating"] = "excellent"
            insights["key_achievements"].append("Maintained excellent stability throughout session")
        elif avg_stability >= 70:
            insights["performance_rating"] = "good"
            insights["key_achievements"].append("Consistent stability performance")
        else:
            insights["performance_rating"] = "needs_improvement"
            insights["areas_for_improvement"].append("Focus on maintaining core stability")
        
        # Duration-based insights
        if duration > 50:  # Good session length
            insights["key_achievements"].append("Completed full training session")
        elif duration < 20:
            insights["areas_for_improvement"].append("Try to extend session duration")
        
        # Exercise-specific recommendations
        if exercise_type == "plank":
            insights["next_session_recommendations"].append("Consider adding side plank variations")
        elif exercise_type == "side_plank":
            insights["next_session_recommendations"].append("Work on plank-to-side-plank transitions")
        
        return insights

# Agent instance for import
core_training_agent = CoreTrainingAgent()

async def main():
    """Main entry point for testing the agent"""
    logger.info("Starting Core Training Agent...")
    
    # Initialize the agent
    await core_training_agent.initialize_mcp_connections()
    
    # Test coaching request
    test_request = {
        "type": "stability_analysis",
        "user_id": "user_123"
    }
    
    response = await core_training_agent.handle_coaching_request(test_request)
    print(json.dumps(response, indent=2))
    
    # Test agent status
    status = core_training_agent.get_agent_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    asyncio.run(main())