# CoreSense Database System

A comprehensive database schema and management system for the CoreSense AI fitness platform, built with SQLAlchemy and Alembic.

## Overview

The CoreSense database system provides:
- **Complete user management** with fitness profiles and preferences
- **Exercise session tracking** with detailed muscle activation data
- **Progress monitoring** and performance analytics
- **AI coaching history** and recommendations
- **Subscription and billing management** for monetization
- **Achievement system** with milestones and gamification
- **Advanced connection pooling** and health monitoring
- **Migration system** with backup and rollback capabilities

## Architecture

### Core Models

1. **User Management**
   - `User`: Enhanced user profiles with fitness data, goals, and preferences
   - `UserSession`: JWT token management and session tracking
   - Role-based access control (Free, Premium, Admin)

2. **Exercise & Training**
   - `ExerciseSession`: Comprehensive workout tracking with performance metrics
   - `MuscleActivationPattern`: Time-series muscle activation and sensor data
   - Support for multiple exercise types (plank, side plank, dead bug, etc.)

3. **Progress & Analytics**
   - `ProgressRecord`: Aggregated progress tracking over time
   - Performance metrics, improvement tracking, goal completion rates
   - Historical data for trend analysis

4. **AI Coaching**
   - `AICoachingSession`: AI-generated recommendations and feedback
   - User interaction tracking and effectiveness measurement
   - Coaching personalization based on user preferences

5. **Monetization**
   - `Subscription`: Flexible subscription management
   - `Payment`: Transaction tracking and billing history
   - Feature gating and usage limits

6. **Gamification**
   - `Achievement`: Achievement definitions and criteria
   - `UserAchievement`: User's earned achievements and milestones
   - Social features and progress sharing

### Database Features

- **Connection Pooling**: Production-ready connection management
- **Health Monitoring**: Real-time database health and performance metrics
- **Auto-scaling**: Adaptive connection pool sizing
- **Query Optimization**: Comprehensive indexing strategy
- **Migration System**: Alembic-based schema versioning with backup/restore
- **Data Integrity**: Foreign key constraints and validation
- **Performance Monitoring**: Slow query detection and logging

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Setup Database

```python
from database import setup_database

# Quick setup with defaults (SQLite)
success = setup_database()

# Setup with PostgreSQL
success = setup_database(
    database_url="postgresql://user:password@localhost/coresense",
    auto_migrate=True
)
```

### 3. Using the CLI

```bash
# Setup database and run migrations
python database/cli.py setup --database-url postgresql://user:pass@localhost/coresense

# Populate with sample data
python database/cli.py setup --sample-data --users 50 --sessions-per-user 30

# Check database health
python database/cli.py health

# Migration management
python database/cli.py migrate init
python database/cli.py migrate create --message "Add new feature"
python database/cli.py migrate up
python database/cli.py migrate status
```

## Configuration

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost/coresense

# Connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Performance monitoring
DB_SLOW_QUERY_THRESHOLD=1.0
DB_QUERY_STATS=true

# Health checks
DB_HEALTH_CHECK=true
DB_HEALTH_CHECK_INTERVAL=300

# Migration settings
DB_AUTO_MIGRATE=false
DB_BACKUP_BEFORE_MIGRATE=true
```

## Usage Examples

### Basic Operations

```python
from database import db_service, User, ExerciseSession

# Create a user
with db_service.session_scope() as session:
    user = User(
        email="john@example.com",
        username="john_doe",
        hashed_password="...",
        fitness_level=FitnessLevel.INTERMEDIATE,
        training_goals={
            "primary": "strength",
            "target_sessions_per_week": 4
        }
    )
    session.add(user)
    session.flush()
    user_id = user.id

# Create an exercise session
session_data = {
    "user_id": user_id,
    "exercise_type": ExerciseType.PLANK,
    "duration_seconds": 300,
    "stability_score": 85.5,
    "form_quality_score": 92.0,
    "muscle_activation_data": {...}
}

with db_service.session_scope() as session:
    exercise_session = ExerciseSession(**session_data)
    session.add(exercise_session)
```

### Advanced Queries

```python
# Get user's exercise history with performance trends
from sqlalchemy import func
from datetime import datetime, timedelta

