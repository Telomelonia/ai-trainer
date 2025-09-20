"""
Rentable Fitness Coaching Agents for CoreSense
Marketplace system for renting specialized fitness coaching agents
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum

from .solana_payments import SolanaPaymentService, PaymentTransaction

class RentalDuration(Enum):
    """Available rental durations"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SESSION = "session"

class AgentSpecialty(Enum):
    """Agent specialization areas"""
    CORE_TRAINING = "core_training"
    STRENGTH_TRAINING = "strength_training"
    CARDIO_CONDITIONING = "cardio_conditioning"
    FLEXIBILITY_MOBILITY = "flexibility_mobility"
    INJURY_REHABILITATION = "injury_rehabilitation"
    NUTRITION_COACHING = "nutrition_coaching"
    MENTAL_WELLNESS = "mental_wellness"
    PERFORMANCE_ANALYSIS = "performance_analysis"

@dataclass
class RentableAgent:
    """Represents a rentable fitness coaching agent"""
    agent_id: str
    name: str
    description: str
    specialty: AgentSpecialty
    capabilities: List[str]
    pricing: Dict[RentalDuration, float]  # Prices in SOL
    rating: float
    total_sessions: int
    creator_id: str
    coral_uri: str
    metadata: Dict[str, Any]
    availability: Dict[str, Any]
    created_at: str
    updated_at: str

@dataclass
class AgentRental:
    """Represents an active agent rental"""
    rental_id: str
    agent_id: str
    renter_id: str
    duration: RentalDuration
    price_sol: float
    started_at: datetime
    expires_at: datetime
    status: str  # active, expired, cancelled
    session_count: int
    payment_transaction_id: str
    usage_stats: Dict[str, Any]

@dataclass
class RentalSession:
    """Represents a coaching session with a rented agent"""
    session_id: str
    rental_id: str
    agent_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    session_data: Dict[str, Any]
    feedback: Optional[Dict[str, Any]]
    cost: float

