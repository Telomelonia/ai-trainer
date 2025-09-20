#!/usr/bin/env python3
"""
Fabric Sensor Simulation Agent
CoreSense AI Platform

Simulates smart compression band with 6 pressure sensors
mapping core muscle activation patterns.
"""

import asyncio
import random
import logging
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fabric-sensor-agent")

class FabricSensorAgent:
    """
    Simulates CoreSense smart compression band
    6-zone pressure sensor array for muscle activation tracking
    """
    
    def __init__(self, user_profile: Dict = None):
        self.user_profile = user_profile or {}
        self.sensor_zones = {
            'upper_rectus': {'position': 'upper_abs', 'baseline': 0.0},
            'lower_rectus': {'position': 'lower_abs', 'baseline': 0.0},
            'right_oblique': {'position': 'right_side', 'baseline': 0.0},
            'left_oblique': {'position': 'left_side', 'baseline': 0.0},
            'transverse': {'position': 'deep_core', 'baseline': 0.0},
            'erector_spinae': {'position': 'lower_back', 'baseline': 0.0}
        }
        self.is_calibrated = False
        self.exercise_mode = "idle"
        self.session_data = []
        
    async def calibrate_sensors(self) -> Dict[str, Any]:
        """
        Calibrate fabric sensors to user's resting muscle tone
        Essential for accurate muscle activation measurement
        """
        logger.info("🔧 Starting CoreSense fabric sensor calibration...")
        
        calibration_data = {}
        for zone, config in self.sensor_zones.items():
            # Simulate calibration process with realistic baseline values
            await asyncio.sleep(0.1)  # Simulate sensor reading time
            baseline = random.uniform(0.1, 0.3)  # Resting muscle tone
            config['baseline'] = baseline
            calibration_data[zone] = {
                'baseline_pressure': baseline,
                'sensitivity': random.uniform(0.8, 1.2),
                'position': config['position']
            }
            
        self.is_calibrated = True
        logger.info("✅ CoreSense sensors calibrated successfully")
        return {
            'status': 'calibrated',
            'zones': calibration_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def start_exercise_monitoring(self, exercise_type: str) -> Dict[str, Any]:
        """
        Begin real-time muscle activation monitoring
        """
        if not self.is_calibrated:
            await self.calibrate_sensors()
            
        self.exercise_mode = exercise_type
        logger.info(f"🏃‍♂️ Starting muscle monitoring for: {exercise_type}")
        
        return {
            'status': 'monitoring_started',
            'exercise': exercise_type,
            'zones_active': list(self.sensor_zones.keys()),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_realtime_muscle_data(self) -> Dict[str, Any]:
        """
        Generate realistic muscle activation patterns
        Based on exercise type and user profile
        """
        if not self.is_calibrated:
            return {'error': 'Sensors not calibrated'}
            
        muscle_data = {}
        
        # Generate exercise-specific activation patterns
        if self.exercise_mode == "plank":
            muscle_data = await self._simulate_plank_activation()
        elif self.exercise_mode == "side_plank":
            muscle_data = await self._simulate_side_plank_activation()
        elif self.exercise_mode == "dead_bug":
            muscle_data = await self._simulate_dead_bug_activation()
        elif self.exercise_mode == "bird_dog":
            muscle_data = await self._simulate_bird_dog_activation()
        else:
            muscle_data = await self._simulate_idle_state()
            
        # Add timestamp and session tracking
        reading = {
            'timestamp': datetime.now().isoformat(),
            'exercise': self.exercise_mode,
            'muscle_activation': muscle_data,
            'overall_stability': self._calculate_stability_score(muscle_data),
            'form_analysis': self._analyze_form(muscle_data)
        }
        
        self.session_data.append(reading)
        return reading
    
    async def _simulate_plank_activation(self) -> Dict[str, float]:
        """Simulate muscle activation during plank exercise"""
        return {
            'upper_rectus': random.uniform(0.6, 0.9),    # High activation
            'lower_rectus': random.uniform(0.7, 0.95),   # Very high activation
            'right_oblique': random.uniform(0.4, 0.7),   # Moderate activation
            'left_oblique': random.uniform(0.4, 0.7),    # Moderate activation
            'transverse': random.uniform(0.8, 1.0),      # Maximum activation
            'erector_spinae': random.uniform(0.5, 0.8)   # High activation
        }
    
    async def _simulate_side_plank_activation(self) -> Dict[str, float]:
        """Simulate muscle activation during side plank"""
        # Asymmetric activation pattern
        return {
            'upper_rectus': random.uniform(0.3, 0.6),
            'lower_rectus': random.uniform(0.4, 0.7),
            'right_oblique': random.uniform(0.8, 1.0),   # Primary mover
            'left_oblique': random.uniform(0.2, 0.4),    # Support
            'transverse': random.uniform(0.7, 0.9),
            'erector_spinae': random.uniform(0.6, 0.8)
        }
    
    async def _simulate_dead_bug_activation(self) -> Dict[str, float]:
        """Simulate muscle activation during dead bug exercise"""
        return {
            'upper_rectus': random.uniform(0.4, 0.7),
            'lower_rectus': random.uniform(0.6, 0.8),
            'right_oblique': random.uniform(0.5, 0.8),
            'left_oblique': random.uniform(0.5, 0.8),
            'transverse': random.uniform(0.9, 1.0),      # Core stability focus
            'erector_spinae': random.uniform(0.3, 0.5)
        }
    
    async def _simulate_bird_dog_activation(self) -> Dict[str, float]:
        """Simulate muscle activation during bird dog exercise"""
        return {
            'upper_rectus': random.uniform(0.3, 0.6),
            'lower_rectus': random.uniform(0.4, 0.7),
            'right_oblique': random.uniform(0.6, 0.9),
            'left_oblique': random.uniform(0.6, 0.9),
            'transverse': random.uniform(0.8, 1.0),
            'erector_spinae': random.uniform(0.7, 0.95)  # High back activation
        }
    
    async def _simulate_idle_state(self) -> Dict[str, float]:
        """Simulate resting muscle tone"""
        return {
            zone: config['baseline'] + random.uniform(-0.05, 0.05)
            for zone, config in self.sensor_zones.items()
        }
    
    def _calculate_stability_score(self, muscle_data: Dict[str, float]) -> float:
        """
        Calculate overall core stability score (0-100)
        Based on muscle activation balance and intensity
        """
        # Check for balanced activation
        values = list(muscle_data.values())
        avg_activation = sum(values) / len(values)
        activation_variance = sum((x - avg_activation) ** 2 for x in values) / len(values)
        
        # Penalize excessive imbalance
        balance_score = max(0, 1 - (activation_variance * 2))
        
        # Reward appropriate activation levels for exercise
        intensity_score = min(1, avg_activation)
        
        # Combined stability score
        stability = (balance_score * 0.6 + intensity_score * 0.4) * 100
        return round(stability, 1)
    
    def _analyze_form(self, muscle_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze exercise form based on muscle activation patterns
        """
        analysis = {
            'form_score': 85,  # Default good form
            'issues': [],
            'recommendations': []
        }
        
        # Check for common form issues
        if muscle_data.get('transverse', 0) < 0.5:
            analysis['issues'].append("Insufficient deep core activation")
            analysis['recommendations'].append("Focus on drawing belly button to spine")
            analysis['form_score'] -= 10
            
        # Check for muscle imbalances
        left_right_diff = abs(muscle_data.get('left_oblique', 0) - muscle_data.get('right_oblique', 0))
        if left_right_diff > 0.3:
            analysis['issues'].append("Left-right muscle imbalance detected")
            analysis['recommendations'].append("Focus on even weight distribution")
            analysis['form_score'] -= 5
            
        if muscle_data.get('erector_spinae', 0) > 0.9 and self.exercise_mode == "plank":
            analysis['issues'].append("Excessive back arch - hip position")
            analysis['recommendations'].append("Lower hips slightly, engage glutes")
            analysis['form_score'] -= 8
            
        return analysis
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive session analytics
        """
        if not self.session_data:
            return {'error': 'No session data available'}
            
        # Calculate session metrics
        stability_scores = [reading['overall_stability'] for reading in self.session_data]
        avg_stability = sum(stability_scores) / len(stability_scores)
        
        # Muscle activation averages
        muscle_averages = {}
        for zone in self.sensor_zones.keys():
            activations = [reading['muscle_activation'][zone] for reading in self.session_data]
            muscle_averages[zone] = sum(activations) / len(activations)
            
        return {
            'session_duration': len(self.session_data),
            'average_stability': round(avg_stability, 1),
            'muscle_activation_averages': muscle_averages,
            'stability_trend': stability_scores[-10:],  # Last 10 readings
            'exercise_type': self.exercise_mode,
            'total_readings': len(self.session_data),
            'timestamp': datetime.now().isoformat()
        }
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop exercise monitoring and return session summary
        """
        logger.info("⏹️ Stopping CoreSense muscle monitoring")
        summary = await self.get_session_summary()
        self.exercise_mode = "idle"
        return {
            'status': 'monitoring_stopped',
            'session_summary': summary
        }

# Integration with existing sensor system
class CoreSenseFabricSensor:
    """
    Integration wrapper for existing sensor framework
    """
    
    def __init__(self):
        self.agent = FabricSensorAgent()
        self.is_active = False
        
    async def initialize(self) -> bool:
        """Initialize the fabric sensor system"""
        try:
            await self.agent.calibrate_sensors()
            self.is_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize CoreSense fabric sensors: {e}")
            return False
    
    async def start_exercise(self, exercise_type: str) -> Dict[str, Any]:
        """Start exercise monitoring"""
        if not self.is_active:
            await self.initialize()
        return await self.agent.start_exercise_monitoring(exercise_type)
    
    async def get_data(self) -> Dict[str, Any]:
        """Get real-time muscle activation data"""
        return await self.agent.get_realtime_muscle_data()
    
    async def stop_exercise(self) -> Dict[str, Any]:
        """Stop exercise and get summary"""
        return await self.agent.stop_monitoring()

# Export for main application
__all__ = ['FabricSensorAgent', 'CoreSenseFabricSensor']