with db_service.session_scope() as session:
    recent_sessions = session.query(ExerciseSession).filter(
        ExerciseSession.user_id == user_id,
        ExerciseSession.started_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(ExerciseSession.started_at.desc()).all()

    # Calculate average performance
    avg_performance = session.query(
        func.avg(ExerciseSession.stability_score).label('avg_stability'),
        func.avg(ExerciseSession.form_quality_score).label('avg_form'),
        func.count(ExerciseSession.id).label('session_count')
    ).filter(
        ExerciseSession.user_id == user_id,
        ExerciseSession.status == SessionStatus.COMPLETED
    ).first()
```

### Health Monitoring

```python
from database import get_db_health

# Get database health metrics
health_data = get_db_health()
print(f"Connection Status: {health_data['connection_healthy']}")
print(f"Active Connections: {health_data['checked_out']}")
print(f"Query Count: {health_data['query_count']}")
print(f"Slow Queries: {health_data['slow_query_count']}")
```

## Performance Optimization

### Indexing Strategy

The database includes comprehensive indexes for optimal query performance:

- **User lookups**: Email, username, role-based queries
- **Session tracking**: User-date ranges, exercise types, completion status
- **Progress analysis**: Time-based progress queries
- **AI coaching**: Coaching history and effectiveness tracking
- **Billing**: Subscription status and payment tracking

### Connection Pooling

Optimized for high-concurrency workloads:
- **QueuePool** for PostgreSQL/MySQL with adaptive sizing
- **StaticPool** for SQLite development environments
- **Pre-ping** connection validation
- **Graceful degradation** under load

### Query Optimization

- **Lazy loading** relationships to minimize data transfer
- **Bulk operations** for batch processing
- **Raw SQL support** for complex analytics
- **Query monitoring** and slow query detection

## Migration Management

### Creating Migrations

```bash
# Auto-generate migration from model changes
python database/cli.py migrate create --message "Add user preferences"

# Manual migration
python database/cli.py migrate create --message "Custom data migration"
```

### Running Migrations

```bash
# Run all pending migrations
python database/cli.py migrate up

# Check migration status
python database/cli.py migrate status

# Rollback to previous version
python database/cli.py migrate down --revision -1
```

### Backup and Restore

The system automatically creates backups before migrations (SQLite). For production PostgreSQL deployments, integrate with your backup strategy.

## Development Tools

### Sample Data Generation

```python
from database.sample_data import populate_sample_data, clear_all_data

# Generate test data
populate_sample_data(users=100, sessions_per_user=50)

# Clear all data (development only)
clear_all_data()
```

### CLI Management

The included CLI provides comprehensive database management:
- Database setup and initialization
- Migration management
- Health monitoring
- Sample data generation
- Schema introspection

## Production Deployment

### Recommended Settings

```bash
# Production PostgreSQL configuration
DATABASE_URL=postgresql://coresense:password@db-cluster/coresense
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=60
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_SLOW_QUERY_THRESHOLD=0.5
DB_HEALTH_CHECK=true
```

### Monitoring

- Database health endpoints for load balancer checks
- Query performance monitoring
- Connection pool metrics
- Migration status tracking

## Security Considerations

- **Password hashing** with bcrypt
- **SQL injection protection** via parameterized queries
- **Session management** with secure token handling
- **Role-based access control** for feature gating
- **Audit logging** for sensitive operations

## Contributing

When adding new models or modifying existing ones:

1. Update the model in `models.py`
2. Create a migration: `python database/cli.py migrate create --message "Description"`
3. Run migration: `python database/cli.py migrate up`
4. Update sample data if needed
5. Add appropriate indexes for new query patterns
6. Update documentation

## File Structure

```
database/
├── __init__.py          # Package initialization and exports
├── models.py            # SQLAlchemy models and schema definitions
├── database.py          # Connection management and configuration
├── migrations.py        # Alembic migration management
├── sample_data.py       # Test data generation utilities
├── cli.py              # Command-line management interface
├── README.md           # This documentation
├── migrations/         # Alembic migration files
└── backups/           # Database backups (SQLite)
```

## License

This database system is part of the CoreSense AI platform. See the main project license for usage terms.