class RentableAgentMarketplace:
    """Marketplace for renting specialized fitness coaching agents"""
    
    def __init__(self, payment_service: SolanaPaymentService):
        self.payment_service = payment_service
        self.logger = logging.getLogger(__name__)
        
        # Storage
        self.available_agents = {}
        self.active_rentals = {}
        self.rental_history = {}
        self.session_history = {}
        
        # Initialize marketplace with featured agents
        self._initialize_featured_agents()
    
    def _initialize_featured_agents(self):
        """Initialize the marketplace with featured coaching agents"""
        
        # Elite Core Trainer Agent
        elite_core_trainer = RentableAgent(
            agent_id="elite-core-trainer-v2",
            name="Elite Core Trainer Pro",
            description="Advanced core training specialist with Olympic-level expertise",
            specialty=AgentSpecialty.CORE_TRAINING,
            capabilities=[
                "advanced_muscle_activation_analysis",
                "elite_performance_coaching",
                "injury_prevention_protocols",
                "competition_preparation",
                "biomechanical_optimization"
            ],
            pricing={
                RentalDuration.SESSION: 0.15,
                RentalDuration.HOURLY: 0.50,
                RentalDuration.DAILY: 3.00,
                RentalDuration.WEEKLY: 18.00,
                RentalDuration.MONTHLY: 65.00
            },
            rating=4.9,
            total_sessions=2847,
            creator_id="olympictrainer_pro",
            coral_uri="coral://elite-core-trainer-v2",
            metadata={
                "experience_years": 15,
                "certifications": ["NASM-CPT", "CSCS", "Olympic Training"],
                "languages": ["English", "Spanish", "French"],
                "specializations": ["Olympic Prep", "Injury Recovery", "Elite Performance"]
            },
            availability={
                "timezone": "UTC",
                "hours": "24/7",
                "response_time": "< 30 seconds"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Rehabilitation Specialist
        rehab_specialist = RentableAgent(
            agent_id="rehabilitation-specialist-ai",
            name="Physical Therapy AI Specialist",
            description="Expert in injury rehabilitation and therapeutic exercise",
            specialty=AgentSpecialty.INJURY_REHABILITATION,
            capabilities=[
                "injury_assessment",
                "rehabilitation_planning",
                "pain_management_strategies",
                "recovery_tracking",
                "therapeutic_exercise_design"
            ],
            pricing={
                RentalDuration.SESSION: 0.25,
                RentalDuration.HOURLY: 0.75,
                RentalDuration.DAILY: 4.50,
                RentalDuration.WEEKLY: 25.00,
                RentalDuration.MONTHLY: 85.00
            },
            rating=4.8,
            total_sessions=1923,
            creator_id="medfit_innovations",
            coral_uri="coral://rehabilitation-specialist-ai",
            metadata={
                "medical_background": "Licensed Physical Therapist",
                "specializations": ["Sports Injuries", "Chronic Pain", "Post-Surgery Recovery"],
                "evidence_based": True,
                "peer_reviewed": True
            },
            availability={
                "timezone": "UTC",
                "hours": "24/7",
                "emergency_support": True
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Nutrition Performance Coach
        nutrition_coach = RentableAgent(
            agent_id="nutrition-performance-coach",
            name="Performance Nutrition AI Coach",
            description="Advanced nutrition coaching for optimal athletic performance",
            specialty=AgentSpecialty.NUTRITION_COACHING,
            capabilities=[
                "performance_nutrition_planning",
                "macro_optimization",
                "supplement_guidance",
                "hydration_strategies",
                "recovery_nutrition"
            ],
            pricing={
                RentalDuration.SESSION: 0.12,
                RentalDuration.HOURLY: 0.40,
                RentalDuration.DAILY: 2.50,
                RentalDuration.WEEKLY: 15.00,
                RentalDuration.MONTHLY: 55.00
            },
            rating=4.7,
            total_sessions=3156,
            creator_id="sportsnutrition_lab",
            coral_uri="coral://nutrition-performance-coach",
            metadata={
                "credentials": ["RD", "CSSD", "Sports Nutrition Specialist"],
                "specializations": ["Endurance Sports", "Strength Training", "Weight Management"],
                "research_backed": True
            },
            availability={
                "timezone": "UTC",
                "hours": "24/7",
                "meal_planning": True
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Mental Performance Coach
        mental_coach = RentableAgent(
            agent_id="mental-performance-coach",
            name="Mental Performance & Mindfulness Coach",
            description="Expert in sports psychology and mental wellness for athletes",
            specialty=AgentSpecialty.MENTAL_WELLNESS,
            capabilities=[
                "mental_performance_coaching",
                "stress_management",
                "confidence_building",
                "focus_training",
                "mindfulness_practices"
            ],
            pricing={
                RentalDuration.SESSION: 0.20,
                RentalDuration.HOURLY: 0.60,
                RentalDuration.DAILY: 3.50,
                RentalDuration.WEEKLY: 20.00,
                RentalDuration.MONTHLY: 70.00
            },
            rating=4.9,
            total_sessions=1674,
            creator_id="mindfulathlete_ai",
            coral_uri="coral://mental-performance-coach",
            metadata={
                "credentials": ["Licensed Psychologist", "CMPC", "Mindfulness Instructor"],
                "specializations": ["Performance Anxiety", "Goal Setting", "Meditation"],
                "approach": "Evidence-based CBT and Mindfulness"
            },
            availability={
                "timezone": "UTC",
                "hours": "24/7",
                "crisis_support": True
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Store agents
        self.available_agents = {
            elite_core_trainer.agent_id: elite_core_trainer,
            rehab_specialist.agent_id: rehab_specialist,
            nutrition_coach.agent_id: nutrition_coach,
            mental_coach.agent_id: mental_coach
        }
    
    def get_marketplace_catalog(self, 
                               specialty: Optional[AgentSpecialty] = None,
                               price_range: Optional[tuple] = None,
                               rating_min: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get catalog of available agents for rent"""
        
        agents = list(self.available_agents.values())
        
        # Apply filters
        if specialty:
            agents = [a for a in agents if a.specialty == specialty]
        
        if rating_min:
            agents = [a for a in agents if a.rating >= rating_min]
        
        if price_range:
            min_price, max_price = price_range
            agents = [a for a in agents 
                     if any(min_price <= price <= max_price 
                           for price in a.pricing.values())]
        
        # Convert to catalog format
        catalog = []
        for agent in agents:
            catalog.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "specialty": agent.specialty.value,
                "rating": agent.rating,
                "total_sessions": agent.total_sessions,
                "pricing": {duration.value: price for duration, price in agent.pricing.items()},
                "capabilities": agent.capabilities,
                "creator": agent.creator_id,
                "metadata": agent.metadata,
                "coral_uri": agent.coral_uri
            })
        
        return sorted(catalog, key=lambda x: x["rating"], reverse=True)
    
    async def rent_agent(self, 
                        user_id: str,
                        agent_id: str,
                        duration: RentalDuration,
                        user_wallet: str) -> Dict[str, Any]:
        """Rent an agent for specified duration"""
        
        try:
            if agent_id not in self.available_agents:
                return {"success": False, "error": "Agent not found"}
            
            agent = self.available_agents[agent_id]
            
            if duration not in agent.pricing:
                return {"success": False, "error": "Duration not available for this agent"}
            
            price_sol = agent.pricing[duration]
            rental_id = str(uuid.uuid4())
            
            # Calculate expiration time
            now = datetime.now()
            if duration == RentalDuration.HOURLY:
                expires_at = now + timedelta(hours=1)
            elif duration == RentalDuration.DAILY:
                expires_at = now + timedelta(days=1)
            elif duration == RentalDuration.WEEKLY:
                expires_at = now + timedelta(weeks=1)
            elif duration == RentalDuration.MONTHLY:
                expires_at = now + timedelta(days=30)
            elif duration == RentalDuration.SESSION:
                expires_at = now + timedelta(hours=2)  # Session expires in 2 hours
            else:
                expires_at = now + timedelta(hours=1)
            
            # Process payment
            payment_result = await self.payment_service.create_payment_request(
                user_id=user_id,
                plan_id=f"agent_rental_{duration.value}",
                user_wallet=user_wallet
            )
            
            if not payment_result.get("success"):
                return {"success": False, "error": "Payment processing failed"}
            
            # Create rental record
            rental = AgentRental(
                rental_id=rental_id,
                agent_id=agent_id,
                renter_id=user_id,
                duration=duration,
                price_sol=price_sol,
                started_at=now,
                expires_at=expires_at,
                status="pending_payment",
                session_count=0,
                payment_transaction_id=payment_result["transaction_id"],
                usage_stats={}
            )
            
            self.active_rentals[rental_id] = rental
            
            return {
                "success": True,
                "rental_id": rental_id,
                "agent_name": agent.name,
                "duration": duration.value,
                "price_sol": price_sol,
                "expires_at": expires_at.isoformat(),
                "payment_details": payment_result["payment_details"],
                "coral_uri": agent.coral_uri
            }
            
        except Exception as e:
            self.logger.error(f"Failed to rent agent: {e}")
            return {"success": False, "error": str(e)}
    
    async def confirm_rental_payment(self, 
                                   rental_id: str,
                                   transaction_hash: str) -> Dict[str, Any]:
        """Confirm payment and activate agent rental"""
        
        try:
            if rental_id not in self.active_rentals:
                return {"success": False, "error": "Rental not found"}
            
            rental = self.active_rentals[rental_id]
            
            # Verify payment
            payment_result = await self.payment_service.verify_payment(
                rental.payment_transaction_id,
                transaction_hash
            )
            
            if payment_result.get("success"):
                # Activate rental
                rental.status = "active"
                
                # Agent is now available for use
                return {
                    "success": True,
                    "rental_activated": True,
                    "agent_id": rental.agent_id,
                    "expires_at": rental.expires_at.isoformat(),
                    "coral_uri": self.available_agents[rental.agent_id].coral_uri
                }
            else:
                return {"success": False, "error": "Payment verification failed"}
                
        except Exception as e:
            self.logger.error(f"Failed to confirm rental payment: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_coaching_session(self, 
                                   rental_id: str,
                                   session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a coaching session with a rented agent"""
        
        try:
            if rental_id not in self.active_rentals:
                return {"success": False, "error": "Rental not found"}
            
            rental = self.active_rentals[rental_id]
            
            if rental.status != "active":
                return {"success": False, "error": "Rental not active"}
            
            if datetime.now() > rental.expires_at:
                rental.status = "expired"
                return {"success": False, "error": "Rental has expired"}
            
            session_id = str(uuid.uuid4())
            
            session = RentalSession(
                session_id=session_id,
                rental_id=rental_id,
                agent_id=rental.agent_id,
                user_id=rental.renter_id,
                started_at=datetime.now(),
                ended_at=None,
                session_data=session_data,
                feedback=None,
                cost=0.0  # Included in rental cost
            )
            
            self.session_history[session_id] = session
            rental.session_count += 1
            
            agent = self.available_agents[rental.agent_id]
            
            return {
                "success": True,
                "session_id": session_id,
                "agent_name": agent.name,
                "capabilities": agent.capabilities,
                "coral_uri": agent.coral_uri,
                "session_started_at": session.started_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start coaching session: {e}")
            return {"success": False, "error": str(e)}
    
    async def end_coaching_session(self, 
                                 session_id: str,
                                 feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """End a coaching session and collect feedback"""
        
        try:
            if session_id not in self.session_history:
                return {"success": False, "error": "Session not found"}
            
            session = self.session_history[session_id]
            session.ended_at = datetime.now()
            session.feedback = feedback
            
            # Calculate session duration
            duration = (session.ended_at - session.started_at).total_seconds() / 60  # minutes
            
            # Update usage stats
            rental = self.active_rentals[session.rental_id]
            if "total_session_time" not in rental.usage_stats:
                rental.usage_stats["total_session_time"] = 0
            rental.usage_stats["total_session_time"] += duration
            
            # Update agent rating if feedback provided
            if feedback and "rating" in feedback:
                await self._update_agent_rating(session.agent_id, feedback["rating"])
            
            return {
                "success": True,
                "session_duration_minutes": round(duration, 1),
                "total_sessions": rental.session_count,
                "rental_expires_at": rental.expires_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to end coaching session: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_agent_rating(self, agent_id: str, new_rating: float):
        """Update agent rating with new feedback"""
        if agent_id in self.available_agents:
            agent = self.available_agents[agent_id]
            
            # Simple rating update (in production, would be more sophisticated)
            current_rating = agent.rating
            total_sessions = agent.total_sessions
            
            # Weighted average
            updated_rating = ((current_rating * total_sessions) + new_rating) / (total_sessions + 1)
            agent.rating = round(updated_rating, 2)
            agent.total_sessions += 1
            agent.updated_at = datetime.now().isoformat()
    
    def get_user_rentals(self, user_id: str) -> Dict[str, Any]:
        """Get all rentals for a user"""
        user_rentals = []
        
        for rental in self.active_rentals.values():
            if rental.renter_id == user_id:
                agent = self.available_agents.get(rental.agent_id)
                user_rentals.append({
                    "rental_id": rental.rental_id,
                    "agent_name": agent.name if agent else "Unknown",
                    "agent_id": rental.agent_id,
                    "duration": rental.duration.value,
                    "status": rental.status,
                    "started_at": rental.started_at.isoformat(),
                    "expires_at": rental.expires_at.isoformat(),
                    "session_count": rental.session_count,
                    "price_sol": rental.price_sol
                })
        
        return {
            "success": True,
            "active_rentals": len([r for r in user_rentals if r["status"] == "active"]),
            "total_rentals": len(user_rentals),
            "rentals": sorted(user_rentals, key=lambda x: x["started_at"], reverse=True)
        }
    
    def get_agent_analytics(self, agent_id: str) -> Dict[str, Any]:
        """Get analytics for an agent"""
        if agent_id not in self.available_agents:
            return {"success": False, "error": "Agent not found"}
        
        agent = self.available_agents[agent_id]
        
        # Calculate earnings and usage stats
        total_rentals = sum(1 for r in self.active_rentals.values() if r.agent_id == agent_id)
        total_revenue = sum(r.price_sol for r in self.active_rentals.values() 
                           if r.agent_id == agent_id and r.status in ["active", "expired"])
        
        total_sessions = sum(r.session_count for r in self.active_rentals.values() 
                           if r.agent_id == agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "rating": agent.rating,
            "total_rentals": total_rentals,
            "total_revenue_sol": total_revenue,
            "total_sessions": total_sessions,
            "average_session_rating": agent.rating,  # Simplified
            "creator_earnings": total_revenue * 0.7,  # 70% to creator
            "platform_fee": total_revenue * 0.3       # 30% platform fee
        }

# Global marketplace instance
rentable_agent_marketplace = RentableAgentMarketplace(None)  # Will be initialized with payment service