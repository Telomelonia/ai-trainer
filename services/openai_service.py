"""
OpenAI Integration Service for CoreSense AI Platform
Centralized AI service for fitness insights, form analysis, and personalized recommendations
Includes error handling, rate limiting, and response caching
"""

import os
import json
import logging
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import openai
from openai import AsyncOpenAI
import tiktoken
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

class AIModelType(Enum):
    """Available AI model types"""
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class AnalysisType(Enum):
    """Types of AI analysis"""
    FORM_ANALYSIS = "form_analysis"
    PROGRESS_INSIGHTS = "progress_insights"
    EXERCISE_RECOMMENDATIONS = "exercise_recommendations"
    PERFORMANCE_SUMMARY = "performance_summary"
    GOAL_SUGGESTIONS = "goal_suggestions"
    WORKOUT_PLANNING = "workout_planning"

@dataclass
class AIResponse:
    """Structured AI response"""
    content: str
    analysis_type: AnalysisType
    confidence: float
    model_used: str
    tokens_used: int
    response_time: float
    cached: bool = False
    metadata: Dict[str, Any] = None

class RateLimiter:
    """Rate limiter for OpenAI API calls"""
    
    def __init__(self, max_requests_per_minute: int = 50, max_tokens_per_minute: int = 40000):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.request_history = []
        self.token_history = []
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self, estimated_tokens: int = 1000):
        """Wait if rate limits would be exceeded"""
        async with self._lock:
            now = time.time()
            
            # Clean old entries (older than 1 minute)
            self.request_history = [t for t in self.request_history if now - t < 60]
            self.token_history = [(t, tokens) for t, tokens in self.token_history if now - t < 60]
            
            # Check request rate limit
            if len(self.request_history) >= self.max_requests_per_minute:
                wait_time = 60 - (now - self.request_history[0])
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Check token rate limit
            current_tokens = sum(tokens for _, tokens in self.token_history)
            if current_tokens + estimated_tokens > self.max_tokens_per_minute:
                wait_time = 60 - (now - self.token_history[0][0])
                if wait_time > 0:
                    logger.info(f"Token rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self.request_history.append(now)
            self.token_history.append((now, estimated_tokens))

class ResponseCache:
    """In-memory cache for AI responses"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.cache = {}
        self._access_times = {}
    
    def _generate_key(self, prompt: str, model: str, analysis_type: AnalysisType) -> str:
        """Generate cache key"""
        content = f"{prompt}|{model}|{analysis_type.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, analysis_type: AnalysisType) -> Optional[AIResponse]:
        """Get cached response"""
        key = self._generate_key(prompt, model, analysis_type)
        
        if key in self.cache:
            cached_time, response = self.cache[key]
            
            # Check if expired
            if time.time() - cached_time > self.ttl_seconds:
                del self.cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None
            
            # Update access time
            self._access_times[key] = time.time()
            response.cached = True
            return response
        
        return None
    
    def set(self, prompt: str, model: str, analysis_type: AnalysisType, response: AIResponse):
        """Cache response"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        key = self._generate_key(prompt, model, analysis_type)
        self.cache[key] = (time.time(), response)
        self._access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self.cache[lru_key]
        del self._access_times[lru_key]

class OpenAIService:
    """OpenAI integration service for fitness AI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.rate_limiter = RateLimiter()
        self.cache = ResponseCache()
        
        # Model configurations
        self.model_configs = {
            AIModelType.GPT_4_TURBO: {
                "model": "gpt-4-turbo-preview",
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            AIModelType.GPT_4: {
                "model": "gpt-4",
                "max_tokens": 3000,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            AIModelType.GPT_3_5_TURBO: {
                "model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        # System prompts for different analysis types
        self.system_prompts = {
            AnalysisType.FORM_ANALYSIS: """You are an expert fitness coach and biomechanics analyst. 
            Analyze exercise form data and provide detailed, actionable feedback on technique, 
            stability, and performance improvements. Focus on specific corrections and positive reinforcement.""",
            
            AnalysisType.PROGRESS_INSIGHTS: """You are a fitness analytics expert who specializes in 
            interpreting workout data and identifying meaningful progress patterns. Provide insightful 
            analysis of performance trends, achievements, and areas for improvement with specific metrics.""",
            
            AnalysisType.EXERCISE_RECOMMENDATIONS: """You are a certified personal trainer with expertise 
            in progressive exercise programming. Generate personalized exercise recommendations based on 
            user data, fitness level, goals, and performance history. Include difficulty progressions.""",
            
            AnalysisType.PERFORMANCE_SUMMARY: """You are a fitness data analyst who creates comprehensive 
            performance summaries. Transform complex workout data into clear, motivating insights that 
            highlight achievements, improvements, and strategic next steps.""",
            
            AnalysisType.GOAL_SUGGESTIONS: """You are a goal-setting specialist in fitness and wellness. 
            Analyze user data to suggest realistic, achievable fitness goals that align with their current 
            capabilities and desired outcomes. Include timelines and milestones.""",
            
            AnalysisType.WORKOUT_PLANNING: """You are an expert workout planner who designs personalized 
            training programs. Create structured workout plans based on user preferences, fitness level, 
            available time, and specific goals. Include progression and variation strategies."""
        }
    
    def _estimate_tokens(self, text: str, model: AIModelType) -> int:
        """Estimate token count for text"""
        try:
            encoding = tiktoken.encoding_for_model(self.model_configs[model]["model"])
            return len(encoding.encode(text))
        except:
            # Fallback estimation: ~4 characters per token
            return len(text) // 4
    
    async def _make_api_call(
        self, 
        messages: List[Dict[str, str]], 
        model: AIModelType,
        analysis_type: AnalysisType
    ) -> AIResponse:
        """Make OpenAI API call with error handling"""
        start_time = time.time()
        config = self.model_configs[model]
        
        try:
            # Estimate tokens and wait for rate limit
            prompt_text = "\n".join([msg["content"] for msg in messages])
            estimated_tokens = self._estimate_tokens(prompt_text, model)
            await self.rate_limiter.wait_if_needed(estimated_tokens)
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=config["model"],
                messages=messages,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                top_p=config["top_p"],
                response_format={"type": "json_object"} if analysis_type in [
                    AnalysisType.FORM_ANALYSIS, 
                    AnalysisType.PROGRESS_INSIGHTS,
                    AnalysisType.EXERCISE_RECOMMENDATIONS
                ] else {"type": "text"}
            )
            
            response_time = time.time() - start_time
            content = response.choices[0].message.content
            
            # Extract confidence if available in JSON response
            confidence = 0.85  # Default confidence
            try:
                if content.startswith("{"):
                    parsed = json.loads(content)
                    confidence = parsed.get("confidence", 0.85)
            except:
                pass
            
            return AIResponse(
                content=content,
                analysis_type=analysis_type,
                confidence=confidence,
                model_used=config["model"],
                tokens_used=response.usage.total_tokens,
                response_time=response_time
            )
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            await asyncio.sleep(60)  # Wait 1 minute
            return await self._make_api_call(messages, model, analysis_type)
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI call: {e}")
            raise
    
    async def analyze_form(
        self, 
        sensor_data: Dict[str, Any],
        exercise_type: str,
        user_level: str = "intermediate",
        model: AIModelType = AIModelType.GPT_4_TURBO
    ) -> AIResponse:
        """Analyze exercise form from sensor data"""
        
        prompt = f"""
        Analyze the following exercise form data for a {exercise_type} exercise performed by a {user_level} level user.
        
        Sensor Data:
        {json.dumps(sensor_data, indent=2)}
        
        Provide a detailed form analysis in JSON format with:
        {{
            "overall_score": <0-100>,
            "form_quality": "<excellent|good|fair|needs_improvement>",
            "key_strengths": ["strength1", "strength2"],
            "areas_for_improvement": ["improvement1", "improvement2"],
            "specific_feedback": {{
                "stability": "feedback on stability",
                "alignment": "feedback on body alignment",
                "consistency": "feedback on movement consistency"
            }},
            "corrective_actions": ["action1", "action2"],
            "confidence": <0-1.0>
        }}
        """
        
        # Check cache first
        cached_response = self.cache.get(prompt, model.value, AnalysisType.FORM_ANALYSIS)
        if cached_response:
            return cached_response
        
        messages = [
            {"role": "system", "content": self.system_prompts[AnalysisType.FORM_ANALYSIS]},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_api_call(messages, model, AnalysisType.FORM_ANALYSIS)
        self.cache.set(prompt, model.value, AnalysisType.FORM_ANALYSIS, response)
        
        return response
    
    async def generate_progress_insights(
        self,
        user_data: Dict[str, Any],
        recent_sessions: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        model: AIModelType = AIModelType.GPT_4_TURBO
    ) -> AIResponse:
        """Generate progress insights from user data"""
        
        prompt = f"""
        Generate comprehensive progress insights for a user based on their fitness data.
        
        User Profile:
        {json.dumps(user_data, indent=2)}
        
        Recent Sessions:
        {json.dumps(recent_sessions, indent=2)}
        
        Current Goals:
        {json.dumps(goals, indent=2)}
        
        Provide insights in JSON format with:
        {{
            "progress_summary": "overall progress description",
            "key_achievements": ["achievement1", "achievement2"],
            "performance_trends": {{
                "stability": "trend description",
                "endurance": "trend description",
                "consistency": "trend description"
            }},
            "goal_progress": [
                {{
                    "goal": "goal name",
                    "progress_percentage": <0-100>,
                    "status": "on_track|ahead|behind",
                    "insights": "specific insights"
                }}
            ],
            "recommendations": ["recommendation1", "recommendation2"],
            "motivation_message": "personalized motivational message",
            "confidence": <0-1.0>
        }}
        """
        
        cached_response = self.cache.get(prompt, model.value, AnalysisType.PROGRESS_INSIGHTS)
        if cached_response:
            return cached_response
        
        messages = [
            {"role": "system", "content": self.system_prompts[AnalysisType.PROGRESS_INSIGHTS]},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_api_call(messages, model, AnalysisType.PROGRESS_INSIGHTS)
        self.cache.set(prompt, model.value, AnalysisType.PROGRESS_INSIGHTS, response)
        
        return response
    
    async def recommend_exercises(
        self,
        user_profile: Dict[str, Any],
        performance_data: Dict[str, Any],
        preferences: Dict[str, Any],
        model: AIModelType = AIModelType.GPT_4
    ) -> AIResponse:
        """Generate personalized exercise recommendations"""
        
        prompt = f"""
        Generate personalized exercise recommendations based on user data.
        
        User Profile:
        {json.dumps(user_profile, indent=2)}
        
        Recent Performance:
        {json.dumps(performance_data, indent=2)}
        
        Preferences:
        {json.dumps(preferences, indent=2)}
        
        Provide recommendations in JSON format with:
        {{
            "recommended_exercises": [
                {{
                    "exercise_name": "name",
                    "category": "core|stability|strength|mobility",
                    "difficulty": "beginner|intermediate|advanced",
                    "duration_seconds": <seconds>,
                    "reasoning": "why this exercise",
                    "progression_tips": "how to advance",
                    "priority": "high|medium|low"
                }}
            ],
            "workout_structure": {{
                "warm_up_duration": <minutes>,
                "main_exercises": <count>,
                "cool_down_duration": <minutes>,
                "total_duration": <minutes>
            }},
            "weekly_schedule": "suggested frequency",
            "adaptation_timeline": "expected progression timeline",
            "confidence": <0-1.0>
        }}
        """
        
        cached_response = self.cache.get(prompt, model.value, AnalysisType.EXERCISE_RECOMMENDATIONS)
        if cached_response:
            return cached_response
        
        messages = [
            {"role": "system", "content": self.system_prompts[AnalysisType.EXERCISE_RECOMMENDATIONS]},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_api_call(messages, model, AnalysisType.EXERCISE_RECOMMENDATIONS)
        self.cache.set(prompt, model.value, AnalysisType.EXERCISE_RECOMMENDATIONS, response)
        
        return response
    
    async def create_performance_summary(
        self,
        weekly_data: Dict[str, Any],
        user_context: Dict[str, Any],
        model: AIModelType = AIModelType.GPT_3_5_TURBO
    ) -> AIResponse:
        """Create a natural language performance summary"""
        
        prompt = f"""
        Create a comprehensive, motivating performance summary for a user's weekly fitness progress.
        
        Weekly Data:
        {json.dumps(weekly_data, indent=2)}
        
        User Context:
        {json.dumps(user_context, indent=2)}
        
        Write a natural, encouraging summary that:
        1. Highlights key achievements and improvements
        2. Acknowledges effort and consistency
        3. Provides specific insights about performance
        4. Offers encouragement for continued progress
        5. Includes actionable next steps
        
        Keep the tone positive, personal, and motivating while being specific about metrics and improvements.
        """
        
        messages = [
            {"role": "system", "content": self.system_prompts[AnalysisType.PERFORMANCE_SUMMARY]},
            {"role": "user", "content": prompt}
        ]
        
        return await self._make_api_call(messages, model, AnalysisType.PERFORMANCE_SUMMARY)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "cache_size": len(self.cache.cache),
            "cache_hit_rate": getattr(self.cache, '_hits', 0) / max(getattr(self.cache, '_requests', 1), 1),
            "rate_limiter_status": {
                "recent_requests": len(self.rate_limiter.request_history),
                "recent_tokens": sum(tokens for _, tokens in self.rate_limiter.token_history),
                "max_requests_per_minute": self.rate_limiter.max_requests_per_minute,
                "max_tokens_per_minute": self.rate_limiter.max_tokens_per_minute
            }
        }

# Global OpenAI service instance
openai_service = OpenAIService()

# Convenience functions
async def analyze_exercise_form(sensor_data: Dict, exercise_type: str, user_level: str = "intermediate") -> AIResponse:
    """Analyze exercise form (convenience function)"""
    return await openai_service.analyze_form(sensor_data, exercise_type, user_level)

async def get_progress_insights(user_data: Dict, sessions: List[Dict], goals: List[Dict]) -> AIResponse:
    """Get progress insights (convenience function)"""
    return await openai_service.generate_progress_insights(user_data, sessions, goals)

async def get_exercise_recommendations(profile: Dict, performance: Dict, preferences: Dict) -> AIResponse:
    """Get exercise recommendations (convenience function)"""
    return await openai_service.recommend_exercises(profile, performance, preferences)