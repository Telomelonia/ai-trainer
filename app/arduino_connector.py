import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArduinoConnector:
    """
    Arduino connector for Core Training stability sensor
    Falls back to simulation if Arduino not available
    """
    
    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 115200, simulation_mode: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.simulation_mode = simulation_mode
        self.serial_connection = None
        self.is_connected = False
        self.data_callbacks = []
        
        # Simulation parameters
        self.base_stability = 85.0
        self.stability_trend = 0.0
        self.session_start_time = datetime.now()
        
        # Try to establish connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection to Arduino or enable simulation mode"""
        if self.simulation_mode:
            logger.info("Arduino connector initialized in SIMULATION MODE")
            self.is_connected = True
            return
            
        try:
            # Try to import and connect to serial
            import serial
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset
            self.is_connected = True
            logger.info(f"Connected to Arduino on {self.port}")
        except ImportError:
            logger.warning("pyserial not available, switching to simulation mode")
            self.simulation_mode = True
            self.is_connected = True
        except Exception as e:
            logger.warning(f"Failed to connect to Arduino: {e}")
            logger.info("Switching to simulation mode")
            self.simulation_mode = True
            self.is_connected = True
    
    def get_current_stability_data(self) -> Dict[str, Any]:
        """Get current stability data from Arduino or simulation"""
        if self.simulation_mode:
            return self._simulate_stability_data()
        else:
            return self._read_arduino_data()
    
    def _read_arduino_data(self) -> Dict[str, Any]:
        """Read real data from Arduino"""
        try:
            if self.serial_connection and self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()
                data = json.loads(line)
                
                # Process and validate Arduino data
                processed_data = {
                    "timestamp": datetime.now().isoformat(),
                    "stability_score": float(data.get("stability", 0)),
                    "x_acceleration": float(data.get("x_accel", 0)),
                    "y_acceleration": float(data.get("y_accel", 0)),
                    "z_acceleration": float(data.get("z_accel", 0)),
                    "movement_variance": float(data.get("variance", 0)),
                    "source": "arduino"
                }
                
                # Calculate derived metrics
                processed_data.update(self._calculate_derived_metrics(processed_data))
                return processed_data
                
        except Exception as e:
            logger.error(f"Error reading Arduino data: {e}")
            logger.info("Falling back to simulation")
            return self._simulate_stability_data()
    
    def _simulate_stability_data(self) -> Dict[str, Any]:
        """Generate realistic stability data for testing"""
        # Add some realistic trends and variations
        time_factor = (datetime.now() - self.session_start_time).total_seconds()
        
        # Simulate fatigue over time
        fatigue_factor = max(0.7, 1.0 - (time_factor / 600))  # Gradual decline over 10 minutes
        
        # Add random variation
        random_variation = random.uniform(-5, 5)
        
        # Calculate stability score
        current_stability = self.base_stability * fatigue_factor + random_variation
        current_stability = max(50, min(100, current_stability))
        
        # Simulate accelerometer data
        x_accel = random.uniform(-0.5, 0.5)
        y_accel = random.uniform(-0.5, 0.5)
        z_accel = random.uniform(9.5, 10.5)  # Gravity + small variations
        
        # Calculate movement variance
        movement_variance = abs(x_accel) + abs(y_accel) + abs(z_accel - 9.8)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "stability_score": round(current_stability, 1),
            "x_acceleration": round(x_accel, 3),
            "y_acceleration": round(y_accel, 3),
            "z_acceleration": round(z_accel, 3),
            "movement_variance": round(movement_variance, 3),
            "source": "simulation"
        }
        
        # Add derived metrics
        data.update(self._calculate_derived_metrics(data))
        return data
    
    def _calculate_derived_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics from raw sensor data"""
        stability_score = data["stability_score"]
        movement_variance = data["movement_variance"]
        
        # Form quality assessment
        if stability_score > 90:
            form_quality = "Excellent"
            form_color = "green"
        elif stability_score > 75:
            form_quality = "Good"
            form_color = "yellow"
        elif stability_score > 60:
            form_quality = "Fair"
            form_color = "orange"
        else:
            form_quality = "Needs Improvement"
            form_color = "red"
        
        # Session duration
        duration = datetime.now() - self.session_start_time
        duration_str = f"{duration.seconds // 60}:{(duration.seconds % 60):02d}"
        
        # Movement stability classification
        if movement_variance < 0.2:
            stability_level = "Very Stable"
        elif movement_variance < 0.5:
            stability_level = "Stable"
        elif movement_variance < 0.8:
            stability_level = "Moderate"
        else:
            stability_level = "Unstable"
        
        return {
            "form_quality": form_quality,
            "form_color": form_color,
            "session_duration": duration_str,
            "stability_level": stability_level,
            "trend": self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """Calculate stability trend"""
        # Simple trend calculation (would be more sophisticated with real data history)
        if hasattr(self, '_last_stability'):
            current = self.base_stability
            diff = current - self._last_stability
            if diff > 2:
                return "improving"
            elif diff < -2:
                return "declining"
            else:
                return "stable"
        return "stable"
    
    async def start_monitoring(self, callback=None):
        """Start continuous monitoring with optional callback"""
        logger.info("Starting stability monitoring...")
        
        while self.is_connected:
            try:
                data = self.get_current_stability_data()
                
                # Store for trend calculation
                self._last_stability = data["stability_score"]
                
                # Call callback if provided
                if callback:
                    await callback(data)
                
                # Notify all registered callbacks
                for cb in self.data_callbacks:
                    try:
                        await cb(data)
                    except Exception as e:
                        logger.error(f"Error in data callback: {e}")
                
                # Wait before next reading
                await asyncio.sleep(1)  # 1 Hz sampling rate
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def add_data_callback(self, callback):
        """Add a callback function to be called when new data is available"""
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback):
        """Remove a data callback"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def reset_session(self):
        """Reset session timing and statistics"""
        self.session_start_time = datetime.now()
        self.base_stability = 85.0
        logger.info("Training session reset")
    
    def close(self):
        """Close the connection"""
        if self.serial_connection:
            self.serial_connection.close()
        self.is_connected = False
        logger.info("Arduino connector closed")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "connected": self.is_connected,
            "mode": "simulation" if self.simulation_mode else "hardware",
            "port": self.port if not self.simulation_mode else "N/A",
            "session_duration": str(datetime.now() - self.session_start_time).split('.')[0]
        }

# Convenience function for quick testing
def test_arduino_connector():
    """Test function for Arduino connector"""
    print("Testing Arduino Connector...")
    
    # Create connector in simulation mode
    connector = ArduinoConnector(simulation_mode=True)
    
    # Get a few data points
    for i in range(5):
        data = connector.get_current_stability_data()
        print(f"Sample {i+1}: Stability = {data['stability_score']}%, Quality = {data['form_quality']}")
        time.sleep(1)
    
    # Show connection info
    info = connector.get_connection_info()
    print(f"Connection Info: {info}")
    
    connector.close()

if __name__ == "__main__":
    test_arduino_connector()