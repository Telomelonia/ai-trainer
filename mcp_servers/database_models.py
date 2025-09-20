"""
Production Database Models for CoreSense MCP Servers
Extended models for fitness data, analytics, and real-time monitoring
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from typing import Optional, Dict, Any, List
import json

Base = declarative_base()

class ExerciseType(enum.Enum):
    """Exercise type enumeration"""
    PLANK = "plank"
    SIDE_PLANK = "side_plank"
    DEAD_BUG = "dead_bug"
    BIRD_DOG = "bird_dog"
    MODIFIED_PLANK = "modified_plank"
    PALLOF_PRESS = "pallof_press"
    TURKISH_GETUP = "turkish_getup"
    WALL_SIT = "wall_sit"
    KNEE_PLANK = "knee_plank"
    SINGLE_ARM_PLANK = "single_arm_plank"

class SessionStatus(enum.Enum):
    """Training session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"

class FitnessLevel(enum.Enum):
    """User fitness level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class FitnessSession(Base):
    """Comprehensive fitness session tracking with real-time data"""
    __tablename__ = "fitness_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Session identification
    session_uuid = Column(String(36), unique=True, index=True, nullable=False)
    
    # Exercise details
    exercise_type = Column(SQLEnum(ExerciseType), nullable=False)
    planned_duration_seconds = Column(Integer)
    actual_duration_seconds = Column(Integer)
    
    # Performance metrics
    stability_score = Column(Float)
    average_stability = Column(Float)
    peak_stability = Column(Float)
    stability_variance = Column(Float)
    movement_quality_score = Column(Float)
    form_consistency = Column(Float)
    
    # Real-time sensor data aggregated
    sensor_data_summary = Column(JSON)  # Aggregated sensor metrics
    ai_feedback_log = Column(JSON)      # AI coaching throughout session
    
    # Session metadata
    session_status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    paused_duration_seconds = Column(Integer, default=0)
    
    # Environmental factors
    device_type = Column(String(50))
    sensor_quality = Column(String(20))  # excellent, good, poor
    calibration_status = Column(String(20))  # calibrated, needs_calibration
    
    # Progress tracking
    personal_best = Column(Boolean, default=False)
    improvement_from_last = Column(Float)
    goals_achieved = Column(JSON)  # List of goals met in this session
    
    # Notes and feedback
    user_notes = Column(Text)
    ai_summary = Column(Text)
    coach_recommendations = Column(JSON)
    
    def __repr__(self):
        return f"<FitnessSession(id={self.id}, user_id={self.user_id}, exercise='{self.exercise_type.value}')>"
    
    @property
    def duration_minutes(self) -> float:
        """Get actual session duration in minutes"""
        if self.actual_duration_seconds:
            return round(self.actual_duration_seconds / 60, 2)
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_uuid": self.session_uuid,
            "exercise_type": self.exercise_type.value,
            "duration_minutes": self.duration_minutes,
            "stability_score": self.stability_score,
            "session_status": self.session_status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "personal_best": self.personal_best,
            "form_quality": self._get_form_quality(),
            "ai_summary": self.ai_summary
        }
    
    def _get_form_quality(self) -> str:
        """Calculate form quality based on stability score"""
        if not self.stability_score:
            return "unknown"
        if self.stability_score >= 90:
            return "excellent"
        elif self.stability_score >= 80:
            return "good"
        elif self.stability_score >= 70:
            return "fair"
        else:
            return "needs_improvement"

class UserProfile(Base):
    """Extended user profile for fitness and preferences"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Personal information
    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    fitness_level = Column(SQLEnum(FitnessLevel), default=FitnessLevel.BEGINNER)
    
    # Fitness goals (JSON array)
    fitness_goals = Column(JSON)  # ["core_strength", "balance_improvement", "injury_prevention"]
    
    # Preferences
    preferred_session_duration_minutes = Column(Integer, default=30)
    preferred_exercises = Column(JSON)  # List of preferred exercise types
    avoided_exercises = Column(JSON)    # List of exercises to avoid
    difficulty_preference = Column(String(20), default="medium")  # easy, medium, hard
    training_frequency = Column(String(20), default="daily")  # daily, 3x_week, etc.
    preferred_time_of_day = Column(String(20))  # morning, afternoon, evening
    
    # Health information
    dietary_restrictions = Column(JSON)  # ["vegetarian", "gluten_free", etc.]
    allergies = Column(JSON)
    injuries_history = Column(JSON)
    medical_conditions = Column(JSON)
    medications = Column(JSON)
    
    # Calculated metrics
    bmi = Column(Float)
    target_weight_kg = Column(Float)
    estimated_calories_per_day = Column(Integer)
    
    # Progress tracking
    baseline_stability_score = Column(Float)
    current_fitness_assessment = Column(JSON)
    last_assessment_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, fitness_level='{self.fitness_level.value}')>"
    
    def calculate_bmi(self):
        """Calculate and update BMI"""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "age": self.age,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "fitness_level": self.fitness_level.value if self.fitness_level else None,
            "fitness_goals": self.fitness_goals or [],
            "preferences": {
                "session_duration_minutes": self.preferred_session_duration_minutes,
                "difficulty_level": self.difficulty_preference,
                "preferred_exercises": self.preferred_exercises or [],
                "avoided_exercises": self.avoided_exercises or [],
                "training_frequency": self.training_frequency,
                "preferred_time": self.preferred_time_of_day
            },
            "health_info": {
                "dietary_restrictions": self.dietary_restrictions or [],
                "allergies": self.allergies or [],
                "injuries": self.injuries_history or [],
                "medical_conditions": self.medical_conditions or [],
                "medications": self.medications or []
            },
            "metrics": {
                "bmi": self.bmi,
                "target_weight_kg": self.target_weight_kg,
                "baseline_stability": self.baseline_stability_score
            },
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ProgressMetrics(Base):
    """Daily/weekly aggregated progress metrics for analytics"""
    __tablename__ = "progress_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Time period
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly
    
    # Session statistics
    total_sessions = Column(Integer, default=0)
    total_duration_minutes = Column(Float, default=0.0)
    average_session_duration = Column(Float, default=0.0)
    
    # Performance metrics
    average_stability_score = Column(Float)
    best_stability_score = Column(Float)
    worst_stability_score = Column(Float)
    stability_improvement_rate = Column(Float)  # Change from previous period
    
    # Exercise variety
    exercises_performed = Column(JSON)  # List of exercise types
    exercise_variety_score = Column(Float)  # 0-1 based on variety
    most_frequent_exercise = Column(String(50))
    
    # Goals and achievements
    goals_achieved_count = Column(Integer, default=0)
    personal_bests_count = Column(Integer, default=0)
    consistency_score = Column(Float)  # Based on frequency vs. goals
    
    # Trend analysis
    trend_direction = Column(String(20))  # improving, stable, declining
    trend_strength = Column(Float)  # 0-1 confidence in trend
    
    # Calculated fields
    performance_grade = Column(String(2))  # A, B, C, D, F
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<ProgressMetrics(user_id={self.user_id}, date='{self.metric_date}', grade='{self.performance_grade}')>"

