#!/usr/bin/env python3
"""
OpenAI API Integration Module for CoreSense Fitness Platform
Provides intelligent AI coaching with security, rate limiting, and error handling
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import os
from functools import lru_cache
import hashlib

import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openai-integration")

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls per time window
            time_window: Time window in seconds (default: 1 hour)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        
    def is_allowed(self) -> bool:
        """Check if a call is allowed under rate limits"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                      if now - call_time < self.time_window]
        
        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def get_reset_time(self) -> int:
        """Get time until rate limit resets"""
        if not self.calls:
            return 0
        
        oldest_call = min(self.calls)
        reset_time = oldest_call + self.time_window
        return max(0, int(reset_time - time.time()))

class ContentFilter:
    """Content filtering and sanitization for fitness coaching"""
    
    # Medical advice patterns to avoid
    MEDICAL_PATTERNS = [
        r'\b(diagnos[ie]s?|prescription|medication|treatment|therapy)\b',
        r'\b(pain|injury|hurt|damage|strain|sprain)\b.*\b(treat|cure|fix|heal)\b',
        r'\b(see\s+a?\s*(doctor|physician|medical|healthcare))\b',
        r'\b(medical\s+(advice|treatment|diagnosis))\b'
    ]
    
    # Inappropriate content patterns
    INAPPROPRIATE_PATTERNS = [
        r'\b(extreme|dangerous|risky|unsafe)\b.*\b(exercise|workout|training)\b',
        r'\b(push\s+through|ignore)\b.*\b(pain|discomfort)\b',
        r'\b(rapid\s+weight\s+loss|crash\s+diet|starvation)\b'
    ]
    
    def __init__(self):
        """Initialize content filter"""
        self.medical_regex = re.compile('|'.join(self.MEDICAL_PATTERNS), re.IGNORECASE)
        self.inappropriate_regex = re.compile('|'.join(self.INAPPROPRIATE_PATTERNS), re.IGNORECASE)
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize input text to prevent prompt injection
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove potential prompt injection patterns
        sanitized = re.sub(r'(ignore\s+previous|forget\s+instructions|new\s+instructions)', 
                          '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace and special characters
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'[^\w\s\.\,\?\!\-\(\)]', '', sanitized)
        
        # Limit length
        return sanitized[:500].strip()
    
    def filter_response(self, response: str) -> tuple[str, bool]:
        """
        Filter AI response for inappropriate content
        
        Args:
            response: AI response to filter
            
        Returns:
            Tuple of (filtered_response, is_safe)
        """
        if not isinstance(response, str):
            return "Invalid response format", False
        
        # Check for medical advice
        if self.medical_regex.search(response):
            logger.warning("Medical advice detected in AI response")
            return ("I focus on fitness coaching and form guidance. For any pain or medical concerns, please consult a healthcare professional.", False)
        
        # Check for inappropriate content
        if self.inappropriate_regex.search(response):
            logger.warning("Inappropriate content detected in AI response")
            return ("Let's focus on safe, effective training techniques that build strength gradually.", False)
        
        return response, True

class ResponseCache:
    """Simple in-memory cache for AI responses"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize response cache
        
        Args:
            max_size: Maximum cache entries
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
    
    def _generate_key(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate cache key from prompt and context"""
        key_data = f"{prompt}_{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, context: Dict[str, Any]) -> Optional[str]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, context)
        
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        logger.info(f"Cache hit for key: {key[:8]}...")
        return self.cache[key]
    
    def set(self, prompt: str, context: Dict[str, Any], response: str):
        """Cache response"""
        key = self._generate_key(prompt, context)
        
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = response
        self.timestamps[key] = time.time()
        logger.info(f"Cached response for key: {key[:8]}...")

