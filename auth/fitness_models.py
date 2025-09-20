"""
Extended Fitness Database Models for CoreSense AI Platform
Additional SQLAlchemy models for fitness data, analytics, and real-time sensor management
Extends the authentication models for production MCP server integration
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from auth.models import Base, User, TrainingSession
import json
from typing import Dict, List, Optional, Any
import uuid

class ExerciseType(Base):
    """Exercise type definitions for standardized exercise management"""
    __tablename__ = "exercise_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # core, stability, strength, mobility
    difficulty_level = Column(String(20))  # beginner, intermediate, advanced
    
    # Exercise specifications
    description = Column(Text)
    instructions = Column(Text)
    duration_range_min = Column(Integer)  # seconds
    duration_range_max = Column(Integer)  # seconds
    target_muscles = Column(JSON)  # List of target muscle groups
    
    # Sensor requirements
    required_sensors = Column(JSON)  # List of required sensor types
    sensor_configurations = Column(JSON)  # Sensor-specific settings
    
    # Difficulty progression
    prerequisites = Column(JSON)  # List of prerequisite exercise IDs
    progressions = Column(JSON)  # List of progression exercise IDs
    
    # System data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sessions = relationship("FitnessSession", back_populates="exercise_type")
    recommendations = relationship("ExerciseRecommendation", back_populates="exercise_type")
    
    def __repr__(self):
        return f"<ExerciseType(id={self.id}, name='{self.name}', category='{self.category}')>"

class FitnessSession(Base):
    """Enhanced fitness session model with detailed sensor data and analytics"""
    __tablename__ = "fitness_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_type_id = Column(Integer, ForeignKey("exercise_types.id"), nullable=False)
    
    # Session identification
    session_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Session metadata
    planned_duration = Column(Integer)  # seconds
    actual_duration = Column(Integer)  # seconds
    session_mode = Column(String(30))  # guided, free_training, assessment
    difficulty_level = Column(String(20))
    
    # Performance metrics
    stability_score = Column(Float)
    form_quality_score = Column(Float)
    consistency_score = Column(Float)
    endurance_score = Column(Float)
    overall_performance = Column(Float)
    
    # Detailed metrics
    movement_variance = Column(Float)
    balance_deviation = Column(Float)
    tempo_consistency = Column(Float)
    range_of_motion = Column(Float)
    
    # Session results
    completion_status = Column(String(20))  # completed, paused, abandoned, failed
    completion_percentage = Column(Float)
    calories_burned = Column(Float)
    heart_rate_avg = Column(Integer)
    heart_rate_max = Column(Integer)
    
    # AI feedback and analysis
    ai_form_feedback = Column(JSON)  # Structured AI feedback
    improvement_suggestions = Column(JSON)  # AI recommendations
    performance_insights = Column(JSON)  # AI-generated insights
    
    # Progress tracking
    personal_best = Column(Boolean, default=False)
    improvement_from_last = Column(Float)  # percentage
    goal_progress = Column(Float)  # percentage toward goal
    
    # Session lifecycle
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True))
    
    # Data quality and validation
    data_quality_score = Column(Float)  # 0-100
    sensor_connectivity = Column(JSON)  # Sensor status during session
    
    # Relationships
    user = relationship("User", back_populates="training_sessions")
    exercise_type = relationship("ExerciseType", back_populates="sessions")
    sensor_data = relationship("SensorData", back_populates="session", cascade="all, delete-orphan")
    real_time_events = relationship("RealTimeEvent", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FitnessSession(id={self.id}, user_id={self.user_id}, exercise='{self.exercise_type.name if self.exercise_type else 'N/A'}')>"
    
    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        if self.actual_duration:
            return round(self.actual_duration / 60, 2)
        return 0.0
    
    def calculate_overall_performance(self):
        """Calculate overall performance score from individual metrics"""
        scores = [s for s in [self.stability_score, self.form_quality_score, 
                             self.consistency_score, self.endurance_score] if s is not None]
        if scores:
            self.overall_performance = sum(scores) / len(scores)
        return self.overall_performance

class SensorData(Base):
    """Real-time sensor data storage for detailed analytics"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("fitness_sessions.id"), nullable=False)
    
    # Sensor identification
    sensor_type = Column(String(30))  # emg, imu, pressure, heart_rate
    sensor_id = Column(String(50))  # Device-specific identifier
    
    # Data payload
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    raw_data = Column(JSON)  # Raw sensor readings
    processed_data = Column(JSON)  # Processed/filtered data
    
    # Data quality metrics
    signal_quality = Column(Float)  # 0-100
    noise_level = Column(Float)
    calibration_offset = Column(Float)
    
    # Batch processing
    batch_id = Column(String(36))  # For grouping related data points
    sequence_number = Column(Integer)  # Order within batch
    
    # Relationships
    session = relationship("FitnessSession", back_populates="sensor_data")
    
    def __repr__(self):
        return f"<SensorData(id={self.id}, session_id={self.session_id}, sensor='{self.sensor_type}')>"

