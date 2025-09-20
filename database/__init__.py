"""
CoreSense Database Package
Complete database management system for CoreSense AI Platform
"""

from .models import (
    Base, User, UserSession, ExerciseSession, ProgressRecord,
    AICoachingSession, Subscription, Payment, MuscleActivationPattern,
    Achievement, UserAchievement,
    # Enums
    UserRole, FitnessLevel, ExerciseType, SessionStatus,
    SubscriptionStatus, PaymentStatus, AchievementType
)

from .database import (
    DatabaseConfig, DatabaseManager, DatabaseService,
    DatabaseHealthMonitor, db_service, get_db_session, get_db_health
)

from .migrations import (
    MigrationManager, migration_manager, init_migrations,
    create_migration, run_migrations, rollback_migration, get_schema_status
)

# Version information
__version__ = "1.0.0"

# Quick setup function
def setup_database(database_url: str = None, auto_migrate: bool = True) -> bool:
    """
    Quick setup function for CoreSense database
    
    Args:
        database_url: Database connection URL
        auto_migrate: Whether to run migrations automatically
        
    Returns:
        True if setup successful, False otherwise
    """
    import os
    
    # Set database URL if provided
    if database_url:
        os.environ["DATABASE_URL"] = database_url
    
    # Set auto-migrate flag
    if auto_migrate:
        os.environ["DB_AUTO_MIGRATE"] = "true"
    
    # Initialize database service
    success = db_service.initialize()
    
    if success and auto_migrate:
        # Initialize migrations if needed
        init_migrations()
        
        # Run any pending migrations
        run_migrations()
    
    return success

# Export all public classes and functions
__all__ = [
    # Models
    'Base', 'User', 'UserSession', 'ExerciseSession', 'ProgressRecord',
    'AICoachingSession', 'Subscription', 'Payment', 'MuscleActivationPattern',
    'Achievement', 'UserAchievement',
    
    # Enums
    'UserRole', 'FitnessLevel', 'ExerciseType', 'SessionStatus',
    'SubscriptionStatus', 'PaymentStatus', 'AchievementType',
    
    # Database management
    'DatabaseConfig', 'DatabaseManager', 'DatabaseService',
    'DatabaseHealthMonitor', 'db_service', 'get_db_session', 'get_db_health',
    
    # Migration management
    'MigrationManager', 'migration_manager', 'init_migrations',
    'create_migration', 'run_migrations', 'rollback_migration', 'get_schema_status',
    
    # Utilities
    'setup_database'
]