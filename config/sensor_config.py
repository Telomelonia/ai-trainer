#!/usr/bin/env python3
"""
Sensor Configuration
Core Training AI Ecosystem - Multi-Sensor Platform

Configuration settings for the multi-sensor architecture.
Supports different deployment modes and sensor combinations.
"""

import os
from typing import Dict, Any, List

# Demo and deployment modes
DEMO_MODE = True  # Set to False when hardware is available
SIMULATION_MODE = True  # Always use simulation for demo reliability

# Active sensor configuration
ACTIVE_SENSORS = {
    "primary_imu": {
        "type": "imu",
        "enabled": True,
        "config": {
            "sample_rate": 50,
            "simulation_mode": SIMULATION_MODE,
            "arduino_port": "/dev/ttyUSB0"
        }
    },
    "emg_muscles": {
        "type": "emg", 
        "enabled": False,  # Planned for post-hackathon
        "config": {
            "sample_rate": 1000,
            "simulation_mode": True,
            "muscle_groups": [
                "rectus_abdominis", 
                "external_oblique", 
                "internal_oblique",
                "transverse_abdominis",
                "erector_spinae"
            ]
        }
    },
    "pressure_zones": {
        "type": "pressure",
        "enabled": False,  # Planned for post-hackathon  
        "config": {
            "sample_rate": 100,
            "simulation_mode": True,
            "sensor_zones": [
                "left_foot", "right_foot",
                "left_hand", "right_hand", 
                "core_front", "core_back"
            ]
        }
    }
}

# Hardware-specific configurations
ARDUINO_CONFIG = {
    "nano_33_ble": {
        "port": "/dev/ttyUSB0",
        "baudrate": 9600,
        "timeout": 1.0,
        "sensor_type": "imu"
    }
}

# Demo configurations for different scenarios
DEMO_SCENARIOS = {
    "basic_stability": {
        "description": "Basic core stability monitoring with IMU",
        "sensors": ["primary_imu"],
        "duration": 300,  # 5 minutes
        "exercises": ["plank", "side_plank", "dead_bug"]
    },
    "advanced_monitoring": {
        "description": "Multi-sensor core training analysis", 
        "sensors": ["primary_imu", "emg_muscles", "pressure_zones"],
        "duration": 900,  # 15 minutes
        "exercises": ["plank", "side_plank", "dead_bug", "bird_dog", "pallof_press"]
    },
    "rehabilitation": {
        "description": "Rehabilitation-focused gentle monitoring",
        "sensors": ["primary_imu"],
        "duration": 600,  # 10 minutes
        "exercises": ["modified_plank", "dead_bug", "bird_dog"]
    }
}

# Sensor data processing settings
PROCESSING_CONFIG = {
    "imu": {
        "filter_cutoff": 10.0,  # Hz
        "stability_threshold": 75.0,  # Score threshold
        "movement_variance_max": 0.5
    },
    "emg": {
        "filter_range": [20.0, 450.0],  # Hz bandpass
        "activation_threshold": 10.0,  # % of MVC
        "fatigue_detection": True
    },
    "pressure": {
        "filter_cutoff": 5.0,  # Hz
        "balance_threshold": 80.0,  # Symmetry score
        "stability_min_pressure": 5.0  # kPa
    }
}

# AI agent integration settings
AGENT_CONFIG = {
    "update_frequency": 2.0,  # seconds
    "coaching_sensitivity": "moderate",  # low, moderate, high
    "real_time_feedback": True,
    "progress_tracking": True
}

# UI configuration
UI_CONFIG = {
    "refresh_rate": 2.0,  # seconds
    "chart_history_points": 20,
    "show_advanced_metrics": False,  # Set True for detailed view
    "auto_refresh": True
}

def get_active_sensor_config(sensor_id: str) -> Dict[str, Any]:
    """Get configuration for a specific sensor"""
    return ACTIVE_SENSORS.get(sensor_id, {})

def get_enabled_sensors() -> List[str]:
    """Get list of currently enabled sensors"""
    return [
        sensor_id for sensor_id, config in ACTIVE_SENSORS.items()
        if config.get("enabled", False)
    ]

def get_demo_scenario(scenario_name: str) -> Dict[str, Any]:
    """Get configuration for a specific demo scenario"""
    return DEMO_SCENARIOS.get(scenario_name, DEMO_SCENARIOS["basic_stability"])

def is_sensor_enabled(sensor_id: str) -> bool:
    """Check if a sensor is enabled"""
    return ACTIVE_SENSORS.get(sensor_id, {}).get("enabled", False)

def get_sensor_type(sensor_id: str) -> str:
    """Get the type of a sensor"""
    return ACTIVE_SENSORS.get(sensor_id, {}).get("type", "unknown")

# Environment-based configuration overrides
def load_environment_config():
    """Load configuration overrides from environment variables"""
    global DEMO_MODE, SIMULATION_MODE
    
    # Check for environment overrides
    if os.getenv("AI_TRAINER_DEMO_MODE"):
        DEMO_MODE = os.getenv("AI_TRAINER_DEMO_MODE").lower() == "true"
    
    if os.getenv("AI_TRAINER_SIMULATION_MODE"):
        SIMULATION_MODE = os.getenv("AI_TRAINER_SIMULATION_MODE").lower() == "true"
    
    # Hardware availability check
    if os.getenv("AI_TRAINER_ARDUINO_PORT"):
        ARDUINO_CONFIG["nano_33_ble"]["port"] = os.getenv("AI_TRAINER_ARDUINO_PORT")

# Initialize configuration
load_environment_config()

# Export key configurations
__all__ = [
    'DEMO_MODE', 'SIMULATION_MODE', 'ACTIVE_SENSORS', 'DEMO_SCENARIOS',
    'get_active_sensor_config', 'get_enabled_sensors', 'get_demo_scenario',
    'is_sensor_enabled', 'get_sensor_type'
]