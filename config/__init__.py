"""
Configuration Package
Core Training AI Ecosystem - Multi-Sensor Platform

Centralized configuration management for the entire system.
"""

from .sensor_config import (
    DEMO_MODE, SIMULATION_MODE, ACTIVE_SENSORS, DEMO_SCENARIOS,
    get_active_sensor_config, get_enabled_sensors, get_demo_scenario,
    is_sensor_enabled, get_sensor_type
)

__all__ = [
    'DEMO_MODE', 'SIMULATION_MODE', 'ACTIVE_SENSORS', 'DEMO_SCENARIOS',
    'get_active_sensor_config', 'get_enabled_sensors', 'get_demo_scenario',
    'is_sensor_enabled', 'get_sensor_type'
]