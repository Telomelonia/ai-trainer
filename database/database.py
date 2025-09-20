"""
CoreSense Database Configuration and Connection Management
Advanced SQLAlchemy database setup with connection pooling, session management,
health monitoring, and production-ready features.
"""

import os
import logging
from typing import Generator, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, MetaData, text, event, pool, exc
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.engine import Engine
import time

# Import our models
from .models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Comprehensive database configuration with environment-based settings"""
    
    def __init__(self):
        # Database URL - supports PostgreSQL, MySQL, SQLite
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./coresense.db")
        
        # Connection Pool Settings
        self.POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
        self.MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
        self.POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
        
        # SQLite-specific settings
        self.SQLITE_CONNECT_ARGS = {
            "check_same_thread": False,
            "timeout": 20,
            "isolation_level": None
        }
        
        # PostgreSQL-specific settings
        self.POSTGRES_CONNECT_ARGS = {
            "connect_timeout": 10,
            "command_timeout": 60,
            "server_settings": {
                "jit": "off"  # Disable JIT for better connection time
            }
        }
        
        # MySQL-specific settings
        self.MYSQL_CONNECT_ARGS = {
            "connect_timeout": 10,
            "read_timeout": 60,
            "write_timeout": 60,
            "charset": "utf8mb4"
        }
        
        # General settings
        self.ECHO_SQL: bool = os.getenv("DB_ECHO", "false").lower() == "true"
        self.AUTOCOMMIT: bool = False
        self.AUTOFLUSH: bool = False
        
        # Health check settings
        self.HEALTH_CHECK_ENABLED: bool = os.getenv("DB_HEALTH_CHECK", "true").lower() == "true"
        self.HEALTH_CHECK_INTERVAL: int = int(os.getenv("DB_HEALTH_CHECK_INTERVAL", "300"))  # 5 minutes
        
        # Performance monitoring
        self.SLOW_QUERY_THRESHOLD: float = float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "1.0"))
        self.ENABLE_QUERY_STATS: bool = os.getenv("DB_QUERY_STATS", "false").lower() == "true"
        
        # Migration settings
        self.AUTO_MIGRATE: bool = os.getenv("DB_AUTO_MIGRATE", "false").lower() == "true"
        self.BACKUP_BEFORE_MIGRATE: bool = os.getenv("DB_BACKUP_BEFORE_MIGRATE", "true").lower() == "true"

class DatabaseHealthMonitor:
    """Database health monitoring and metrics collection"""
    
    def __init__(self):
        self.connection_count = 0
        self.query_count = 0
        self.slow_query_count = 0
        self.error_count = 0
        self.last_health_check = None
        self.health_status = "unknown"
        
    def record_connection(self):
        self.connection_count += 1
        
    def record_query(self, duration: float):
        self.query_count += 1
        if duration > DatabaseConfig().SLOW_QUERY_THRESHOLD:
            self.slow_query_count += 1
            logger.warning(f"Slow query detected: {duration:.2f}s")
            
    def record_error(self):
        self.error_count += 1
        
    def get_health_stats(self) -> Dict[str, Any]:
        return {
            "connection_count": self.connection_count,
            "query_count": self.query_count,
            "slow_query_count": self.slow_query_count,
            "error_count": self.error_count,
            "last_health_check": self.last_health_check,
            "health_status": self.health_status
        }

class DatabaseManager:
    """Advanced database manager with connection pooling and monitoring"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine: Optional[Engine] = None
        self.session_factory = None
        self._initialized = False
        self.health_monitor = DatabaseHealthMonitor()
        self._last_health_check = None
        
    def _get_pool_class(self) -> type:
        """Determine appropriate pool class based on database type"""
        if self.config.DATABASE_URL.startswith("sqlite"):
            return StaticPool
        elif "sqlite" in self.config.DATABASE_URL:
            return StaticPool
        else:
            return QueuePool
            
    def _get_connect_args(self) -> Dict[str, Any]:
        """Get database-specific connection arguments"""
        if self.config.DATABASE_URL.startswith("sqlite"):
            return self.config.SQLITE_CONNECT_ARGS
        elif self.config.DATABASE_URL.startswith("postgresql"):
            return self.config.POSTGRES_CONNECT_ARGS
        elif self.config.DATABASE_URL.startswith("mysql"):
            return self.config.MYSQL_CONNECT_ARGS
        else:
            return {}
    
    def _setup_engine_events(self):
        """Setup SQLAlchemy engine event listeners for monitoring"""
        if not self.engine:
            return
            
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.health_monitor.record_connection()
            logger.debug("Database connection established")
            
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self.health_monitor.record_query(total)
            
            if self.config.ENABLE_QUERY_STATS and total > self.config.SLOW_QUERY_THRESHOLD:
                logger.warning(f"Slow query: {total:.2f}s - {statement[:100]}...")
                
        @event.listens_for(self.engine, "handle_error")
        def handle_error(exception_context):
            self.health_monitor.record_error()
            logger.error(f"Database error: {exception_context.original_exception}")
    
    def initialize(self) -> bool:
        """
        Initialize database connection with advanced configuration
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            pool_class = self._get_pool_class()
            connect_args = self._get_connect_args()
            
            # Create engine with appropriate settings
            if pool_class == StaticPool:
                # SQLite configuration
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    connect_args=connect_args,
                    poolclass=pool_class,
                    echo=self.config.ECHO_SQL
                )
            else:
                # PostgreSQL/MySQL configuration with connection pooling
                self.engine = create_engine(
                    self.config.DATABASE_URL,
                    pool_size=self.config.POOL_SIZE,
                    max_overflow=self.config.MAX_OVERFLOW,
                    pool_timeout=self.config.POOL_TIMEOUT,
                    pool_recycle=self.config.POOL_RECYCLE,
                    pool_pre_ping=self.config.POOL_PRE_PING,
                    connect_args=connect_args,
                    echo=self.config.ECHO_SQL,
                    poolclass=pool_class
                )
            
            # Setup event listeners for monitoring
            self._setup_engine_events()
            
            # Create session factory
            self.session_factory = sessionmaker(
                autocommit=self.config.AUTOCOMMIT,
                autoflush=self.config.AUTOFLUSH,
                bind=self.engine
            )
            
            # Test connection and create tables
            self.test_connection()
            
            if self.config.AUTO_MIGRATE:
                self.create_tables()
            
            self._initialized = True
            self.health_monitor.health_status = "healthy"
            logger.info(f"Database initialized successfully: {self._mask_url(self.config.DATABASE_URL)}")
            
            return True
            
        except Exception as e:
            self.health_monitor.health_status = "unhealthy"
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive information in database URL for logging"""
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                auth, host_db = rest.split("@", 1)
                return f"{scheme}://***:***@{host_db}"
        return url
    
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
        Test database connection with retry logic
        
        Returns:
            True if connection successful, False otherwise
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    result.fetchone()
                    
                self.health_monitor.last_health_check = datetime.now(timezone.utc)
                self.health_monitor.health_status = "healthy"
                logger.info("Database connection test successful")
                return True
                
            except Exception as e:
                logger.warning(f"Database connection test attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.health_monitor.health_status = "unhealthy"
                    logger.error("Database connection test failed after all retries")
                    
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Dictionary containing health status and metrics
        """
        health_data = self.health_monitor.get_health_stats()
        
        # Test current connection
        connection_healthy = self.test_connection()
        health_data["connection_healthy"] = connection_healthy
        
        # Check pool status if available
        if hasattr(self.engine.pool, 'size'):
            health_data["pool_size"] = self.engine.pool.size()
            health_data["checked_in"] = self.engine.pool.checkedin()
            health_data["checked_out"] = self.engine.pool.checkedout()
            health_data["invalid"] = self.engine.pool.invalidated()
        
        return health_data
    
    def get_session(self) -> Session:
        """
        Get a new database session with error handling
        
        Returns:
            SQLAlchemy session object
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            return self.session_factory()
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            raise
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup and error handling
        
        Yields:
            SQLAlchemy session object with automatic commit/rollback
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database engine and connections"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database connections closed")
                self.health_monitor.health_status = "closed"
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

