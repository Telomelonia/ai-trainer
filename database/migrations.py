"""
CoreSense Database Migration System
Alembic-based migration management with backup and rollback capabilities
"""

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text

from .database import DatabaseManager, DatabaseConfig

logger = logging.getLogger(__name__)

class MigrationManager:
    """Database migration management with backup and safety features"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.config = DatabaseConfig()
        self.alembic_cfg = None
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.backups_dir = Path(__file__).parent / "backups"
        
        # Ensure directories exist
        self.migrations_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        
        self._setup_alembic()
    
    def _setup_alembic(self):
        """Setup Alembic configuration"""
        try:
            # Create alembic.ini if it doesn't exist
            alembic_ini_path = self.migrations_dir / "alembic.ini"
            if not alembic_ini_path.exists():
                self._create_alembic_ini()
            
            # Setup Alembic config
            self.alembic_cfg = Config(str(alembic_ini_path))
            self.alembic_cfg.set_main_option("script_location", str(self.migrations_dir))
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.config.DATABASE_URL)
            
            # Create versions directory if it doesn't exist
            versions_dir = self.migrations_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            
            # Create env.py if it doesn't exist
            env_py_path = self.migrations_dir / "env.py"
            if not env_py_path.exists():
                self._create_env_py()
                
            logger.info("Alembic configuration setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup Alembic: {e}")
            raise
    
    def _create_alembic_ini(self):
        """Create alembic.ini configuration file"""
        alembic_ini_content = """
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = %(here)s

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format (uses python format strings)
# version_num_format = %(base)s_%(rev)s

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os  # Use os.pathsep. Default behavior is to split on spaces

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        
        alembic_ini_path = self.migrations_dir / "alembic.ini"
        with open(alembic_ini_path, 'w') as f:
            f.write(alembic_ini_content.strip())
    
    def _create_env_py(self):
        """Create env.py migration environment file"""
        env_py_content = '''
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your models here
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        env_py_path = self.migrations_dir / "env.py"
        with open(env_py_path, 'w') as f:
            f.write(env_py_content.strip())
    
    def init_migrations(self) -> bool:
        """Initialize migration repository"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
                
            # Check if already initialized
            versions_dir = self.migrations_dir / "versions"
            if versions_dir.exists() and list(versions_dir.glob("*.py")):
                logger.info("Migration repository already initialized")
                return True
            
            # Initialize Alembic
            command.init(self.alembic_cfg, str(self.migrations_dir))
            logger.info("Migration repository initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize migrations: {e}")
            return False
    
    def create_backup(self) -> Optional[str]:
        """Create database backup before migration"""
        try:
            if not self.config.DATABASE_URL.startswith("sqlite"):
                logger.info("Backup not implemented for non-SQLite databases")
                return None
            
            # For SQLite, copy the database file
            db_path = self.config.DATABASE_URL.replace("sqlite:///", "")
            if not os.path.exists(db_path):
                logger.warning(f"Database file not found: {db_path}")
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = self.backups_dir / backup_filename
            
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not self.config.DATABASE_URL.startswith("sqlite"):
                logger.error("Restore not implemented for non-SQLite databases")
                return False
            
            db_path = self.config.DATABASE_URL.replace("sqlite:///", "")
            
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Close all connections
            if self.db_manager.engine:
                self.db_manager.engine.dispose()
            
            # Restore backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from backup: {backup_path}")
            
            # Reinitialize database
            return self.db_manager.initialize()
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def generate_migration(self, message: str, autogenerate: bool = True) -> Optional[str]:
        """Generate a new migration"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
            
            # Create backup if enabled
            if self.config.BACKUP_BEFORE_MIGRATE:
                backup_path = self.create_backup()
                if backup_path:
                    logger.info(f"Backup created before migration: {backup_path}")
            
            # Generate migration
            if autogenerate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message)
            
            logger.info(f"Migration generated: {message}")
            
            # Get the latest revision
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            latest_revision = script_dir.get_current_head()
            
            return latest_revision
            
        except Exception as e:
            logger.error(f"Failed to generate migration: {e}")
            return None
    
    def migrate(self, revision: str = "head") -> bool:
        """Run migrations to specified revision"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
            
            # Create backup if enabled
            if self.config.BACKUP_BEFORE_MIGRATE:
                backup_path = self.create_backup()
                if backup_path:
                    logger.info(f"Backup created before migration: {backup_path}")
            
            # Run migration
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"Migration completed to revision: {revision}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run migration: {e}")
            return False
    
    def rollback(self, revision: str) -> bool:
        """Rollback to specified revision"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
            
            # Create backup before rollback
            backup_path = self.create_backup()
            if backup_path:
                logger.info(f"Backup created before rollback: {backup_path}")
            
            # Perform rollback
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Rollback completed to revision: {revision}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return False
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
            
            with self.db_manager.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
                
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            revisions = []
            
            for revision in script_dir.walk_revisions():
                revisions.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "doc": revision.doc,
                    "create_date": revision.create_date,
                    "is_current": revision.revision == self.get_current_revision()
                })
            
            return revisions
            
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def check_database_schema(self) -> Dict[str, Any]:
        """Check database schema status"""
        try:
            if not self.db_manager._initialized:
                self.db_manager.initialize()
            
            inspector = inspect(self.db_manager.engine)
            
            # Get current tables
            tables = inspector.get_table_names()
            
            # Get current revision
            current_revision = self.get_current_revision()
            
            # Get available migrations
            migration_history = self.get_migration_history()
            
            return {
                "tables": tables,
                "current_revision": current_revision,
                "migration_count": len(migration_history),
                "pending_migrations": [
                    m for m in migration_history 
                    if not m["is_current"] and m["revision"] != current_revision
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to check database schema: {e}")
            return {}

# Global migration manager
migration_manager = MigrationManager()

# Convenience functions
def init_migrations() -> bool:
    """Initialize migration system"""
    return migration_manager.init_migrations()

def create_migration(message: str) -> Optional[str]:
    """Create a new migration"""
    return migration_manager.generate_migration(message)

def run_migrations() -> bool:
    """Run all pending migrations"""
    return migration_manager.migrate()

def rollback_migration(revision: str = "-1") -> bool:
    """Rollback to previous revision"""
    return migration_manager.rollback(revision)

def get_schema_status() -> Dict[str, Any]:
    """Get current schema status"""
    return migration_manager.check_database_schema()

# Export classes and functions
__all__ = [
    'MigrationManager',
    'migration_manager',
    'init_migrations',
    'create_migration',
    'run_migrations',
    'rollback_migration',
    'get_schema_status'
]