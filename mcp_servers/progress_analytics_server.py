#!/usr/bin/env python3
"""
Progress Analytics MCP Server
Core Training AI Ecosystem - Phase 2

Provides advanced analytics, progress tracking, and performance insights.
Generates weekly reports, calculates improvement rates, and recommends adjustments.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import statistics
import math

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("progress-analytics-server")

# Mock exercise data for analytics (in production, this would come from fitness_data_server)
exercise_history = [
    {"user_id": "user_123", "date": "2025-09-11", "stability_score": 78.5, "duration": 25, "exercise": "plank"},
    {"user_id": "user_123", "date": "2025-09-12", "stability_score": 80.2, "duration": 27, "exercise": "dead_bug"},
    {"user_id": "user_123", "date": "2025-09-13", "stability_score": 82.1, "duration": 30, "exercise": "plank"},
    {"user_id": "user_123", "date": "2025-09-14", "stability_score": 83.7, "duration": 28, "exercise": "bird_dog"},
    {"user_id": "user_123", "date": "2025-09-15", "stability_score": 85.3, "duration": 32, "exercise": "plank"},
    {"user_id": "user_123", "date": "2025-09-16", "stability_score": 87.1, "duration": 35, "exercise": "side_plank"},
    {"user_id": "user_123", "date": "2025-09-17", "stability_score": 88.9, "duration": 38, "exercise": "plank"},
    {"user_id": "user_123", "date": "2025-09-18", "stability_score": 90.2, "duration": 40, "exercise": "dead_bug"},
    
    {"user_id": "user_456", "date": "2025-09-15", "stability_score": 65.2, "duration": 15, "exercise": "modified_plank"},
    {"user_id": "user_456", "date": "2025-09-16", "stability_score": 67.8, "duration": 18, "exercise": "wall_sit"},
    {"user_id": "user_456", "date": "2025-09-17", "stability_score": 70.1, "duration": 20, "exercise": "modified_plank"},
    {"user_id": "user_456", "date": "2025-09-18", "stability_score": 72.3, "duration": 22, "exercise": "dead_bug"},
]

# Create MCP server
server = Server("progress-analytics-server")

def get_user_exercise_data(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get exercise data for a user within specified days"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    user_data = [
        data for data in exercise_history
        if data["user_id"] == user_id and
        datetime.strptime(data["date"], "%Y-%m-%d") >= cutoff_date
    ]
    
    return sorted(user_data, key=lambda x: x["date"])

def calculate_improvement_rate(user_id: str, metric: str = "stability_score", days: int = 14) -> Dict[str, Any]:
    """Calculate improvement rate for a specific metric"""
    data = get_user_exercise_data(user_id, days)
    
    if len(data) < 2:
        return {
            "error": "Insufficient data",
            "message": "Need at least 2 data points to calculate improvement rate"
        }
    
    # Extract metric values
    values = [entry[metric] for entry in data if metric in entry]
    dates = [datetime.strptime(entry["date"], "%Y-%m-%d") for entry in data if metric in entry]
    
    if len(values) < 2:
        return {
            "error": "Insufficient metric data",
            "message": f"Need at least 2 {metric} values"
        }
    
    # Calculate linear regression for trend
    n = len(values)
    x_values = list(range(n))
    
    # Calculate slope (improvement rate)
    x_mean = sum(x_values) / n
    y_mean = sum(values) / n
    
    numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    # Calculate R-squared for trend strength
    y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
    ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Interpret results
    days_span = (dates[-1] - dates[0]).days if len(dates) > 1 else 1
    daily_improvement = slope
    weekly_improvement = daily_improvement * 7
    
    # Determine trend strength
    if abs(r_squared) > 0.8:
        trend_strength = "strong"
    elif abs(r_squared) > 0.5:
        trend_strength = "moderate"
    else:
        trend_strength = "weak"
    
    # Determine trend direction
    if slope > 0.5:
        trend_direction = "improving"
    elif slope < -0.5:
        trend_direction = "declining"
    else:
        trend_direction = "stable"
    
    return {
        "user_id": user_id,
        "metric": metric,
        "analysis_period_days": days,
        "data_points": n,
        "current_value": values[-1],
        "starting_value": values[0],
        "total_change": values[-1] - values[0],
        "daily_improvement_rate": round(daily_improvement, 3),
        "weekly_improvement_rate": round(weekly_improvement, 3),
        "trend_direction": trend_direction,
        "trend_strength": trend_strength,
        "correlation_coefficient": round(math.sqrt(max(0, r_squared)), 3),
        "confidence": round(r_squared, 3),
        "calculated_at": datetime.now().isoformat()
    }

def generate_weekly_report(user_id: str) -> Dict[str, Any]:
    """Generate comprehensive weekly progress report"""
    # Get last 7 days of data
    weekly_data = get_user_exercise_data(user_id, 7)
    
    if not weekly_data:
        return {
            "error": "No data available",
            "message": "No exercise data found for the past week"
        }
    
    # Calculate basic stats
    stability_scores = [d["stability_score"] for d in weekly_data]
    durations = [d["duration"] for d in weekly_data]
    exercises = [d["exercise"] for d in weekly_data]
    
    # Weekly summary
    total_sessions = len(weekly_data)
    total_duration = sum(durations)
    avg_stability = statistics.mean(stability_scores)
    max_stability = max(stability_scores)
    min_stability = min(stability_scores)
    
    # Exercise variety
    unique_exercises = list(set(exercises))
    most_common_exercise = max(set(exercises), key=exercises.count) if exercises else "none"
    
    # Improvement analysis
    improvement_analysis = calculate_improvement_rate(user_id, "stability_score", 7)
    
    # Performance grades
    if avg_stability >= 90:
        performance_grade = "A"
        performance_comment = "Excellent performance!"
    elif avg_stability >= 80:
        performance_grade = "B"
        performance_comment = "Good progress, keep it up!"
    elif avg_stability >= 70:
        performance_grade = "C"
        performance_comment = "Steady improvement, focus on consistency."
    else:
        performance_grade = "D"
        performance_comment = "Room for improvement, consider adjusting difficulty."
    
    # Goals assessment
    weekly_goal_sessions = 5  # Assumed goal
    session_completion_rate = (total_sessions / weekly_goal_sessions) * 100
    
    # Recommendations
    recommendations = []
    
    if session_completion_rate < 80:
        recommendations.append("Increase training frequency to meet weekly goals")
    
    if improvement_analysis.get("trend_direction") == "declining":
        recommendations.append("Consider reducing exercise difficulty or duration to prevent burnout")
    elif improvement_analysis.get("trend_direction") == "stable":
        recommendations.append("Try increasing exercise difficulty or duration to continue progressing")
    
    if len(unique_exercises) < 3:
        recommendations.append("Add more exercise variety to prevent adaptation plateau")
    
    if avg_stability < 75:
        recommendations.append("Focus on form quality over quantity")
    
    return {
        "user_id": user_id,
        "report_period": "past_7_days",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "session_completion_rate_percent": round(session_completion_rate, 1),
            "performance_grade": performance_grade,
            "performance_comment": performance_comment
        },
        "stability_metrics": {
            "average_score": round(avg_stability, 1),
            "highest_score": max_stability,
            "lowest_score": min_stability,
            "score_range": round(max_stability - min_stability, 1),
            "standard_deviation": round(statistics.stdev(stability_scores) if len(stability_scores) > 1 else 0, 1)
        },
        "exercise_analysis": {
            "unique_exercises_count": len(unique_exercises),
            "exercises_performed": unique_exercises,
            "most_frequent_exercise": most_common_exercise,
            "average_session_duration": round(statistics.mean(durations), 1)
        },
        "improvement_trend": improvement_analysis,
        "recommendations": recommendations,
        "next_week_goals": {
            "target_sessions": weekly_goal_sessions,
            "target_avg_stability": round(avg_stability + 2, 1),
            "focus_areas": ["consistency", "form_quality", "progressive_overload"]
        }
    }

def recommend_adjustments(user_id: str) -> Dict[str, Any]:
    """Recommend training adjustments based on performance analysis"""
    # Get recent performance data
    recent_data = get_user_exercise_data(user_id, 14)
    
    if len(recent_data) < 3:
        return {
            "error": "Insufficient data",
            "message": "Need at least 3 sessions to provide meaningful recommendations"
        }
    
    # Analyze trends
    stability_trend = calculate_improvement_rate(user_id, "stability_score", 14)
    duration_trend = calculate_improvement_rate(user_id, "duration", 14)
    
    adjustments = {
        "user_id": user_id,
        "analysis_date": datetime.now().isoformat(),
        "adjustments": []
    }
    
    # Stability-based adjustments
    current_stability = stability_trend.get("current_value", 75)
    trend_direction = stability_trend.get("trend_direction", "stable")
    
    if current_stability >= 90 and trend_direction != "declining":
        adjustments["adjustments"].append({
            "category": "difficulty",
            "recommendation": "increase_difficulty",
            "reason": "High stability scores indicate readiness for advanced exercises",
            "suggested_actions": [
                "Add single-limb variations",
                "Increase hold times by 10-15 seconds",
                "Introduce unstable surface training"
            ]
        })
    
    elif current_stability < 70 or trend_direction == "declining":
        adjustments["adjustments"].append({
            "category": "difficulty",
            "recommendation": "decrease_difficulty",
            "reason": "Low or declining stability scores suggest current program is too challenging",
            "suggested_actions": [
                "Return to basic exercise variations",
                "Reduce hold times by 20-30%",
                "Focus on form quality over duration"
            ]
        })
    
    # Duration-based adjustments
    avg_duration = statistics.mean([d["duration"] for d in recent_data])
    
    if avg_duration < 20:
        adjustments["adjustments"].append({
            "category": "volume",
            "recommendation": "increase_duration",
            "reason": "Short session durations may limit training adaptations",
            "suggested_actions": [
                "Gradually increase session time by 5 minutes weekly",
                "Add 1-2 additional exercises per session",
                "Include brief rest periods to extend workout"
            ]
        })
    
    elif avg_duration > 45:
        adjustments["adjustments"].append({
            "category": "volume", 
            "recommendation": "optimize_efficiency",
            "reason": "Very long sessions may indicate inefficient training",
            "suggested_actions": [
                "Focus on higher intensity, shorter duration exercises",
                "Reduce rest periods between exercises",
                "Eliminate less effective exercises"
            ]
        })
    
    # Consistency adjustments
    sessions_per_week = len(recent_data) / 2  # 14 days = 2 weeks
    
    if sessions_per_week < 3:
        adjustments["adjustments"].append({
            "category": "frequency",
            "recommendation": "increase_frequency",
            "reason": "Low training frequency limits progress potential",
            "suggested_actions": [
                "Aim for 4-5 sessions per week",
                "Schedule shorter, more frequent workouts",
                "Set daily movement reminders"
            ]
        })
    
    # Exercise variety adjustments
    exercises = [d["exercise"] for d in recent_data]
    unique_exercises = len(set(exercises))
    
    if unique_exercises < 3:
        adjustments["adjustments"].append({
            "category": "variety",
            "recommendation": "increase_variety",
            "reason": "Limited exercise variety may lead to adaptation plateau",
            "suggested_actions": [
                "Introduce 2-3 new core exercises",
                "Rotate exercises weekly",
                "Combine stability with mobility work"
            ]
        })
    
    # Priority ranking
    priority_map = {
        "difficulty": 1,
        "frequency": 2,
        "volume": 3,
        "variety": 4
    }
    
    adjustments["adjustments"].sort(key=lambda x: priority_map.get(x["category"], 5))
    
    # Add summary
    adjustments["summary"] = {
        "total_recommendations": len(adjustments["adjustments"]),
        "priority_focus": adjustments["adjustments"][0]["category"] if adjustments["adjustments"] else "maintain_current",
        "implementation_timeline": "gradual_over_2_weeks"
    }
    
    return adjustments

def generate_comparative_analysis(user_id: str, comparison_period_days: int = 30) -> Dict[str, Any]:
    """Generate comparative analysis against previous periods"""
    # Get current period data
    current_data = get_user_exercise_data(user_id, comparison_period_days)
    
    # Get previous period data
    start_date = datetime.now() - timedelta(days=comparison_period_days * 2)
    end_date = datetime.now() - timedelta(days=comparison_period_days)
    
    previous_data = [
        data for data in exercise_history
        if data["user_id"] == user_id and
        start_date <= datetime.strptime(data["date"], "%Y-%m-%d") <= end_date
    ]
    
    if not current_data or not previous_data:
        return {
            "error": "Insufficient data for comparison",
            "message": "Need data from both current and previous periods"
        }
    
    # Calculate metrics for both periods
    current_avg_stability = statistics.mean([d["stability_score"] for d in current_data])
    previous_avg_stability = statistics.mean([d["stability_score"] for d in previous_data])
    
    current_avg_duration = statistics.mean([d["duration"] for d in current_data])
    previous_avg_duration = statistics.mean([d["duration"] for d in previous_data])
    
    # Calculate improvements
    stability_improvement = current_avg_stability - previous_avg_stability
    duration_improvement = current_avg_duration - previous_avg_duration
    
    # Calculate percentage changes
    stability_percent_change = (stability_improvement / previous_avg_stability) * 100
    duration_percent_change = (duration_improvement / previous_avg_duration) * 100
    
    return {
        "user_id": user_id,
        "comparison_period_days": comparison_period_days,
        "analysis_date": datetime.now().isoformat(),
        "current_period": {
            "sessions": len(current_data),
            "avg_stability": round(current_avg_stability, 1),
            "avg_duration": round(current_avg_duration, 1)
        },
        "previous_period": {
            "sessions": len(previous_data),
            "avg_stability": round(previous_avg_stability, 1),
            "avg_duration": round(previous_avg_duration, 1)
        },
        "improvements": {
            "stability_score_change": round(stability_improvement, 1),
            "stability_percent_change": round(stability_percent_change, 1),
            "duration_change_minutes": round(duration_improvement, 1),
            "duration_percent_change": round(duration_percent_change, 1),
            "session_count_change": len(current_data) - len(previous_data)
        },
        "performance_assessment": {
            "overall_trend": "improving" if stability_improvement > 1 else "stable" if abs(stability_improvement) <= 1 else "needs_attention",
            "key_strength": "stability" if stability_improvement > duration_improvement else "endurance",
            "focus_recommendation": "maintain_progress" if stability_improvement > 0 else "adjust_training_approach"
        }
    }

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Define available tools for the progress analytics server"""
    return [
        Tool(
            name="calculate_improvement_rate",
            description="Calculate improvement rate for specific metrics over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Metric to analyze (stability_score, duration, etc.)",
                        "default": "stability_score"
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days to analyze (default: 14)",
                        "default": 14
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="generate_weekly_report",
            description="Generate comprehensive weekly progress report with insights and recommendations",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="recommend_adjustments",
            description="Provide personalized training adjustments based on performance analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="generate_comparative_analysis",
            description="Compare current performance with previous periods",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "comparison_period_days": {
                        "type": "number",
                        "description": "Period length for comparison (default: 30)",
                        "default": 30
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_performance_insights",
            description="Get detailed performance insights and trend analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Depth of analysis (basic, detailed, comprehensive)",
                        "default": "detailed"
                    }
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls from agents"""
    
    try:
        if name == "calculate_improvement_rate":
            user_id = arguments["user_id"]
            metric = arguments.get("metric", "stability_score")
            days = arguments.get("days", 14)
            
            result = calculate_improvement_rate(user_id, metric, days)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "generate_weekly_report":
            user_id = arguments["user_id"]
            
            report = generate_weekly_report(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(report, indent=2)
            )]
        
        elif name == "recommend_adjustments":
            user_id = arguments["user_id"]
            
            recommendations = recommend_adjustments(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2)
            )]
        
        elif name == "generate_comparative_analysis":
            user_id = arguments["user_id"]
            comparison_days = arguments.get("comparison_period_days", 30)
            
            analysis = generate_comparative_analysis(user_id, comparison_days)
            
            return [TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
        
        elif name == "get_performance_insights":
            user_id = arguments["user_id"]
            analysis_depth = arguments.get("analysis_depth", "detailed")
            
            # Combine multiple analyses for comprehensive insights
            improvement = calculate_improvement_rate(user_id, "stability_score", 14)
            weekly_report = generate_weekly_report(user_id)
            adjustments = recommend_adjustments(user_id)
            
            insights = {
                "user_id": user_id,
                "analysis_depth": analysis_depth,
                "generated_at": datetime.now().isoformat(),
                "improvement_analysis": improvement,
                "weekly_summary": weekly_report.get("summary", {}),
                "recommended_adjustments": adjustments.get("adjustments", [])[:3],  # Top 3
                "key_insights": [
                    f"Current trend: {improvement.get('trend_direction', 'unknown')}",
                    f"Performance grade: {weekly_report.get('summary', {}).get('performance_grade', 'N/A')}",
                    f"Priority focus: {adjustments.get('summary', {}).get('priority_focus', 'maintain_current')}"
                ]
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(insights, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "calculate_improvement_rate",
                        "generate_weekly_report",
                        "recommend_adjustments",
                        "generate_comparative_analysis",
                        "get_performance_insights"
                    ]
                })
            )]
    
    except Exception as e:
        logger.error(f"Error in tool call {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments
            })
        )]

async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Progress Analytics MCP Server...")
    logger.info(f"Loaded {len(exercise_history)} exercise data points for analysis")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="progress-analytics-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())