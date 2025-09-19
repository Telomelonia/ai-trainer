#!/usr/bin/env python3
"""
End-to-End Test Suite
Core Training AI Ecosystem - Phase 3

Comprehensive test suite to validate all agent functionality,
MCP integrations, and system coordination.
"""

import asyncio
import json
import logging
import sys
import os
import importlib.util
from datetime import datetime

# Add agent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("e2e-test")

def import_agent_module(module_name):
    """Dynamically import an agent module"""
    try:
        module_path = os.path.join(os.path.dirname(__file__), 'agents', f'{module_name}.py')
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        else:
            print(f"Agent file not found: {module_path}")
            return None
    except Exception as e:
        print(f"Error importing {module_name}: {e}")
        return None

class CoreTrainingE2ETest:
    """End-to-end test suite for the Core Training AI ecosystem"""
    
    def __init__(self):
        self.test_results = {}
        self.test_user = "test_user_e2e"
        
    async def run_all_tests(self):
        """Run all end-to-end tests"""
        logger.info("🚀 Starting Core Training AI Ecosystem E2E Tests")
        
        tests = [
            ("MCP Client Manager", self.test_mcp_client_manager),
            ("Core Training Agent", self.test_core_training_agent),
            ("Agent Orchestrator", self.test_agent_orchestrator),
            ("Agent Coordination", self.test_agent_coordination),
            ("Coral Protocol Preparation", self.test_coral_protocol_prep),
            ("System Integration", self.test_system_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running test: {test_name}")
            try:
                result = await test_func()
                self.test_results[test_name] = {"status": "PASS", "result": result}
                logger.info(f"✅ {test_name}: PASSED")
            except Exception as e:
                self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
                logger.error(f"❌ {test_name}: FAILED - {str(e)}")
        
        self.print_test_summary()
        return self.test_results
    
    async def test_mcp_client_manager(self):
        """Test MCP client manager functionality"""
        from mcp_client_manager import mcp_client_manager
        
        # Test initialization
        success = await mcp_client_manager.initialize_connections()
        assert success, "MCP client manager initialization failed"
        
        # Test fitness data tools
        stability_data = await mcp_client_manager.call_tool(
            "fitness_data", "get_current_stability_score", {"user_id": self.test_user}
        )
        assert "current_data" in stability_data, "Stability data missing"
        assert "stability_score" in stability_data["current_data"], "Stability score missing"
        
        # Test user profile tools
        user_prefs = await mcp_client_manager.call_tool(
            "user_profile", "get_user_preferences", {"user_id": self.test_user}
        )
        assert "personal_info" in user_prefs, "User preferences missing personal info"
        
        # Test analytics tools
        weekly_report = await mcp_client_manager.call_tool(
            "progress_analytics", "generate_weekly_report", {"user_id": self.test_user}
        )
        assert "summary" in weekly_report, "Weekly report missing summary"
        
        return {
            "mcp_connected": True,
            "tools_tested": 3,
            "stability_score": stability_data["current_data"]["stability_score"]
        }
    
    async def test_core_training_agent(self):
        """Test Core Training Agent capabilities"""
        from core_training_agent import core_training_agent
        
        # Initialize agent
        success = await core_training_agent.initialize_mcp_connections()
        assert success, "Core training agent MCP initialization failed"
        
        # Test stability analysis
        stability_analysis = await core_training_agent.analyze_stability(self.test_user)
        assert "stability_analysis" in stability_analysis, "Stability analysis missing"
        assert "coaching_advice" in stability_analysis, "Coaching advice missing"
        assert stability_analysis["confidence"] > 0, "Confidence score invalid"
        
        # Test real-time coaching
        realtime_coaching = await core_training_agent.provide_realtime_coaching(self.test_user, "plank")
        assert "realtime_feedback" in realtime_coaching, "Real-time feedback missing"
        assert "adjustments" in realtime_coaching, "Coaching adjustments missing"
        
        # Test workout plan creation
        workout_plan = await core_training_agent.create_workout_plan(self.test_user)
        assert "exercises" in workout_plan, "Workout exercises missing"
        assert len(workout_plan["exercises"]) > 0, "No exercises in workout plan"
        
        # Test progress analysis
        progress_analysis = await core_training_agent.analyze_progress(self.test_user)
        assert "progress_metrics" in progress_analysis, "Progress metrics missing"
        assert "achievements" in progress_analysis, "Achievements missing"
        
        return {
            "agent_connected": True,
            "capabilities_tested": 4,
            "stability_score": stability_analysis["stability_analysis"]["current_score"],
            "workout_exercises": len(workout_plan["exercises"]),
            "confidence": stability_analysis["confidence"]
        }
    
    async def test_agent_orchestrator(self):
        """Test Agent Orchestrator functionality"""
        from agent_orchestrator import agent_orchestrator, AgentCapability
        from core_training_agent import core_training_agent
        
        # Register agent with orchestrator
        capabilities = [
            AgentCapability(
                name="stability_analysis",
                description="Analyze core stability",
                input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"analysis": {"type": "object"}}}
            )
        ]
        
        agent_orchestrator.register_agent("core-training-agent", core_training_agent, capabilities)
        
        # Test comprehensive session
        session_result = await agent_orchestrator.create_coaching_session(self.test_user, "comprehensive")
        assert "session_id" in session_result, "Session ID missing"
        assert "results" in session_result, "Session results missing"
        assert "coordination_summary" in session_result, "Coordination summary missing"
        
        # Test quick check session
        quick_session = await agent_orchestrator.create_coaching_session(self.test_user, "quick_check")
        assert "results" in quick_session, "Quick session results missing"
        
        # Get orchestrator status
        status = agent_orchestrator.get_orchestrator_status()
        assert status["registered_agents"] > 0, "No registered agents"
        
        return {
            "orchestrator_active": True,
            "registered_agents": status["registered_agents"],
            "comprehensive_session_id": session_result["session_id"],
            "coordination_successful": "coordination_summary" in session_result
        }
    
    async def test_agent_coordination(self):
        """Test multi-agent coordination capabilities"""
        from agent_orchestrator import agent_orchestrator
        
        # Test coaching request routing
        test_request = {
            "type": "stability_analysis",
            "user_id": self.test_user
        }
        
        from core_training_agent import core_training_agent
        response = await core_training_agent.handle_coaching_request(test_request)
        assert "stability_analysis" in response, "Request routing failed"
        
        # Test different request types
        request_types = ["stability_analysis", "realtime_coaching", "workout_plan", "progress_analysis"]
        successful_requests = 0
        
        for req_type in request_types:
            test_req = {"type": req_type, "user_id": self.test_user}
            if req_type == "realtime_coaching":
                test_req["current_exercise"] = "plank"
            
            try:
                result = await core_training_agent.handle_coaching_request(test_req)
                if "error" not in result:
                    successful_requests += 1
            except Exception as e:
                logger.warning(f"Request type {req_type} failed: {e}")
        
        return {
            "request_routing_working": True,
            "successful_request_types": successful_requests,
            "total_request_types": len(request_types),
            "coordination_success_rate": successful_requests / len(request_types)
        }
    
    async def test_coral_protocol_prep(self):
        """Test Coral Protocol preparation"""
        from agent_orchestrator import agent_orchestrator
        
        # Test Coral manifest generation
        coral_manifest = agent_orchestrator.prepare_coral_integration()
        
        assert "ecosystem_id" in coral_manifest, "Ecosystem ID missing"
        assert "agents" in coral_manifest, "Agents list missing"
        assert "payment_model" in coral_manifest, "Payment model missing"
        assert "coral_integration" in coral_manifest, "Coral integration config missing"
        
        # Validate agent entries
        agents = coral_manifest["agents"]
        assert len(agents) > 0, "No agents in manifest"
        
        agent = agents[0]
        assert "agent_id" in agent, "Agent ID missing"
        assert "capabilities" in agent, "Agent capabilities missing"
        assert "pricing" in agent, "Agent pricing missing"
        
        # Validate payment model
        payment_model = coral_manifest["payment_model"]
        assert payment_model["base_price"] > 0, "Invalid base price"
        assert "USD" in payment_model["currency"], "Currency not set"
        
        return {
            "coral_manifest_generated": True,
            "agents_in_manifest": len(agents),
            "ecosystem_ready": coral_manifest["coral_integration"]["marketplace_ready"],
            "base_price": payment_model["base_price"]
        }
    
    async def test_system_integration(self):
        """Test overall system integration"""
        from mcp_client_manager import mcp_client_manager
        from core_training_agent import core_training_agent
        from agent_orchestrator import agent_orchestrator
        
        # Full workflow test: User requests coaching session
        logger.info("Testing full coaching workflow...")
        
        # 1. Initialize all systems
        mcp_success = await mcp_client_manager.initialize_connections()
        agent_success = await core_training_agent.initialize_mcp_connections()
        
        # 2. Create comprehensive coaching session
        session = await agent_orchestrator.create_coaching_session(self.test_user, "comprehensive")
        
        # 3. Validate data flow
        stability_data = session["results"]["stability_analysis"]
        progress_data = session["results"]["progress_analysis"]
        workout_data = session["results"]["workout_plan"]
        
        # Validate cross-system data consistency
        stability_score = stability_data["stability_analysis"]["current_score"]
        workout_difficulty = workout_data["difficulty_level"]
        progress_improvement = progress_data["progress_metrics"]["stability_improvement"]
        
        assert stability_score > 0, "Invalid stability score"
        assert workout_difficulty in ["beginner", "intermediate", "advanced"], "Invalid difficulty level"
        assert "%" in progress_improvement, "Invalid progress format"
        
        # Test agent status
        agent_status = core_training_agent.get_agent_status()
        mcp_status = mcp_client_manager.get_connection_status()
        orchestrator_status = agent_orchestrator.get_orchestrator_status()
        
        return {
            "full_workflow_successful": True,
            "mcp_connected": mcp_status["is_connected"],
            "agent_active": agent_status["status"] == "active",
            "orchestrator_ready": orchestrator_status["coral_integration_ready"],
            "data_consistency_validated": True,
            "session_id": session["session_id"],
            "total_capabilities": sum(len(tools) for tools in mcp_status["servers"].values())
        }
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "="*60)
        logger.info("🏆 CORE TRAINING AI ECOSYSTEM - TEST SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        logger.info(f"📊 Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"🎯 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"{status_emoji} {test_name}: {result['status']}")
            
            if result["status"] == "PASS" and "result" in result:
                # Print key metrics from successful tests
                test_result = result["result"]
                if isinstance(test_result, dict):
                    key_metrics = {k: v for k, v in test_result.items() if isinstance(v, (int, float, bool, str))}
                    if key_metrics:
                        logger.info(f"   📈 Key metrics: {key_metrics}")
            elif result["status"] == "FAIL":
                logger.info(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 ALL TESTS PASSED! Phase 3 Complete!")
            logger.info("🚀 Ready for Phase 4: Coral Protocol Integration")
        else:
            logger.info(f"\n⚠️  {failed_tests} test(s) failed. Review and fix issues.")
        
        logger.info("="*60)

async def main():
    """Run the complete end-to-end test suite"""
    test_suite = CoreTrainingE2ETest()
    results = await test_suite.run_all_tests()
    
    # Generate test report
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "ecosystem_version": "1.0.0",
        "phase": "3 - Agent Development",
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results.values() if r["status"] == "PASS"),
            "failed": sum(1 for r in results.values() if r["status"] == "FAIL")
        }
    }
    
    # Save test report
    with open("e2e_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📄 Test report saved to: e2e_test_report.json")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())