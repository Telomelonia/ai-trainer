"""
Multi-Agent Orchestrator for CoreSense
Manages complex multi-agent workflows and compositions for comprehensive fitness training
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum

from .agent_communication import AgentCommunicationProtocol, AgentCapabilityRequest
from .coral_client import CoralProtocolClient, CoralAgentInvocation

class WorkflowType(Enum):
    """Types of multi-agent workflows"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    HYBRID = "hybrid"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """Represents a step in a multi-agent workflow"""
    step_id: str
    agent_id: str
    capability: str
    input_data: Dict[str, Any]
    depends_on: List[str] = None
    conditions: Dict[str, Any] = None
    timeout: int = 30
    retry_count: int = 3

@dataclass
class WorkflowDefinition:
    """Defines a multi-agent workflow"""
    workflow_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    global_timeout: int = 300
    cost_limit: Optional[float] = None
    metadata: Dict[str, Any] = None

@dataclass
class WorkflowExecution:
    """Tracks workflow execution state"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = None
    total_cost: float = 0.0
    error: Optional[str] = None

class MultiAgentOrchestrator:
    """Orchestrates complex multi-agent workflows for comprehensive fitness training"""
    
    def __init__(self, communication_protocol: Optional[AgentCommunicationProtocol] = None):
        self.communication = communication_protocol or AgentCommunicationProtocol()
        self.coral_client = CoralProtocolClient()
        self.logger = logging.getLogger(__name__)
        
        # Workflow storage
        self.workflow_definitions = {}
        self.active_executions = {}
        self.execution_history = {}
        
        # Pre-built workflow templates
        self._initialize_workflow_templates()
    
    def _initialize_workflow_templates(self):
        """Initialize pre-built workflow templates"""
        
        # Comprehensive Fitness Assessment Workflow
        fitness_assessment = WorkflowDefinition(
            workflow_id="comprehensive_fitness_assessment",
            name="Comprehensive Fitness Assessment",
            description="Complete fitness analysis using multiple specialized agents",
            workflow_type=WorkflowType.SEQUENTIAL,
            steps=[
                WorkflowStep(
                    step_id="muscle_analysis",
                    agent_id="coresense-fabric-sensor",
                    capability="muscle_activation_analysis",
                    input_data={"exercise": "assessment_plank", "duration": 60}
                ),
                WorkflowStep(
                    step_id="compensation_check",
                    agent_id="coresense-fabric-sensor",
                    capability="compensation_detection",
                    input_data={},
                    depends_on=["muscle_analysis"]
                ),
                WorkflowStep(
                    step_id="injury_assessment",
                    agent_id="physiotherapy-assistant",
                    capability="injury_assessment",
                    input_data={},
                    depends_on=["compensation_check"]
                ),
                WorkflowStep(
                    step_id="nutrition_analysis",
                    agent_id="external-nutrition-coach",
                    capability="nutrition_analysis",
                    input_data={},
                    depends_on=["muscle_analysis"]
                ),
                WorkflowStep(
                    step_id="personalized_plan",
                    agent_id="coresense-ai-coach",
                    capability="personalized_coaching",
                    input_data={},
                    depends_on=["compensation_check", "injury_assessment", "nutrition_analysis"]
                )
            ],
            global_timeout=600,
            cost_limit=2.0
        )
        
        # Real-time Coaching Session Workflow
        realtime_coaching = WorkflowDefinition(
            workflow_id="realtime_coaching_session",
            name="Real-time Coaching Session",
            description="Live coaching with real-time feedback and adjustments",
            workflow_type=WorkflowType.HYBRID,
            steps=[
                WorkflowStep(
                    step_id="session_start",
                    agent_id="coresense-orchestrator",
                    capability="session_management",
                    input_data={"action": "start_session"}
                ),
                WorkflowStep(
                    step_id="continuous_monitoring",
                    agent_id="coresense-fabric-sensor",
                    capability="muscle_activation_analysis",
                    input_data={"mode": "continuous"},
                    depends_on=["session_start"]
                ),
                WorkflowStep(
                    step_id="real_time_coaching",
                    agent_id="coresense-ai-coach",
                    capability="personalized_coaching",
                    input_data={"mode": "realtime"},
                    depends_on=["continuous_monitoring"]
                )
            ],
            global_timeout=1800,  # 30 minutes
            cost_limit=5.0
        )
        
        # Team Training Orchestration
        team_training = WorkflowDefinition(
            workflow_id="team_training_orchestration",
            name="Team Training Orchestration",
            description="Coordinate training for multiple users simultaneously",
            workflow_type=WorkflowType.PARALLEL,
            steps=[
                WorkflowStep(
                    step_id="team_assessment",
                    agent_id="coresense-orchestrator",
                    capability="multi_agent_coordination",
                    input_data={"mode": "team_analysis"}
                ),
                WorkflowStep(
                    step_id="individual_analysis_1",
                    agent_id="coresense-fabric-sensor",
                    capability="muscle_activation_analysis",
                    input_data={"user_id": "user_1"},
                    depends_on=["team_assessment"]
                ),
                WorkflowStep(
                    step_id="individual_analysis_2",
                    agent_id="coresense-fabric-sensor",
                    capability="muscle_activation_analysis",
                    input_data={"user_id": "user_2"},
                    depends_on=["team_assessment"]
                ),
                WorkflowStep(
                    step_id="team_coaching",
                    agent_id="coresense-ai-coach",
                    capability="personalized_coaching",
                    input_data={"mode": "team"},
                    depends_on=["individual_analysis_1", "individual_analysis_2"]
                )
            ],
            global_timeout=900,
            cost_limit=10.0
        )
        
        # Store templates
        self.workflow_definitions = {
            fitness_assessment.workflow_id: fitness_assessment,
            realtime_coaching.workflow_id: realtime_coaching,
            team_training.workflow_id: team_training
        }
    
    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a new workflow definition"""
        try:
            self.workflow_definitions[workflow.workflow_id] = workflow
            self.logger.info(f"Workflow {workflow.workflow_id} registered successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register workflow: {e}")
            return False
    
    async def execute_workflow(self, 
                             workflow_id: str,
                             input_data: Dict[str, Any],
                             user_context: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """Execute a multi-agent workflow"""
        
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflow_definitions[workflow_id]
        execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now(),
            results={}
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # Execute based on workflow type
            if workflow.workflow_type == WorkflowType.SEQUENTIAL:
                results = await self._execute_sequential_workflow(workflow, input_data, user_context)
            elif workflow.workflow_type == WorkflowType.PARALLEL:
                results = await self._execute_parallel_workflow(workflow, input_data, user_context)
            elif workflow.workflow_type == WorkflowType.CONDITIONAL:
                results = await self._execute_conditional_workflow(workflow, input_data, user_context)
            elif workflow.workflow_type == WorkflowType.HYBRID:
                results = await self._execute_hybrid_workflow(workflow, input_data, user_context)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")
            
            execution.results = results
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.total_cost = results.get("total_cost", 0.0)
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            self.logger.error(f"Workflow execution failed: {e}")
        
        finally:
            # Move to history
            self.execution_history[execution_id] = execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return execution
    
    async def _execute_sequential_workflow(self, 
                                         workflow: WorkflowDefinition,
                                         input_data: Dict[str, Any],
                                         user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow steps sequentially"""
        results = {}
        step_results = {}
        total_cost = 0.0
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(workflow.steps)
        execution_order = self._topological_sort(dependency_graph)
        
        for step_id in execution_order:
            step = next(s for s in workflow.steps if s.step_id == step_id)
            
            try:
                # Prepare step input data
                step_input = step.input_data.copy()
                step_input.update(input_data)
                
                # Add results from dependent steps
                if step.depends_on:
                    for dep_step in step.depends_on:
                        if dep_step in step_results:
                            step_input[f"{dep_step}_result"] = step_results[dep_step]
                
                # Add user context if available
                if user_context:
                    step_input["user_context"] = user_context
                
                # Execute step
                step_result = await self._execute_step(step, step_input)
                
                step_results[step_id] = step_result
                results[step_id] = step_result
                
                if step_result.get("cost"):
                    total_cost += step_result["cost"]
                
                # Check cost limit
                if workflow.cost_limit and total_cost > workflow.cost_limit:
                    raise Exception(f"Cost limit exceeded: {total_cost} > {workflow.cost_limit}")
                
            except Exception as e:
                results[step_id] = {"error": str(e)}
                raise Exception(f"Step {step_id} failed: {e}")
        
        results["total_cost"] = total_cost
        results["execution_summary"] = {
            "steps_completed": len([r for r in results.values() if not isinstance(r, dict) or "error" not in r]),
            "total_steps": len(workflow.steps),
            "success_rate": len([r for r in results.values() if not isinstance(r, dict) or "error" not in r]) / len(workflow.steps)
        }
        
        return results
    
    async def _execute_parallel_workflow(self, 
                                        workflow: WorkflowDefinition,
                                        input_data: Dict[str, Any],
                                        user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow steps in parallel where possible"""
        results = {}
        total_cost = 0.0
        
        # Group steps by dependency level
        dependency_levels = self._group_by_dependency_level(workflow.steps)
        
        for level, steps in dependency_levels.items():
            # Execute all steps in this level in parallel
            tasks = []
            for step in steps:
                step_input = step.input_data.copy()
                step_input.update(input_data)
                
                # Add user context
                if user_context:
                    step_input["user_context"] = user_context
                
                # Add results from previous levels
                for prev_level in range(level):
                    if prev_level in dependency_levels:
                        for prev_step in dependency_levels[prev_level]:
                            if prev_step.step_id in results:
                                step_input[f"{prev_step.step_id}_result"] = results[prev_step.step_id]
                
                task = self._execute_step(step, step_input)
                tasks.append((step.step_id, task))
            
            # Wait for all tasks in this level to complete
            level_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (step_id, _), result in zip(tasks, level_results):
                if isinstance(result, Exception):
                    results[step_id] = {"error": str(result)}
                else:
                    results[step_id] = result
                    if result.get("cost"):
                        total_cost += result["cost"]
        
        results["total_cost"] = total_cost
        return results
    
    async def _execute_conditional_workflow(self, 
                                          workflow: WorkflowDefinition,
                                          input_data: Dict[str, Any],
                                          user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow with conditional branching"""
        results = {}
        step_results = {}
        total_cost = 0.0
        
        for step in workflow.steps:
            # Check conditions
            if step.conditions and not self._evaluate_conditions(step.conditions, step_results):
                results[step.step_id] = {"skipped": True, "reason": "conditions_not_met"}
                continue
            
            # Prepare input
            step_input = step.input_data.copy()
            step_input.update(input_data)
            
            if user_context:
                step_input["user_context"] = user_context
            
            # Add dependent results
            if step.depends_on:
                for dep_step in step.depends_on:
                    if dep_step in step_results:
                        step_input[f"{dep_step}_result"] = step_results[dep_step]
            
            # Execute step
            try:
                step_result = await self._execute_step(step, step_input)
                step_results[step.step_id] = step_result
                results[step.step_id] = step_result
                
                if step_result.get("cost"):
                    total_cost += step_result["cost"]
                    
            except Exception as e:
                results[step.step_id] = {"error": str(e)}
        
        results["total_cost"] = total_cost
        return results
    
    async def _execute_hybrid_workflow(self, 
                                     workflow: WorkflowDefinition,
                                     input_data: Dict[str, Any],
                                     user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow with mixed sequential and parallel execution"""
        # For hybrid workflows, use dependency-based parallel execution
        return await self._execute_parallel_workflow(workflow, input_data, user_context)
    
    async def _execute_step(self, step: WorkflowStep, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        retries = 0
        last_error = None
        
        while retries <= step.retry_count:
            try:
                # Check if it's a CoreSense agent or external agent
                if step.agent_id.startswith("coresense-"):
                    # Use internal communication protocol
                    request = AgentCapabilityRequest(
                        capability_name=step.capability,
                        input_data=input_data
                    )
                    
                    response = await self.communication.request_capability(
                        from_agent="orchestrator",
                        target_agent=step.agent_id,
                        capability_request=request
                    )
                    
                    if response.success:
                        return {
                            "success": True,
                            "result": response.result,
                            "cost": response.cost,
                            "execution_time": response.execution_time
                        }
                    else:
                        raise Exception(response.error)
                        
                else:
                    # Use Coral Protocol for external agents
                    async with self.coral_client as coral:
                        invocation = CoralAgentInvocation(
                            agent_id=step.agent_id,
                            capability=step.capability,
                            input_data=input_data
                        )
                        
                        response = await coral.invoke_agent(invocation)
                        
                        if response.get("success"):
                            return {
                                "success": True,
                                "result": response.get("result"),
                                "cost": response.get("cost"),
                                "execution_time": response.get("execution_time")
                            }
                        else:
                            raise Exception(response.get("error", "Unknown error"))
                
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= step.retry_count:
                    await asyncio.sleep(1 * retries)  # Exponential backoff
        
        # All retries failed
        return {
            "success": False,
            "error": str(last_error),
            "retries_attempted": retries - 1
        }
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for workflow steps"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.depends_on or []
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on dependency graph"""
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        return result
    
    def _group_by_dependency_level(self, steps: List[WorkflowStep]) -> Dict[int, List[WorkflowStep]]:
        """Group steps by their dependency level for parallel execution"""
        levels = {}
        step_map = {step.step_id: step for step in steps}
        
        def get_level(step_id: str, visited: set) -> int:
            if step_id in visited:
                return 0  # Avoid cycles
            
            visited.add(step_id)
            step = step_map[step_id]
            
            if not step.depends_on:
                return 0
            
            max_dep_level = 0
            for dep in step.depends_on:
                if dep in step_map:
                    dep_level = get_level(dep, visited.copy())
                    max_dep_level = max(max_dep_level, dep_level)
            
            return max_dep_level + 1
        
        for step in steps:
            level = get_level(step.step_id, set())
            if level not in levels:
                levels[level] = []
            levels[level].append(step)
        
        return levels
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], step_results: Dict[str, Any]) -> bool:
        """Evaluate workflow step conditions"""
        # Simple condition evaluation
        # In production, this would be more sophisticated
        for condition_key, condition_value in conditions.items():
            if condition_key == "require_success":
                for step_id in condition_value:
                    if step_id not in step_results or not step_results[step_id].get("success", False):
                        return False
            elif condition_key == "require_value":
                for step_id, expected_value in condition_value.items():
                    if step_id not in step_results:
                        return False
                    result = step_results[step_id].get("result", {})
                    if result.get(expected_value["field"]) != expected_value["value"]:
                        return False
        
        return True
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a workflow execution"""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        elif execution_id in self.execution_history:
            return self.execution_history[execution_id]
        return None
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel an active workflow execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            
            # Move to history
            self.execution_history[execution_id] = execution
            del self.active_executions[execution_id]
            
            self.logger.info(f"Workflow execution {execution_id} cancelled")
            return True
        
        return False
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflow templates"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "type": wf.workflow_type.value,
                "steps": len(wf.steps),
                "estimated_cost": wf.cost_limit,
                "estimated_duration": wf.global_timeout
            }
            for wf in self.workflow_definitions.values()
        ]

# Global orchestrator instance
multi_agent_orchestrator = MultiAgentOrchestrator()  # Now uses default communication protocol