class UserPreferences(Base):
    """User preferences and settings for personalized experience"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Exercise preferences
    preferred_exercise_types = Column(JSON)  # List of preferred exercise IDs
    avoided_exercise_types = Column(JSON)  # List of exercises to avoid
    preferred_difficulty = Column(String(20))
    preferred_session_duration = Column(Integer)  # minutes
    
    # Notification preferences
    workout_reminders = Column(Boolean, default=True)
    progress_notifications = Column(Boolean, default=True)
    achievement_notifications = Column(Boolean, default=True)
    email_summaries = Column(Boolean, default=True)
    
    # AI coaching preferences
    coaching_style = Column(String(30))  # encouraging, neutral, detailed, minimal
    feedback_frequency = Column(String(20))  # real_time, post_session, weekly
    voice_guidance = Column(Boolean, default=True)
    
    # Display preferences
    metric_units = Column(String(10))  # metric, imperial
    theme_preference = Column(String(20))  # light, dark, auto
    dashboard_layout = Column(JSON)  # Customized dashboard configuration
    
    # Privacy settings
    data_sharing_consent = Column(Boolean, default=True)
    analytics_consent = Column(Boolean, default=True)
    research_participation = Column(Boolean, default=False)
    
    # Goals and targets
    weekly_session_target = Column(Integer, default=5)
    monthly_improvement_target = Column(Float, default=10.0)  # percentage
    long_term_goals = Column(JSON)  # List of long-term fitness goals
    
    # System preferences
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id})>"

class FitnessGoal(Base):
    """User fitness goals and progress tracking"""
    __tablename__ = "fitness_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Goal definition
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # strength, endurance, balance, flexibility
    
    # Target metrics
    target_metric = Column(String(50))  # stability_score, duration, frequency
    target_value = Column(Float)
    current_value = Column(Float, default=0.0)
    
    # Timeline
    start_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    target_date = Column(DateTime(timezone=True))
    achieved_date = Column(DateTime(timezone=True))
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    milestones = Column(JSON)  # List of milestone definitions
    achieved_milestones = Column(JSON)  # List of achieved milestone IDs
    
    # Goal status
    status = Column(String(20))  # active, paused, completed, abandoned
    priority = Column(String(20))  # high, medium, low
    
    # AI assistance
    ai_recommendations = Column(JSON)  # AI-generated goal recommendations
    success_probability = Column(Float)  # AI-calculated success likelihood
    
    # System data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="fitness_goals")
    
    def __repr__(self):
        return f"<FitnessGoal(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
    
    def update_progress(self, current_value: float):
        """Update goal progress based on current value"""
        self.current_value = current_value
        if self.target_value > 0:
            self.progress_percentage = min(100.0, (current_value / self.target_value) * 100)
        
        # Check if goal is completed
        if self.progress_percentage >= 100 and self.status == "active":
            self.status = "completed"
            self.achieved_date = datetime.now(timezone.utc)

class ExerciseRecommendation(Base):
    """AI-generated exercise recommendations for users"""
    __tablename__ = "exercise_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_type_id = Column(Integer, ForeignKey("exercise_types.id"), nullable=False)
    
    # Recommendation metadata
    recommendation_type = Column(String(30))  # progression, variation, recovery, challenge
    confidence_score = Column(Float)  # AI confidence in recommendation
    reasoning = Column(Text)  # AI explanation for recommendation
    
    # Recommendation parameters
    suggested_duration = Column(Integer)  # seconds
    suggested_difficulty = Column(String(20))
    suggested_frequency = Column(String(50))  # daily, 3x_week, etc.
    
    # Priority and timing
    priority = Column(String(20))  # high, medium, low
    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True))
    
    # User interaction
    presented_at = Column(DateTime(timezone=True))
    user_response = Column(String(20))  # accepted, declined, ignored
    response_date = Column(DateTime(timezone=True))
    
    # Outcome tracking
    attempted = Column(Boolean, default=False)
    attempt_date = Column(DateTime(timezone=True))
    outcome_rating = Column(Float)  # User satisfaction rating
    
    # System data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ai_model_version = Column(String(20))  # Track which AI model generated this
    
    # Relationships
    user = relationship("User", back_populates="exercise_recommendations")
    exercise_type = relationship("ExerciseType", back_populates="recommendations")
    
    def __repr__(self):
        return f"<ExerciseRecommendation(id={self.id}, user_id={self.user_id}, type='{self.recommendation_type}')>"

class AnalyticsCache(Base):
    """Cache for expensive analytics calculations"""
    __tablename__ = "analytics_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Cache identification
    cache_key = Column(String(200), nullable=False, index=True)
    cache_type = Column(String(50))  # weekly_report, improvement_rate, comparison
    
    # Cache data
    cached_data = Column(JSON)
    calculation_parameters = Column(JSON)  # Parameters used for calculation
    
    # Cache metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True))
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Data freshness
    data_version = Column(String(50))  # Hash of source data
    is_valid = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_cache")
    
    def __repr__(self):
        return f"<AnalyticsCache(id={self.id}, user_id={self.user_id}, key='{self.cache_key}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def update_access(self):
        """Update access tracking"""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1

class RealTimeEvent(Base):
    """Real-time events and notifications during sessions"""
    __tablename__ = "real_time_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("fitness_sessions.id"), nullable=False)
    
    # Event details
    event_type = Column(String(50))  # form_correction, milestone, warning, achievement
    event_subtype = Column(String(50))  # specific event classification
    severity = Column(String(20))  # info, warning, error, critical
    
    # Event data
    event_data = Column(JSON)  # Event-specific data payload
    message = Column(Text)  # Human-readable message
    action_required = Column(Boolean, default=False)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    session_timestamp = Column(Float)  # Seconds from session start
    
    # Processing status
    processed = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    user_response = Column(JSON)  # User's response to event
    
    # Relationships
    session = relationship("FitnessSession", back_populates="real_time_events")
    
    def __repr__(self):
        return f"<RealTimeEvent(id={self.id}, session_id={self.session_id}, type='{self.event_type}')>"

# Update existing User model to include new relationships
# Add these to the User class in models.py:
User.preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
User.fitness_goals = relationship("FitnessGoal", back_populates="user", cascade="all, delete-orphan")
User.exercise_recommendations = relationship("ExerciseRecommendation", back_populates="user", cascade="all, delete-orphan")
User.analytics_cache = relationship("AnalyticsCache", back_populates="user", cascade="all, delete-orphan")

# Create additional indexes for optimal query performance
Index('idx_fitness_session_user_date', FitnessSession.user_id, FitnessSession.started_at)
Index('idx_fitness_session_exercise_type', FitnessSession.exercise_type_id, FitnessSession.completion_status)
Index('idx_sensor_data_session_timestamp', SensorData.session_id, SensorData.timestamp)
Index('idx_sensor_data_type_quality', SensorData.sensor_type, SensorData.signal_quality)
Index('idx_user_preferences_user', UserPreferences.user_id)
Index('idx_fitness_goal_user_status', FitnessGoal.user_id, FitnessGoal.status)
Index('idx_exercise_recommendation_user_priority', ExerciseRecommendation.user_id, ExerciseRecommendation.priority)
Index('idx_analytics_cache_key_valid', AnalyticsCache.cache_key, AnalyticsCache.is_valid)
Index('idx_real_time_event_session_timestamp', RealTimeEvent.session_id, RealTimeEvent.timestamp)