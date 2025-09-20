"""
Production Database Service for CoreSense MCP Servers
High-performance database layer with connection pooling, caching, and error handling
"""

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
import json
import uuid

from sqlalchemy import create_engine, and_, or_, desc, asc, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import IntegrityError, OperationalError
import redis
from cachetools import TTLCache
import threading

# Import our models
from .database_models import (
    Base, FitnessSession, UserProfile, ProgressMetrics, 
    RealTimeData, ExerciseRecommendation, AIInsight,
    ExerciseType, SessionStatus, FitnessLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Production database configuration"""
    
    # Database connection
    DATABASE_URL = os.getenv("MCP_DATABASE_URL", "sqlite:///./coresense_mcp.db")
    
    # Connection pooling
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # SQLite settings
    SQLITE_CONNECT_ARGS = {
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": None
    }
    
    # Redis caching
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    
    # Performance settings
    ECHO_SQL = os.getenv("DB_ECHO", "false").lower() == "true"
    BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", "1000"))

class CacheManager:
    """Redis-based caching with fallback to in-memory cache"""
    
    def __init__(self, redis_url: str, ttl: int = 300):
        self.ttl = ttl
        self.local_cache = TTLCache(maxsize=1000, ttl=ttl)
        self.cache_lock = threading.RLock()
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available, using local cache: {e}")
            self.redis_client = None
            self.use_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            
            with self.cache_lock:
                return self.local_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.ttl
            
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            
            with self.cache_lock:
                self.local_cache[key] = value
            
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            
            with self.cache_lock:
                self.local_cache.pop(key, None)
            
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_user_cache(self, user_id: int):
        """Clear all cache entries for a user"""
        patterns = [
            f"user:{user_id}:*",
            f"sessions:{user_id}:*",
            f"progress:{user_id}:*",
            f"profile:{user_id}"
        ]
        
        for pattern in patterns:
            try:
                if self.use_redis and self.redis_client:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Cache clear error for pattern {pattern}: {e}")

class ProductionDatabaseService:
    """Production-grade database service with advanced features"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self.cache = CacheManager(self.config.REDIS_URL, self.config.CACHE_TTL)
        self._initialized = False
        self._connection_health = True
    
    def initialize(self) -> bool:
        """Initialize database connection with production settings"""
        try:
            # Create production engine
            if self.config.DATABASE_URL.startswith("sqlite"):
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    connect_args=self.config.SQLITE_CONNECT_ARGS,
                    echo=self.config.ECHO_SQL,
                    pool_pre_ping=True
                )
            else:
                # Production PostgreSQL with connection pooling
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    poolclass=QueuePool,
                    pool_size=self.config.POOL_SIZE,
                    max_overflow=self.config.MAX_OVERFLOW,
                    pool_timeout=self.config.POOL_TIMEOUT,
                    pool_recycle=self.config.POOL_RECYCLE,
                    pool_pre_ping=True,
                    echo=self.config.ECHO_SQL
                )
            
            # Create session factory
            self.session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Test connection
            self._test_connection()
            
            self._initialized = True
            logger.info("Production database service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            self._connection_health = False
            return False
    
    def _test_connection(self) -> bool:
        """Test database connection health"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._connection_health = True
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            self._connection_health = False
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            "database": "healthy" if self._connection_health else "unhealthy",
            "cache": "healthy" if self.cache.use_redis else "local_only",
            "initialized": self._initialized,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Test database
            with self.get_session() as session:
                session.execute(text("SELECT COUNT(*) FROM fitness_sessions"))
            health["database"] = "healthy"
        except Exception as e:
            health["database"] = f"unhealthy: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        return health
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with async context manager"""
        if not self._initialized:
            raise RuntimeError("Database service not initialized")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get synchronous database session"""
        if not self._initialized:
            raise RuntimeError("Database service not initialized")
        return self.session_factory()
    
    # Fitness Session Operations
    
    def create_fitness_session(self, user_id: int, exercise_type: str, **kwargs) -> Optional[FitnessSession]:
        """Create a new fitness session"""
        try:
            session = self.get_session_sync()
            try:
                fitness_session = FitnessSession(
                    user_id=user_id,
                    session_uuid=str(uuid.uuid4()),
                    exercise_type=ExerciseType(exercise_type),
                    **kwargs
                )
                session.add(fitness_session)
                session.commit()
                session.refresh(fitness_session)
                
                # Clear user cache
                self.cache.clear_user_cache(user_id)
                
                logger.info(f"Created fitness session {fitness_session.session_uuid} for user {user_id}")
                return fitness_session
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to create fitness session: {e}")
            return None
    
    def get_user_sessions(self, user_id: int, limit: int = 50, 
                         exercise_type: Optional[str] = None,
                         days_back: Optional[int] = None) -> List[FitnessSession]:
        """Get user's fitness sessions with optional filters"""
        cache_key = f"sessions:{user_id}:{limit}:{exercise_type}:{days_back}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return [FitnessSession(**session_data) for session_data in cached]
        
        try:
            session = self.get_session_sync()
            try:
                query = session.query(FitnessSession).filter(
                    FitnessSession.user_id == user_id
                )
                
                if exercise_type:
                    query = query.filter(FitnessSession.exercise_type == ExerciseType(exercise_type))
                
                if days_back:
                    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
                    query = query.filter(FitnessSession.started_at >= cutoff)
                
                sessions = query.order_by(desc(FitnessSession.started_at)).limit(limit).all()
                
                # Cache results
                session_data = [session.to_dict() for session in sessions]
                self.cache.set(cache_key, session_data, ttl=300)
                
                return sessions
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def update_session_metrics(self, session_uuid: str, 
                             stability_score: float,
                             other_metrics: Dict[str, Any]) -> bool:
        """Update session with performance metrics"""
        try:
            session = self.get_session_sync()
            try:
                fitness_session = session.query(FitnessSession).filter(
                    FitnessSession.session_uuid == session_uuid
                ).first()
                
                if not fitness_session:
                    return False
                
                fitness_session.stability_score = stability_score
                for key, value in other_metrics.items():
                    if hasattr(fitness_session, key):
                        setattr(fitness_session, key, value)
                
                session.commit()
                
                # Clear user cache
                self.cache.clear_user_cache(fitness_session.user_id)
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to update session metrics: {e}")
            return False
    
    def complete_session(self, session_uuid: str, 
                        stability_score: float,
                        ai_summary: str,
                        session_data: Dict[str, Any]) -> bool:
        """Mark session as completed with final metrics"""
        try:
            session = self.get_session_sync()
            try:
                fitness_session = session.query(FitnessSession).filter(
                    FitnessSession.session_uuid == session_uuid
                ).first()
                
                if not fitness_session:
                    return False
                
                # Update completion metrics
                fitness_session.session_status = SessionStatus.COMPLETED
                fitness_session.completed_at = datetime.now(timezone.utc)
                fitness_session.stability_score = stability_score
                fitness_session.ai_summary = ai_summary
                
                if fitness_session.started_at:
                    duration = fitness_session.completed_at - fitness_session.started_at
                    fitness_session.actual_duration_seconds = int(duration.total_seconds())
                
                # Store session data
                fitness_session.sensor_data_summary = session_data
                
                # Check for personal best
                best_session = session.query(FitnessSession).filter(
                    FitnessSession.user_id == fitness_session.user_id,
                    FitnessSession.exercise_type == fitness_session.exercise_type,
                    FitnessSession.session_status == SessionStatus.COMPLETED
                ).order_by(desc(FitnessSession.stability_score)).first()
                
                if not best_session or stability_score > best_session.stability_score:
                    fitness_session.personal_best = True
                
                session.commit()
                
                # Clear user cache and trigger metrics calculation
                self.cache.clear_user_cache(fitness_session.user_id)
                self._update_progress_metrics(fitness_session.user_id)
                
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to complete session: {e}")
            return False
    
    # User Profile Operations
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile with caching"""
        cache_key = f"profile:{user_id}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return UserProfile(**cached)
        
        try:
            session = self.get_session_sync()
            try:
                profile = session.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                
                if profile:
                    # Cache profile
                    self.cache.set(cache_key, profile.to_dict())
                
                return profile
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """Update user profile"""
        try:
            session = self.get_session_sync()
            try:
                profile = session.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                
                if not profile:
                    # Create new profile
                    profile = UserProfile(user_id=user_id)
                    session.add(profile)
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                
                # Recalculate BMI if height/weight changed
                if 'height_cm' in updates or 'weight_kg' in updates:
                    profile.calculate_bmi()
                
                profile.updated_at = datetime.now(timezone.utc)
                session.commit()
                session.refresh(profile)
                
                # Clear cache
                self.cache.delete(f"profile:{user_id}")
                
                return profile
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return None
    
    # Progress Analytics
    
    def get_progress_metrics(self, user_id: int, period_type: str = "daily", 
                           days_back: int = 30) -> List[ProgressMetrics]:
        """Get progress metrics for analytics"""
        cache_key = f"progress:{user_id}:{period_type}:{days_back}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return [ProgressMetrics(**metric) for metric in cached]
        
        try:
            session = self.get_session_sync()
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
                
                metrics = session.query(ProgressMetrics).filter(
                    ProgressMetrics.user_id == user_id,
                    ProgressMetrics.period_type == period_type,
                    ProgressMetrics.metric_date >= cutoff
                ).order_by(desc(ProgressMetrics.metric_date)).all()
                
                # Cache results
                metrics_data = [metric.__dict__ for metric in metrics]
                self.cache.set(cache_key, metrics_data, ttl=600)  # 10 minutes
                
                return metrics
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get progress metrics: {e}")
            return []
    
    def _update_progress_metrics(self, user_id: int):
        """Update daily progress metrics for a user"""
        try:
            session = self.get_session_sync()
            try:
                today = datetime.now(timezone.utc).date()
                
                # Get today's sessions
                today_sessions = session.query(FitnessSession).filter(
                    FitnessSession.user_id == user_id,
                    func.date(FitnessSession.started_at) == today,
                    FitnessSession.session_status == SessionStatus.COMPLETED
                ).all()
                
                if not today_sessions:
                    return
                
                # Calculate metrics
                total_sessions = len(today_sessions)
                total_duration = sum(s.actual_duration_seconds or 0 for s in today_sessions) / 60
                avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
                
                stability_scores = [s.stability_score for s in today_sessions if s.stability_score]
                avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0
                best_stability = max(stability_scores) if stability_scores else 0
                worst_stability = min(stability_scores) if stability_scores else 0
                
                exercises = list(set(s.exercise_type.value for s in today_sessions))
                exercise_variety = len(exercises) / len(ExerciseType) if exercises else 0
                
                personal_bests = sum(1 for s in today_sessions if s.personal_best)
                
                # Calculate performance grade
                if avg_stability >= 90:
                    grade = "A"
                elif avg_stability >= 80:
                    grade = "B"
                elif avg_stability >= 70:
                    grade = "C"
                elif avg_stability >= 60:
                    grade = "D"
                else:
                    grade = "F"
                
                # Update or create metrics record
                existing = session.query(ProgressMetrics).filter(
                    ProgressMetrics.user_id == user_id,
                    ProgressMetrics.period_type == "daily",
                    func.date(ProgressMetrics.metric_date) == today
                ).first()
                
                if existing:
                    metric = existing
                else:
                    metric = ProgressMetrics(
                        user_id=user_id,
                        metric_date=datetime.now(timezone.utc),
                        period_type="daily"
                    )
                    session.add(metric)
                
                # Update values
                metric.total_sessions = total_sessions
                metric.total_duration_minutes = total_duration
                metric.average_session_duration = avg_duration
                metric.average_stability_score = avg_stability
                metric.best_stability_score = best_stability
                metric.worst_stability_score = worst_stability
                metric.exercises_performed = exercises
                metric.exercise_variety_score = exercise_variety
                metric.personal_bests_count = personal_bests
                metric.performance_grade = grade
                metric.calculated_at = datetime.now(timezone.utc)
                
                session.commit()
                
                # Clear progress cache
                cache_patterns = [f"progress:{user_id}:*"]
                for pattern in cache_patterns:
                    self.cache.delete(pattern)
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to update progress metrics: {e}")
    
    # Real-time Data Operations
    
    def store_realtime_data(self, session_id: int, user_id: int, 
                          sensor_data: Dict[str, Any]) -> bool:
        """Store real-time sensor data point"""
        try:
            session = self.get_session_sync()
            try:
                data_point = RealTimeData(
                    session_id=session_id,
                    user_id=user_id,
                    **sensor_data
                )
                session.add(data_point)
                session.commit()
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to store realtime data: {e}")
            return False
    
    def batch_store_realtime_data(self, data_points: List[Dict[str, Any]]) -> bool:
        """Batch store multiple real-time data points for performance"""
        try:
            session = self.get_session_sync()
            try:
                realtime_objects = [RealTimeData(**data) for data in data_points]
                session.bulk_save_objects(realtime_objects)
                session.commit()
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to batch store realtime data: {e}")
            return False
    
    # AI Operations
    
    def create_ai_insight(self, user_id: int, insight_type: str, 
                         title: str, content: str, **kwargs) -> Optional[AIInsight]:
        """Create AI-generated insight"""
        try:
            session = self.get_session_sync()
            try:
                insight = AIInsight(
                    user_id=user_id,
                    insight_type=insight_type,
                    title=title,
                    content=content,
                    **kwargs
                )
                session.add(insight)
                session.commit()
                session.refresh(insight)
                
                # Clear user insights cache
                self.cache.delete(f"insights:{user_id}")
                
                return insight
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to create AI insight: {e}")
            return None
    
    def get_user_insights(self, user_id: int, unread_only: bool = False) -> List[AIInsight]:
        """Get AI insights for user"""
        cache_key = f"insights:{user_id}:{unread_only}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return [AIInsight(**insight) for insight in cached]
        
        try:
            session = self.get_session_sync()
            try:
                query = session.query(AIInsight).filter(
                    AIInsight.user_id == user_id,
                    AIInsight.archived_at.is_(None)
                )
                
                if unread_only:
                    query = query.filter(AIInsight.is_read == False)
                
                insights = query.order_by(desc(AIInsight.created_at)).limit(20).all()
                
                # Cache results
                insights_data = [insight.__dict__ for insight in insights]
                self.cache.set(cache_key, insights_data, ttl=300)
                
                return insights
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to get user insights: {e}")
            return []
    
    # Cleanup and Maintenance
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data beyond retention period"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        cleanup_stats = {"realtime_data": 0, "ai_insights": 0}
        
        try:
            session = self.get_session_sync()
            try:
                # Clean old real-time data
                old_realtime = session.query(RealTimeData).filter(
                    RealTimeData.timestamp < cutoff
                ).delete()
                cleanup_stats["realtime_data"] = old_realtime
                
                # Archive old AI insights
                old_insights = session.query(AIInsight).filter(
                    AIInsight.created_at < cutoff,
                    AIInsight.archived_at.is_(None)
                ).update({"archived_at": datetime.now(timezone.utc)})
                cleanup_stats["ai_insights"] = old_insights
                
                session.commit()
                
                logger.info(f"Cleaned up old data: {cleanup_stats}")
                return cleanup_stats
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return cleanup_stats

# Global service instance
db_service = ProductionDatabaseService()