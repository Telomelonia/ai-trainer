#!/usr/bin/env python3
"""
Sensor System Test Script
Core Training AI Ecosystem - Multi-Sensor Platform

Tests the complete sensor abstraction layer and multi-sensor functionality.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

async def test_sensor_factory():
    """Test the sensor factory system"""
    print("🏭 Testing Sensor Factory...")
    
    try:
        from sensors import BaseSensor, SensorFactory
        
        # Test available sensor types
        available_types = SensorFactory.get_available_sensor_types()
        print(f"   Available sensor types: {available_types}")
        
        # Test creating different sensor types
        for sensor_type in available_types:
            print(f"   Creating {sensor_type} sensor...")
            sensor = SensorFactory.create_sensor(
                sensor_type=sensor_type,
                sensor_id=f"test_{sensor_type}_01"
            )
            print(f"   ✓ {sensor_type} sensor created: {sensor.sensor_id}")
            print(f"     Supported metrics: {len(sensor.supported_metrics)}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Sensor factory test failed: {e}")
        return False

async def test_imu_sensor():
    """Test IMU sensor functionality"""
    print("\n📱 Testing IMU Sensor...")
    
    try:
        from sensors import SensorFactory
        
        # Create IMU sensor
        imu = SensorFactory.create_sensor("imu", "test_imu", {
            "simulation_mode": True,
            "sample_rate": 50
        })
        
        # Test connection
        print("   Connecting to IMU...")
        connected = await imu.connect()
        if not connected:
            print("   ❌ IMU connection failed")
            return False
        print("   ✓ IMU connected")
        
        # Test calibration
        print("   Calibrating IMU...")
        calibrated = await imu.calibrate()
        if not calibrated:
            print("   ❌ IMU calibration failed")
            return False
        print("   ✓ IMU calibrated")
        
        # Test data reading
        print("   Reading IMU data...")
        for i in range(3):
            data = await imu.get_data()
            print(f"     Sample {i+1}: Stability={data.data['stability_score']}%, "
                  f"Balance={data.data['balance_score']}%")
            await asyncio.sleep(0.1)
        
        # Test health check
        health = await imu.health_check()
        print(f"   Health status: {'Healthy' if health['healthy'] else 'Issues found'}")
        
        # Disconnect
        await imu.disconnect()
        print("   ✓ IMU disconnected")
        
        return True
    
    except Exception as e:
        print(f"   ❌ IMU sensor test failed: {e}")
        return False

async def test_emg_sensor():
    """Test EMG sensor functionality"""
    print("\n💪 Testing EMG Sensor...")
    
    try:
        from sensors import SensorFactory
        
        # Create EMG sensor
        emg = SensorFactory.create_sensor("emg", "test_emg", {
            "simulation_mode": True,
            "muscle_groups": ["rectus_abdominis", "external_oblique"]
        })
        
        # Test connection
        connected = await emg.connect()
        if not connected:
            print("   ❌ EMG connection failed")
            return False
        print("   ✓ EMG connected")
        
        # Test calibration
        calibrated = await emg.calibrate()
        if not calibrated:
            print("   ❌ EMG calibration failed")
            return False
        print("   ✓ EMG calibrated")
        
        # Test data reading
        print("   Reading EMG data...")
        data = await emg.get_data()
        print(f"     Core engagement: {data.data['core_engagement_score']}%")
        print(f"     Training intensity: {data.data['training_intensity']}")
        
        await emg.disconnect()
        print("   ✓ EMG disconnected")
        
        return True
    
    except Exception as e:
        print(f"   ❌ EMG sensor test failed: {e}")
        return False

async def test_pressure_sensor():
    """Test pressure sensor functionality"""
    print("\n⚖️ Testing Pressure Sensor...")
    
    try:
        from sensors import SensorFactory
        
        # Create pressure sensor
        pressure = SensorFactory.create_sensor("pressure", "test_pressure", {
            "simulation_mode": True,
            "sensor_zones": ["left_foot", "right_foot", "core_front"]
        })
        
        # Test connection
        connected = await pressure.connect()
        if not connected:
            print("   ❌ Pressure connection failed")
            return False
        print("   ✓ Pressure sensor connected")
        
        # Test calibration
        calibrated = await pressure.calibrate()
        if not calibrated:
            print("   ❌ Pressure calibration failed")
            return False
        print("   ✓ Pressure sensor calibrated")
        
        # Test data reading
        print("   Reading pressure data...")
        data = await pressure.get_data()
        print(f"     Stability index: {data.data['stability_index']}%")
        print(f"     Balance symmetry: {data.data['balance_symmetry']}%")
        
        await pressure.disconnect()
        print("   ✓ Pressure sensor disconnected")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Pressure sensor test failed: {e}")
        return False

async def test_multi_sensor_coordination():
    """Test multiple sensors working together"""
    print("\n🤝 Testing Multi-Sensor Coordination...")
    
    try:
        from sensors import SensorFactory
        from config import get_enabled_sensors, get_active_sensor_config
        
        # Create multiple sensors
        sensors = {}
        
        # Create IMU sensor
        imu_config = {
            "simulation_mode": True,
            "sample_rate": 50
        }
        sensors["imu"] = SensorFactory.create_sensor("imu", "coord_imu", imu_config)
        
        # Create EMG sensor
        emg_config = {
            "simulation_mode": True,
            "muscle_groups": ["rectus_abdominis", "external_oblique"]
        }
        sensors["emg"] = SensorFactory.create_sensor("emg", "coord_emg", emg_config)
        
        # Connect all sensors
        print("   Connecting all sensors...")
        for name, sensor in sensors.items():
            connected = await sensor.connect()
            calibrated = await sensor.calibrate()
            if connected and calibrated:
                print(f"   ✓ {name} sensor ready")
            else:
                print(f"   ❌ {name} sensor failed")
                return False
        
        # Collect synchronized data
        print("   Collecting synchronized data...")
        for round_num in range(3):
            print(f"   Round {round_num + 1}:")
            
            # Collect from all sensors
            all_data = {}
            for name, sensor in sensors.items():
                data = await sensor.get_data()
                all_data[name] = data
            
            # Show combined insights
            imu_data = all_data["imu"].data
            emg_data = all_data["emg"].data
            
            print(f"     IMU Stability: {imu_data['stability_score']}%")
            print(f"     EMG Core Engagement: {emg_data['core_engagement_score']}%")
            
            # Simple fusion algorithm
            combined_score = (imu_data['stability_score'] + emg_data['core_engagement_score']) / 2
            print(f"     Combined Training Score: {combined_score:.1f}%")
            
            await asyncio.sleep(0.2)
        
        # Disconnect all sensors
        for name, sensor in sensors.items():
            await sensor.disconnect()
        
        print("   ✓ Multi-sensor coordination test completed")
        return True
    
    except Exception as e:
        print(f"   ❌ Multi-sensor coordination test failed: {e}")
        return False

async def test_configuration_system():
    """Test the configuration system"""
    print("\n⚙️ Testing Configuration System...")
    
    try:
        from config import (
            DEMO_MODE, SIMULATION_MODE, get_enabled_sensors,
            get_active_sensor_config, get_demo_scenario
        )
        
        print(f"   Demo mode: {DEMO_MODE}")
        print(f"   Simulation mode: {SIMULATION_MODE}")
        
        # Test sensor configurations
        enabled_sensors = get_enabled_sensors()
        print(f"   Enabled sensors: {enabled_sensors}")
        
        for sensor_id in ["primary_imu", "emg_muscles", "pressure_zones"]:
            config = get_active_sensor_config(sensor_id)
            enabled = config.get("enabled", False)
            sensor_type = config.get("type", "unknown")
            print(f"   {sensor_id}: {sensor_type} ({'enabled' if enabled else 'disabled'})")
        
        # Test demo scenarios
        scenario = get_demo_scenario("basic_stability")
        print(f"   Demo scenario: {scenario['description']}")
        print(f"   Sensors: {scenario['sensors']}")
        print(f"   Duration: {scenario['duration']}s")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Configuration system test failed: {e}")
        return False

async def main():
    """Run all sensor tests"""
    print("🚀 Starting Sensor System Tests")
    print("=" * 50)
    
    tests = [
        ("Sensor Factory", test_sensor_factory),
        ("IMU Sensor", test_imu_sensor),
        ("EMG Sensor", test_emg_sensor),
        ("Pressure Sensor", test_pressure_sensor),
        ("Multi-Sensor Coordination", test_multi_sensor_coordination),
        ("Configuration System", test_configuration_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All sensor tests passed! The multi-sensor platform is ready.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)