class RealTimeData(Base):
    """Real-time sensor data points for live monitoring"""
    __tablename__ = "realtime_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("fitness_sessions.id"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    elapsed_seconds = Column(Float)  # Seconds since session start
    
    # Sensor readings
    stability_score = Column(Float)
    x_acceleration = Column(Float)
    y_acceleration = Column(Float)
    z_acceleration = Column(Float)
    gyro_x = Column(Float)
    gyro_y = Column(Float)
    gyro_z = Column(Float)
    
    # Calculated metrics
    movement_variance = Column(Float)
    balance_deviation = Column(Float)
    form_quality_instant = Column(Float)
    
    # AI feedback
    ai_feedback_type = Column(String(50))  # coaching, warning, encouragement
    ai_feedback_text = Column(Text)
    confidence_score = Column(Float)
    
    def __repr__(self):
        return f"<RealTimeData(session_id={self.session_id}, timestamp='{self.timestamp}')>"

class ExerciseRecommendation(Base):
    """AI-generated exercise recommendations"""
    __tablename__ = "exercise_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Recommendation details
    recommended_exercise = Column(SQLEnum(ExerciseType), nullable=False)
    difficulty_level = Column(String(20))
    duration_minutes = Column(Integer)
    sets_count = Column(Integer)
    rest_between_sets = Column(Integer)
    
    # AI reasoning
    recommendation_reason = Column(Text)
    confidence_score = Column(Float)
    expected_benefit = Column(Text)
    
    # Context
    based_on_sessions = Column(JSON)  # List of session IDs used for recommendation
    user_goals_addressed = Column(JSON)  # Which goals this addresses
    safety_considerations = Column(JSON)
    
    # Scheduling
    recommended_time = Column(DateTime(timezone=True))
    priority_score = Column(Float)  # 0-1, higher = more important
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, declined, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ExerciseRecommendation(user_id={self.user_id}, exercise='{self.recommended_exercise.value}')>"

class AIInsight(Base):
    """AI-generated insights and coaching feedback"""
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Insight details
    insight_type = Column(String(50))  # progress_analysis, form_correction, motivation, goal_adjustment
    title = Column(String(200))
    content = Column(Text)
    
    # AI metadata
    confidence_level = Column(Float)
    data_sources = Column(JSON)  # Which data was used to generate insight
    openai_model_used = Column(String(50))
    tokens_used = Column(Integer)
    
    # User interaction
    is_read = Column(Boolean, default=False)
    user_rating = Column(Integer)  # 1-5 star rating
    user_feedback = Column(Text)
    
    # Context
    related_sessions = Column(JSON)  # Session IDs this insight relates to
    action_items = Column(JSON)     # Suggested actions for user
    
    # Scheduling and priority
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    displayed_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<AIInsight(user_id={self.user_id}, type='{self.insight_type}', priority='{self.priority}')>"

# Create indexes for performance
from sqlalchemy import Index

# Performance indexes for common queries
Index('idx_fitness_session_user_date', FitnessSession.user_id, FitnessSession.started_at)
Index('idx_fitness_session_status', FitnessSession.session_status)
Index('idx_fitness_session_exercise_type', FitnessSession.exercise_type)

Index('idx_progress_metrics_user_period', ProgressMetrics.user_id, ProgressMetrics.metric_date, ProgressMetrics.period_type)
Index('idx_progress_metrics_date', ProgressMetrics.metric_date)

Index('idx_realtime_data_session', RealTimeData.session_id)
Index('idx_realtime_data_timestamp', RealTimeData.timestamp)
Index('idx_realtime_data_user_time', RealTimeData.user_id, RealTimeData.timestamp)

Index('idx_recommendations_user_status', ExerciseRecommendation.user_id, ExerciseRecommendation.status)
Index('idx_recommendations_priority', ExerciseRecommendation.priority_score.desc())

Index('idx_ai_insights_user_priority', AIInsight.user_id, AIInsight.priority)
Index('idx_ai_insights_unread', AIInsight.user_id, AIInsight.is_read)