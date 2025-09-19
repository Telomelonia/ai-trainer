#!/usr/bin/env python3
"""
EMG Sensor Implementation (Planned)
Core Training AI Ecosystem - Multi-Sensor Platform

Implements EMG (Electromyography) sensor for muscle activation monitoring.
Currently a stub implementation showing the planned architecture.
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_sensor import BaseSensor, SensorData, SensorFactory

class EMGSensor(BaseSensor):
    """
    EMG sensor implementation for muscle activation monitoring.
    
    Measures electrical activity in muscles to assess core engagement,
    muscle fatigue, and training effectiveness.
    
    Note: This is currently a planned implementation showing the architecture.
    Hardware integration planned for post-hackathon development.
    """
    
    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)
        
        # EMG-specific configuration
        self.sample_rate = config.get('sample_rate', 1000) if config else 1000  # Hz (higher for EMG)
        self.simulation_mode = True  # Always simulation for now
        self.muscle_groups = config.get('muscle_groups', [
            'rectus_abdominis', 'external_oblique', 'internal_oblique', 
            'transverse_abdominis', 'erector_spinae'
        ]) if config else ['rectus_abdominis', 'external_oblique', 'internal_oblique', 
                          'transverse_abdominis', 'erector_spinae']
        
        # EMG-specific calibration
        self.baseline_emg = {}
        self.max_voluntary_contraction = {}
        
        # Simulation state
        self.sim_time = 0.0
        self.exercise_phase = "rest"  # rest, engagement, hold, release
        
    @property
    def sensor_type(self) -> str:
        return "emg"
    
    @property
    def supported_metrics(self) -> List[str]:
        metrics = []
        for muscle in self.muscle_groups:
            metrics.extend([
                f"{muscle}_emg_raw",
                f"{muscle}_emg_rms", 
                f"{muscle}_activation_percent"
            ])
        
        metrics.extend([
            "core_engagement_score",
            "muscle_fatigue_index",
            "activation_symmetry",
            "training_intensity"
        ])
        
        return metrics
    
    async def connect(self) -> bool:
        """Connect to EMG sensor"""
        try:
            if self.simulation_mode:
                await asyncio.sleep(0.2)  # Simulate connection time
                self.is_connected = True
                print(f"EMG sensor {self.sensor_id} connected in simulation mode")
                print(f"Monitoring muscle groups: {', '.join(self.muscle_groups)}")
                return True
            else:
                # Future hardware connection logic
                print("EMG hardware integration planned for future release")
                return False
        
        except Exception as e:
            print(f"EMG connection error: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from EMG sensor"""
        try:
            self.is_connected = False
            print(f"EMG sensor {self.sensor_id} disconnected")
            return True
        
        except Exception as e:
            print(f"EMG disconnection error: {e}")
            return False
    
    async def calibrate(self) -> bool:
        """Calibrate EMG sensor"""
        try:
            print(f"Calibrating EMG sensor {self.sensor_id}...")
            
            if self.simulation_mode:
                # Simulate calibration phases
                print("Phase 1: Recording baseline muscle activity...")
                await asyncio.sleep(1.0)
                
                print("Phase 2: Maximum voluntary contraction test...")
                await asyncio.sleep(2.0)
                
                # Generate simulated calibration data
                for muscle in self.muscle_groups:
                    self.baseline_emg[muscle] = random.uniform(0.001, 0.005)  # mV
                    self.max_voluntary_contraction[muscle] = random.uniform(0.5, 1.5)  # mV
                
                self.is_calibrated = True
                print("EMG calibration complete")
                return True
            else:
                print("Hardware calibration not yet implemented")
                return False
        
        except Exception as e:
            print(f"EMG calibration error: {e}")
            return False
    
    async def get_data(self) -> SensorData:
        """Get current EMG reading"""
        try:
            if not self.is_connected:
                raise Exception("EMG sensor not connected")
            
            timestamp = datetime.now()
            data = self._generate_simulation_data()
            
            sensor_data = SensorData(
                sensor_type=self.sensor_type,
                timestamp=timestamp,
                data=data,
                metadata={
                    'sensor_id': self.sensor_id,
                    'muscle_groups': self.muscle_groups,
                    'sample_rate': self.sample_rate,
                    'calibrated': self.is_calibrated
                }
            )
            
            self.last_reading = sensor_data
            return sensor_data
        
        except Exception as e:
            print(f"EMG data reading error: {e}")
            self.error_count += 1
            raise
    
    def _generate_simulation_data(self) -> Dict[str, Any]:
        """Generate realistic EMG simulation data"""
        self.sim_time += 1.0 / self.sample_rate
        
        # Simulate exercise phases
        phase_time = self.sim_time % 20.0  # 20-second cycle
        
        if phase_time < 2.0:
            self.exercise_phase = "rest"
            base_activation = 0.1
        elif phase_time < 8.0:
            self.exercise_phase = "engagement"
            base_activation = 0.6 + 0.3 * (phase_time - 2.0) / 6.0
        elif phase_time < 15.0:
            self.exercise_phase = "hold"
            base_activation = 0.8 + 0.1 * random.uniform(-1, 1)
        else:
            self.exercise_phase = "release"
            base_activation = 0.8 - 0.7 * (phase_time - 15.0) / 5.0
        
        data = {}
        muscle_activations = []
        
        # Generate data for each muscle group
        for muscle in self.muscle_groups:
            # Muscle-specific activation patterns
            muscle_factor = {
                'rectus_abdominis': 1.0,
                'external_oblique': 0.8,
                'internal_oblique': 0.7,
                'transverse_abdominis': 0.9,
                'erector_spinae': 0.6
            }.get(muscle, 0.7)
            
            # Raw EMG signal (mV)
            baseline = self.baseline_emg.get(muscle, 0.003)
            max_mvc = self.max_voluntary_contraction.get(muscle, 1.0)
            
            # Add realistic noise and signal characteristics
            noise = random.gauss(0, 0.002)
            signal_variation = random.uniform(0.8, 1.2)
            
            emg_raw = baseline + (max_mvc * base_activation * muscle_factor * signal_variation) + noise
            emg_raw = max(0, emg_raw)  # EMG can't be negative
            
            # RMS (Root Mean Square) - standard EMG processing
            emg_rms = emg_raw * 0.7  # Simplified RMS calculation
            
            # Activation percentage (0-100%)
            activation_percent = min(100, max(0, 
                ((emg_rms - baseline) / max_mvc) * 100
            ))
            
            data[f"{muscle}_emg_raw"] = round(emg_raw, 4)
            data[f"{muscle}_emg_rms"] = round(emg_rms, 4)
            data[f"{muscle}_activation_percent"] = round(activation_percent, 1)
            
            muscle_activations.append(activation_percent)
        
        # Calculate derived metrics
        avg_activation = sum(muscle_activations) / len(muscle_activations)
        
        # Core engagement score (0-100)
        core_muscles = ['rectus_abdominis', 'external_oblique', 'internal_oblique', 'transverse_abdominis']
        core_activations = [
            data[f"{muscle}_activation_percent"] for muscle in core_muscles 
            if muscle in self.muscle_groups
        ]
        core_engagement_score = sum(core_activations) / len(core_activations) if core_activations else 0
        
        # Muscle fatigue index (higher = more fatigued)
        fatigue_factor = min(100, (self.sim_time / 60.0) * 15)  # Fatigue increases over time
        muscle_fatigue_index = fatigue_factor + random.uniform(-5, 5)
        muscle_fatigue_index = max(0, min(100, muscle_fatigue_index))
        
        # Activation symmetry (0-100, higher = more symmetric)
        if len(muscle_activations) > 1:
            activation_std = (sum([(x - avg_activation)**2 for x in muscle_activations]) / len(muscle_activations))**0.5
            activation_symmetry = max(0, 100 - activation_std * 2)
        else:
            activation_symmetry = 100
        
        # Training intensity assessment
        if avg_activation > 80:
            training_intensity = "High"
        elif avg_activation > 60:
            training_intensity = "Moderate"
        elif avg_activation > 30:
            training_intensity = "Light"
        else:
            training_intensity = "Minimal"
        
        # Add summary metrics
        data.update({
            "core_engagement_score": round(core_engagement_score, 1),
            "muscle_fatigue_index": round(muscle_fatigue_index, 1),
            "activation_symmetry": round(activation_symmetry, 1),
            "training_intensity": training_intensity,
            "exercise_phase": self.exercise_phase,
            "average_activation": round(avg_activation, 1)
        })
        
        return data
    
    async def start_streaming(self, callback=None) -> bool:
        """Start EMG data streaming"""
        try:
            if not self.is_connected:
                return False
            
            print(f"EMG streaming started at {self.sample_rate}Hz")
            # EMG streaming implementation would go here
            return True
        
        except Exception as e:
            print(f"EMG streaming error: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop EMG data streaming"""
        try:
            print("EMG streaming stopped")
            return True
        
        except Exception as e:
            print(f"EMG streaming stop error: {e}")
            return False

# Register EMG sensor with factory
SensorFactory.register_sensor("emg", EMGSensor)