class DatabaseService:
    """High-level database service with comprehensive CRUD operations"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        
    def initialize(self) -> bool:
        """Initialize database service"""
        return self.db_manager.initialize()
    
    def health_check(self) -> Dict[str, Any]:
        """Get database health status"""
        return self.db_manager.health_check()
    
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
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new user with comprehensive error handling
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            User ID if successful, None if failed
        """
        try:
            from .models import User
            
            with self.session_scope() as session:
                user = User(**user_data)
                session.add(user)
                session.flush()  # Get the ID without committing
                return user.id
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def batch_insert(self, model_class, data_list: list) -> bool:
        """
        Perform batch insert for better performance
        
        Args:
            model_class: SQLAlchemy model class
            data_list: List of dictionaries with data to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.session_scope() as session:
                objects = [model_class(**data) for data in data_list]
                session.bulk_save_objects(objects)
                return True
                
        except Exception as e:
            logger.error(f"Failed to perform batch insert: {e}")
            return False
    
    def execute_raw_query(self, query: str, params: Dict = None) -> Any:
        """
        Execute raw SQL query with parameters
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            with self.session_scope() as session:
                result = session.execute(text(query), params or {})
                return result.fetchall()
                
        except Exception as e:
            logger.error(f"Failed to execute raw query: {e}")
            raise
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data across all relevant tables
        
        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {}
        
        try:
            from .models import UserSession, AICoachingSession
            from datetime import datetime, timezone
            
            with self.session_scope() as session:
                # Clean up expired sessions
                expired_sessions = session.query(UserSession).filter(
                    UserSession.expires_at < datetime.now(timezone.utc),
                    UserSession.is_active == True
                ).all()
                
                for user_session in expired_sessions:
                    user_session.is_active = False
                
                cleanup_stats['expired_sessions'] = len(expired_sessions)
                
                logger.info(f"Cleanup completed: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return {}

# Global database service instance
db_service = DatabaseService()

# Dependency for getting database sessions in FastAPI/other frameworks
def get_db_session() -> Generator[Session, None, None]:
    """Dependency function for getting database sessions"""
    with db_service.session_scope() as session:
        yield session

def get_db_health() -> Dict[str, Any]:
    """Get database health status for monitoring endpoints"""
    return db_service.health_check()

# Export classes and functions
__all__ = [
    'DatabaseConfig',
    'DatabaseManager', 
    'DatabaseService',
    'DatabaseHealthMonitor',
    'db_service',
    'get_db_session',
    'get_db_health'
]