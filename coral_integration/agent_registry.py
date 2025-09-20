"""
CoreSense Agent Registry for Coral Protocol
Registry configuration and discovery system for CoreSense fitness coaching agents
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

@dataclass
class AgentCapability:
    """Defines a capability that an agent can perform"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    pricing: float  # Cost per invocation in CORAL tokens
    
@dataclass
class AgentManifest:
    """Agent manifest for Coral Registry registration"""
    agent_id: str
    name: str
    description: str
    version: str
    capabilities: List[AgentCapability]
    pricing: Dict[str, float]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class CoreSenseAgentRegistry:
    """CoreSense Agent Registry for Coral Protocol integration"""
    
    def __init__(self):
        self.registered_agents = {}
        self.agent_manifests = []
        
    def create_fabric_sensor_manifest(self) -> AgentManifest:
        """Create manifest for fabric sensor agent"""
        capabilities = [
            AgentCapability(
                name="muscle_activation_analysis",
                description="Analyze muscle activation patterns from exercise data",
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
                        "muscle_zones": {
                            "type": "object",
                            "properties": {
                                "deep_core": {"type": "number"},
                                "obliques": {"type": "number"},
                                "lower_back": {"type": "number"},
                                "upper_abs": {"type": "number"},
                                "hip_flexors": {"type": "number"},
                                "glutes": {"type": "number"}
                            }
                        },
                        "compensation_detected": {"type": "boolean"},
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    }
                },
                pricing=0.05
            ),
            AgentCapability(
                name="compensation_detection",
                description="Detect muscle compensation patterns and form issues",
                input_schema={
                    "type": "object",
                    "properties": {
                        "muscle_activation": {"type": "object"},
                        "exercise_type": {"type": "string"}
                    },
                    "required": ["muscle_activation", "exercise_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "compensation_score": {"type": "number"},
                        "issues_detected": {"type": "array", "items": {"type": "string"}},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]}
                    }
                },
                pricing=0.03
            )
        ]
        
        return AgentManifest(
            agent_id="coresense-fabric-sensor",
            name="CoreSense Fabric Sensor Agent",
            description="AI-powered fabric sensor simulation for core muscle activation analysis",
            version="1.0.0",
            capabilities=capabilities,
            pricing={
                "per_analysis": 0.05,
                "subscription_hourly": 2.50,
                "subscription_daily": 15.00
            },
            metadata={
                "tags": ["fitness", "core-training", "muscle-analysis", "compensation-detection"],
                "category": "health-wellness",
                "supported_exercises": ["plank", "bridge", "deadbug", "birddog"],
                "accuracy_rating": 0.94,
                "response_time_ms": 150
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def create_coaching_agent_manifest(self) -> AgentManifest:
        """Create manifest for AI coaching agent"""
        capabilities = [
            AgentCapability(
                name="personalized_coaching",
                description="Provide personalized fitness coaching based on muscle activation data",
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
                pricing=0.10
            ),
            AgentCapability(
                name="progress_analysis",
                description="Analyze user progress and provide insights",
                input_schema={
                    "type": "object",
                    "properties": {
                        "historical_data": {"type": "array"},
                        "timeframe": {"type": "string"}
                    },
                    "required": ["historical_data"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "progress_score": {"type": "number"},
                        "improvements": {"type": "array", "items": {"type": "string"}},
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    }
                },
                pricing=0.15
            )
        ]
        
        return AgentManifest(
            agent_id="coresense-ai-coach",
            name="CoreSense AI Coaching Agent",
            description="Intelligent fitness coaching with real-time feedback and personalization",
            version="1.0.0",
            capabilities=capabilities,
            pricing={
                "per_session": 0.25,
                "subscription_weekly": 12.00,
                "subscription_monthly": 49.00
            },
            metadata={
                "tags": ["coaching", "ai", "fitness", "personalization", "real-time"],
                "category": "health-wellness",
                "specialties": ["core-training", "form-correction", "progress-tracking"],
                "coaching_style": "adaptive",
                "experience_level": "beginner-to-advanced"
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def create_orchestrator_manifest(self) -> AgentManifest:
        """Create manifest for multi-agent orchestration"""
        capabilities = [
            AgentCapability(
                name="multi_agent_coordination",
                description="Coordinate multiple fitness agents for comprehensive training",
                input_schema={
                    "type": "object",
                    "properties": {
                        "workout_plan": {"type": "object"},
                        "available_agents": {"type": "array"},
                        "user_preferences": {"type": "object"}
                    },
                    "required": ["workout_plan"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "orchestration_plan": {"type": "object"},
                        "agent_assignments": {"type": "array"},
                        "execution_timeline": {"type": "object"}
                    }
                },
                pricing=0.20
            ),
            AgentCapability(
                name="session_management",
                description="Manage training sessions across multiple agents",
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_config": {"type": "object"},
                        "participant_agents": {"type": "array"}
                    },
                    "required": ["session_config"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "status": {"type": "string"},
                        "metrics": {"type": "object"}
                    }
                },
                pricing=0.30
            )
        ]
        
        return AgentManifest(
            agent_id="coresense-orchestrator",
            name="CoreSense Multi-Agent Orchestrator",
            description="Intelligent orchestration of fitness coaching agents for comprehensive training",
            version="1.0.0",
            capabilities=capabilities,
            pricing={
                "per_session": 0.50,
                "subscription_monthly": 99.00,
                "enterprise_monthly": 299.00
            },
            metadata={
                "tags": ["orchestration", "multi-agent", "coordination", "enterprise"],
                "category": "agent-management",
                "max_concurrent_agents": 10,
                "session_types": ["individual", "group", "team"],
                "integration_apis": ["coral", "mcp", "rest"]
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def register_all_agents(self) -> List[AgentManifest]:
        """Register all CoreSense agents in the registry"""
        manifests = [
            self.create_fabric_sensor_manifest(),
            self.create_coaching_agent_manifest(),
            self.create_orchestrator_manifest()
        ]
        
        for manifest in manifests:
            self.registered_agents[manifest.agent_id] = manifest
            self.agent_manifests.append(manifest)
        
        return manifests
    
    def get_registry_export(self) -> Dict[str, Any]:
        """Export registry data for Coral Protocol integration"""
        return {
            "registry_version": "1.0.0",
            "platform": "CoreSense AI Platform",
            "provider": "CoreSense Technologies",
            "total_agents": len(self.agent_manifests),
            "agents": [asdict(manifest) for manifest in self.agent_manifests],
            "export_timestamp": datetime.now().isoformat(),
            "coral_protocol_version": "v1",
            "payment_network": "solana"
        }
    
    def save_registry_file(self, filepath: str = "coral_registry.json"):
        """Save registry to JSON file"""
        registry_data = self.get_registry_export()
        with open(filepath, 'w') as f:
            json.dump(registry_data, f, indent=2)
        return filepath
    
    def find_agents_by_capability(self, capability_name: str) -> List[AgentManifest]:
        """Find agents that have a specific capability"""
        matching_agents = []
        for manifest in self.agent_manifests:
            for capability in manifest.capabilities:
                if capability.name == capability_name:
                    matching_agents.append(manifest)
                    break
        return matching_agents
    
    def get_agent_pricing(self, agent_id: str, pricing_model: str = "per_session") -> Optional[float]:
        """Get pricing for a specific agent"""
        if agent_id in self.registered_agents:
            manifest = self.registered_agents[agent_id]
            return manifest.pricing.get(pricing_model)
        return None

# Initialize global registry
coresense_registry = CoreSenseAgentRegistry()