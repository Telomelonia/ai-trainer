#!/usr/bin/env python3
"""
CoreSense Database CLI
Command-line interface for database management operations
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database import (
    setup_database, db_service, get_db_health,
    init_migrations, create_migration, run_migrations, 
    rollback_migration, get_schema_status
)
from database.sample_data import populate_sample_data, clear_all_data

def setup_db_command(args):
    """Setup database and run migrations"""
    print("Setting up CoreSense database...")
    
    # Set database URL if provided
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
        print(f"Using database URL: {args.database_url}")
    
    # Setup database
    success = setup_database(auto_migrate=args.migrate)
    
    if success:
        print("✅ Database setup completed successfully!")
        
        # Populate with sample data if requested
        if args.sample_data:
            print("Populating with sample data...")
            if populate_sample_data(args.users, args.sessions_per_user):
                print(f"✅ Created {args.users} users with {args.sessions_per_user} sessions each")
            else:
                print("❌ Failed to populate sample data")
        
        return 0
    else:
        print("❌ Database setup failed")
        return 1

def health_command(args):
    """Check database health"""
    print("Checking database health...")
    
    try:
        health_data = get_db_health()
        
        print(f"Connection Status: {'✅ Healthy' if health_data.get('connection_healthy') else '❌ Unhealthy'}")
        print(f"Health Status: {health_data.get('health_status', 'Unknown')}")
        print(f"Total Connections: {health_data.get('connection_count', 0)}")
        print(f"Total Queries: {health_data.get('query_count', 0)}")
        print(f"Slow Queries: {health_data.get('slow_query_count', 0)}")
        print(f"Errors: {health_data.get('error_count', 0)}")
        
        if 'pool_size' in health_data:
            print(f"Pool Size: {health_data['pool_size']}")
            print(f"Checked In: {health_data['checked_in']}")
            print(f"Checked Out: {health_data['checked_out']}")
        
        return 0 if health_data.get('connection_healthy') else 1
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

def migrate_command(args):
    """Migration management"""
    try:
        if args.action == "init":
            print("Initializing migration repository...")
            if init_migrations():
                print("✅ Migration repository initialized")
                return 0
            else:
                print("❌ Failed to initialize migrations")
                return 1
                
        elif args.action == "create":
            if not args.message:
                print("❌ Migration message is required")
                return 1
            
            print(f"Creating migration: {args.message}")
            revision = create_migration(args.message)
            if revision:
                print(f"✅ Migration created: {revision}")
                return 0
            else:
                print("❌ Failed to create migration")
                return 1
                
        elif args.action == "up":
            print("Running migrations...")
            if run_migrations():
                print("✅ Migrations completed")
                return 0
            else:
                print("❌ Migration failed")
                return 1
                
        elif args.action == "down":
            revision = args.revision or "-1"
            print(f"Rolling back to revision: {revision}")
            if rollback_migration(revision):
                print("✅ Rollback completed")
                return 0
            else:
                print("❌ Rollback failed")
                return 1
                
        elif args.action == "status":
            print("Getting migration status...")
            status = get_schema_status()
            
            print(f"Current Revision: {status.get('current_revision', 'None')}")
            print(f"Total Tables: {len(status.get('tables', []))}")
            print(f"Total Migrations: {status.get('migration_count', 0)}")
            
            pending = status.get('pending_migrations', [])
            if pending:
                print(f"Pending Migrations: {len(pending)}")
                for migration in pending:
                    print(f"  - {migration['revision']}: {migration['doc']}")
            else:
                print("No pending migrations")
            
            return 0
            
    except Exception as e:
        print(f"❌ Migration command failed: {e}")
        return 1

def data_command(args):
    """Data management"""
    try:
        if args.action == "populate":
            print(f"Populating database with sample data...")
            print(f"Users: {args.users}, Sessions per user: {args.sessions_per_user}")
            
            if populate_sample_data(args.users, args.sessions_per_user):
                print("✅ Sample data populated successfully")
                return 0
            else:
                print("❌ Failed to populate sample data")
                return 1
                
        elif args.action == "clear":
            if not args.confirm:
                print("❌ This will delete ALL data. Use --confirm to proceed.")
                return 1
                
            print("Clearing all data from database...")
            if clear_all_data():
                print("✅ All data cleared")
                return 0
            else:
                print("❌ Failed to clear data")
                return 1
                
    except Exception as e:
        print(f"❌ Data command failed: {e}")
        return 1

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="CoreSense Database Management CLI")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup database and run migrations")
    setup_parser.add_argument("--database-url", help="Database connection URL")
    setup_parser.add_argument("--no-migrate", dest="migrate", action="store_false", 
                             help="Skip running migrations")
    setup_parser.add_argument("--sample-data", action="store_true", 
                             help="Populate with sample data")
    setup_parser.add_argument("--users", type=int, default=10, 
                             help="Number of sample users to create")
    setup_parser.add_argument("--sessions-per-user", type=int, default=20,
                             help="Number of sample sessions per user")
    setup_parser.set_defaults(func=setup_db_command)
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check database health")
    health_parser.set_defaults(func=health_command)
    
    # Migration commands
    migrate_parser = subparsers.add_parser("migrate", help="Migration management")
    migrate_parser.add_argument("action", choices=["init", "create", "up", "down", "status"],
                               help="Migration action")
    migrate_parser.add_argument("--message", help="Migration message (for create)")
    migrate_parser.add_argument("--revision", help="Target revision (for down)")
    migrate_parser.set_defaults(func=migrate_command)
    
    # Data commands
    data_parser = subparsers.add_parser("data", help="Data management")
    data_parser.add_argument("action", choices=["populate", "clear"],
                            help="Data action")
    data_parser.add_argument("--users", type=int, default=10,
                            help="Number of sample users (for populate)")
    data_parser.add_argument("--sessions-per-user", type=int, default=20,
                            help="Sessions per user (for populate)")
    data_parser.add_argument("--confirm", action="store_true",
                            help="Confirm destructive operations")
    data_parser.set_defaults(func=data_command)
    
    # Parse arguments and run command
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())