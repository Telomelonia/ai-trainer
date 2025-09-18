#!/usr/bin/env python3
"""
Agent Orchestrator
Core Training AI Ecosystem - Phase 3

Orchestrates multiple agents and prepares for Coral Protocol integration.
Manages agent-to-agent communication and coordination.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-orchestrator")

@dataclass
class AgentMessage:
    """Represents a message between agents"""
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    correlation_id: str

@dataclass
class AgentCapability:
    """Represents an agent capability"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class AgentOrchestrator:
    """
    Orchestrates multiple agents in the Core Training ecosystem.
    Prepares for Coral Protocol integration.
    """
    
    def __init__(self):
        """Initialize the Agent Orchestrator"""
        self.agents = {}
        self.message_queue = []
        self.active_sessions = {}
        self.coral_ready = False
        
        logger.info("AgentOrchestrator initialized")
    
    def register_agent(self, agent_id: str, agent_instance: Any, capabilities: List[AgentCapability]):
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = {
            "instance": agent_instance,
            "capabilities": capabilities,
            "status": "active",
            "last_heartbeat": datetime.now().isoformat()
        }
        
        logger.info(f"Registered agent {agent_id} with {len(capabilities)} capabilities")
    
    async def create_coaching_session(self, user_id: str, session_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Create a comprehensive coaching session using multiple agents
        
        Args:
            user_id: User identifier
            session_type: Type of session (comprehensive, quick_check, workout_plan)
        
        Returns:
            Dict containing session results from multiple agents
        """
        try:
            session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "session_type": session_type,
                "started_at": datetime.now().isoformat(),
                "agents_involved": [],
                "results": {}
            }
            
            # Get the core training agent
            core_agent = self.agents.get("core-training-agent", {}).get("instance")
            if not core_agent:
                return {"error": "Core training agent not available"}
            
            session_results = {
                "session_id": session_id,
                "user_id": user_id,
                "session_type": session_type,
                "results": {},
                "agent_coordination": {
                    "agents_used": ["core-training-agent"],
                    "coordination_patterns": [],
                    "communication_log": []
                }
            }
            
            if session_type == "comprehensive":
                # Run comprehensive analysis with multiple agent calls
                
                # 1. Stability Analysis
                stability_result = await core_agent.analyze_stability(user_id)
                session_results["results"]["stability_analysis"] = stability_result
                self._log_agent_interaction(session_id, "core-training-agent", "stability_analysis", stability_result)
                
                # 2. Progress Analysis
                progress_result = await core_agent.analyze_progress(user_id)
                session_results["results"]["progress_analysis"] = progress_result
                self._log_agent_interaction(session_id, "core-training-agent", "progress_analysis", progress_result)
                
                # 3. Workout Plan Creation
                workout_plan = await core_agent.create_workout_plan(user_id)
                session_results["results"]["workout_plan"] = workout_plan
                self._log_agent_interaction(session_id, "core-training-agent", "workout_plan", workout_plan)
                
                # 4. Coordination Summary
                session_results["coordination_summary"] = self._generate_coordination_summary(
                    stability_result, progress_result, workout_plan
                )
                
            elif session_type == "quick_check":
                # Quick stability and form check
                stability_result = await core_agent.analyze_stability(user_id)
                realtime_coaching = await core_agent.provide_realtime_coaching(user_id, "plank")
                
                session_results["results"]["stability_check"] = stability_result
                session_results["results"]["realtime_coaching"] = realtime_coaching
                
            elif session_type == "workout_plan":
                # Focus on workout planning
                workout_plan = await core_agent.create_workout_plan(user_id)
                session_results["results"]["workout_plan"] = workout_plan
            
            # Mark session as completed
            self.active_sessions[session_id]["completed_at"] = datetime.now().isoformat()
            self.active_sessions[session_id]["results"] = session_results
            
            logger.info(f"Completed coaching session {session_id} for user {user_id}")
            return session_results
            
        except Exception as e:
            logger.error(f"Error in coaching session: {str(e)}")
            return {
                "error": f"Session failed: {str(e)}",
                "session_id": session_id,
                "user_id": user_id
            }
    
    async def send_agent_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Send a message between agents (preparing for Coral Protocol)"""
        try:
            # For now, implement basic agent-to-agent communication
            # In Coral Protocol, this would use the protocol's messaging system
            
            from_agent = self.agents.get(message.from_agent)
            to_agent = self.agents.get(message.to_agent)
            
            if not from_agent or not to_agent:
                return {"error": "Agent not found"}
            
            # Log the message
            self.message_queue.append({
                "message": message,
                "processed_at": datetime.now().isoformat(),
                "status": "delivered"
            })
            
            # Simulate processing (in Coral Protocol, this would be handled by the protocol)
            response = {
                "message_id": message.correlation_id,
                "from_agent": message.to_agent,
                "to_agent": message.from_agent,
                "response_type": f"response_to_{message.message_type}",
                "content": {
                    "status": "received",
                    "processed": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Agent message sent: {message.from_agent} -> {message.to_agent}")
            return response
            
        except Exception as e:
            logger.error(f"Error sending agent message: {str(e)}")
            return {"error": f"Message delivery failed: {str(e)}"}
    
    def prepare_coral_integration(self) -> Dict[str, Any]:
        """Prepare agent capabilities for Coral Protocol registration"""
        
        coral_manifest = {
            "ecosystem_id": "core-training-ai",
            "version": "1.0.0",
            "agents": [],
            "capabilities": [],
            "payment_model": {
                "pricing_type": "per_session",
                "base_price": 0.10,  # $0.10 per coaching session
                "currency": "USD",
                "payment_methods": ["crypto", "credit_card"]
            },
            "coral_integration": {
                "marketplace_ready": True,
                "agent_discovery": True,
                "cross_agent_communication": True,
                "reputation_tracking": True
            }
        }
        
        # Add registered agents to the manifest
        for agent_id, agent_data in self.agents.items():
            agent_manifest = {
                "agent_id": agent_id,
                "name": agent_id.replace("-", " ").title(),
                "description": f"AI agent for {agent_id} in core training ecosystem",
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "input_schema": cap.input_schema,
                        "output_schema": cap.output_schema
                    }
                    for cap in agent_data["capabilities"]
                ],
                "status": agent_data["status"],
                "pricing": {
                    "per_request": 0.05,
                    "per_session": 0.10,
                    "bulk_discount": 0.08
                }
            }
            coral_manifest["agents"].append(agent_manifest)
        
        # Global ecosystem capabilities
        coral_manifest["capabilities"] = [
            "real_time_stability_monitoring",
            "personalized_coaching",
            "progress_analytics", 
            "workout_planning",
            "form_feedback",
            "multi_agent_coordination"
        ]
        
        self.coral_ready = True
        logger.info("Coral Protocol integration prepared")
        
        return coral_manifest
    
    def _log_agent_interaction(self, session_id: str, agent_id: str, action: str, result: Dict[str, Any]):
        """Log agent interaction for session tracking"""
        if session_id in self.active_sessions:
            if "interactions" not in self.active_sessions[session_id]:
                self.active_sessions[session_id]["interactions"] = []
            
            self.active_sessions[session_id]["interactions"].append({
                "agent_id": agent_id,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "success": "error" not in result,
                "result_summary": {
                    "keys": list(result.keys()),
                    "has_error": "error" in result
                }
            })
    
    def _generate_coordination_summary(self, stability_result: Dict, progress_result: Dict, workout_plan: Dict) -> Dict[str, Any]:
        """Generate a summary of how agents coordinated to provide comprehensive coaching"""
        
        # Extract key insights from each agent result
        stability_score = stability_result.get("stability_analysis", {}).get("current_score", 0)
        improvement_rate = progress_result.get("progress_metrics", {}).get("stability_improvement", "0%")
        workout_exercises = len(workout_plan.get("exercises", []))
        
        coordination_insights = {
            "data_integration": {
                "stability_data": "Used for real-time form assessment",
                "progress_data": "Informed workout progression decisions",
                "user_preferences": "Personalized exercise selection"
            },
            "agent_synergy": {
                "current_performance": f"Stability score: {stability_score}",
                "progress_trend": f"Improvement: {improvement_rate}",
                "personalized_plan": f"Generated {workout_exercises} exercises"
            },
            "coordination_value": [
                "Real-time data informed workout planning",
                "Progress history guided difficulty adjustments", 
                "User preferences ensured relevant recommendations",
                "Multi-source analysis provided comprehensive coaching"
            ],
            "coral_benefits": [
                "Agent specialization improves accuracy",
                "Coordinated analysis provides deeper insights",
                "Marketplace allows for specialized agent services",
                "Cross-agent learning improves recommendations"
            ]
        }
        
        return coordination_insights
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "registered_agents": len(self.agents),
            "active_sessions": len(self.active_sessions),
            "message_queue_size": len(self.message_queue),
            "coral_integration_ready": self.coral_ready,
            "agents": {
                agent_id: {
                    "status": data["status"],
                    "capabilities_count": len(data["capabilities"]),
                    "last_heartbeat": data["last_heartbeat"]
                }
                for agent_id, data in self.agents.items()
            },
            "last_updated": datetime.now().isoformat()
        }

# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()

async def main():
    """Test the agent orchestrator"""
    logger.info("Testing Agent Orchestrator...")
    
    # Test with mock agent
    try:
        from core_training_agent import core_training_agent
    except ImportError:
        # Create a mock agent for testing
        class MockAgent:
            async def initialize_mcp_connections(self):
                return True
            async def analyze_stability(self, user_id):
                return {"user_id": user_id, "score": 87.5, "status": "good"}
            async def analyze_progress(self, user_id):
                return {"user_id": user_id, "improvement": "12.7%", "status": "improving"}
            async def create_workout_plan(self, user_id):
                return {"user_id": user_id, "exercises": ["plank", "dead_bug"], "duration": 30}
        
        core_training_agent = MockAgent()
    
    # Register the core training agent
    capabilities = [
        AgentCapability(
            name="stability_analysis",
            description="Analyze core stability and provide coaching insights",
            input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"analysis": {"type": "object"}}}
        ),
        AgentCapability(
            name="workout_planning",
            description="Create personalized workout plans",
            input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"plan": {"type": "object"}}}
        )
    ]
    
    agent_orchestrator.register_agent("core-training-agent", core_training_agent, capabilities)
    
    # Initialize the agent
    await core_training_agent.initialize_mcp_connections()
    
    # Test comprehensive coaching session
    session_result = await agent_orchestrator.create_coaching_session("user_123", "comprehensive")
    print(f"Session result: {json.dumps(session_result, indent=2)}")
    
    # Test Coral Protocol preparation
    coral_manifest = agent_orchestrator.prepare_coral_integration()
    print(f"Coral manifest: {json.dumps(coral_manifest, indent=2)}")
    
    # Get orchestrator status
    status = agent_orchestrator.get_orchestrator_status()
    print(f"Orchestrator status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())