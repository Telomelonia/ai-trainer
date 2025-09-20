"""
Database Configuration and Connection Management for CoreSense Authentication
SQLAlchemy database setup with proper connection pooling and session management
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from contextlib import contextmanager

# Import our models
from .models import Base, User, UserSession, PasswordResetToken, EmailVerificationToken, TrainingSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration with environment-based settings"""
    
    # Default to SQLite for development, can be overridden with environment variables
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./coresense_auth.db")
    
    # SQLite-specific settings for development
    SQLITE_CONNECT_ARGS = {
        "check_same_thread": False,
        "timeout": 20,
        "isolation_level": None
    }
    
    # PostgreSQL settings for production
    POSTGRES_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    POSTGRES_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    POSTGRES_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POSTGRES_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # General database settings
    ECHO_SQL: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    AUTOCOMMIT: bool = False
    AUTOFLUSH: bool = False

class DatabaseManager:
    """Database manager for connection and session handling"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize database connection and create tables
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create engine based on database type
            if self.config.DATABASE_URL.startswith("sqlite"):
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    connect_args=self.config.SQLITE_CONNECT_ARGS,
                    poolclass=StaticPool,
                    echo=self.config.ECHO_SQL
                )
            else:
                # PostgreSQL or other databases
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    pool_size=self.config.POSTGRES_POOL_SIZE,
                    max_overflow=self.config.POSTGRES_MAX_OVERFLOW,
                    pool_timeout=self.config.POSTGRES_POOL_TIMEOUT,
                    pool_recycle=self.config.POSTGRES_POOL_RECYCLE,
                    echo=self.config.ECHO_SQL
                )
            
            # Create session factory
            self.session_factory = sessionmaker(
                autocommit=self.config.AUTOCOMMIT,
                autoflush=self.config.AUTOFLUSH,
                bind=self.engine
            )
            
            # Create all tables
            self.create_tables()
            
            # Test connection
            self.test_connection()
            
            self._initialized = True
            logger.info(f"Database initialized successfully: {self.config.DATABASE_URL}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_session(self) -> Session:
        """
        Get a new database session
        
        Returns:
            SQLAlchemy session object
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.session_factory()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup
        
        Yields:
            SQLAlchemy session object with automatic commit/rollback
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database engine and connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

class DatabaseService:
    """High-level database service for application use"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def initialize(self) -> bool:
        """Initialize database service"""
        return self.db_manager.initialize()
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.db_manager.get_session()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations
        
        Usage:
            with db_service.session_scope() as session:
                # Database operations here
                user = session.query(User).filter_by(email=email).first()
        """
        with self.db_manager.get_session_context() as session:
            yield session
    
    def create_user(self, email: str, username: str, hashed_password: str, **kwargs) -> Optional[User]:
        """
        Create a new user
        
        Args:
            email: User email
            username: Username
            hashed_password: Pre-hashed password
            **kwargs: Additional user fields
            
        Returns:
            Created User object or None if failed
        """
        try:
            with self.session_scope() as session:
                user = User(
                    email=email,
                    username=username,
                    hashed_password=hashed_password,
                    **kwargs
                )
                session.add(user)
                session.flush()  # Get the ID without committing
                session.refresh(user)  # Refresh to get all fields
                return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            with self.session_scope() as session:
                return session.query(User).filter(User.email == email, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with self.session_scope() as session:
                return session.query(User).filter(User.username == username, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with self.session_scope() as session:
                return session.query(User).filter(User.id == user_id, User.is_active == True).first()
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    def update_user(self, user_id: int, **updates) -> Optional[User]:
        """Update user fields"""
        try:
            with self.session_scope() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    for key, value in updates.items():
                        if hasattr(user, key):
                            setattr(user, key, value)
                    session.flush()
                    session.refresh(user)
                return user
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return None
    
    def create_user_session(self, user_id: int, session_token: str, refresh_token: str, 
                           expires_at, **kwargs) -> Optional[UserSession]:
        """Create a new user session"""
        try:
            with self.session_scope() as session:
                user_session = UserSession(
                    user_id=user_id,
                    session_token=session_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    **kwargs
                )
                session.add(user_session)
                session.flush()
                session.refresh(user_session)
                return user_session
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return None
    
    def get_session_by_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by token"""
        try:
            with self.session_scope() as session:
                return session.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                ).first()
        except Exception as e:
            logger.error(f"Failed to get session by token: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a user session"""
        try:
            with self.session_scope() as session:
                user_session = session.query(UserSession).filter(
                    UserSession.session_token == session_token
                ).first()
                if user_session:
                    user_session.invalidate()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of cleaned sessions"""
        try:
            from datetime import datetime, timezone
            with self.session_scope() as session:
                expired_sessions = session.query(UserSession).filter(
                    UserSession.expires_at < datetime.now(timezone.utc)
                ).all()
                
                count = len(expired_sessions)
                for user_session in expired_sessions:
                    user_session.invalidate()
                
                return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

# Global database service instance
db_service = DatabaseService()

# Dependency for getting database sessions in FastAPI/other frameworks
def get_db_session() -> Generator[Session, None, None]:
    """Dependency function for getting database sessions"""
    with db_service.session_scope() as session:
        yield session

# Export classes and service
__all__ = [
    'DatabaseConfig',
    'DatabaseManager', 
    'DatabaseService',
    'db_service',
    'get_db_session'
]