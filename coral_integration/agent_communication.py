"""
Agent-to-Agent Communication Protocol for CoreSense
Enables seamless communication between CoreSense agents and external Coral agents
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import logging
from enum import Enum

class MessageType(Enum):
    """Types of messages that can be sent between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentMessage:
    """Represents a message between agents"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    priority: MessagePriority
    payload: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    expires_at: Optional[str] = None

@dataclass
class AgentCapabilityRequest:
    """Request for an agent capability"""
    capability_name: str
    input_data: Dict[str, Any]
    expected_response_time: Optional[int] = None
    cost_limit: Optional[float] = None

@dataclass
class AgentResponse:
    """Response from an agent capability"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[int] = None
    cost: Optional[float] = None

class AgentCommunicationProtocol:
    """Protocol for agent-to-agent communication in CoreSense"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.message_handlers = {}
        self.active_sessions = {}
        self.message_queue = asyncio.Queue()
        self.registered_agents = {}
        
        # Communication patterns
        self.communication_patterns = {
            "sequential": self._handle_sequential_communication,
            "parallel": self._handle_parallel_communication,
            "pipeline": self._handle_pipeline_communication,
            "broadcast": self._handle_broadcast_communication
        }
    
    def register_agent(self, agent_id: str, capabilities: List[str], 
                      message_handler: Callable):
        """Register an agent with the communication protocol"""
        self.registered_agents[agent_id] = {
            "capabilities": capabilities,
            "handler": message_handler,
            "status": "active",
            "last_heartbeat": datetime.now().isoformat()
        }
        self.logger.info(f"Agent {agent_id} registered with capabilities: {capabilities}")
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to an agent"""
        try:
            if message.to_agent not in self.registered_agents:
                self.logger.error(f"Target agent {message.to_agent} not registered")
                return False
            
            # Add message to queue
            await self.message_queue.put(message)
            
            # Route message to target agent
            target_agent = self.registered_agents[message.to_agent]
            await target_agent["handler"](message)
            
            self.logger.info(f"Message {message.message_id} sent from {message.from_agent} to {message.to_agent}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def request_capability(self, 
                               from_agent: str,
                               target_agent: str, 
                               capability_request: AgentCapabilityRequest,
                               session_id: Optional[str] = None) -> AgentResponse:
        """Request a capability from another agent"""
        try:
            message_id = str(uuid.uuid4())
            correlation_id = str(uuid.uuid4())
            
            message = AgentMessage(
                message_id=message_id,
                from_agent=from_agent,
                to_agent=target_agent,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.NORMAL,
                payload={
                    "capability": capability_request.capability_name,
                    "input": capability_request.input_data,
                    "cost_limit": capability_request.cost_limit,
                    "expected_response_time": capability_request.expected_response_time
                },
                timestamp=datetime.now().isoformat(),
                correlation_id=correlation_id,
                session_id=session_id
            )
            
            # Send request and wait for response
            response = await self._send_request_and_wait(message)
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to request capability: {e}")
            return AgentResponse(success=False, error=str(e))
    
    async def _send_request_and_wait(self, request_message: AgentMessage, 
                                   timeout: int = 30) -> AgentResponse:
        """Send request and wait for response"""
        response_future = asyncio.Future()
        
        # Store future for correlation ID
        if request_message.correlation_id:
            self.active_sessions[request_message.correlation_id] = response_future
        
        # Send the request
        await self.send_message(request_message)
        
        try:
            # Wait for response with timeout
            response_message = await asyncio.wait_for(response_future, timeout=timeout)
            
            # Parse response
            if response_message.message_type == MessageType.RESPONSE:
                return AgentResponse(
                    success=response_message.payload.get("success", False),
                    result=response_message.payload.get("result"),
                    error=response_message.payload.get("error"),
                    execution_time=response_message.payload.get("execution_time"),
                    cost=response_message.payload.get("cost")
                )
            else:
                return AgentResponse(success=False, error="Invalid response type")
                
        except asyncio.TimeoutError:
            return AgentResponse(success=False, error="Request timeout")
        finally:
            # Clean up
            if request_message.correlation_id in self.active_sessions:
                del self.active_sessions[request_message.correlation_id]
    
    async def handle_response(self, response_message: AgentMessage):
        """Handle incoming response message"""
        if response_message.correlation_id in self.active_sessions:
            future = self.active_sessions[response_message.correlation_id]
            if not future.done():
                future.set_result(response_message)
    
    # Communication patterns
    
    async def _handle_sequential_communication(self, 
                                            agents: List[str],
                                            data: Dict[str, Any],
                                            session_id: str) -> Dict[str, Any]:
        """Handle sequential agent communication (pipeline)"""
        current_data = data.copy()
        results = []
        
        for i, agent_id in enumerate(agents):
            try:
                if agent_id in self.registered_agents:
                    # Determine capability based on agent type
                    capability = self._get_primary_capability(agent_id)
                    
                    request = AgentCapabilityRequest(
                        capability_name=capability,
                        input_data=current_data
                    )
                    
                    response = await self.request_capability(
                        from_agent="orchestrator",
                        target_agent=agent_id,
                        capability_request=request,
                        session_id=session_id
                    )
                    
                    if response.success:
                        results.append({
                            "agent": agent_id,
                            "step": i + 1,
                            "result": response.result,
                            "cost": response.cost
                        })
                        
                        # Use output as input for next agent
                        if response.result:
                            current_data.update(response.result)
                    else:
                        results.append({
                            "agent": agent_id,
                            "step": i + 1,
                            "error": response.error
                        })
                        break
                        
            except Exception as e:
                self.logger.error(f"Error in sequential communication with {agent_id}: {e}")
                break
        
        return {
            "pattern": "sequential",
            "results": results,
            "final_data": current_data,
            "total_cost": sum(r.get("cost", 0) for r in results if "cost" in r)
        }
    
    async def _handle_parallel_communication(self, 
                                           agents: List[str],
                                           data: Dict[str, Any],
                                           session_id: str) -> Dict[str, Any]:
        """Handle parallel agent communication"""
        tasks = []
        
        for agent_id in agents:
            if agent_id in self.registered_agents:
                capability = self._get_primary_capability(agent_id)
                
                request = AgentCapabilityRequest(
                    capability_name=capability,
                    input_data=data
                )
                
                task = self.request_capability(
                    from_agent="orchestrator",
                    target_agent=agent_id,
                    capability_request=request,
                    session_id=session_id
                )
                tasks.append((agent_id, task))
        
        # Execute all requests in parallel
        results = []
        responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for i, (agent_id, response) in enumerate(zip([agent for agent, _ in tasks], responses)):
            if isinstance(response, Exception):
                results.append({
                    "agent": agent_id,
                    "error": str(response)
                })
            elif isinstance(response, AgentResponse):
                results.append({
                    "agent": agent_id,
                    "success": response.success,
                    "result": response.result,
                    "error": response.error,
                    "cost": response.cost
                })
        
        return {
            "pattern": "parallel",
            "results": results,
            "total_cost": sum(r.get("cost", 0) for r in results if "cost" in r)
        }
    
    async def _handle_pipeline_communication(self, 
                                           pipeline_config: Dict[str, Any],
                                           data: Dict[str, Any],
                                           session_id: str) -> Dict[str, Any]:
        """Handle pipeline communication with branching and merging"""
        # Implementation would depend on pipeline configuration
        # For now, simplified version
        return await self._handle_sequential_communication(
            pipeline_config.get("agents", []),
            data,
            session_id
        )
    
    async def _handle_broadcast_communication(self, 
                                            agents: List[str],
                                            data: Dict[str, Any],
                                            session_id: str) -> Dict[str, Any]:
        """Handle broadcast communication (notification to all agents)"""
        results = []
        
        for agent_id in agents:
            if agent_id in self.registered_agents:
                try:
                    message = AgentMessage(
                        message_id=str(uuid.uuid4()),
                        from_agent="orchestrator",
                        to_agent=agent_id,
                        message_type=MessageType.NOTIFICATION,
                        priority=MessagePriority.NORMAL,
                        payload=data,
                        timestamp=datetime.now().isoformat(),
                        session_id=session_id
                    )
                    
                    success = await self.send_message(message)
                    results.append({
                        "agent": agent_id,
                        "notified": success
                    })
                    
                except Exception as e:
                    results.append({
                        "agent": agent_id,
                        "error": str(e)
                    })
        
        return {
            "pattern": "broadcast",
            "results": results,
            "agents_notified": len([r for r in results if r.get("notified")])
        }
    
    def _get_primary_capability(self, agent_id: str) -> str:
        """Get the primary capability for an agent"""
        capability_mapping = {
            "coresense-fabric-sensor": "muscle_activation_analysis",
            "coresense-ai-coach": "personalized_coaching",
            "coresense-orchestrator": "multi_agent_coordination",
            "external-nutrition-coach": "nutrition_analysis",
            "physiotherapy-assistant": "injury_assessment"
        }
        return capability_mapping.get(agent_id, "unknown_capability")
    
    async def create_coaching_session(self, 
                                    user_data: Dict[str, Any],
                                    session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive coaching session using multiple agents"""
        session_id = f"coaching_session_{datetime.now().timestamp()}"
        
        try:
            # Step 1: Analyze current muscle activation (Fabric Sensor Agent)
            muscle_analysis = await self.request_capability(
                from_agent="orchestrator",
                target_agent="coresense-fabric-sensor",
                capability_request=AgentCapabilityRequest(
                    capability_name="muscle_activation_analysis",
                    input_data={
                        "exercise": user_data.get("current_exercise", "plank"),
                        "stability_score": user_data.get("stability_score", 0.75)
                    }
                ),
                session_id=session_id
            )
            
            # Step 2: Get AI coaching based on muscle data (AI Coach Agent)
            if muscle_analysis.success:
                coaching_response = await self.request_capability(
                    from_agent="orchestrator",
                    target_agent="coresense-ai-coach", 
                    capability_request=AgentCapabilityRequest(
                        capability_name="personalized_coaching",
                        input_data={
                            "user_profile": user_data.get("profile", {}),
                            "current_exercise": user_data.get("current_exercise", "plank"),
                            "muscle_data": muscle_analysis.result,
                            "goals": user_data.get("goals", ["core_strength"])
                        }
                    ),
                    session_id=session_id
                )
            else:
                coaching_response = AgentResponse(success=False, error="Muscle analysis failed")
            
            # Step 3: External agent consultation (if enabled)
            external_insights = {}
            if session_config.get("include_external_agents", False):
                # Nutrition consultation
                nutrition_response = await self.request_capability(
                    from_agent="orchestrator",
                    target_agent="external-nutrition-coach",
                    capability_request=AgentCapabilityRequest(
                        capability_name="nutrition_analysis",
                        input_data={
                            "fitness_goals": user_data.get("goals", []),
                            "current_activity": user_data.get("current_exercise", "plank"),
                            "user_profile": user_data.get("profile", {})
                        }
                    ),
                    session_id=session_id
                )
                
                if nutrition_response.success:
                    external_insights["nutrition"] = nutrition_response.result
            
            # Compile session results
            session_result = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "muscle_analysis": muscle_analysis.result if muscle_analysis.success else None,
                "coaching_feedback": coaching_response.result if coaching_response.success else None,
                "external_insights": external_insights,
                "total_cost": (
                    (muscle_analysis.cost or 0) + 
                    (coaching_response.cost or 0) +
                    sum(getattr(r, 'cost', 0) for r in [nutrition_response] if hasattr(r, 'cost') and r.cost)
                ),
                "success": muscle_analysis.success and coaching_response.success
            }
            
            return session_result
            
        except Exception as e:
            self.logger.error(f"Failed to create coaching session: {e}")
            return {
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }

# Global communication protocol instance
agent_communication = AgentCommunicationProtocol()