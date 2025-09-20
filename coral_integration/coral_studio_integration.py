"""
Coral Studio Integration for CoreSense
Debugging, monitoring, and deployment tools for CoreSense agents
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
import logging
import traceback

@dataclass
class AgentTelemetry:
    """Telemetry data for agent monitoring"""
    agent_id: str
    timestamp: str
    event_type: str  # start, end, error, metric
    data: Dict[str, Any]
    session_id: Optional[str] = None
    execution_id: Optional[str] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for agent execution"""
    agent_id: str
    capability: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error: Optional[str] = None
    timestamp: str = None

@dataclass
class DebugSession:
    """Debug session for agent development"""
    session_id: str
    agent_id: str
    developer_id: str
    started_at: datetime
    status: str  # active, paused, completed
    breakpoints: List[str]
    variables: Dict[str, Any]
    call_stack: List[str]

class CoralStudioIntegration:
    """Integration with Coral Studio for agent debugging and deployment"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Telemetry storage
        self.telemetry_data = []
        self.performance_metrics = []
        self.debug_sessions = {}
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.debug_mode = False
        self.telemetry_handlers = []
        
        # Performance thresholds
        self.performance_thresholds = {
            "execution_time_ms": 5000,    # 5 seconds
            "memory_usage_mb": 512,       # 512 MB
            "cpu_usage_percent": 80,      # 80%
            "error_rate_percent": 5       # 5%
        }
    
    def enable_monitoring(self, agent_id: str):
        """Enable monitoring for a specific agent"""
        self._log_telemetry(agent_id, "monitoring_enabled", {
            "timestamp": datetime.now().isoformat(),
            "enabled": True
        })
        self.logger.info(f"Monitoring enabled for agent {agent_id}")
    
    def disable_monitoring(self, agent_id: str):
        """Disable monitoring for a specific agent"""
        self._log_telemetry(agent_id, "monitoring_disabled", {
            "timestamp": datetime.now().isoformat(),
            "enabled": False
        })
        self.logger.info(f"Monitoring disabled for agent {agent_id}")
    
    def start_debug_session(self, 
                           agent_id: str, 
                           developer_id: str,
                           breakpoints: List[str] = None) -> str:
        """Start a debugging session for an agent"""
        session_id = str(uuid.uuid4())
        
        debug_session = DebugSession(
            session_id=session_id,
            agent_id=agent_id,
            developer_id=developer_id,
            started_at=datetime.now(),
            status="active",
            breakpoints=breakpoints or [],
            variables={},
            call_stack=[]
        )
        
        self.debug_sessions[session_id] = debug_session
        self.debug_mode = True
        
        self._log_telemetry(agent_id, "debug_session_started", {
            "session_id": session_id,
            "developer_id": developer_id,
            "breakpoints": breakpoints
        })
        
        self.logger.info(f"Debug session {session_id} started for agent {agent_id}")
        return session_id
    
    def add_breakpoint(self, session_id: str, breakpoint: str) -> bool:
        """Add a breakpoint to a debug session"""
        if session_id in self.debug_sessions:
            self.debug_sessions[session_id].breakpoints.append(breakpoint)
            
            self._log_telemetry(
                self.debug_sessions[session_id].agent_id,
                "breakpoint_added",
                {"session_id": session_id, "breakpoint": breakpoint}
            )
            return True
        return False
    
    def capture_agent_state(self, 
                           agent_id: str,
                           session_id: str,
                           variables: Dict[str, Any],
                           call_stack: List[str]):
        """Capture agent state during execution"""
        if session_id in self.debug_sessions:
            debug_session = self.debug_sessions[session_id]
            debug_session.variables = variables
            debug_session.call_stack = call_stack
            
            self._log_telemetry(agent_id, "state_captured", {
                "session_id": session_id,
                "variable_count": len(variables),
                "stack_depth": len(call_stack),
                "timestamp": datetime.now().isoformat()
            })
    
    def log_agent_execution(self, 
                           agent_id: str,
                           capability: str,
                           input_data: Dict[str, Any],
                           output_data: Dict[str, Any],
                           execution_time: float,
                           success: bool,
                           error: Optional[str] = None,
                           session_id: Optional[str] = None):
        """Log agent execution for monitoring and debugging"""
        
        execution_id = str(uuid.uuid4())
        
        # Log telemetry
        telemetry_data = {
            "execution_id": execution_id,
            "capability": capability,
            "input_size": len(json.dumps(input_data)) if input_data else 0,
            "output_size": len(json.dumps(output_data)) if output_data else 0,
            "execution_time": execution_time,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self._log_telemetry(agent_id, "execution_completed", telemetry_data, session_id, execution_id)
        
        # Record performance metrics
        metrics = PerformanceMetrics(
            agent_id=agent_id,
            capability=capability,
            execution_time=execution_time,
            memory_usage=self._get_memory_usage(),
            cpu_usage=self._get_cpu_usage(),
            success=success,
            error=error,
            timestamp=datetime.now().isoformat()
        )
        
        self.performance_metrics.append(metrics)
        
        # Check performance thresholds
        self._check_performance_thresholds(metrics)
        
        # Debug mode handling
        if self.debug_mode and session_id in self.debug_sessions:
            self._handle_debug_execution(agent_id, session_id, telemetry_data)
    
    def _log_telemetry(self, 
                      agent_id: str,
                      event_type: str,
                      data: Dict[str, Any],
                      session_id: Optional[str] = None,
                      execution_id: Optional[str] = None):
        """Log telemetry data"""
        if not self.monitoring_enabled:
            return
        
        telemetry = AgentTelemetry(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            data=data,
            session_id=session_id,
            execution_id=execution_id
        )
        
        self.telemetry_data.append(telemetry)
        
        # Call registered handlers
        for handler in self.telemetry_handlers:
            try:
                handler(telemetry)
            except Exception as e:
                self.logger.error(f"Telemetry handler error: {e}")
    
    def register_telemetry_handler(self, handler: Callable):
        """Register a handler for telemetry events"""
        self.telemetry_handlers.append(handler)
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check if performance metrics exceed thresholds"""
        alerts = []
        
        if metrics.execution_time > self.performance_thresholds["execution_time_ms"]:
            alerts.append(f"Execution time ({metrics.execution_time}ms) exceeds threshold")
        
        if metrics.memory_usage > self.performance_thresholds["memory_usage_mb"]:
            alerts.append(f"Memory usage ({metrics.memory_usage}MB) exceeds threshold")
        
        if metrics.cpu_usage > self.performance_thresholds["cpu_usage_percent"]:
            alerts.append(f"CPU usage ({metrics.cpu_usage}%) exceeds threshold")
        
        if alerts:
            self._log_telemetry(metrics.agent_id, "performance_alert", {
                "alerts": alerts,
                "metrics": asdict(metrics)
            })
    
    def _handle_debug_execution(self, 
                               agent_id: str,
                               session_id: str,
                               execution_data: Dict[str, Any]):
        """Handle execution in debug mode"""
        debug_session = self.debug_sessions[session_id]
        
        # Check if execution should pause at breakpoint
        for breakpoint in debug_session.breakpoints:
            if breakpoint in execution_data.get("capability", ""):
                debug_session.status = "paused"
                
                self._log_telemetry(agent_id, "breakpoint_hit", {
                    "session_id": session_id,
                    "breakpoint": breakpoint,
                    "execution_data": execution_data
                })
                break
    
    def get_agent_telemetry(self, 
                           agent_id: str,
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           event_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get telemetry data for an agent"""
        filtered_telemetry = []
        
        for telemetry in self.telemetry_data:
            if telemetry.agent_id != agent_id:
                continue
            
            if start_time and telemetry.timestamp < start_time:
                continue
            
            if end_time and telemetry.timestamp > end_time:
                continue
            
            if event_types and telemetry.event_type not in event_types:
                continue
            
            filtered_telemetry.append(asdict(telemetry))
        
        return filtered_telemetry
    
    def get_performance_report(self, 
                              agent_id: str,
                              timeframe_hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for an agent"""
        cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
        
        relevant_metrics = [
            m for m in self.performance_metrics 
            if m.agent_id == agent_id and 
            datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not relevant_metrics:
            return {"agent_id": agent_id, "message": "No metrics available"}
        
        # Calculate statistics
        execution_times = [m.execution_time for m in relevant_metrics]
        memory_usage = [m.memory_usage for m in relevant_metrics]
        cpu_usage = [m.cpu_usage for m in relevant_metrics]
        
        success_count = sum(1 for m in relevant_metrics if m.success)
        total_count = len(relevant_metrics)
        
        report = {
            "agent_id": agent_id,
            "timeframe_hours": timeframe_hours,
            "total_executions": total_count,
            "success_rate": (success_count / total_count) * 100 if total_count > 0 else 0,
            "performance": {
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times),
                "avg_memory_usage": sum(memory_usage) / len(memory_usage),
                "peak_memory_usage": max(memory_usage),
                "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage),
                "peak_cpu_usage": max(cpu_usage)
            },
            "errors": [
                {"timestamp": m.timestamp, "error": m.error, "capability": m.capability}
                for m in relevant_metrics if not m.success and m.error
            ],
            "capabilities_used": list(set(m.capability for m in relevant_metrics)),
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def export_debug_logs(self, session_id: str) -> Dict[str, Any]:
        """Export debug logs for a session"""
        if session_id not in self.debug_sessions:
            return {"error": "Debug session not found"}
        
        debug_session = self.debug_sessions[session_id]
        
        # Get all telemetry for this session
        session_telemetry = [
            asdict(t) for t in self.telemetry_data 
            if t.session_id == session_id
        ]
        
        # Get performance metrics for this agent during session
        session_start = debug_session.started_at
        session_metrics = [
            asdict(m) for m in self.performance_metrics
            if m.agent_id == debug_session.agent_id and
            datetime.fromisoformat(m.timestamp) >= session_start
        ]
        
        return {
            "session_info": asdict(debug_session),
            "telemetry_events": session_telemetry,
            "performance_metrics": session_metrics,
            "export_timestamp": datetime.now().isoformat()
        }
    
    def deploy_agent_to_coral(self, 
                             agent_id: str,
                             deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy agent to Coral Protocol network"""
        try:
            # Validate agent performance before deployment
            performance_report = self.get_performance_report(agent_id, timeframe_hours=1)
            
            if performance_report.get("success_rate", 0) < 95:
                return {
                    "success": False,
                    "error": "Agent performance below deployment threshold",
                    "performance_report": performance_report
                }
            
            # Simulate deployment to Coral network
            deployment_id = str(uuid.uuid4())
            
            deployment_result = {
                "success": True,
                "deployment_id": deployment_id,
                "agent_id": agent_id,
                "coral_uri": f"coral://{agent_id}",
                "deployment_config": deployment_config,
                "deployed_at": datetime.now().isoformat(),
                "status": "deployed",
                "performance_validated": True,
                "endpoints": {
                    "invoke": f"https://coral.api/v1/agents/{agent_id}/invoke",
                    "status": f"https://coral.api/v1/agents/{agent_id}/status",
                    "metrics": f"https://coral.api/v1/agents/{agent_id}/metrics"
                }
            }
            
            # Log deployment
            self._log_telemetry(agent_id, "deployed_to_coral", {
                "deployment_id": deployment_id,
                "config": deployment_config,
                "performance_report": performance_report
            })
            
            return deployment_result
            
        except Exception as e:
            self.logger.error(f"Failed to deploy agent {agent_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (simulated)"""
        # In production, would use psutil or similar
        import random
        return random.uniform(100, 400)  # MB
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage (simulated)"""
        # In production, would use psutil or similar
        import random
        return random.uniform(10, 70)  # Percentage
    
    def get_studio_dashboard(self) -> Dict[str, Any]:
        """Get Coral Studio dashboard data"""
        # Agent overview
        agents = set(t.agent_id for t in self.telemetry_data)
        
        dashboard = {
            "overview": {
                "total_agents": len(agents),
                "active_debug_sessions": len([s for s in self.debug_sessions.values() if s.status == "active"]),
                "total_telemetry_events": len(self.telemetry_data),
                "monitoring_enabled": self.monitoring_enabled,
                "debug_mode": self.debug_mode
            },
            "recent_activity": [
                asdict(t) for t in sorted(self.telemetry_data, key=lambda x: x.timestamp, reverse=True)[:10]
            ],
            "performance_summary": {
                agent_id: self.get_performance_report(agent_id, timeframe_hours=1)
                for agent_id in list(agents)[:5]  # Top 5 agents
            },
            "active_sessions": [
                asdict(s) for s in self.debug_sessions.values() if s.status == "active"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard

# Global Coral Studio integration instance
coral_studio = CoralStudioIntegration()