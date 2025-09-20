"""
CoreSense Database Sample Data
Sample data generation for testing and development
"""

import random
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from .models import (
    User, ExerciseSession, ProgressRecord, AICoachingSession,
    Subscription, Payment, MuscleActivationPattern, Achievement, UserAchievement,
    UserRole, FitnessLevel, ExerciseType, SessionStatus,
    SubscriptionStatus, PaymentStatus, AchievementType
)
from .database import db_service

class SampleDataGenerator:
    """Generate sample data for CoreSense database"""
    
    def __init__(self):
        self.exercise_types = list(ExerciseType)
        self.fitness_levels = list(FitnessLevel)
        
    def generate_sample_users(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate sample user data"""
        users = []
        
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emily", "Chris", "Lisa", "Alex", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            user_data = {
                "email": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                "username": f"{first_name.lower()}{last_name.lower()}{i}",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFGw1CmPVJQg9Pu",  # "password123"
                "is_verified": True,
                "role": random.choice([UserRole.FREE, UserRole.PREMIUM]),
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": datetime.now(timezone.utc) - timedelta(days=random.randint(18*365, 65*365)),
                "gender": random.choice(["male", "female", "other"]),
                "height_cm": random.randint(150, 200),
                "weight_kg": round(random.uniform(50, 120), 1),
                "fitness_level": random.choice(self.fitness_levels),
                "training_goals": {
                    "primary": random.choice(["strength", "endurance", "flexibility", "weight_loss", "general_fitness"]),
                    "secondary": ["core_stability", "posture_improvement"],
                    "target_sessions_per_week": random.randint(2, 6)
                },
                "preferred_session_duration": random.choice([15, 20, 30, 45, 60]),
                "weekly_training_frequency": random.randint(2, 6),
                "health_considerations": {
                    "injuries": random.choice([[], ["lower_back"], ["knee"], ["shoulder"]]),
                    "medical_conditions": random.choice([[], ["diabetes"], ["hypertension"]]),
                    "limitations": []
                },
                "notification_preferences": {
                    "workout_reminders": True,
                    "progress_updates": True,
                    "achievement_notifications": True,
                    "email_frequency": "weekly"
                },
                "coaching_preferences": {
                    "feedback_style": random.choice(["encouraging", "technical", "balanced"]),
                    "correction_frequency": random.choice(["immediate", "end_of_set", "end_of_session"]),
                    "difficulty_progression": "adaptive"
                }
            }
            users.append(user_data)
        
        return users
    
    def generate_sample_exercise_sessions(self, user_ids: List[int], sessions_per_user: int = 20) -> List[Dict[str, Any]]:
        """Generate sample exercise session data"""
        sessions = []
        
        for user_id in user_ids:
            for i in range(sessions_per_user):
                exercise_type = random.choice(self.exercise_types)
                started_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))
                duration = random.randint(300, 3600)  # 5 minutes to 1 hour
                completed_at = started_at + timedelta(seconds=duration)
                
                session_data = {
                    "user_id": user_id,
                    "exercise_type": exercise_type,
                    "session_name": f"{exercise_type.value.title()} Training Session",
                    "difficulty_level": random.randint(1, 10),
                    "planned_duration_seconds": duration + random.randint(-300, 300),
                    "actual_duration_seconds": duration,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "stability_score": round(random.uniform(60, 95), 2),
                    "form_quality_score": round(random.uniform(65, 98), 2),
                    "endurance_score": round(random.uniform(70, 95), 2),
                    "movement_variance": round(random.uniform(0.1, 2.5), 2),
                    "balance_symmetry": round(random.uniform(85, 98), 2),
                    "muscle_engagement_level": round(random.uniform(75, 95), 2),
                    "status": SessionStatus.COMPLETED,
                    "completion_percentage": 100.0,
                    "raw_sensor_data": self._generate_sensor_data(),
                    "processed_metrics": self._generate_processed_metrics(),
                    "personal_best": random.choice([True, False]) if random.random() < 0.1 else False,
                    "improvement_percentage": round(random.uniform(-5, 15), 2),
                    "calories_burned": random.randint(50, 300)
                }
                
                # Calculate overall score
                session_data["overall_score"] = round(
                    (session_data["stability_score"] + 
                     session_data["form_quality_score"] + 
                     session_data["endurance_score"]) / 3, 2
                )
                
                sessions.append(session_data)
        
        return sessions
    
    def _generate_sensor_data(self) -> Dict[str, Any]:
        """Generate sample sensor data"""
        return {
            "accelerometer": {
                "x": [round(random.uniform(-2, 2), 3) for _ in range(100)],
                "y": [round(random.uniform(-2, 2), 3) for _ in range(100)],
                "z": [round(random.uniform(8, 12), 3) for _ in range(100)]
            },
            "gyroscope": {
                "x": [round(random.uniform(-5, 5), 3) for _ in range(100)],
                "y": [round(random.uniform(-5, 5), 3) for _ in range(100)],
                "z": [round(random.uniform(-5, 5), 3) for _ in range(100)]
            },
            "sampling_rate": 50  # Hz
        }
    
    def _generate_processed_metrics(self) -> Dict[str, Any]:
        """Generate sample processed metrics"""
        return {
            "average_stability": round(random.uniform(70, 95), 2),
            "peak_stability": round(random.uniform(85, 100), 2),
            "stability_variance": round(random.uniform(0.5, 5.0), 2),
            "form_consistency": round(random.uniform(80, 98), 2),
            "fatigue_progression": {
                "start": round(random.uniform(0, 20), 2),
                "middle": round(random.uniform(20, 60), 2),
                "end": round(random.uniform(40, 90), 2)
            },
            "movement_efficiency": round(random.uniform(75, 95), 2)
        }
    
    def generate_sample_achievements(self) -> List[Dict[str, Any]]:
        """Generate sample achievement definitions"""
        achievements = [
            {
                "name": "First Steps",
                "description": "Complete your first exercise session",
                "type": AchievementType.MILESTONE,
                "criteria": {"sessions_completed": 1},
                "difficulty_level": 1,
                "points_value": 10,
                "category": "getting_started",
                "icon_url": "/achievements/first_steps.png",
                "badge_color": "green"
            },
            {
                "name": "Consistency Champion",
                "description": "Complete 7 sessions in 7 consecutive days",
                "type": AchievementType.CONSISTENCY,
                "criteria": {"consecutive_days": 7, "min_sessions_per_day": 1},
                "difficulty_level": 3,
                "points_value": 50,
                "category": "consistency",
                "icon_url": "/achievements/consistency_champion.png",
                "badge_color": "blue"
            },
            {
                "name": "Endurance Master",
                "description": "Complete a 60-minute session with 90%+ overall score",
                "type": AchievementType.DURATION,
                "criteria": {"session_duration": 3600, "overall_score": 90},
                "difficulty_level": 4,
                "points_value": 75,
                "category": "performance",
                "icon_url": "/achievements/endurance_master.png",
                "badge_color": "gold"
            },
            {
                "name": "Perfect Form",
                "description": "Achieve 95%+ form quality score",
                "type": AchievementType.IMPROVEMENT,
                "criteria": {"form_quality_score": 95},
                "difficulty_level": 3,
                "points_value": 40,
                "category": "technique",
                "icon_url": "/achievements/perfect_form.png",
                "badge_color": "purple"
            },
            {
                "name": "Centennial",
                "description": "Complete 100 exercise sessions",
                "type": AchievementType.MILESTONE,
                "criteria": {"sessions_completed": 100},
                "difficulty_level": 5,
                "points_value": 200,
                "category": "milestones",
                "icon_url": "/achievements/centennial.png",
                "badge_color": "platinum"
            }
        ]
        
        return achievements
    
    def populate_database(self, user_count: int = 10, sessions_per_user: int = 20) -> bool:
        """Populate database with sample data"""
        try:
            # Generate and insert users
            users_data = self.generate_sample_users(user_count)
            user_ids = []
            
            with db_service.session_scope() as session:
                for user_data in users_data:
                    user = User(**user_data)
                    session.add(user)
                    session.flush()
                    user_ids.append(user.id)
                
                print(f"Created {len(user_ids)} sample users")
                
                # Generate and insert exercise sessions
                sessions_data = self.generate_sample_exercise_sessions(user_ids, sessions_per_user)
                for session_data in sessions_data:
                    exercise_session = ExerciseSession(**session_data)
                    session.add(exercise_session)
                
                print(f"Created {len(sessions_data)} sample exercise sessions")
                
                # Generate and insert achievements
                achievements_data = self.generate_sample_achievements()
                for achievement_data in achievements_data:
                    achievement = Achievement(**achievement_data)
                    session.add(achievement)
                
                print(f"Created {len(achievements_data)} sample achievements")
                
                # Generate some sample subscriptions
                for i, user_id in enumerate(user_ids[:3]):  # First 3 users get premium
                    subscription_data = {
                        "user_id": user_id,
                        "subscription_tier": "premium",
                        "billing_cycle": "monthly",
                        "price_amount": 9.99,
                        "currency": "USD",
                        "status": SubscriptionStatus.ACTIVE,
                        "started_at": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
                        "next_billing_date": datetime.now(timezone.utc) + timedelta(days=30),
                        "features_enabled": ["advanced_analytics", "ai_coaching", "unlimited_sessions"],
                        "usage_limits": {"monthly_sessions": -1},  # Unlimited
                        "current_usage": {"monthly_sessions": random.randint(10, 50)}
                    }
                    subscription = Subscription(**subscription_data)
                    session.add(subscription)
                
                print("Created sample subscriptions")
                
            return True
            
        except Exception as e:
            print(f"Failed to populate database: {e}")
            return False

# Global sample data generator
sample_data_generator = SampleDataGenerator()

def populate_sample_data(user_count: int = 10, sessions_per_user: int = 20) -> bool:
    """Convenience function to populate database with sample data"""
    return sample_data_generator.populate_database(user_count, sessions_per_user)

def clear_all_data() -> bool:
    """Clear all data from database (use with caution!)"""
    try:
        with db_service.session_scope() as session:
            # Delete in reverse order of dependencies
            session.query(UserAchievement).delete()
            session.query(Achievement).delete()
            session.query(MuscleActivationPattern).delete()
            session.query(Payment).delete()
            session.query(Subscription).delete()
            session.query(AICoachingSession).delete()
            session.query(ProgressRecord).delete()
            session.query(ExerciseSession).delete()
            session.query(User).delete()
            
        print("All sample data cleared")
        return True
        
    except Exception as e:
        print(f"Failed to clear data: {e}")
        return False

# Export functions
__all__ = [
    'SampleDataGenerator',
    'sample_data_generator',
    'populate_sample_data',
    'clear_all_data'
]