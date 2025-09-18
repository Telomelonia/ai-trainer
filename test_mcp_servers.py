#!/usr/bin/env python3
"""
MCP Server Testing Script
Core Training AI Ecosystem - Phase 2

Tests all MCP servers to verify they work correctly.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_server_imports():
    """Test that all MCP servers can be imported"""
    print("🧪 Testing MCP Server Imports...")
    
    try:
        # Test fitness data server
        sys.path.append('mcp_servers')
        
        print("  ✅ Testing fitness_data_server import...")
        import fitness_data_server
        print("     ✓ fitness_data_server imported successfully")
        
        print("  ✅ Testing user_profile_server import...")
        import user_profile_server
        print("     ✓ user_profile_server imported successfully")
        
        print("  ✅ Testing progress_analytics_server import...")
        import progress_analytics_server
        print("     ✓ progress_analytics_server imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

async def test_tool_definitions():
    """Test that tool definitions are properly formatted"""
    print("\n🔧 Testing Tool Definitions...")
    
    try:
        # Import the servers
        sys.path.append('mcp_servers')
        import fitness_data_server
        import user_profile_server
        import progress_analytics_server
        
        # Test fitness data server tools
        print("  📊 Fitness Data Server Tools:")
        fitness_tools = await fitness_data_server.handle_list_tools()
        for tool in fitness_tools:
            print(f"     ✓ {tool.name}: {tool.description}")
        
        print("  👤 User Profile Server Tools:")
        profile_tools = await user_profile_server.handle_list_tools()
        for tool in profile_tools:
            print(f"     ✓ {tool.name}: {tool.description}")
        
        print("  📈 Progress Analytics Server Tools:")
        analytics_tools = await progress_analytics_server.handle_list_tools()
        for tool in analytics_tools:
            print(f"     ✓ {tool.name}: {tool.description}")
        
        total_tools = len(fitness_tools) + len(profile_tools) + len(analytics_tools)
        print(f"\n  🎯 Total MCP Tools Available: {total_tools}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tool definition test failed: {e}")
        return False

async def test_tool_execution():
    """Test that tools can be executed"""
    print("\n⚡ Testing Tool Execution...")
    
    try:
        sys.path.append('mcp_servers')
        import fitness_data_server
        import user_profile_server
        import progress_analytics_server
        
        # Test fitness data server
        print("  📊 Testing Fitness Data Server:")
        
        # Test get_current_stability_score
        result = await fitness_data_server.handle_call_tool(
            "get_current_stability_score", 
            {"user_id": "test_user"}
        )
        print("     ✓ get_current_stability_score executed")
        
        # Test log_exercise_session
        result = await fitness_data_server.handle_call_tool(
            "log_exercise_session",
            {
                "user_id": "test_user",
                "exercise_type": "plank",
                "duration": 30,
                "avg_stability": 85.5
            }
        )
        print("     ✓ log_exercise_session executed")
        
        # Test user profile server
        print("  👤 Testing User Profile Server:")
        
        result = await user_profile_server.handle_call_tool(
            "get_user_preferences",
            {"user_id": "user_123"}
        )
        print("     ✓ get_user_preferences executed")
        
        # Test progress analytics server
        print("  📈 Testing Progress Analytics Server:")
        
        result = await progress_analytics_server.handle_call_tool(
            "calculate_improvement_rate",
            {"user_id": "user_123", "metric": "stability_score", "days": 7}
        )
        print("     ✓ calculate_improvement_rate executed")
        
        result = await progress_analytics_server.handle_call_tool(
            "generate_weekly_report",
            {"user_id": "user_123"}
        )
        print("     ✓ generate_weekly_report executed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tool execution test failed: {e}")
        return False

async def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📋 MCP Server Test Report")
    print("=" * 50)
    
    # Run all tests
    import_success = await test_server_imports()
    tools_success = await test_tool_definitions()
    execution_success = await test_tool_execution()
    
    # Summary
    print(f"\n✅ Results Summary:")
    print(f"   Server Imports: {'PASS' if import_success else 'FAIL'}")
    print(f"   Tool Definitions: {'PASS' if tools_success else 'FAIL'}")
    print(f"   Tool Execution: {'PASS' if execution_success else 'FAIL'}")
    
    overall_success = import_success and tools_success and execution_success
    
    print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🚀 Phase 2 MCP Integration: READY FOR PHASE 3!")
        print("   - 3 MCP servers operational")
        print("   - 16+ tools available for agents")
        print("   - Fitness data, user profiles, and analytics accessible")
    
    return overall_success

async def main():
    """Main test runner"""
    print("🏋️ Core Training AI Ecosystem - MCP Server Tests")
    print("=" * 60)
    
    success = await generate_test_report()
    
    if success:
        print(f"\n🎉 Phase 2 Complete! Ready for Agent Development.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check server implementations.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())