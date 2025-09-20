"""
Authentication Database Models for CoreSense AI Platform
SQLAlchemy models for user authentication, sessions, and profile management
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from typing import Optional

Base = declarative_base()

class UserRole(enum.Enum):
    """User role enumeration for role-based access control"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class User(Base):
    """User model for authentication and profile management"""
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
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    
    # Fitness profile
    fitness_level = Column(String(20))  # beginner, intermediate, advanced
    training_goals = Column(Text)  # JSON string of goals
    preferred_session_duration = Column(Integer, default=30)  # minutes
    health_considerations = Column(Text)
    
    # Account management
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    
    # Premium features
    premium_expires_at = Column(DateTime(timezone=True))
    subscription_status = Column(String(20), default="free")  # free, active, expired, cancelled
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSession", back_populates="user", cascade="all, delete-orphan")
    
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
        if self.role == UserRole.PREMIUM and self.premium_expires_at:
            return datetime.now(timezone.utc) < self.premium_expires_at
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)

class UserSession(Base):
    """User session model for JWT token management and session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session identification
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session metadata
    device_info = Column(Text)  # Browser, OS, etc.
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Session status
    is_active = Column(Boolean, default=True)
    logged_out_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now(timezone.utc)
    
    def invalidate(self):
        """Invalidate the session"""
        self.is_active = False
        self.logged_out_at = datetime.now(timezone.utc)

class PasswordResetToken(Base):
    """Password reset token model for secure password recovery"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token data
    token = Column(String(255), unique=True, index=True, nullable=False)
    token_hash = Column(String(255), nullable=False)  # Hashed version for security
    
    # Token lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    
    # Token status
    is_used = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)
    
    # Security
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired and self.attempt_count < 3
    
    def mark_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
    
    def increment_attempts(self):
        """Increment attempt counter"""
        self.attempt_count += 1

class EmailVerificationToken(Base):
    """Email verification token model for account verification"""
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token data
    token = Column(String(255), unique=True, index=True, nullable=False)
    token_hash = Column(String(255), nullable=False)
    
    # Email information
    email = Column(String(255), nullable=False)  # Email being verified
    
    # Token lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    
    # Token status
    is_verified = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)
    
    # Security
    ip_address = Column(String(45))
    
    # Relationships
    user = relationship("User", back_populates="verification_tokens")
    
    def __repr__(self):
        return f"<EmailVerificationToken(id={self.id}, email='{self.email}', verified={self.is_verified})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not verified and not expired)"""
        return not self.is_verified and not self.is_expired and self.attempt_count < 5
    
    def mark_verified(self):
        """Mark token as verified"""
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)
    
    def increment_attempts(self):
        """Increment attempt counter"""
        self.attempt_count += 1

class TrainingSession(Base):
    """Training session model to track user workouts and progress"""
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_type = Column(String(50))  # workout, assessment, free_training
    exercise_type = Column(String(50))  # plank, side_plank, dead_bug, etc.
    
    # Performance metrics
    duration_seconds = Column(Integer)
    stability_score = Column(Float)
    form_quality = Column(String(20))  # excellent, good, needs_improvement
    movement_variance = Column(Float)
    
    # Session data (JSON string)
    sensor_data = Column(Text)  # JSON of sensor readings
    ai_feedback = Column(Text)  # JSON of AI coaching feedback
    
    # Session lifecycle
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    # Progress tracking
    personal_best = Column(Boolean, default=False)
    improvement_percentage = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="training_sessions")
    
    def __repr__(self):
        return f"<TrainingSession(id={self.id}, user_id={self.user_id}, exercise='{self.exercise_type}')>"
    
    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        if self.duration_seconds:
            return round(self.duration_seconds / 60, 2)
        return 0.0
    
    def complete_session(self, stability_score: float, form_quality: str):
        """Mark session as completed with final metrics"""
        self.completed_at = datetime.now(timezone.utc)
        self.stability_score = stability_score
        self.form_quality = form_quality
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

# Create indexes for better performance
from sqlalchemy import Index

# Indexes for better query performance
Index('idx_user_email_active', User.email, User.is_active)
Index('idx_user_username_active', User.username, User.is_active)
Index('idx_session_token_active', UserSession.session_token, UserSession.is_active)
Index('idx_session_user_active', UserSession.user_id, UserSession.is_active)
Index('idx_password_reset_token', PasswordResetToken.token)
Index('idx_email_verification_token', EmailVerificationToken.token)
Index('idx_training_session_user_date', TrainingSession.user_id, TrainingSession.started_at)