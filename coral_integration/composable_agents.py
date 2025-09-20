"""
Composable and Interoperable Agent System for CoreSense
Enables mixing and matching of agents for custom workflows
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import logging
from enum import Enum

from .agent_communication import AgentCommunicationProtocol, AgentCapabilityRequest, AgentResponse
from .multi_agent_orchestrator import MultiAgentOrchestrator, WorkflowDefinition, WorkflowStep, WorkflowType

class CompositionType(Enum):
    """Types of agent compositions"""
    SEQUENTIAL_CHAIN = "sequential_chain"
    PARALLEL_ENSEMBLE = "parallel_ensemble"
    HIERARCHICAL_TREE = "hierarchical_tree"
    FEEDBACK_LOOP = "feedback_loop"
    CONDITIONAL_BRANCH = "conditional_branch"

class AgentRole(Enum):
    """Roles agents can play in compositions"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    VALIDATOR = "validator"
    AGGREGATOR = "aggregator"
    FALLBACK = "fallback"

@dataclass
class AgentInterface:
    """Standardized interface for agent interoperability"""
    agent_id: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str]
    compatibility_tags: List[str]
    version: str

@dataclass
class CompositionNode:
    """Node in an agent composition"""
    node_id: str
    agent_id: str
    role: AgentRole
    input_mapping: Dict[str, str]  # Maps composition inputs to agent inputs
    output_mapping: Dict[str, str]  # Maps agent outputs to composition outputs
    conditions: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retry_policy: Optional[Dict[str, Any]] = None

@dataclass
class AgentComposition:
    """Defines a composition of multiple agents"""
    composition_id: str
    name: str
    description: str
    composition_type: CompositionType
    nodes: List[CompositionNode]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    version: str

