#!/usr/bin/env python3
"""
IMU Sensor Implementation
Core Training AI Ecosystem - Multi-Sensor Platform

Implements IMU (Inertial Measurement Unit) sensor for core stability monitoring.
Supports both real hardware (Arduino Nano 33 BLE) and simulation mode.
"""

import asyncio
import random
import math
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from .base_sensor import BaseSensor, SensorData, SensorFactory

class IMUSensor(BaseSensor):
    """
    IMU sensor implementation for core stability monitoring.
    
    Provides 9-axis sensor data: accelerometer, gyroscope, magnetometer
    Used for analyzing core stability, balance, and movement patterns.
    """
    
    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)
        
        # IMU-specific configuration
        self.sample_rate = config.get('sample_rate', 50) if config else 50  # Hz
        self.simulation_mode = config.get('simulation_mode', True) if config else True
        self.arduino_port = config.get('arduino_port', '/dev/ttyUSB0') if config else '/dev/ttyUSB0'
        
        # Calibration data
        self.calibration_data = {
            'accel_offset': [0.0, 0.0, 0.0],
            'gyro_offset': [0.0, 0.0, 0.0],
            'mag_offset': [0.0, 0.0, 0.0]
        }
        
        # Streaming state
        self.streaming = False
        self.stream_callback = None
        
        # Simulation state
        self.sim_time = 0.0
        self.base_stability = 85.0
        
    @property
    def sensor_type(self) -> str:
        return "imu"
    
    @property
    def supported_metrics(self) -> List[str]:
        return [
            "acceleration_x", "acceleration_y", "acceleration_z",
            "gyro_x", "gyro_y", "gyro_z", 
            "magnetometer_x", "magnetometer_y", "magnetometer_z",
            "stability_score", "balance_score", "movement_quality"
        ]
    
    async def connect(self) -> bool:
        """Connect to IMU sensor"""
        try:
            if self.simulation_mode:
                # Simulate connection delay
                await asyncio.sleep(0.1)
                self.is_connected = True
                print(f"IMU sensor {self.sensor_id} connected in simulation mode")
                return True
            else:
                # Real hardware connection logic would go here
                # For now, we'll simulate this
                try:
                    import serial
                    # This would be the real hardware connection
                    # self.serial_connection = serial.Serial(self.arduino_port, 9600)
                    self.is_connected = True
                    print(f"IMU sensor {self.sensor_id} connected to hardware")
                    return True
                except ImportError:
                    print("pyserial not available, falling back to simulation mode")
                    self.simulation_mode = True
                    self.is_connected = True
                    return True
                except Exception as e:
                    print(f"Failed to connect to hardware: {e}")
                    return False
        
        except Exception as e:
            print(f"IMU connection error: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from IMU sensor"""
        try:
            if hasattr(self, 'serial_connection'):
                self.serial_connection.close()
            
            self.is_connected = False
            self.streaming = False
            print(f"IMU sensor {self.sensor_id} disconnected")
            return True
        
        except Exception as e:
            print(f"IMU disconnection error: {e}")
            self.error_count += 1
            return False
    
    async def calibrate(self) -> bool:
        """Calibrate the IMU sensor"""
        try:
            print(f"Calibrating IMU sensor {self.sensor_id}...")
            
            if self.simulation_mode:
                # Simulate calibration process
                await asyncio.sleep(1.0)
                
                # Generate simulated calibration offsets
                self.calibration_data['accel_offset'] = [
                    random.uniform(-0.1, 0.1) for _ in range(3)
                ]
                self.calibration_data['gyro_offset'] = [
                    random.uniform(-0.05, 0.05) for _ in range(3)
                ]
                self.calibration_data['mag_offset'] = [
                    random.uniform(-5.0, 5.0) for _ in range(3)
                ]
            else:
                # Real calibration would collect baseline readings
                calibration_samples = 100
                accel_sum = [0.0, 0.0, 0.0]
                gyro_sum = [0.0, 0.0, 0.0]
                
                for _ in range(calibration_samples):
                    # Collect calibration data from hardware
                    await asyncio.sleep(0.01)  # 100Hz sampling
                    # Real hardware reading would go here
                
                # Calculate offsets (simplified)
                self.calibration_data['accel_offset'] = [x/calibration_samples for x in accel_sum]
                self.calibration_data['gyro_offset'] = [x/calibration_samples for x in gyro_sum]
            
            self.is_calibrated = True
            print(f"IMU sensor {self.sensor_id} calibration complete")
            return True
        
        except Exception as e:
            print(f"IMU calibration error: {e}")
            self.error_count += 1
            return False
    
    async def get_data(self) -> SensorData:
        """Get current IMU reading"""
        try:
            if not self.is_connected:
                raise Exception("Sensor not connected")
            
            timestamp = datetime.now()
            
            if self.simulation_mode:
                data = self._generate_simulation_data()
            else:
                data = await self._read_hardware_data()
            
            sensor_data = SensorData(
                sensor_type=self.sensor_type,
                timestamp=timestamp,
                data=data,
                metadata={
                    'sensor_id': self.sensor_id,
                    'sample_rate': self.sample_rate,
                    'calibrated': self.is_calibrated,
                    'simulation_mode': self.simulation_mode
                }
            )
            
            self.last_reading = sensor_data
            return sensor_data
        
        except Exception as e:
            print(f"IMU data reading error: {e}")
            self.error_count += 1
            raise
    
    def _generate_simulation_data(self) -> Dict[str, Any]:
        """Generate realistic simulation data"""
        self.sim_time += 1.0 / self.sample_rate
        
        # Base movement with realistic noise and patterns
        time_factor = self.sim_time * 0.5
        
        # Simulate core exercise patterns
        stability_variation = math.sin(time_factor * 0.3) * 5.0  # Slow stability changes
        balance_variation = math.cos(time_factor * 0.7) * 3.0   # Balance adjustments
        
        # Add realistic noise
        noise_level = 0.1
        
        # Accelerometer data (m/s²) - includes gravity
        accel_x = random.uniform(-0.5, 0.5) + random.gauss(0, noise_level)
        accel_y = random.uniform(-0.5, 0.5) + random.gauss(0, noise_level)
        accel_z = 9.81 + random.uniform(-0.2, 0.2) + random.gauss(0, noise_level)
        
        # Gyroscope data (degrees/sec)
        gyro_x = random.uniform(-2.0, 2.0) + random.gauss(0, noise_level)
        gyro_y = random.uniform(-2.0, 2.0) + random.gauss(0, noise_level)
        gyro_z = random.uniform(-1.0, 1.0) + random.gauss(0, noise_level)
        
        # Magnetometer data (μT)
        mag_x = 25.0 + random.uniform(-5.0, 5.0)
        mag_y = 15.0 + random.uniform(-5.0, 5.0)
        mag_z = -35.0 + random.uniform(-5.0, 5.0)
        
        # Calculate derived metrics
        total_acceleration = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        total_rotation = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
        
        # Stability score (0-100)
        movement_penalty = min(total_rotation * 5, 20)  # Penalize excessive movement
        stability_score = max(0, min(100, 
            self.base_stability + stability_variation - movement_penalty
        ))
        
        # Balance score (0-100)
        lateral_tilt = abs(accel_x) + abs(accel_y)
        balance_score = max(0, min(100, 95 - lateral_tilt * 10 + balance_variation))
        
        # Movement quality assessment
        if stability_score > 90:
            movement_quality = "Excellent"
        elif stability_score > 75:
            movement_quality = "Good"
        elif stability_score > 60:
            movement_quality = "Fair"
        else:
            movement_quality = "Needs Improvement"
        
        return {
            # Raw IMU data
            "acceleration_x": round(accel_x, 3),
            "acceleration_y": round(accel_y, 3),
            "acceleration_z": round(accel_z, 3),
            "gyro_x": round(gyro_x, 3),
            "gyro_y": round(gyro_y, 3),
            "gyro_z": round(gyro_z, 3),
            "magnetometer_x": round(mag_x, 1),
            "magnetometer_y": round(mag_y, 1),
            "magnetometer_z": round(mag_z, 1),
            
            # Derived metrics
            "total_acceleration": round(total_acceleration, 3),
            "total_rotation": round(total_rotation, 3),
            "stability_score": round(stability_score, 1),
            "balance_score": round(balance_score, 1),
            "movement_quality": movement_quality,
            
            # Analysis
            "is_stable": stability_score > 75,
            "is_balanced": balance_score > 80,
            "lateral_tilt": round(lateral_tilt, 3),
            "movement_variance": round(total_rotation, 3)
        }
    
    async def _read_hardware_data(self) -> Dict[str, Any]:
        """Read data from actual hardware"""
        # This would contain the real hardware reading logic
        # For now, return simulation data as placeholder
        return self._generate_simulation_data()
    
    async def start_streaming(self, callback=None) -> bool:
        """Start continuous data streaming"""
        try:
            if not self.is_connected:
                return False
            
            self.streaming = True
            self.stream_callback = callback
            
            # Start streaming task
            asyncio.create_task(self._stream_data())
            
            print(f"IMU sensor {self.sensor_id} streaming started at {self.sample_rate}Hz")
            return True
        
        except Exception as e:
            print(f"IMU streaming start error: {e}")
            self.error_count += 1
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop continuous data streaming"""
        try:
            self.streaming = False
            self.stream_callback = None
            print(f"IMU sensor {self.sensor_id} streaming stopped")
            return True
        
        except Exception as e:
            print(f"IMU streaming stop error: {e}")
            self.error_count += 1
            return False
    
    async def _stream_data(self):
        """Internal streaming loop"""
        interval = 1.0 / self.sample_rate
        
        while self.streaming and self.is_connected:
            try:
                data = await self.get_data()
                
                if self.stream_callback:
                    await self.stream_callback(data)
                
                await asyncio.sleep(interval)
            
            except Exception as e:
                print(f"Streaming error: {e}")
                self.error_count += 1
                if self.error_count > 10:
                    print("Too many streaming errors, stopping...")
                    break
        
        self.streaming = False

# Register IMU sensor with factory
SensorFactory.register_sensor("imu", IMUSensor)