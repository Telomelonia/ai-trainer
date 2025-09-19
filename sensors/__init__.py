"""
Sensor Abstraction Layer
Core Training AI Ecosystem - Multi-Sensor Platform

This module provides a unified interface for different sensor types,
allowing the AI system to work with any sensor hardware.
"""

from .base_sensor import BaseSensor, SensorData, SensorFactory
from .imu_sensor import IMUSensor
from .emg_sensor import EMGSensor
from .pressure_sensor import PressureSensor

__all__ = ['BaseSensor', 'SensorData', 'SensorFactory', 'IMUSensor', 'EMGSensor', 'PressureSensor']