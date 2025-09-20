"""
CoreSense Complete Database Models
SQLAlchemy models for the full CoreSense platform including user profiles, exercise sessions,
progress tracking, AI coaching, subscriptions, muscle activation patterns, and achievements.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, 
    Enum as SQLEnum, JSON, BigInteger, Numeric, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()

# Enumerations
class UserRole(enum.Enum):
    """User role enumeration for role-based access control"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class FitnessLevel(enum.Enum):
    """Fitness level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ExerciseType(enum.Enum):
    """Exercise type enumeration"""
    PLANK = "plank"
    SIDE_PLANK = "side_plank"
    DEAD_BUG = "dead_bug"
    BIRD_DOG = "bird_dog"
    GLUTE_BRIDGE = "glute_bridge"
    WALL_SIT = "wall_sit"
    CUSTOM = "custom"

class SessionStatus(enum.Enum):
    """Session status enumeration"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class SubscriptionStatus(enum.Enum):
    """Subscription status enumeration"""
    FREE = "free"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    SUSPENDED = "suspended"

class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class AchievementType(enum.Enum):
    """Achievement type enumeration"""
    DURATION = "duration"
    CONSISTENCY = "consistency"
    IMPROVEMENT = "improvement"
    MILESTONE = "milestone"
    SPECIAL = "special"