@dataclass
class CompositionExecution:
    """Tracks execution of an agent composition"""
    execution_id: str
    composition_id: str
    input_data: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    node_results: Dict[str, Any] = None
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ComposableAgentSystem:
    """System for creating and managing composable agent workflows"""
    
    def __init__(self, 
                 communication_protocol: AgentCommunicationProtocol,
                 orchestrator: MultiAgentOrchestrator):
        self.communication = communication_protocol
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        
        # Storage
        self.agent_interfaces = {}
        self.compositions = {}
        self.active_executions = {}
        self.execution_history = {}
        
        # Initialize with CoreSense agent interfaces
        self._initialize_agent_interfaces()
        
        # Create pre-built compositions
        self._create_predefined_compositions()
    
    def _initialize_agent_interfaces(self):
        """Initialize agent interfaces for CoreSense agents"""
        
        # Fabric Sensor Agent Interface
        fabric_sensor_interface = AgentInterface(
            agent_id="coresense-fabric-sensor",
            input_schema={
                "type": "object",
                "properties": {
                    "exercise": {"type": "string", "enum": ["plank", "bridge", "deadbug", "birddog"]},
                    "stability_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "duration": {"type": "number", "minimum": 0}
                },
                "required": ["exercise", "stability_score"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "muscle_zones": {"type": "object"},
                    "compensation_detected": {"type": "boolean"},
                    "recommendations": {"type": "array", "items": {"type": "string"}}
                }
            },
            capabilities=["muscle_activation_analysis", "compensation_detection"],
            compatibility_tags=["fitness", "analysis", "real-time", "muscle-data"],
            version="1.0.0"
        )
        
        # AI Coach Interface
        ai_coach_interface = AgentInterface(
            agent_id="coresense-ai-coach",
            input_schema={
                "type": "object",
                "properties": {
                    "user_profile": {"type": "object"},
                    "current_exercise": {"type": "string"},
                    "muscle_data": {"type": "object"},
                    "goals": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["current_exercise", "muscle_data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "coaching_message": {"type": "string"},
                    "form_corrections": {"type": "array", "items": {"type": "string"}},
                    "next_exercise": {"type": "string"},
                    "difficulty_adjustment": {"type": "string"}
                }
            },
            capabilities=["personalized_coaching", "progress_analysis"],
            compatibility_tags=["fitness", "coaching", "personalization", "guidance"],
            version="1.0.0"
        )
        
        # External Nutrition Coach Interface
        nutrition_interface = AgentInterface(
            agent_id="external-nutrition-coach",
            input_schema={
                "type": "object",
                "properties": {
                    "fitness_goals": {"type": "array"},
                    "current_activity": {"type": "string"},
                    "user_profile": {"type": "object"}
                },
                "required": ["fitness_goals"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "nutrition_plan": {"type": "object"},
                    "meal_suggestions": {"type": "array"},
                    "supplements": {"type": "array"}
                }
            },
            capabilities=["nutrition_analysis", "meal_planning"],
            compatibility_tags=["nutrition", "wellness", "planning", "health"],
            version="1.0.0"
        )
        
        # Physical Therapy Interface
        physio_interface = AgentInterface(
            agent_id="physiotherapy-assistant",
            input_schema={
                "type": "object",
                "properties": {
                    "symptoms": {"type": "array"},
                    "injury_history": {"type": "object"},
                    "current_pain_level": {"type": "number"}
                },
                "required": ["symptoms"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "assessment": {"type": "string"},
                    "exercises": {"type": "array"},
                    "frequency": {"type": "string"},
                    "follow_up": {"type": "string"}
                }
            },
            capabilities=["injury_assessment", "recovery_planning"],
            compatibility_tags=["medical", "rehabilitation", "therapy", "recovery"],
            version="1.0.0"
        )
        
        # Store interfaces
        self.agent_interfaces = {
            fabric_sensor_interface.agent_id: fabric_sensor_interface,
            ai_coach_interface.agent_id: ai_coach_interface,
            nutrition_interface.agent_id: nutrition_interface,
            physio_interface.agent_id: physio_interface
        }
    
    def _create_predefined_compositions(self):
        """Create pre-built agent compositions"""
        
        # Complete Wellness Composition
        wellness_composition = AgentComposition(
            composition_id="complete-wellness-analysis",
            name="Complete Wellness Analysis",
            description="Comprehensive analysis combining muscle, nutrition, and mental wellness",
            composition_type=CompositionType.HIERARCHICAL_TREE,
            nodes=[
                CompositionNode(
                    node_id="muscle_analysis",
                    agent_id="coresense-fabric-sensor",
                    role=AgentRole.PRIMARY,
                    input_mapping={
                        "exercise": "user_exercise",
                        "stability_score": "user_stability"
                    },
                    output_mapping={
                        "muscle_data": "muscle_zones",
                        "compensation": "compensation_detected"
                    }
                ),
                CompositionNode(
                    node_id="nutrition_planning",
                    agent_id="external-nutrition-coach",
                    role=AgentRole.SECONDARY,
                    input_mapping={
                        "fitness_goals": "user_goals",
                        "current_activity": "user_exercise"
                    },
                    output_mapping={
                        "nutrition_recommendations": "nutrition_plan"
                    }
                ),
                CompositionNode(
                    node_id="coaching_synthesis",
                    agent_id="coresense-ai-coach",
                    role=AgentRole.AGGREGATOR,
                    input_mapping={
                        "muscle_data": "muscle_analysis.muscle_data",
                        "nutrition_data": "nutrition_planning.nutrition_recommendations",
                        "current_exercise": "user_exercise"
                    },
                    output_mapping={
                        "final_recommendations": "coaching_message",
                        "next_steps": "form_corrections"
                    }
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "user_exercise": {"type": "string"},
                    "user_stability": {"type": "number"},
                    "user_goals": {"type": "array"},
                    "user_profile": {"type": "object"}
                },
                "required": ["user_exercise", "user_stability", "user_goals"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "muscle_analysis": {"type": "object"},
                    "nutrition_recommendations": {"type": "object"},
                    "final_recommendations": {"type": "string"},
                    "next_steps": {"type": "array"}
                }
            },
            metadata={
                "category": "wellness",
                "complexity": "high",
                "estimated_duration": 45,
                "target_users": ["fitness_enthusiasts", "beginners", "rehabilitation"]
            },
            created_at=datetime.now().isoformat(),
            version="1.0.0"
        )
        
        # Injury Recovery Composition
        recovery_composition = AgentComposition(
            composition_id="injury-recovery-protocol",
            name="Injury Recovery Protocol",
            description="Specialized composition for injury assessment and recovery planning",
            composition_type=CompositionType.SEQUENTIAL_CHAIN,
            nodes=[
                CompositionNode(
                    node_id="initial_assessment",
                    agent_id="physiotherapy-assistant",
                    role=AgentRole.PRIMARY,
                    input_mapping={
                        "symptoms": "user_symptoms",
                        "injury_history": "user_history"
                    },
                    output_mapping={
                        "assessment_result": "assessment"
                    }
                ),
                CompositionNode(
                    node_id="muscle_compensation_check",
                    agent_id="coresense-fabric-sensor",
                    role=AgentRole.VALIDATOR,
                    input_mapping={
                        "exercise": "assessment_exercise",
                        "stability_score": "baseline_stability"
                    },
                    output_mapping={
                        "compensation_patterns": "compensation_detected"
                    },
                    conditions={"require_success": ["initial_assessment"]}
                ),
                CompositionNode(
                    node_id="recovery_coaching",
                    agent_id="coresense-ai-coach",
                    role=AgentRole.AGGREGATOR,
                    input_mapping={
                        "assessment_data": "initial_assessment.assessment_result",
                        "muscle_data": "muscle_compensation_check.compensation_patterns",
                        "current_exercise": "recovery_exercise"
                    },
                    output_mapping={
                        "recovery_plan": "coaching_message",
                        "progressive_exercises": "form_corrections"
                    }
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "user_symptoms": {"type": "array"},
                    "user_history": {"type": "object"},
                    "baseline_stability": {"type": "number"},
                    "assessment_exercise": {"type": "string"},
                    "recovery_exercise": {"type": "string"}
                },
                "required": ["user_symptoms", "baseline_stability"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "assessment_result": {"type": "string"},
                    "compensation_patterns": {"type": "boolean"},
                    "recovery_plan": {"type": "string"},
                    "progressive_exercises": {"type": "array"}
                }
            },
            metadata={
                "category": "rehabilitation",
                "complexity": "medium",
                "estimated_duration": 30,
                "target_users": ["injured_athletes", "rehabilitation_patients"]
            },
            created_at=datetime.now().isoformat(),
            version="1.0.0"
        )
        
        # Real-time Performance Optimization
        performance_composition = AgentComposition(
            composition_id="realtime-performance-optimization",
            name="Real-time Performance Optimization",
            description="Live performance coaching with multiple feedback loops",
            composition_type=CompositionType.FEEDBACK_LOOP,
            nodes=[
                CompositionNode(
                    node_id="continuous_monitoring",
                    agent_id="coresense-fabric-sensor",
                    role=AgentRole.PRIMARY,
                    input_mapping={
                        "exercise": "current_exercise",
                        "stability_score": "live_stability"
                    },
                    output_mapping={
                        "muscle_feedback": "muscle_zones",
                        "compensation_alerts": "compensation_detected"
                    }
                ),
                CompositionNode(
                    node_id="instant_coaching",
                    agent_id="coresense-ai-coach",
                    role=AgentRole.PRIMARY,
                    input_mapping={
                        "muscle_data": "continuous_monitoring.muscle_feedback",
                        "current_exercise": "current_exercise",
                        "user_profile": "athlete_profile"
                    },
                    output_mapping={
                        "live_feedback": "coaching_message",
                        "form_adjustments": "form_corrections"
                    }
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "current_exercise": {"type": "string"},
                    "live_stability": {"type": "number"},
                    "athlete_profile": {"type": "object"},
                    "session_duration": {"type": "number"}
                },
                "required": ["current_exercise", "live_stability"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "muscle_feedback": {"type": "object"},
                    "compensation_alerts": {"type": "boolean"},
                    "live_feedback": {"type": "string"},
                    "form_adjustments": {"type": "array"}
                }
            },
            metadata={
                "category": "performance",
                "complexity": "high",
                "estimated_duration": 60,
                "real_time": True,
                "target_users": ["athletes", "advanced_users"]
            },
            created_at=datetime.now().isoformat(),
            version="1.0.0"
        )
        
        # Store compositions
        self.compositions = {
            wellness_composition.composition_id: wellness_composition,
            recovery_composition.composition_id: recovery_composition,
            performance_composition.composition_id: performance_composition
        }
    
    def register_agent_interface(self, interface: AgentInterface) -> bool:
        """Register a new agent interface for composition"""
        try:
            self.agent_interfaces[interface.agent_id] = interface
            self.logger.info(f"Agent interface registered: {interface.agent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register agent interface: {e}")
            return False
    
    def create_custom_composition(self, composition: AgentComposition) -> bool:
        """Create a custom agent composition"""
        try:
            # Validate composition
            validation_result = self._validate_composition(composition)
            if not validation_result["valid"]:
                self.logger.error(f"Composition validation failed: {validation_result['errors']}")
                return False
            
            self.compositions[composition.composition_id] = composition
            self.logger.info(f"Custom composition created: {composition.composition_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create composition: {e}")
            return False
    
    def _validate_composition(self, composition: AgentComposition) -> Dict[str, Any]:
        """Validate a composition for correctness"""
        errors = []
        
        # Check if all referenced agents exist
        for node in composition.nodes:
            if node.agent_id not in self.agent_interfaces:
                errors.append(f"Agent {node.agent_id} not found in registered interfaces")
        
        # Check input/output mapping consistency
        for node in composition.nodes:
            agent_interface = self.agent_interfaces.get(node.agent_id)
            if agent_interface:
                # Validate input mapping
                for comp_input, agent_input in node.input_mapping.items():
                    if agent_input not in agent_interface.input_schema.get("properties", {}):
                        errors.append(f"Invalid input mapping: {agent_input} not in {node.agent_id} schema")
        
        # Check for circular dependencies
        if self._has_circular_dependencies(composition.nodes):
            errors.append("Circular dependencies detected in composition")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _has_circular_dependencies(self, nodes: List[CompositionNode]) -> bool:
        """Check for circular dependencies in composition nodes"""
        # Simplified check - in production would use graph algorithms
        dependencies = {}
        for node in nodes:
            dependencies[node.node_id] = []
            for mapping_value in node.input_mapping.values():
                if "." in mapping_value:  # References another node
                    dep_node = mapping_value.split(".")[0]
                    dependencies[node.node_id].append(dep_node)
        
        # Simple cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id):
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep in dependencies.get(node_id, []):
                if has_cycle(dep):
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in dependencies:
            if has_cycle(node_id):
                return True
        
        return False
    
    async def execute_composition(self, 
                                composition_id: str,
                                input_data: Dict[str, Any],
                                execution_config: Optional[Dict[str, Any]] = None) -> CompositionExecution:
        """Execute an agent composition"""
        
        if composition_id not in self.compositions:
            raise ValueError(f"Composition {composition_id} not found")
        
        composition = self.compositions[composition_id]
        execution_id = str(uuid.uuid4())
        
        execution = CompositionExecution(
            execution_id=execution_id,
            composition_id=composition_id,
            input_data=input_data,
            started_at=datetime.now(),
            node_results={}
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            # Execute based on composition type
            if composition.composition_type == CompositionType.SEQUENTIAL_CHAIN:
                result = await self._execute_sequential_composition(composition, input_data, execution)
            elif composition.composition_type == CompositionType.PARALLEL_ENSEMBLE:
                result = await self._execute_parallel_composition(composition, input_data, execution)
            elif composition.composition_type == CompositionType.HIERARCHICAL_TREE:
                result = await self._execute_hierarchical_composition(composition, input_data, execution)
            elif composition.composition_type == CompositionType.FEEDBACK_LOOP:
                result = await self._execute_feedback_composition(composition, input_data, execution)
            else:
                raise ValueError(f"Unsupported composition type: {composition.composition_type}")
            
            execution.final_result = result
            execution.status = "completed"
            execution.completed_at = datetime.now()
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now()
            self.logger.error(f"Composition execution failed: {e}")
        
        finally:
            # Move to history
            self.execution_history[execution_id] = execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return execution
    
    async def _execute_sequential_composition(self, 
                                            composition: AgentComposition,
                                            input_data: Dict[str, Any],
                                            execution: CompositionExecution) -> Dict[str, Any]:
        """Execute composition sequentially"""
        results = {}
        current_data = input_data.copy()
        
        for node in composition.nodes:
            # Prepare node input
            node_input = self._prepare_node_input(node, current_data, results)
            
            # Execute node
            node_result = await self._execute_composition_node(node, node_input)
            results[node.node_id] = node_result
            execution.node_results[node.node_id] = node_result
            
            # Update current data with node outputs
            if node_result.get("success"):
                mapped_output = self._map_node_output(node, node_result.get("result", {}))
                current_data.update(mapped_output)
        
        return {
            "composition_type": "sequential",
            "node_results": results,
            "final_data": current_data
        }
    
    async def _execute_parallel_composition(self, 
                                          composition: AgentComposition,
                                          input_data: Dict[str, Any],
                                          execution: CompositionExecution) -> Dict[str, Any]:
        """Execute composition in parallel"""
        tasks = []
        
        for node in composition.nodes:
            node_input = self._prepare_node_input(node, input_data, {})
            task = self._execute_composition_node(node, node_input)
            tasks.append((node.node_id, task))
        
        # Execute all nodes in parallel
        results = {}
        responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (node_id, _), response in zip(tasks, responses):
            if isinstance(response, Exception):
                results[node_id] = {"success": False, "error": str(response)}
            else:
                results[node_id] = response
            
            execution.node_results[node_id] = results[node_id]
        
        return {
            "composition_type": "parallel",
            "node_results": results
        }
    
    async def _execute_hierarchical_composition(self, 
                                              composition: AgentComposition,
                                              input_data: Dict[str, Any],
                                              execution: CompositionExecution) -> Dict[str, Any]:
        """Execute composition in hierarchical order"""
        # Group nodes by role/level
        primary_nodes = [n for n in composition.nodes if n.role == AgentRole.PRIMARY]
        secondary_nodes = [n for n in composition.nodes if n.role == AgentRole.SECONDARY]
        aggregator_nodes = [n for n in composition.nodes if n.role == AgentRole.AGGREGATOR]
        
        results = {}
        
        # Execute primary nodes first (parallel)
        primary_tasks = []
        for node in primary_nodes:
            node_input = self._prepare_node_input(node, input_data, {})
            task = self._execute_composition_node(node, node_input)
            primary_tasks.append((node.node_id, task))
        
        primary_responses = await asyncio.gather(*[task for _, task in primary_tasks], return_exceptions=True)
        
        for (node_id, _), response in zip(primary_tasks, primary_responses):
            results[node_id] = response if not isinstance(response, Exception) else {"success": False, "error": str(response)}
            execution.node_results[node_id] = results[node_id]
        
        # Execute secondary nodes with primary results
        for node in secondary_nodes:
            node_input = self._prepare_node_input(node, input_data, results)
            node_result = await self._execute_composition_node(node, node_input)
            results[node.node_id] = node_result
            execution.node_results[node.node_id] = node_result
        
        # Execute aggregator nodes with all previous results
        for node in aggregator_nodes:
            node_input = self._prepare_node_input(node, input_data, results)
            node_result = await self._execute_composition_node(node, node_input)
            results[node.node_id] = node_result
            execution.node_results[node.node_id] = node_result
        
        return {
            "composition_type": "hierarchical",
            "node_results": results
        }
    
    async def _execute_feedback_composition(self, 
                                          composition: AgentComposition,
                                          input_data: Dict[str, Any],
                                          execution: CompositionExecution) -> Dict[str, Any]:
        """Execute composition with feedback loops"""
        # Simplified feedback loop implementation
        results = {}
        iterations = 0
        max_iterations = 10
        
        while iterations < max_iterations:
            iteration_results = {}
            
            for node in composition.nodes:
                node_input = self._prepare_node_input(node, input_data, results)
                node_result = await self._execute_composition_node(node, node_input)
                iteration_results[node.node_id] = node_result
            
            results.update(iteration_results)
            execution.node_results = results
            iterations += 1
            
            # Check convergence condition (simplified)
            if all(r.get("success", False) for r in iteration_results.values()):
                break
            
            # Brief pause between iterations
            await asyncio.sleep(0.1)
        
        return {
            "composition_type": "feedback_loop",
            "iterations": iterations,
            "node_results": results
        }
    
    def _prepare_node_input(self, 
                           node: CompositionNode,
                           input_data: Dict[str, Any],
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for a composition node"""
        node_input = {}
        
        for comp_key, agent_key in node.input_mapping.items():
            if "." in agent_key:
                # Reference to another node's output
                node_id, output_key = agent_key.split(".", 1)
                if node_id in previous_results:
                    node_result = previous_results[node_id]
                    if node_result.get("success") and "result" in node_result:
                        value = node_result["result"].get(output_key)
                        if value is not None:
                            node_input[comp_key] = value
            else:
                # Direct input from composition input
                if agent_key in input_data:
                    node_input[comp_key] = input_data[agent_key]
        
        return node_input
    
    def _map_node_output(self, 
                        node: CompositionNode,
                        node_result: Dict[str, Any]) -> Dict[str, Any]:
        """Map node output to composition output"""
        mapped_output = {}
        
        for comp_key, result_key in node.output_mapping.items():
            if result_key in node_result:
                mapped_output[comp_key] = node_result[result_key]
        
        return mapped_output
    
    async def _execute_composition_node(self, 
                                      node: CompositionNode,
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node in a composition"""
        try:
            # Check conditions
            if node.conditions and not self._evaluate_node_conditions(node.conditions, input_data):
                return {"success": True, "result": {}, "skipped": True}
            
            # Get primary capability for agent
            agent_interface = self.agent_interfaces.get(node.agent_id)
            if not agent_interface:
                return {"success": False, "error": f"Agent interface not found: {node.agent_id}"}
            
            primary_capability = agent_interface.capabilities[0] if agent_interface.capabilities else "default"
            
            # Execute through communication protocol
            request = AgentCapabilityRequest(
                capability_name=primary_capability,
                input_data=input_data
            )
            
            response = await self.communication.request_capability(
                from_agent="composition_executor",
                target_agent=node.agent_id,
                capability_request=request
            )
            
            return {
                "success": response.success,
                "result": response.result,
                "error": response.error,
                "execution_time": response.execution_time,
                "cost": response.cost
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _evaluate_node_conditions(self, 
                                 conditions: Dict[str, Any],
                                 context: Dict[str, Any]) -> bool:
        """Evaluate conditions for node execution"""
        # Simplified condition evaluation
        return True  # In production, would implement proper condition logic
    
    def find_compatible_agents(self, 
                              required_capabilities: List[str],
                              compatibility_tags: List[str] = None) -> List[AgentInterface]:
        """Find agents compatible with given requirements"""
        compatible = []
        
        for interface in self.agent_interfaces.values():
            # Check capabilities
            has_capabilities = any(cap in interface.capabilities for cap in required_capabilities)
            
            # Check compatibility tags
            has_compatible_tags = True
            if compatibility_tags:
                has_compatible_tags = any(tag in interface.compatibility_tags for tag in compatibility_tags)
            
            if has_capabilities and has_compatible_tags:
                compatible.append(interface)
        
        return compatible
    
    def get_composition_catalog(self) -> List[Dict[str, Any]]:
        """Get catalog of available compositions"""
        catalog = []
        
        for composition in self.compositions.values():
            catalog.append({
                "composition_id": composition.composition_id,
                "name": composition.name,
                "description": composition.description,
                "type": composition.composition_type.value,
                "agents_required": [node.agent_id for node in composition.nodes],
                "complexity": composition.metadata.get("complexity", "medium"),
                "estimated_duration": composition.metadata.get("estimated_duration", 30),
                "category": composition.metadata.get("category", "general"),
                "target_users": composition.metadata.get("target_users", [])
            })
        
        return catalog
    
    def get_execution_status(self, execution_id: str) -> Optional[CompositionExecution]:
        """Get status of a composition execution"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        elif execution_id in self.execution_history:
            return self.execution_history[execution_id]
        return None

# Global composable agent system
composable_agent_system = ComposableAgentSystem(None, None)  # Will be initialized with dependencies