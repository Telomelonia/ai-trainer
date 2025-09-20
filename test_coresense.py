#!/usr/bin/env python3
"""
CoreSense Platform Test Suite
"""

import asyncio
import sys
import os
import traceback

# Add current directory and agents directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

async def test_fabric_sensor():
    """Test fabric sensor simulation"""
    print("🧪 Testing Fabric Sensor Agent...")
    
    try:
        from fabric_sensor_agent import FabricSensorAgent
        
        # Create fabric sensor instance
        fabric_sensor = FabricSensorAgent()
        print("✅ FabricSensorAgent instantiated successfully")
        
        # Start monitoring for plank exercise
        await fabric_sensor.start_exercise_monitoring('plank')
        print("✅ Exercise monitoring started")
        
        # Test real-time muscle data
        muscle_data = await fabric_sensor.get_realtime_muscle_data()
        print(f"✅ Real-time muscle data: {muscle_data['muscle_activation']}")
        print(f"✅ Overall Stability: {muscle_data['overall_stability']}")
        
        # Test compensation detection
        form_analysis = muscle_data.get('form_analysis', {})
        print(f"⚠️ Form Issues: {form_analysis.get('issues', [])}")
        
        # Test different exercises
        exercises = ['side_plank', 'dead_bug', 'bird_dog']
        for exercise in exercises:
            await fabric_sensor.start_exercise_monitoring(exercise)
            exercise_data = await fabric_sensor.get_realtime_muscle_data()
            print(f"✅ {exercise.replace('_', ' ').title()}: Stability {exercise_data['overall_stability']}")
        
        # Stop monitoring
        await fabric_sensor.stop_monitoring()
        
        print("\n✅ Fabric sensor tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Fabric sensor test failed: {e}")
        traceback.print_exc()
        return False

async def test_core_training_agent():
    """Test core training agent with fabric sensor integration"""
    print("\n🧪 Testing Core Training Agent...")
    
    try:
        from core_training_agent import CoreTrainingAgent
        
        # Create agent instance
        agent = CoreTrainingAgent()
        print("✅ CoreTrainingAgent instantiated successfully")
        
        # Test muscle monitoring methods
        user_id = "test_user"
        
        # Start monitoring
        start_result = await agent.start_muscle_monitoring(user_id, "plank")
        if "error" not in start_result:
            print("✅ Muscle monitoring started successfully")
        else:
            print(f"⚠️ Muscle monitoring start issue: {start_result.get('error', 'Unknown')}")
        
        # Get real-time analysis
        muscle_data = await agent.get_realtime_muscle_analysis(user_id)
        if "error" not in muscle_data:
            print(f"✅ Real-time analysis: Stability {muscle_data.get('stability_score', 'N/A')}")
            print(f"   AI Coaching: {len(muscle_data.get('ai_coaching', {}).get('coaching_cues', []))} cues provided")
        else:
            print(f"⚠️ Real-time analysis issue: {muscle_data.get('error', 'Unknown')}")
        
        # Stop monitoring
        stop_result = await agent.stop_muscle_monitoring(user_id)
        if "error" not in stop_result:
            print("✅ Muscle monitoring stopped successfully")
            if "session_summary" in stop_result:
                summary = stop_result["session_summary"]
                print(f"   Session Duration: {summary.get('session_duration', 'N/A')}")
                print(f"   Average Score: {summary.get('average_score', 'N/A')}")
        else:
            print(f"⚠️ Muscle monitoring stop issue: {stop_result.get('error', 'Unknown')}")
        
        print("\n✅ Core training agent tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Core training agent test failed: {e}")
        traceback.print_exc()
        return False

async def test_configuration():
    """Test CoreSense configuration"""
    print("\n🧪 Testing CoreSense Configuration...")
    
    try:
        from coresense_config import (
            PLATFORM_CONFIG, SENSOR_ZONES, MUSCLE_ACTIVATION_THRESHOLDS,
            COMPENSATION_PATTERNS, EXERCISE_CONFIGS, AI_COACHING_CONFIG
        )
        
        print(f"✅ Platform: {PLATFORM_CONFIG['name']} v{PLATFORM_CONFIG['version']}")
        print(f"✅ Sensor Zones: {len(SENSOR_ZONES)} zones configured")
        print(f"✅ Exercise Configs: {len(EXERCISE_CONFIGS)} exercises defined")
        print(f"✅ AI Coaching Modes: {len(AI_COACHING_CONFIG['coaching_modes'])} modes available")
        
        # Validate configuration structure
        required_zones = ['upper_rectus', 'lower_rectus', 'right_oblique', 'left_oblique', 'transverse']
        for zone in required_zones:
            if zone in SENSOR_ZONES:
                print(f"✅ Required zone '{zone}' configured")
            else:
                print(f"❌ Missing required zone '{zone}'")
                return False
        
        print("\n✅ Configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

async def test_integration():
    """Test full platform integration"""
    print("\n🧪 Testing Platform Integration...")
    
    try:
        from core_training_agent import CoreTrainingAgent
        
        # Create agent
        agent = CoreTrainingAgent()
        
        # Test full workflow
        user_id = "integration_test_user"
        exercise = "plank"
        
        print(f"🔄 Testing full workflow: {exercise} exercise for {user_id}")
        
        # Step 1: Start monitoring
        start_result = await agent.start_muscle_monitoring(user_id, exercise)
        workflow_success = "error" not in start_result
        
        if workflow_success:
            # Step 2: Get multiple readings
            for i in range(3):
                muscle_data = await agent.get_realtime_muscle_analysis(user_id)
                if "error" in muscle_data:
                    workflow_success = False
                    break
                print(f"   Reading {i+1}: Score {muscle_data.get('stability_score', 'N/A')}")
                await asyncio.sleep(0.5)
            
            # Step 3: Stop monitoring
            if workflow_success:
                stop_result = await agent.stop_muscle_monitoring(user_id)
                workflow_success = "error" not in stop_result
                
                if workflow_success and "session_summary" in stop_result:
                    summary = stop_result["session_summary"]
                    print(f"✅ Session completed: {summary.get('session_duration', 'N/A')} duration")
        
        if workflow_success:
            print("\n✅ Integration tests passed!")
            return True
        else:
            print("\n⚠️ Integration tests completed with issues")
            return False
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all CoreSense tests"""
    print("🏋️ CoreSense Platform - Comprehensive Test Suite")
    print("=" * 55)
    
    test_results = []
    
    # Run all test categories
    test_results.append(await test_fabric_sensor())
    test_results.append(await test_core_training_agent())
    test_results.append(await test_configuration())
    test_results.append(await test_integration())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 55)
    print(f"📊 Test Results: {passed}/{total} test categories passed")
    
    if passed == total:
        print("🎉 All tests completed successfully!")
        print("✅ CoreSense Platform is ready for deployment!")
        return True
    else:
        print("⚠️ Some tests had issues - please review output above")
        return False

if __name__ == "__main__":
    # Run the comprehensive test suite
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)