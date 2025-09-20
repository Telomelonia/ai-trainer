"""
CoreSense AI Platform - Coral Orchestration UI
User interface for managing multi-agent workflows and coral protocol integration
"""

import streamlit as st
from typing import Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from core.logging import get_logger
from coral_integration.multi_agent_orchestrator import WorkflowExecution, WorkflowStatus

logger = get_logger(__name__)


def render_coral_orchestration(service_manager):
    """Render coral orchestration and multi-agent workflow interface"""
    
    st.title("🧠 Coral Multi-Agent Orchestration")
    st.markdown("Manage complex multi-agent workflows for comprehensive fitness training")
    
    # Get services
    coral_orchestrator = service_manager.get_service('coral_orchestrator')
    agent_orchestrator = service_manager.get_service('agent_orchestrator')
    
    if not coral_orchestrator:
        st.warning("⚠️ Coral orchestration service not available")
        st.info("Coral orchestration enables advanced multi-agent workflows for:")
        st.markdown("""
        - **Comprehensive Fitness Assessment**: Multi-agent analysis combining muscle activation, compensation detection, and personalized coaching
        - **Real-time Coaching Sessions**: Live feedback with continuous monitoring and adaptive coaching
        - **Team Training Coordination**: Simultaneous training analysis for multiple users
        - **Advanced Analytics**: Complex data processing workflows across multiple specialized agents
        """)
        return
    
    # Create tabs for different functionality
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Quick Workflows", 
        "📊 Workflow Status", 
        "⚙️ Custom Workflows",
        "🔧 Agent Management"
    ])
    
    with tab1:
        render_quick_workflows(coral_orchestrator)
    
    with tab2:
        render_workflow_status(coral_orchestrator)
    
    with tab3:
        render_custom_workflows(coral_orchestrator)
    
    with tab4:
        render_agent_management(agent_orchestrator)


