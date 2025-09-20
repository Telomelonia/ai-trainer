"""
CoreSense Coral Protocol Integration
Complete Internet of Agents integration for CoreSense AI Platform
"""

from .agent_registry import coresense_registry, CoreSenseAgentRegistry
from .coral_client import coral_client, CoralProtocolClient
from .solana_payments import solana_payment_service, SolanaPaymentService
from .agent_communication import agent_communication, AgentCommunicationProtocol
from .multi_agent_orchestrator import multi_agent_orchestrator, MultiAgentOrchestrator
from .rentable_agents import rentable_agent_marketplace, RentableAgentMarketplace
from .coral_studio_integration import coral_studio, CoralStudioIntegration
from .composable_agents import composable_agent_system, ComposableAgentSystem

# Version information
__version__ = "1.0.0"
__author__ = "CoreSense Technologies"
__description__ = "Internet of Agents integration for CoreSense AI Platform"

# Initialize integrated system
def initialize_coral_integration():
    """Initialize the complete Coral Protocol integration"""
    
    # Initialize dependencies
    global multi_agent_orchestrator, composable_agent_system, rentable_agent_marketplace
    
    # Set up communication protocol
    multi_agent_orchestrator.communication = agent_communication
    
    # Set up composable system
    composable_agent_system.communication = agent_communication
    composable_agent_system.orchestrator = multi_agent_orchestrator
    
    # Set up marketplace
    rentable_agent_marketplace.payment_service = solana_payment_service
    
    # Register CoreSense agents
    coresense_registry.register_all_agents()
    
    return {
        "registry": coresense_registry,
        "client": coral_client,
        "payments": solana_payment_service,
        "communication": agent_communication,
        "orchestrator": multi_agent_orchestrator,
        "marketplace": rentable_agent_marketplace,
        "studio": coral_studio,
        "composable": composable_agent_system
    }

# Export main components
__all__ = [
    "coresense_registry",
    "coral_client", 
    "solana_payment_service",
    "agent_communication",
    "multi_agent_orchestrator",
    "rentable_agent_marketplace",
    "coral_studio",
    "composable_agent_system",
    "initialize_coral_integration"
]