# Core Models
class User(Base):
    """Enhanced user model with comprehensive profile management"""
    __tablename__ = "users"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role-based access control
    role = Column(SQLEnum(UserRole), default=UserRole.FREE)
    
    # Personal information
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(DateTime(timezone=True))
    gender = Column(String(20))
    height_cm = Column(Integer)
    weight_kg = Column(Float)
    
    # Fitness profile
    fitness_level = Column(SQLEnum(FitnessLevel), default=FitnessLevel.BEGINNER)
    training_goals = Column(JSON)  # Structured goals data
    preferred_session_duration = Column(Integer, default=30)  # minutes
    weekly_training_frequency = Column(Integer, default=3)
    health_considerations = Column(JSON)  # Medical conditions, injuries, etc.
    
    # Preferences
    notification_preferences = Column(JSON)
    privacy_settings = Column(JSON)
    coaching_preferences = Column(JSON)  # AI coaching style, feedback frequency
    
    # Account management
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    
    # Premium features
    premium_expires_at = Column(DateTime(timezone=True))
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.FREE)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    exercise_sessions = relationship("ExerciseSession", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("ProgressRecord", back_populates="user", cascade="all, delete-orphan")
    ai_coaching_sessions = relationship("AICoachingSession", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    muscle_activation_data = relationship("MuscleActivationPattern", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    @property
    def is_premium(self) -> bool:
        """Check if user has active premium subscription"""
        if self.role == UserRole.ADMIN:
            return True
        if self.subscription_status == SubscriptionStatus.ACTIVE and self.premium_expires_at:
            return datetime.now(timezone.utc) < self.premium_expires_at
        return False
    
    @property
    def age(self) -> Optional[int]:
        """Calculate user's age from date of birth"""
        if self.date_of_birth:
            today = datetime.now(timezone.utc)
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class UserSession(Base):
    """User session model for JWT token management and session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session identification
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session metadata
    device_info = Column(JSON)  # Device details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    location = Column(JSON)  # Geolocation data
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Session status
    is_active = Column(Boolean, default=True)
    logged_out_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

class ExerciseSession(Base):
    """Comprehensive exercise session model with muscle activation data"""
    __tablename__ = "exercise_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session identification
    session_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Session details
    exercise_type = Column(SQLEnum(ExerciseType), nullable=False)
    session_name = Column(String(200))
    description = Column(Text)
    difficulty_level = Column(Integer, default=1)  # 1-10 scale
    
    # Timing
    planned_duration_seconds = Column(Integer)
    actual_duration_seconds = Column(Integer)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    # Performance metrics
    stability_score = Column(Float)  # 0-100 scale
    form_quality_score = Column(Float)  # 0-100 scale
    endurance_score = Column(Float)  # 0-100 scale
    overall_score = Column(Float)  # Composite score
    
    # Movement analysis
    movement_variance = Column(Float)
    balance_symmetry = Column(Float)
    muscle_engagement_level = Column(Float)
    
    # Session status and outcome
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.PLANNED)
    completion_percentage = Column(Float, default=0.0)
    
    # Data storage
    raw_sensor_data = Column(JSON)  # Raw sensor readings
    processed_metrics = Column(JSON)  # Calculated metrics
    environmental_data = Column(JSON)  # Temperature, humidity, etc.
    
    # Progress indicators
    personal_best = Column(Boolean, default=False)
    improvement_percentage = Column(Float)
    calories_burned = Column(Integer)
    
    # Session metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="exercise_sessions")
    muscle_activations = relationship("MuscleActivationPattern", back_populates="exercise_session", cascade="all, delete-orphan")
    ai_feedback = relationship("AICoachingSession", back_populates="exercise_session", cascade="all, delete-orphan")
    
    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        if self.actual_duration_seconds:
            return round(self.actual_duration_seconds / 60, 2)
        return 0.0

class ProgressRecord(Base):
    """Progress tracking model for monitoring user improvements over time"""
    __tablename__ = "progress_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Record identification
    record_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    record_type = Column(String(50))  # weekly, monthly, milestone, custom
    
    # Performance metrics
    average_stability_score = Column(Float)
    average_form_quality = Column(Float)
    average_endurance_score = Column(Float)
    average_session_duration = Column(Float)
    
    # Progress metrics
    total_sessions_completed = Column(Integer, default=0)
    total_training_time_minutes = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    consistency_percentage = Column(Float)
    
    # Improvement tracking
    stability_improvement = Column(Float)  # % change from previous period
    endurance_improvement = Column(Float)
    form_improvement = Column(Float)
    overall_improvement = Column(Float)
    
    # Goals and targets
    goal_completion_rate = Column(Float)
    weekly_target_met = Column(Boolean, default=False)
    
    # Additional metrics
    weight_kg = Column(Float)  # Weight at time of record
    body_fat_percentage = Column(Float)
    muscle_mass_kg = Column(Float)
    
    # Data aggregation
    exercise_type_breakdown = Column(JSON)  # Sessions by exercise type
    time_of_day_preferences = Column(JSON)  # Preferred training times
    difficulty_progression = Column(JSON)  # Difficulty level over time
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="progress_records")

class AICoachingSession(Base):
    """AI coaching history and recommendations model"""
    __tablename__ = "ai_coaching_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_session_id = Column(Integer, ForeignKey("exercise_sessions.id"))
    
    # Coaching session details
    coaching_type = Column(String(50))  # real_time, post_session, weekly_review, goal_setting
    triggered_by = Column(String(50))  # poor_form, fatigue, achievement, schedule
    
    # AI analysis
    analysis_data = Column(JSON)  # Detailed AI analysis
    confidence_score = Column(Float)  # AI confidence in recommendations
    
    # Recommendations
    recommendations = Column(JSON)  # Structured recommendations
    feedback_text = Column(Text)  # Human-readable feedback
    suggested_exercises = Column(JSON)  # Exercise suggestions
    difficulty_adjustments = Column(JSON)  # Difficulty modifications
    
    # User interaction
    user_rating = Column(Integer)  # 1-5 rating of coaching quality
    user_feedback = Column(Text)  # User's response to coaching
    recommendations_followed = Column(JSON)  # Which recommendations were followed
    
    # Coaching effectiveness
    improvement_observed = Column(Boolean)
    next_session_impact = Column(Float)  # Impact on next session performance
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # AI model information
    model_version = Column(String(50))
    processing_time_ms = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="ai_coaching_sessions")
    exercise_session = relationship("ExerciseSession", back_populates="ai_feedback")

class Subscription(Base):
    """Subscription and billing management model"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Subscription details
    subscription_tier = Column(String(50))  # free, premium, premium_plus, enterprise
    billing_cycle = Column(String(20))  # monthly, yearly, lifetime
    
    # Pricing
    price_amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    discount_applied = Column(Numeric(10, 2), default=0)
    
    # Subscription lifecycle
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Payment information
    payment_method_id = Column(String(100))  # External payment provider ID
    last_payment_date = Column(DateTime(timezone=True))
    next_billing_date = Column(DateTime(timezone=True))
    
    # Trial information
    is_trial = Column(Boolean, default=False)
    trial_expires_at = Column(DateTime(timezone=True))
    trial_used = Column(Boolean, default=False)
    
    # Subscription features
    features_enabled = Column(JSON)  # List of enabled features
    usage_limits = Column(JSON)  # Monthly limits for various features
    current_usage = Column(JSON)  # Current period usage
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

class Payment(Base):
    """Payment transaction model for billing"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    
    # Payment identification
    transaction_id = Column(String(100), unique=True)  # External transaction ID
    payment_intent_id = Column(String(100))  # Payment provider intent ID
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50))  # credit_card, paypal, bank_transfer
    
    # Payment status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = Column(DateTime(timezone=True))
    
    # Payment provider information
    provider_name = Column(String(50))  # stripe, paypal, etc.
    provider_fee = Column(Numeric(10, 2))
    net_amount = Column(Numeric(10, 2))
    
    # Transaction details
    description = Column(String(200))
    invoice_url = Column(String(500))
    receipt_url = Column(String(500))
    
    # Refund information
    refunded_amount = Column(Numeric(10, 2), default=0)
    refund_reason = Column(String(200))
    refunded_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

class MuscleActivationPattern(Base):
    """Time-series muscle activation data model"""
    __tablename__ = "muscle_activation_patterns"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_session_id = Column(Integer, ForeignKey("exercise_sessions.id"), nullable=False)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    session_time_offset_ms = Column(Integer)  # Milliseconds from session start
    
    # Muscle group data
    core_activation = Column(Float)  # Core muscle group activation (0-100)
    glute_activation = Column(Float)
    hip_flexor_activation = Column(Float)
    back_activation = Column(Float)
    shoulder_activation = Column(Float)
    
    # Sensor readings
    accelerometer_data = Column(JSON)  # x, y, z accelerometer readings
    gyroscope_data = Column(JSON)  # x, y, z gyroscope readings
    pressure_data = Column(JSON)  # Pressure sensor readings
    
    # Stability metrics
    center_of_gravity_x = Column(Float)
    center_of_gravity_y = Column(Float)
    sway_velocity = Column(Float)
    postural_stability_index = Column(Float)
    
    # Movement quality
    movement_smoothness = Column(Float)
    compensation_patterns = Column(JSON)  # Detected compensation movements
    form_deviations = Column(JSON)  # Form problems detected
    
    # Environmental factors
    fatigue_level = Column(Float)  # Estimated fatigue at this point
    difficulty_perceived = Column(Float)  # Real-time difficulty perception
    
    # Data quality
    signal_quality = Column(Float)  # Sensor signal quality (0-100)
    data_confidence = Column(Float)  # Confidence in the measurements
    
    # Relationships
    user = relationship("User", back_populates="muscle_activation_data")
    exercise_session = relationship("ExerciseSession", back_populates="muscle_activations")

class Achievement(Base):
    """Achievement definitions and templates"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Achievement details
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(SQLEnum(AchievementType), nullable=False)
    
    # Achievement criteria
    criteria = Column(JSON, nullable=False)  # Structured criteria for earning
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    
    # Display information
    icon_url = Column(String(500))
    badge_color = Column(String(20))
    points_value = Column(Integer, default=0)
    
    # Achievement properties
    is_active = Column(Boolean, default=True)
    is_repeatable = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)  # Hidden until unlocked
    
    # Ordering and categorization
    category = Column(String(50))
    sort_order = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")

class UserAchievement(Base):
    """User's earned achievements and milestones"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    # Achievement earning details
    earned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    progress_when_earned = Column(JSON)  # User's stats when achievement was earned
    
    # Achievement context
    triggering_session_id = Column(Integer, ForeignKey("exercise_sessions.id"))
    milestone_value = Column(Float)  # The specific value that triggered the achievement
    
    # Display and notification
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True))
    is_featured = Column(Boolean, default=False)  # Featured on profile
    
    # Social features
    is_public = Column(Boolean, default=True)
    share_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

# Create comprehensive indexes for optimal performance
Index('idx_user_email_active', User.email, User.is_active)
Index('idx_user_username_active', User.username, User.is_active)
Index('idx_user_subscription_status', User.subscription_status)
Index('idx_user_role_active', User.role, User.is_active)

Index('idx_session_token_active', UserSession.session_token, UserSession.is_active)
Index('idx_session_user_active', UserSession.user_id, UserSession.is_active)
Index('idx_session_expires', UserSession.expires_at)

Index('idx_exercise_session_user_date', ExerciseSession.user_id, ExerciseSession.started_at)
Index('idx_exercise_session_type_status', ExerciseSession.exercise_type, ExerciseSession.status)
Index('idx_exercise_session_completion', ExerciseSession.completed_at)
Index('idx_exercise_session_uuid', ExerciseSession.session_uuid)

Index('idx_progress_user_date', ProgressRecord.user_id, ProgressRecord.record_date)
Index('idx_progress_type_date', ProgressRecord.record_type, ProgressRecord.record_date)

Index('idx_ai_coaching_user_date', AICoachingSession.user_id, AICoachingSession.created_at)
Index('idx_ai_coaching_type', AICoachingSession.coaching_type)
Index('idx_ai_coaching_session', AICoachingSession.exercise_session_id)

Index('idx_subscription_user_status', Subscription.user_id, Subscription.status)
Index('idx_subscription_expires', Subscription.expires_at)
Index('idx_subscription_billing_date', Subscription.next_billing_date)

Index('idx_payment_subscription', Payment.subscription_id)
Index('idx_payment_status_date', Payment.status, Payment.payment_date)
Index('idx_payment_transaction_id', Payment.transaction_id)

Index('idx_muscle_activation_session_time', MuscleActivationPattern.exercise_session_id, MuscleActivationPattern.timestamp)
Index('idx_muscle_activation_user_time', MuscleActivationPattern.user_id, MuscleActivationPattern.timestamp)

Index('idx_achievement_type_active', Achievement.type, Achievement.is_active)
Index('idx_achievement_category', Achievement.category)

Index('idx_user_achievement_user', UserAchievement.user_id)
Index('idx_user_achievement_earned_date', UserAchievement.earned_at)
Index('idx_user_achievement_acknowledged', UserAchievement.is_acknowledged)