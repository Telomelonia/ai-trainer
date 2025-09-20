"""
Database Service for CoreSense AI Platform
Centralized database connection management and session handling for MCP servers
Supports connection pooling, health monitoring, and concurrent user access
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, Optional, Any, Dict, List
import asyncio
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.pool import QueuePool
import threading
import time
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        # Database connection settings
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://coresense:coresense123@localhost:5432/coresense_db"
        )
        
        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
        self.pool_pre_ping = True
        
        # Query settings
        self.query_timeout = int(os.getenv("DB_QUERY_TIMEOUT", "30"))
        self.statement_timeout = int(os.getenv("DB_STATEMENT_TIMEOUT", "30000"))  # milliseconds
        
        # Health check settings
        self.health_check_interval = int(os.getenv("DB_HEALTH_CHECK_INTERVAL", "60"))  # seconds
        self.max_connection_retries = int(os.getenv("DB_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("DB_RETRY_DELAY", "1.0"))
        
        # Performance settings
        self.enable_query_logging = os.getenv("DB_ENABLE_QUERY_LOGGING", "false").lower() == "true"
        self.slow_query_threshold = float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "1.0"))  # seconds
        
        # Security settings
        self.ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
        self.ssl_cert = os.getenv("DB_SSL_CERT")
        self.ssl_key = os.getenv("DB_SSL_KEY")
        self.ssl_ca = os.getenv("DB_SSL_CA")

class DatabaseService:
    """Centralized database service for MCP servers"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.config = DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self.scoped_session_factory = None
        self._health_check_task = None
        self._stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'queries_executed': 0,
            'slow_queries': 0,
            'errors': 0,
            'last_health_check': None,
            'is_healthy': False
        }
        self._initialized = True
        
    async def initialize(self):
        """Initialize database connection and services"""
        try:
            logger.info("Initializing database service...")
            
            # Create engine with connection pooling
            self.engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.enable_query_logging,
                connect_args={
                    "connect_timeout": self.config.query_timeout,
                    "options": f"-c statement_timeout={self.config.statement_timeout}"
                }
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create scoped session for thread safety
            self.scoped_session_factory = scoped_session(self.SessionLocal)
            
            # Set up event listeners for monitoring
            self._setup_event_listeners()
            
            # Test initial connection
            await self._test_connection()
            
            # Start health check task
            if self._health_check_task is None:
                self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("Database service initialized successfully")
            self._stats['is_healthy'] = True
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            self._stats['is_healthy'] = False
            raise
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._stats['connections_created'] += 1
            logger.debug("Database connection created")
        
        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            self._stats['connections_closed'] += 1
            logger.debug("Database connection closed")
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self._stats['queries_executed'] += 1
            
            if total > self.config.slow_query_threshold:
                self._stats['slow_queries'] += 1
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    async def _test_connection(self):
        """Test database connection"""
        try:
            with self.get_db_session() as db:
                result = db.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def _health_check_loop(self):
        """Continuous health check loop"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self._stats['errors'] += 1
    
    async def _perform_health_check(self):
        """Perform database health check"""
        try:
            start_time = time.time()
            
            with self.get_db_session() as db:
                # Test basic connectivity
                db.execute(text("SELECT 1"))
                
                # Check pool status
                pool = self.engine.pool
                pool_status = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow()
                }
                
                health_duration = time.time() - start_time
                
                self._stats['last_health_check'] = datetime.now(timezone.utc)
                self._stats['is_healthy'] = True
                
                logger.debug(f"Health check passed ({health_duration:.3f}s) - Pool: {pool_status}")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._stats['is_healthy'] = False
            self._stats['errors'] += 1
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.scoped_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            self._stats['errors'] += 1
            raise
        finally:
            session.close()
    
    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_connection_retries):
            try:
                return await operation(*args, **kwargs)
            except (DisconnectionError, SQLAlchemyError) as e:
                last_exception = e
                if attempt < self.config.max_connection_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Database operation failed after {self.config.max_connection_retries} attempts")
        
        raise last_exception
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database service health status"""
        pool = self.engine.pool if self.engine else None
        
        health_status = {
            'is_healthy': self._stats['is_healthy'],
            'last_health_check': self._stats['last_health_check'],
            'stats': self._stats.copy(),
            'pool_status': {
                'size': pool.size() if pool else 0,
                'checked_in': pool.checkedin() if pool else 0,
                'checked_out': pool.checkedout() if pool else 0,
                'overflow': pool.overflow() if pool else 0,
                'total_capacity': (pool.size() + pool.overflow()) if pool else 0
            },
            'config': {
                'pool_size': self.config.pool_size,
                'max_overflow': self.config.max_overflow,
                'pool_timeout': self.config.pool_timeout,
                'pool_recycle': self.config.pool_recycle
            }
        }
        
        return health_status
    
    async def cleanup(self):
        """Cleanup database service"""
        try:
            logger.info("Cleaning up database service...")
            
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            if self.scoped_session_factory:
                self.scoped_session_factory.remove()
            
            if self.engine:
                self.engine.dispose()
                
            logger.info("Database service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during database service cleanup: {e}")

# Utility decorators for database operations
def db_transaction(func):
    """Decorator for automatic database transaction management"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_service = DatabaseService()
        with db_service.get_db_session() as db:
            return func(db, *args, **kwargs)
    return wrapper

def async_db_transaction(func):
    """Decorator for async database transaction management"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db_service = DatabaseService()
        
        async def operation():
            with db_service.get_db_session() as db:
                return await func(db, *args, **kwargs)
        
        return await db_service.execute_with_retry(operation)
    return wrapper

# Global database service instance
db_service = DatabaseService()

# Convenience functions
def get_db_session():
    """Get database session (for use in MCP servers)"""
    return db_service.get_db_session()

async def init_database():
    """Initialize database service (call from main)"""
    await db_service.initialize()

async def cleanup_database():
    """Cleanup database service (call on shutdown)"""
    await db_service.cleanup()

def get_database_health():
    """Get database health status"""
    return db_service.get_health_status()