def render_quick_workflows(coral_orchestrator):
    """Render quick workflow execution interface"""
    
    st.subheader("🚀 Quick Workflow Execution")
    st.markdown("Execute pre-built multi-agent workflows for common scenarios")
    
    # Get available workflows
    try:
        workflows = coral_orchestrator.get_available_workflows()
    except Exception as e:
        st.error(f"Failed to load workflows: {e}")
        return
    
    if not workflows:
        st.info("No workflows available")
        return
    
    # Workflow selection
    workflow_options = {f"{wf['name']} ({wf['workflow_id']})": wf for wf in workflows}
    selected_workflow_name = st.selectbox(
        "Select Workflow",
        options=list(workflow_options.keys())
    )
    
    if selected_workflow_name:
        selected_workflow = workflow_options[selected_workflow_name]
        
        # Display workflow details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Steps", selected_workflow['steps'])
        with col2:
            st.metric("Est. Cost", f"${selected_workflow.get('estimated_cost', 0):.2f}")
        with col3:
            st.metric("Est. Duration", f"{selected_workflow.get('estimated_duration', 0)}s")
        
        st.markdown(f"**Description:** {selected_workflow['description']}")
        
        # Input parameters
        st.subheader("Input Parameters")
        input_data = {}
        
        # Common parameters for different workflow types
        if selected_workflow['workflow_id'] == 'comprehensive_fitness_assessment':
            exercise_type = st.selectbox(
                "Assessment Exercise",
                ["assessment_plank", "squat_assessment", "push_up_assessment", "balance_test"]
            )
            duration = st.slider("Duration (seconds)", 30, 180, 60)
            input_data = {
                "exercise": exercise_type,
                "duration": duration,
                "user_id": st.session_state.get('user_id', 'demo_user')
            }
            
        elif selected_workflow['workflow_id'] == 'realtime_coaching_session':
            session_type = st.selectbox(
                "Session Type",
                ["strength_training", "cardio_workout", "flexibility_session", "balance_training"]
            )
            intensity = st.selectbox("Intensity Level", ["beginner", "intermediate", "advanced"])
            input_data = {
                "session_type": session_type,
                "intensity": intensity,
                "user_id": st.session_state.get('user_id', 'demo_user')
            }
            
        elif selected_workflow['workflow_id'] == 'team_training_orchestration':
            team_size = st.number_input("Team Size", min_value=2, max_value=10, value=2)
            training_focus = st.selectbox(
                "Training Focus",
                ["coordination", "competition", "synchronized_training", "group_assessment"]
            )
            input_data = {
                "team_size": team_size,
                "training_focus": training_focus,
                "team_id": f"team_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        
        # User context
        with st.expander("Advanced Options"):
            user_context = {}
            fitness_level = st.selectbox("Fitness Level", ["beginner", "intermediate", "advanced"])
            has_injuries = st.checkbox("Has Previous Injuries")
            
            if has_injuries:
                injury_details = st.text_input("Injury Details")
                user_context["injury_details"] = injury_details
            
            user_context.update({
                "fitness_level": fitness_level,
                "has_injuries": has_injuries
            })
        
        # Execute workflow
        if st.button("🚀 Execute Workflow", type="primary"):
            with st.spinner("Executing multi-agent workflow..."):
                try:
                    # Store execution in session state for tracking
                    if 'workflow_executions' not in st.session_state:
                        st.session_state.workflow_executions = []
                    
                    # Execute workflow (in a real async environment, this would be awaited)
                    execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # For demo purposes, simulate execution
                    execution_result = {
                        "execution_id": execution_id,
                        "workflow_id": selected_workflow['workflow_id'],
                        "status": "running",
                        "started_at": datetime.now().isoformat(),
                        "input_data": input_data,
                        "user_context": user_context
                    }
                    
                    st.session_state.workflow_executions.append(execution_result)
                    
                    st.success(f"✅ Workflow execution started! Execution ID: {execution_id}")
                    st.info("Check the 'Workflow Status' tab to monitor progress")
                    
                except Exception as e:
                    st.error(f"❌ Failed to execute workflow: {e}")
                    logger.error(f"Workflow execution failed: {e}")


def render_workflow_status(coral_orchestrator):
    """Render workflow execution status interface"""
    
    st.subheader("📊 Workflow Execution Status")
    
    # Check for active executions in session state
    if 'workflow_executions' not in st.session_state:
        st.session_state.workflow_executions = []
    
    executions = st.session_state.workflow_executions
    
    if not executions:
        st.info("No workflow executions found")
        return
    
    # Display executions
    for i, execution in enumerate(reversed(executions)):
        with st.expander(
            f"🔄 {execution['workflow_id']} - {execution['execution_id']} "
            f"({execution['status'].upper()})"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Execution Details:**")
                st.write(f"- **ID:** {execution['execution_id']}")
                st.write(f"- **Workflow:** {execution['workflow_id']}")
                st.write(f"- **Status:** {execution['status']}")
                st.write(f"- **Started:** {execution['started_at']}")
            
            with col2:
                st.write("**Input Data:**")
                st.json(execution.get('input_data', {}))
            
            # Simulate progress for demo
            if execution['status'] == 'running':
                progress = st.progress(0.7)
                st.write("🔄 Currently executing step: Real-time Analysis")
                
                if st.button(f"Cancel Execution {execution['execution_id']}", key=f"cancel_{i}"):
                    execution['status'] = 'cancelled'
                    st.rerun()
            
            elif execution['status'] == 'completed':
                st.success("✅ Workflow completed successfully")
                
                # Mock results
                mock_results = {
                    "muscle_activation_score": 85,
                    "compensation_detected": False,
                    "recommendations": [
                        "Increase core engagement",
                        "Focus on proper breathing technique",
                        "Add stability exercises to routine"
                    ],
                    "total_cost": 1.25,
                    "execution_time": 45.2
                }
                
                st.write("**Results:**")
                st.json(mock_results)
                
                # Download results
                if st.button(f"📥 Download Results", key=f"download_{i}"):
                    st.download_button(
                        label="Download JSON",
                        data=json.dumps(mock_results, indent=2),
                        file_name=f"workflow_results_{execution['execution_id']}.json",
                        mime="application/json"
                    )


def render_custom_workflows(coral_orchestrator):
    """Render custom workflow creation interface"""
    
    st.subheader("⚙️ Custom Workflow Creation")
    st.markdown("Create custom multi-agent workflows for specific use cases")
    
    with st.form("custom_workflow"):
        workflow_name = st.text_input("Workflow Name")
        workflow_description = st.text_area("Description")
        
        workflow_type = st.selectbox(
            "Workflow Type",
            ["sequential", "parallel", "conditional", "hybrid"]
        )
        
        st.subheader("Workflow Steps")
        
        # For simplicity, allow adding a few steps
        num_steps = st.number_input("Number of Steps", min_value=1, max_value=10, value=3)
        
        steps = []
        for i in range(num_steps):
            st.write(f"**Step {i+1}:**")
            col1, col2 = st.columns(2)
            
            with col1:
                agent_id = st.selectbox(
                    f"Agent",
                    ["coresense-fabric-sensor", "coresense-ai-coach", "physiotherapy-assistant"],
                    key=f"agent_{i}"
                )
                capability = st.selectbox(
                    f"Capability",
                    ["muscle_activation_analysis", "compensation_detection", "personalized_coaching"],
                    key=f"capability_{i}"
                )
            
            with col2:
                timeout = st.number_input(f"Timeout (seconds)", min_value=10, max_value=300, value=30, key=f"timeout_{i}")
                retry_count = st.number_input(f"Retry Count", min_value=0, max_value=5, value=3, key=f"retry_{i}")
            
            steps.append({
                "step_id": f"step_{i+1}",
                "agent_id": agent_id,
                "capability": capability,
                "timeout": timeout,
                "retry_count": retry_count
            })
        
        submitted = st.form_submit_button("Create Workflow")
        
        if submitted and workflow_name:
            st.success(f"✅ Custom workflow '{workflow_name}' created successfully!")
            st.info("Custom workflow creation would be implemented in the full system")


def render_agent_management(agent_orchestrator):
    """Render agent management interface"""
    
    st.subheader("🔧 Agent Management")
    
    if not agent_orchestrator:
        st.warning("⚠️ Agent orchestrator not available")
        return
    
    # Get agent status
    try:
        agent_status = agent_orchestrator.get_system_status()
        
        st.subheader("Agent Status")
        
        for agent_id, status in agent_status.get("agents", {}).items():
            with st.expander(f"🤖 {agent_id.title()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    status_color = "🟢" if status.get("status") == "ready" else "🔴"
                    st.write(f"**Status:** {status_color} {status.get('status', 'unknown')}")
                    st.write(f"**Capabilities:** {len(status.get('capabilities', []))}")
                
                with col2:
                    if status.get("capabilities"):
                        st.write("**Available Capabilities:**")
                        for cap in status.get("capabilities", []):
                            st.write(f"- {cap}")
        
        # Coral integration status
        st.subheader("Coral Integration")
        coral_ready = agent_status.get("coral_integration_ready", False)
        
        if coral_ready:
            st.success("✅ Coral Protocol integration ready")
            
            if st.button("🔄 Refresh Coral Manifest"):
                try:
                    coral_manifest = agent_orchestrator.prepare_coral_integration()
                    st.json(coral_manifest)
                except Exception as e:
                    st.error(f"Failed to prepare coral manifest: {e}")
        else:
            st.warning("⚠️ Coral Protocol integration not ready")
            
            if st.button("🚀 Initialize Coral Integration"):
                try:
                    agent_orchestrator.prepare_coral_integration()
                    st.success("✅ Coral integration initialized")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to initialize coral integration: {e}")
    
    except Exception as e:
        st.error(f"Failed to get agent status: {e}")
        logger.error(f"Agent management error: {e}")