class OpenAIFitnessCoach:
    """
    OpenAI integration for intelligent fitness coaching
    Provides real AI-powered coaching with security and safety measures
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI fitness coach
        
        Args:
            api_key: OpenAI API key (will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Initialize security components
        self.rate_limiter = RateLimiter(max_calls=100, time_window=3600)  # 100 calls per hour
        self.content_filter = ContentFilter()
        self.cache = ResponseCache(max_size=500, ttl=1800)  # 30 minute cache
        
        # Model configuration
        self.model = "gpt-4o-mini"  # Cost-effective model for fitness coaching
        self.max_tokens = 300  # Limit response length for efficiency
        
        logger.info("OpenAI Fitness Coach initialized successfully")
    
    async def generate_coaching_advice(self, 
                                     current_score: float, 
                                     form_quality: str, 
                                     improvement_rate: float, 
                                     user_level: str,
                                     additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate intelligent coaching advice using OpenAI
        
        Args:
            current_score: Current stability/form score (0-100)
            form_quality: Form quality assessment
            improvement_rate: Rate of improvement percentage
            user_level: User fitness level (beginner/intermediate/advanced)
            additional_context: Additional context for personalization
            
        Returns:
            Dict containing AI-generated coaching advice
        """
        try:
            # Rate limiting check
            if not self.rate_limiter.is_allowed():
                logger.warning("Rate limit exceeded")
                return self._get_fallback_coaching_advice(current_score, form_quality, user_level)
            
            # Prepare context
            context = {
                "score": current_score,
                "form_quality": form_quality,
                "improvement_rate": improvement_rate,
                "user_level": user_level,
                "additional": additional_context or {}
            }
            
            # Build coaching prompt
            prompt = self._build_coaching_prompt(context)
            
            # Check cache
            cached_response = self.cache.get(prompt, context)
            if cached_response:
                return json.loads(cached_response)
            
            # Call OpenAI API
            response = await self._call_openai(
                prompt=prompt,
                system_message=self._get_coaching_system_message()
            )
            
            # Filter response for safety
            filtered_response, is_safe = self.content_filter.filter_response(response)
            
            if not is_safe:
                logger.warning("Unsafe content filtered from AI response")
                return self._get_fallback_coaching_advice(current_score, form_quality, user_level)
            
            # Parse AI response
            coaching_advice = self._parse_coaching_response(filtered_response, context)
            
            # Cache the response
            self.cache.set(prompt, context, json.dumps(coaching_advice))
            
            logger.info(f"Generated AI coaching advice for score: {current_score}, level: {user_level}")
            return coaching_advice
            
        except Exception as e:
            logger.error(f"Error generating coaching advice: {str(e)}")
            return self._get_fallback_coaching_advice(current_score, form_quality, user_level)
    
    async def analyze_muscle_activation_patterns(self, 
                                               muscle_data: Dict[str, Any], 
                                               user_prefs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze muscle activation patterns using AI
        
        Args:
            muscle_data: Muscle activation data from sensors
            user_prefs: User preferences and profile data
            
        Returns:
            Dict containing AI analysis of muscle activation
        """
        try:
            # Rate limiting check
            if not self.rate_limiter.is_allowed():
                return self._get_fallback_muscle_analysis(muscle_data)
            
            # Sanitize and prepare data
            sanitized_data = self._sanitize_muscle_data(muscle_data)
            context = {"muscle_data": sanitized_data, "user_prefs": user_prefs or {}}
            
            # Build analysis prompt
            prompt = self._build_muscle_analysis_prompt(sanitized_data, user_prefs)
            
            # Check cache
            cached_response = self.cache.get(prompt, context)
            if cached_response:
                return json.loads(cached_response)
            
            # Call OpenAI API
            response = await self._call_openai(
                prompt=prompt,
                system_message=self._get_muscle_analysis_system_message()
            )
            
            # Filter and parse response
            filtered_response, is_safe = self.content_filter.filter_response(response)
            if not is_safe:
                return self._get_fallback_muscle_analysis(muscle_data)
            
            analysis = self._parse_muscle_analysis_response(filtered_response, sanitized_data)
            
            # Cache the response
            self.cache.set(prompt, context, json.dumps(analysis))
            
            logger.info("Generated AI muscle activation analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing muscle patterns: {str(e)}")
            return self._get_fallback_muscle_analysis(muscle_data)
    
    async def generate_exercise_cues(self, 
                                   exercise: str, 
                                   current_score: float, 
                                   user_level: str,
                                   real_time_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate real-time exercise cues using AI
        
        Args:
            exercise: Exercise name
            current_score: Current performance score
            user_level: User fitness level
            real_time_data: Real-time sensor data
            
        Returns:
            Dict containing AI-generated exercise cues
        """
        try:
            # Rate limiting check
            if not self.rate_limiter.is_allowed():
                return self._get_fallback_exercise_cues(exercise, current_score, user_level)
            
            # Sanitize inputs
            exercise = self.content_filter.sanitize_input(exercise)
            context = {
                "exercise": exercise,
                "score": current_score,
                "level": user_level,
                "real_time": real_time_data or {}
            }
            
            # Build cues prompt
            prompt = self._build_exercise_cues_prompt(exercise, current_score, user_level, real_time_data)
            
            # Check cache
            cached_response = self.cache.get(prompt, context)
            if cached_response:
                return json.loads(cached_response)
            
            # Call OpenAI API
            response = await self._call_openai(
                prompt=prompt,
                system_message=self._get_exercise_cues_system_message()
            )
            
            # Filter and parse response
            filtered_response, is_safe = self.content_filter.filter_response(response)
            if not is_safe:
                return self._get_fallback_exercise_cues(exercise, current_score, user_level)
            
            cues = self._parse_exercise_cues_response(filtered_response, context)
            
            # Cache the response
            self.cache.set(prompt, context, json.dumps(cues))
            
            logger.info(f"Generated AI exercise cues for {exercise}")
            return cues
            
        except Exception as e:
            logger.error(f"Error generating exercise cues: {str(e)}")
            return self._get_fallback_exercise_cues(exercise, current_score, user_level)
    
    async def create_personalized_plan(self, 
                                     user_profile: Dict[str, Any], 
                                     performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create personalized workout plan using AI
        
        Args:
            user_profile: User profile and preferences
            performance_data: Recent performance data
            
        Returns:
            Dict containing AI-generated workout plan
        """
        try:
            # Rate limiting check
            if not self.rate_limiter.is_allowed():
                return self._get_fallback_workout_plan(user_profile)
            
            # Sanitize and prepare data
            sanitized_profile = self._sanitize_user_profile(user_profile)
            context = {"profile": sanitized_profile, "performance": performance_data}
            
            # Build planning prompt
            prompt = self._build_workout_plan_prompt(sanitized_profile, performance_data)
            
            # Check cache
            cached_response = self.cache.get(prompt, context)
            if cached_response:
                return json.loads(cached_response)
            
            # Call OpenAI API
            response = await self._call_openai(
                prompt=prompt,
                system_message=self._get_workout_planning_system_message()
            )
            
            # Filter and parse response
            filtered_response, is_safe = self.content_filter.filter_response(response)
            if not is_safe:
                return self._get_fallback_workout_plan(user_profile)
            
            plan = self._parse_workout_plan_response(filtered_response, sanitized_profile)
            
            # Cache the response
            self.cache.set(prompt, context, json.dumps(plan))
            
            logger.info("Generated AI personalized workout plan")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating workout plan: {str(e)}")
            return self._get_fallback_workout_plan(user_profile)
    
    async def _call_openai(self, prompt: str, system_message: str) -> str:
        """
        Make API call to OpenAI
        
        Args:
            prompt: User prompt
            system_message: System message for AI behavior
            
        Returns:
            AI response text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.9,
                frequency_penalty=0.3,  # Reduce repetitive responses
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {str(e)}")
            raise
    
    def _get_coaching_system_message(self) -> str:
        """Get system message for coaching advice"""
        return """You are an expert fitness coach specializing in core training and stability exercises. 
        
        IMPORTANT GUIDELINES:
        - Focus only on form, technique, and training progression
        - NEVER provide medical advice, diagnosis, or injury treatment
        - Always prioritize safety and proper form over intensity
        - Be encouraging and motivational while remaining realistic
        - If someone mentions pain or injury, advise them to consult a healthcare professional
        - Keep responses concise and actionable
        
        Provide coaching advice in JSON format with these fields:
        - "immediate": immediate form correction or focus
        - "session": advice for current workout session  
        - "long_term": long-term training progression
        - "encouragement": motivational message
        - "confidence": confidence level (0.7-0.95)
        """
    
    def _get_muscle_analysis_system_message(self) -> str:
        """Get system message for muscle analysis"""
        return """You are a biomechanics expert analyzing muscle activation patterns for core training.
        
        IMPORTANT GUIDELINES:
        - Focus on muscle activation patterns and movement quality
        - Provide specific coaching cues to improve activation
        - NEVER diagnose issues or suggest medical treatment
        - Always emphasize proper form and gradual progression
        - Be specific about which muscles need more engagement
        
        Respond in JSON format with:
        - "primary_focus": areas working well
        - "improvement_areas": areas needing attention
        - "coaching_cues": specific form cues (max 3)
        - "intensity_level": current effort level
        """
    
    def _get_exercise_cues_system_message(self) -> str:
        """Get system message for exercise cues"""
        return """You are a real-time fitness coach providing immediate exercise guidance.
        
        IMPORTANT GUIDELINES:
        - Give clear, immediate coaching cues
        - Focus on the most important correction first
        - Be encouraging and supportive
        - Never mention pain, injury, or medical concerns
        - Keep cues simple and actionable
        
        Respond in JSON format with:
        - "primary": most important cue right now
        - "secondary": additional focus point
        - "encouragement": motivational phrase
        - "adjustments": specific form adjustments
        - "focus_area": main area of focus
        """
    
    def _get_workout_planning_system_message(self) -> str:
        """Get system message for workout planning"""
        return """You are a certified personal trainer creating safe, effective core training programs.
        
        IMPORTANT GUIDELINES:
        - Design progressive, safe exercise programs
        - Consider user's fitness level and preferences
        - Focus on core stability and functional strength
        - Provide clear exercise parameters (sets, reps, duration)
        - Include progression guidance
        - NEVER recommend extreme or unsafe practices
        
        Respond with workout recommendations in JSON format with:
        - "exercises": list of recommended exercises
        - "progression": how to advance the program
        - "safety_notes": important safety considerations
        - "estimated_duration": workout duration in minutes
        """
    
    def _build_coaching_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for coaching advice"""
        return f"""Analyze this core training performance and provide coaching advice:

        Current Performance:
        - Stability Score: {context['score']}/100
        - Form Quality: {context['form_quality']}
        - Improvement Rate: {context['improvement_rate']}% over past week
        - User Level: {context['user_level']}
        
        Additional Context: {context.get('additional', {})}
        
        Provide specific, actionable coaching advice to help improve performance while maintaining safety."""
    
    def _build_muscle_analysis_prompt(self, muscle_data: Dict[str, Any], user_prefs: Dict[str, Any]) -> str:
        """Build prompt for muscle activation analysis"""
        activation_summary = ", ".join([f"{muscle}: {value:.2f}" for muscle, value in muscle_data.get("activation", {}).items()])
        
        return f"""Analyze this muscle activation pattern for core training:

        Exercise: {muscle_data.get('exercise', 'unknown')}
        Muscle Activation: {activation_summary}
        Form Score: {muscle_data.get('form_score', 'N/A')}
        User Level: {user_prefs.get('fitness_level', 'beginner')}
        
        Provide specific coaching to optimize muscle activation and improve exercise effectiveness."""
    
    def _build_exercise_cues_prompt(self, exercise: str, score: float, level: str, real_time_data: Dict[str, Any]) -> str:
        """Build prompt for real-time exercise cues"""
        return f"""Provide immediate coaching cues for this exercise performance:

        Exercise: {exercise}
        Current Score: {score}/100
        User Level: {level}
        Real-time Data: {real_time_data}
        
        Give specific, immediate feedback to improve form and performance right now."""
    
    def _build_workout_plan_prompt(self, user_profile: Dict[str, Any], performance_data: Dict[str, Any]) -> str:
        """Build prompt for workout planning"""
        return f"""Create a personalized core training workout plan:

        User Profile:
        - Fitness Level: {user_profile.get('fitness_level', 'beginner')}
        - Session Duration: {user_profile.get('session_duration', 20)} minutes
        - Preferred Exercises: {user_profile.get('preferred_exercises', [])}
        - Goals: {user_profile.get('goals', 'improve core strength')}
        
        Recent Performance:
        - Average Score: {performance_data.get('average_score', 0)}
        - Improvement Rate: {performance_data.get('improvement_rate', 0)}%
        - Consistency: {performance_data.get('sessions_per_week', 0)} sessions/week
        
        Design a safe, effective, progressive workout plan."""
    
    def _parse_coaching_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI coaching response into structured format"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                if all(key in parsed for key in ['immediate', 'session', 'long_term']):
                    return {
                        "improvement_areas": ["ai_generated"],
                        "advice": parsed,
                        "confidence": parsed.get("confidence", 0.85)
                    }
            
            # Fallback: parse from text
            return {
                "improvement_areas": ["form_optimization", "strength_building"],
                "advice": {
                    "immediate": response[:100] + "..." if len(response) > 100 else response,
                    "session": "Focus on maintaining good form throughout your session.",
                    "long_term": "Continue consistent practice to build strength progressively.",
                    "encouragement": "Great work! Keep focusing on quality over quantity."
                },
                "confidence": 0.80
            }
            
        except Exception as e:
            logger.error(f"Error parsing coaching response: {str(e)}")
            return self._get_fallback_coaching_advice(context['score'], context['form_quality'], context['user_level'])
    
    def _parse_muscle_analysis_response(self, response: str, muscle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI muscle analysis response"""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Fallback structure
            return {
                "primary_focus": ["core_engagement"],
                "improvement_areas": ["stability", "muscle_activation"],
                "coaching_cues": ["Engage deep core muscles", "Maintain steady breathing"],
                "intensity_level": "moderate"
            }
            
        except Exception as e:
            logger.error(f"Error parsing muscle analysis response: {str(e)}")
            return self._get_fallback_muscle_analysis(muscle_data)
    
    def _parse_exercise_cues_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI exercise cues response"""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Fallback structure
            return {
                "primary": "Focus on maintaining proper form",
                "secondary": "Keep breathing steady",
                "encouragement": "You're doing great! Stay focused.",
                "adjustments": {"immediate": "Engage core muscles", "breathing": "Breathe normally"},
                "focus_area": "core_stability"
            }
            
        except Exception as e:
            logger.error(f"Error parsing exercise cues response: {str(e)}")
            return self._get_fallback_exercise_cues(context['exercise'], context['score'], context['level'])
    
    def _parse_workout_plan_response(self, response: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI workout plan response"""
        try:
            if response.strip().startswith('{'):
                parsed = json.loads(response)
                return {
                    "exercises": parsed.get("exercises", []),
                    "progression": parsed.get("progression", "Increase duration by 5 seconds weekly"),
                    "safety_notes": parsed.get("safety_notes", ["Focus on form", "Stop if you feel pain"]),
                    "estimated_duration": parsed.get("estimated_duration", 20),
                    "ai_generated": True
                }
            
            # Fallback plan
            return self._get_fallback_workout_plan(user_profile)
            
        except Exception as e:
            logger.error(f"Error parsing workout plan response: {str(e)}")
            return self._get_fallback_workout_plan(user_profile)
    
    def _sanitize_muscle_data(self, muscle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize muscle activation data"""
        sanitized = {}
        
        # Only include safe numeric data
        if "activation" in muscle_data and isinstance(muscle_data["activation"], dict):
            sanitized["activation"] = {
                muscle: max(0, min(1, float(value))) 
                for muscle, value in muscle_data["activation"].items()
                if isinstance(value, (int, float))
            }
        
        if "exercise" in muscle_data:
            sanitized["exercise"] = self.content_filter.sanitize_input(str(muscle_data["exercise"]))
        
        if "form_score" in muscle_data:
            sanitized["form_score"] = max(0, min(100, float(muscle_data.get("form_score", 0))))
        
        return sanitized
    
    def _sanitize_user_profile(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize user profile data"""
        sanitized = {}
        
        # Safe string fields
        safe_strings = ["fitness_level", "goals"]
        for field in safe_strings:
            if field in user_profile:
                sanitized[field] = self.content_filter.sanitize_input(str(user_profile[field]))
        
        # Safe numeric fields
        if "session_duration" in user_profile:
            sanitized["session_duration"] = max(5, min(60, int(user_profile.get("session_duration", 20))))
        
        # Safe list fields
        if "preferred_exercises" in user_profile and isinstance(user_profile["preferred_exercises"], list):
            sanitized["preferred_exercises"] = [
                self.content_filter.sanitize_input(str(ex)) 
                for ex in user_profile["preferred_exercises"][:5]  # Limit to 5 exercises
            ]
        
        return sanitized
    
    # Fallback methods when AI is unavailable
    def _get_fallback_coaching_advice(self, score: float, form_quality: str, user_level: str) -> Dict[str, Any]:
        """Fallback coaching advice when AI is unavailable"""
        if score > 85:
            advice = {
                "immediate": "Excellent form! Maintain current quality.",
                "session": "Try adding 5-10 seconds to your holds.",
                "long_term": "Ready for advanced variations.",
                "encouragement": "Outstanding performance!"
            }
        elif score > 70:
            advice = {
                "immediate": "Good stability. Focus on core engagement.",
                "session": "Maintain form quality over duration.",
                "long_term": "Build consistency before progressing.",
                "encouragement": "Great progress! Keep it up."
            }
        else:
            advice = {
                "immediate": "Focus on basic stability and alignment.",
                "session": "Quality over quantity. Short, perfect holds.",
                "long_term": "Build foundation with daily practice.",
                "encouragement": "You're building strength!"
            }
        
        return {
            "improvement_areas": ["core_engagement", "stability"],
            "advice": advice,
            "confidence": 0.75
        }
    
    def _get_fallback_muscle_analysis(self, muscle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback muscle analysis when AI is unavailable"""
        return {
            "primary_focus": ["core_stability"],
            "improvement_areas": ["muscle_activation", "form_quality"],
            "coaching_cues": ["Engage deep core", "Maintain alignment", "Breathe steadily"],
            "intensity_level": "moderate"
        }
    
    def _get_fallback_exercise_cues(self, exercise: str, score: float, user_level: str) -> Dict[str, Any]:
        """Fallback exercise cues when AI is unavailable"""
        cue_map = {
            "plank": "Keep body straight from head to heels",
            "side_plank": "Stack shoulders and keep body straight",
            "dead_bug": "Keep lower back pressed to floor",
            "bird_dog": "Keep hips level and core engaged"
        }
        
        primary_cue = cue_map.get(exercise.lower(), "Focus on proper form and alignment")
        
        return {
            "primary": primary_cue,
            "secondary": "Breathe steadily throughout the exercise",
            "encouragement": "Great effort! Stay focused on form.",
            "adjustments": {"immediate": "Engage core muscles", "breathing": "Maintain steady rhythm"},
            "focus_area": "core_stability"
        }
    
    def _get_fallback_workout_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback workout plan when AI is unavailable"""
        level = user_profile.get("fitness_level", "beginner")
        
        if level == "beginner":
            exercises = [
                {"name": "plank", "duration": 20, "sets": 2, "rest": 45},
                {"name": "dead_bug", "repetitions": 6, "sets": 2, "rest": 60}
            ]
        elif level == "intermediate":
            exercises = [
                {"name": "plank", "duration": 45, "sets": 3, "rest": 30},
                {"name": "side_plank", "duration": 20, "sets": 2, "rest": 45},
                {"name": "dead_bug", "repetitions": 10, "sets": 2, "rest": 45}
            ]
        else:  # advanced
            exercises = [
                {"name": "plank", "duration": 60, "sets": 3, "rest": 20},
                {"name": "side_plank", "duration": 30, "sets": 2, "rest": 30},
                {"name": "bird_dog", "duration": 45, "sets": 3, "rest": 20}
            ]
        
        return {
            "exercises": exercises,
            "progression": "Increase duration by 5 seconds weekly",
            "safety_notes": ["Focus on form over duration", "Stop if you feel any pain"],
            "estimated_duration": user_profile.get("session_duration", 20),
            "ai_generated": False
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the OpenAI integration"""
        return {
            "api_connected": bool(self.api_key),
            "model": self.model,
            "rate_limit_remaining": self.rate_limiter.max_calls - len(self.rate_limiter.calls),
            "rate_limit_reset": self.rate_limiter.get_reset_time(),
            "cache_size": len(self.cache.cache),
            "last_updated": datetime.now().isoformat()
        }

# Global instance for import
openai_fitness_coach = OpenAIFitnessCoach()