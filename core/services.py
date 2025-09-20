"""
CoreSense AI Platform - Service Manager
Centralized service initialization and management
"""

from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from core.config import get_config
from core.logging import get_logger
from core.exceptions import CoreSenseError
from core.utils import import_module_safely, setup_import_paths

logger = get_logger(__name__)


@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    available: bool
    initialized: bool
    error: Optional[str] = None
    instance: Optional[Any] = None


class ServiceManager:
    """Centralized service management for CoreSense platform"""
    
    def __init__(self):
        self.config = get_config()
        self._services: Dict[str, ServiceStatus] = {}
        self._setup_paths()
    
    def _setup_paths(self):
        """Setup import paths"""
        setup_import_paths(self.config.base_dir)
    
    def register_service(self, name: str, service_class: Type, **kwargs) -> ServiceStatus:
        """
        Register and initialize a service
        
        Args:
            name: Service name
            service_class: Service class to instantiate
            **kwargs: Arguments for service initialization
            
        Returns:
            ServiceStatus object
        """
        try:
            logger.info(f"Initializing service: {name}")
            instance = service_class(**kwargs)
            
            # Initialize if it has an initialize method
            if hasattr(instance, 'initialize'):
                success = instance.initialize()
                if not success:
                    raise CoreSenseError(f"Service {name} initialization failed")
            
            status = ServiceStatus(
                name=name,
                available=True,
                initialized=True,
                instance=instance
            )
            
            self._services[name] = status
            logger.info(f"✅ Service {name} initialized successfully")
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize service {name}: {e}")
            status = ServiceStatus(
                name=name,
                available=False,
                initialized=False,
                error=str(e)
            )
            self._services[name] = status
            return status
    
    def register_service_from_module(
        self, 
        name: str, 
        module_path: str, 
        class_name: str,
        **kwargs
    ) -> ServiceStatus:
        """
        Register service by dynamically importing from module
        
        Args:
            name: Service name
            module_path: Path to module file
            class_name: Name of class to instantiate
            **kwargs: Arguments for service initialization
            
        Returns:
            ServiceStatus object
        """
        try:
            module = import_module_safely(module_path, name + "_module")
            if module is None:
                raise CoreSenseError(f"Could not import module: {module_path}")
            
            service_class = getattr(module, class_name, None)
            if service_class is None:
                raise CoreSenseError(f"Class {class_name} not found in module {module_path}")
            
            return self.register_service(name, service_class, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Failed to register service {name} from module: {e}")
            status = ServiceStatus(
                name=name,
                available=False,
                initialized=False,
                error=str(e)
            )
            self._services[name] = status
            return status
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get service instance by name
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not available
        """
        status = self._services.get(name)
        if status and status.available and status.initialized:
            return status.instance
        return None
    
    def get_service_status(self, name: str) -> Optional[ServiceStatus]:
        """
        Get service status by name
        
        Args:
            name: Service name
            
        Returns:
            ServiceStatus or None if not found
        """
        return self._services.get(name)
    
    def is_service_available(self, name: str) -> bool:
        """
        Check if service is available and initialized
        
        Args:
            name: Service name
            
        Returns:
            True if service is available
        """
        status = self._services.get(name)
        return status is not None and status.available and status.initialized
    
    def get_all_services(self) -> Dict[str, ServiceStatus]:
        """Get all registered services"""
        return self._services.copy()
    
    def shutdown_service(self, name: str) -> bool:
        """
        Shutdown a service
        
        Args:
            name: Service name
            
        Returns:
            True if shutdown successful
        """
        try:
            status = self._services.get(name)
            if status and status.instance:
                if hasattr(status.instance, 'shutdown'):
                    status.instance.shutdown()
                status.initialized = False
                logger.info(f"Service {name} shutdown successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error shutting down service {name}: {e}")
            return False
    
    def shutdown_all(self):
        """Shutdown all services"""
        logger.info("Shutting down all services...")
        for name in list(self._services.keys()):
            self.shutdown_service(name)


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


def initialize_core_services() -> ServiceManager:
    """
    Initialize all core services based on configuration
    
    Returns:
        ServiceManager with initialized services
    """
    service_manager = get_service_manager()
    config = get_config()
    
    logger.info("🚀 Initializing CoreSense services...")
    
    # Initialize database service if auth is enabled
    if config.enable_auth:
        try:
            from auth.database_service import DatabaseService
            service_manager.register_service(
                'database',
                DatabaseService,
                database_url=config.database.url
            )
        except ImportError as e:
            logger.warning(f"Database service not available: {e}")
    
    # Initialize authentication service
    if config.enable_auth:
        try:
            from auth.auth_service import AuthService
            service_manager.register_service(
                'auth',
                AuthService
            )
        except ImportError as e:
            logger.warning(f"Auth service not available: {e}")
    
    # Initialize sensor manager if sensors are enabled
    if config.enable_sensors:
        service_manager.register_service_from_module(
            'sensor_manager',
            str(config.base_dir / 'sensors' / '__init__.py'),
            'SensorFactory'
        )
    
    # Initialize agent orchestrator if agents are enabled
    if config.enable_agents:
        service_manager.register_service_from_module(
            'agent_orchestrator',
            str(config.base_dir / 'agents' / 'agent_orchestrator.py'),
            'AgentOrchestrator'
        )
    
    # Initialize core training agent
    if config.enable_agents:
        service_manager.register_service_from_module(
            'core_training_agent',
            str(config.base_dir / 'agents' / 'core_training_agent.py'),
            'CoreTrainingAgent'
        )
    
    # Initialize fabric sensor agent
    if config.enable_agents:
        service_manager.register_service_from_module(
            'fabric_sensor_agent',
            str(config.base_dir / 'agents' / 'fabric_sensor_agent.py'),
            'FabricSensorAgent'
        )
    
    # Initialize coral multi-agent orchestrator for advanced workflows
    if config.enable_agents:
        service_manager.register_service_from_module(
            'coral_orchestrator',
            str(config.base_dir / 'coral_integration' / 'multi_agent_orchestrator.py'),
            'MultiAgentOrchestrator'
        )
    
    # Initialize agent communication protocol for coral integration
    if config.enable_agents:
        service_manager.register_service_from_module(
            'agent_communication',
            str(config.base_dir / 'coral_integration' / 'agent_communication.py'),
            'AgentCommunicationProtocol'
        )
    
    logger.info("✅ Core services initialization completed")
    return service_manager