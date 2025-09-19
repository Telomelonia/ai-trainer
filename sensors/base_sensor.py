#!/usr/bin/env python3
"""
Base Sensor Interface
Core Training AI Ecosystem - Multi-Sensor Platform

Abstract base class that defines the interface all sensors must implement.
This ensures compatibility across different sensor types (IMU, EMG, pressure).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

class SensorData:
    """Standard data structure for sensor readings"""
    
    def __init__(self, sensor_type: str, timestamp: datetime, data: Dict[str, Any], 
                 metadata: Optional[Dict[str, Any]] = None):
        self.sensor_type = sensor_type
        self.timestamp = timestamp
        self.data = data
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'sensor_type': self.sensor_type,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

class BaseSensor(ABC):
    """
    Abstract base class for all sensor types.
    
    This defines the interface that all sensors (IMU, EMG, pressure, etc.)
    must implement to work with the Core Training AI system.
    """
    
    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sensor
        
        Args:
            sensor_id: Unique identifier for this sensor instance
            config: Sensor-specific configuration parameters
        """
        self.sensor_id = sensor_id
        self.config = config or {}
        self.is_connected = False
        self.is_calibrated = False
        self.last_reading = None
        self.error_count = 0
        
    @property
    @abstractmethod
    def sensor_type(self) -> str:
        """Return the sensor type identifier"""
        pass
    
    @property
    @abstractmethod
    def supported_metrics(self) -> List[str]:
        """Return list of metrics this sensor can provide"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the sensor hardware
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the sensor hardware
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def calibrate(self) -> bool:
        """
        Calibrate the sensor
        
        Returns:
            bool: True if calibration successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_data(self) -> SensorData:
        """
        Get current sensor reading
        
        Returns:
            SensorData: Current sensor reading in standard format
        """
        pass
    
    @abstractmethod
    async def start_streaming(self, callback=None) -> bool:
        """
        Start continuous data streaming
        
        Args:
            callback: Optional callback function for streaming data
            
        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop_streaming(self) -> bool:
        """
        Stop continuous data streaming
        
        Returns:
            bool: True if streaming stopped successfully, False otherwise
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get sensor status information
        
        Returns:
            Dict containing sensor status
        """
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'is_connected': self.is_connected,
            'is_calibrated': self.is_calibrated,
            'error_count': self.error_count,
            'last_reading_time': self.last_reading.timestamp.isoformat() if self.last_reading else None,
            'config': self.config
        }
    
    def reset_errors(self):
        """Reset error count"""
        self.error_count = 0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform sensor health check
        
        Returns:
            Dict containing health status
        """
        health_status = {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'healthy': True,
            'issues': []
        }
        
        if not self.is_connected:
            health_status['healthy'] = False
            health_status['issues'].append('Sensor not connected')
        
        if not self.is_calibrated:
            health_status['healthy'] = False
            health_status['issues'].append('Sensor not calibrated')
        
        if self.error_count > 5:
            health_status['healthy'] = False
            health_status['issues'].append(f'High error count: {self.error_count}')
        
        return health_status

class SensorFactory:
    """Factory class for creating sensor instances"""
    
    _sensor_classes = {}
    
    @classmethod
    def register_sensor(cls, sensor_type: str, sensor_class):
        """Register a sensor class"""
        cls._sensor_classes[sensor_type] = sensor_class
    
    @classmethod
    def create_sensor(cls, sensor_type: str, sensor_id: str, 
                     config: Optional[Dict[str, Any]] = None) -> BaseSensor:
        """
        Create a sensor instance
        
        Args:
            sensor_type: Type of sensor to create
            sensor_id: Unique identifier for the sensor
            config: Sensor configuration
            
        Returns:
            BaseSensor: Sensor instance
            
        Raises:
            ValueError: If sensor type is not registered
        """
        if sensor_type not in cls._sensor_classes:
            available = list(cls._sensor_classes.keys())
            raise ValueError(f"Unknown sensor type '{sensor_type}'. Available: {available}")
        
        sensor_class = cls._sensor_classes[sensor_type]
        return sensor_class(sensor_id, config)
    
    @classmethod
    def get_available_sensor_types(cls) -> List[str]:
        """Get list of available sensor types"""
        return list(cls._sensor_classes.keys())