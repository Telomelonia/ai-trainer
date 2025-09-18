#!/usr/bin/env python3
"""
User Profile MCP Server
Core Training AI Ecosystem - Phase 2

Manages user preferences, fitness goals, and personal settings.
Provides personalized training recommendations and dietary restrictions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

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
logger = logging.getLogger("user-profile-server")

# In-memory user profile storage (in production, use a proper database)
user_profiles = {
    "user_123": {
        "personal_info": {
            "name": "Alex Chen",
            "age": 28,
            "fitness_level": "intermediate",
            "height_cm": 175,
            "weight_kg": 70
        },
        "fitness_goals": [
            "core_strength",
            "balance_improvement", 
            "injury_prevention"
        ],
        "preferences": {
            "session_duration_minutes": 30,
            "difficulty_level": "medium",
            "preferred_exercises": ["plank", "dead_bug", "bird_dog"],
            "avoid_exercises": [],
            "training_frequency": "daily",
            "preferred_time": "morning"
        },
        "health_info": {
            "dietary_restrictions": ["vegetarian"],
            "allergies": [],
            "injuries": ["previous_lower_back"],
            "medications": [],
            "medical_conditions": []
        },
        "created_at": "2025-09-17T10:00:00Z",
        "last_updated": "2025-09-18T08:30:00Z"
    },
    "user_456": {
        "personal_info": {
            "name": "Training Enthusiast",
            "age": 35,
            "fitness_level": "beginner",
            "height_cm": 165,
            "weight_kg": 65
        },
        "fitness_goals": [
            "core_stability",
            "general_fitness"
        ],
        "preferences": {
            "session_duration_minutes": 20,
            "difficulty_level": "easy",
            "preferred_exercises": ["modified_plank"],
            "avoid_exercises": ["advanced_planks"],
            "training_frequency": "3_times_week",
            "preferred_time": "evening"
        },
        "health_info": {
            "dietary_restrictions": [],
            "allergies": ["nuts"],
            "injuries": [],
            "medications": [],
            "medical_conditions": []
        },
        "created_at": "2025-09-15T14:00:00Z",
        "last_updated": "2025-09-17T19:15:00Z"
    }
}

# Create MCP server
server = Server("user-profile-server")

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get complete user profile"""
    return user_profiles.get(user_id)

def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile with new data"""
    if user_id not in user_profiles:
        # Create new profile
        user_profiles[user_id] = {
            "personal_info": {},
            "fitness_goals": [],
            "preferences": {},
            "health_info": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    profile = user_profiles[user_id]
    
    # Update each section
    for section, data in updates.items():
        if section in profile:
            if isinstance(profile[section], dict) and isinstance(data, dict):
                profile[section].update(data)
            else:
                profile[section] = data
    
    profile["last_updated"] = datetime.now().isoformat()
    logger.info(f"Updated profile for user {user_id}")
    
    return profile

def generate_exercise_recommendations(user_id: str) -> Dict[str, Any]:
    """Generate personalized exercise recommendations"""
    profile = get_user_profile(user_id)
    
    if not profile:
        return {"error": "User profile not found"}
    
    fitness_level = profile["personal_info"].get("fitness_level", "beginner")
    goals = profile["fitness_goals"]
    preferences = profile["preferences"]
    health_info = profile["health_info"]
    
    # Base recommendations by fitness level
    if fitness_level == "beginner":
        base_exercises = ["modified_plank", "wall_sit", "dead_bug", "bird_dog"]
        duration = 15
        sets = 2
    elif fitness_level == "intermediate":
        base_exercises = ["plank", "side_plank", "dead_bug", "bird_dog", "pallof_press"]
        duration = 25
        sets = 3
    else:  # advanced
        base_exercises = ["extended_plank", "single_arm_plank", "bird_dog_crunches", "pallof_press", "turkish_getup"]
        duration = 35
        sets = 4
    
    # Filter based on preferences and health
    preferred = preferences.get("preferred_exercises", [])
    avoid = preferences.get("avoid_exercises", [])
    injuries = health_info.get("injuries", [])
    
    # Remove exercises to avoid
    recommended_exercises = [ex for ex in base_exercises if ex not in avoid]
    
    # Prioritize preferred exercises
    if preferred:
        recommended_exercises = preferred + [ex for ex in recommended_exercises if ex not in preferred]
    
    # Modify for injuries
    if "lower_back" in " ".join(injuries):
        recommended_exercises = [ex for ex in recommended_exercises if "plank" not in ex or "modified" in ex]
        recommended_exercises.append("knee_plank")
    
    # Adjust duration based on preferences
    preferred_duration = preferences.get("session_duration_minutes", duration)
    
    return {
        "user_id": user_id,
        "recommended_exercises": recommended_exercises[:5],  # Top 5
        "suggested_duration_minutes": preferred_duration,
        "suggested_sets": sets,
        "difficulty_level": fitness_level,
        "goals_addressed": goals,
        "safety_notes": generate_safety_notes(profile),
        "generated_at": datetime.now().isoformat()
    }

def generate_safety_notes(profile: Dict[str, Any]) -> List[str]:
    """Generate safety notes based on user profile"""
    notes = []
    
    health_info = profile.get("health_info", {})
    injuries = health_info.get("injuries", [])
    medical_conditions = health_info.get("medical_conditions", [])
    age = profile.get("personal_info", {}).get("age", 25)
    
    if injuries:
        notes.append("Take extra care with previous injury areas. Stop if you feel pain.")
    
    if age > 50:
        notes.append("Warm up thoroughly before exercise and cool down afterward.")
    
    if "heart" in " ".join(medical_conditions).lower():
        notes.append("Monitor heart rate and avoid breath holding during exercises.")
    
    if not notes:
        notes.append("Listen to your body and maintain proper form throughout exercises.")
    
    return notes

def calculate_nutrition_needs(user_id: str) -> Dict[str, Any]:
    """Calculate basic nutrition needs based on profile"""
    profile = get_user_profile(user_id)
    
    if not profile:
        return {"error": "User profile not found"}
    
    personal_info = profile["personal_info"]
    height = personal_info.get("height_cm", 170)
    weight = personal_info.get("weight_kg", 70)
    age = personal_info.get("age", 25)
    fitness_level = personal_info.get("fitness_level", "intermediate")
    
    # Basic BMR calculation (Harris-Benedict)
    # Assuming average between male/female for simplicity
    bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    
    # Activity multiplier based on fitness level
    activity_multipliers = {
        "beginner": 1.375,  # Light exercise
        "intermediate": 1.55,  # Moderate exercise
        "advanced": 1.725   # Heavy exercise
    }
    
    daily_calories = bmr * activity_multipliers.get(fitness_level, 1.55)
    
    # Macronutrient distribution for fitness
    protein_grams = weight * 1.6  # 1.6g per kg for active individuals
    protein_calories = protein_grams * 4
    
    fat_calories = daily_calories * 0.25  # 25% from fat
    fat_grams = fat_calories / 9
    
    carb_calories = daily_calories - protein_calories - fat_calories
    carb_grams = carb_calories / 4
    
    # Adjust for dietary restrictions
    dietary_restrictions = profile["health_info"].get("dietary_restrictions", [])
    notes = []
    
    if "vegetarian" in dietary_restrictions:
        notes.append("Focus on plant-based protein sources: legumes, quinoa, tofu, tempeh")
    if "vegan" in dietary_restrictions:
        notes.append("Ensure B12 supplementation and varied plant proteins")
    
    return {
        "user_id": user_id,
        "daily_calories": round(daily_calories),
        "macronutrients": {
            "protein_grams": round(protein_grams, 1),
            "carbohydrates_grams": round(carb_grams, 1),
            "fat_grams": round(fat_grams, 1)
        },
        "dietary_restrictions": dietary_restrictions,
        "nutrition_notes": notes,
        "calculated_at": datetime.now().isoformat()
    }

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Define available tools for the user profile server"""
    return [
        Tool(
            name="get_user_preferences",
            description="Get complete user profile including preferences, goals, and health information",
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
            name="update_fitness_goals",
            description="Update user's fitness goals and training preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of fitness goals (e.g., core_strength, balance, injury_prevention)"
                    },
                    "session_duration": {
                        "type": "number",
                        "description": "Preferred session duration in minutes"
                    },
                    "difficulty_level": {
                        "type": "string",
                        "description": "Preferred difficulty level (easy, medium, hard)"
                    },
                    "training_frequency": {
                        "type": "string",
                        "description": "Training frequency (daily, 3_times_week, etc.)"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="set_dietary_restrictions",
            description="Set or update user's dietary restrictions and health information",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dietary restrictions (vegetarian, vegan, gluten_free, etc.)"
                    },
                    "allergies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of food allergies"
                    },
                    "injuries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of current or previous injuries"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_exercise_recommendations",
            description="Get personalized exercise recommendations based on user profile",
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
            name="calculate_nutrition_needs",
            description="Calculate nutritional needs based on user profile and fitness goals",
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
            name="update_personal_info",
            description="Update user's personal information (age, fitness level, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "name": {
                        "type": "string",
                        "description": "User's name"
                    },
                    "age": {
                        "type": "number",
                        "description": "User's age"
                    },
                    "fitness_level": {
                        "type": "string",
                        "description": "Fitness level (beginner, intermediate, advanced)"
                    },
                    "height_cm": {
                        "type": "number",
                        "description": "Height in centimeters"
                    },
                    "weight_kg": {
                        "type": "number",
                        "description": "Weight in kilograms"
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
        if name == "get_user_preferences":
            user_id = arguments["user_id"]
            profile = get_user_profile(user_id)
            
            if not profile:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "User profile not found",
                        "user_id": user_id
                    })
                )]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "user_id": user_id,
                    "profile": profile,
                    "retrieved_at": datetime.now().isoformat()
                }, indent=2)
            )]
        
        elif name == "update_fitness_goals":
            user_id = arguments["user_id"]
            
            updates = {"fitness_goals": []}
            preferences_updates = {}
            
            if "goals" in arguments:
                updates["fitness_goals"] = arguments["goals"]
            
            if "session_duration" in arguments:
                preferences_updates["session_duration_minutes"] = arguments["session_duration"]
            if "difficulty_level" in arguments:
                preferences_updates["difficulty_level"] = arguments["difficulty_level"]
            if "training_frequency" in arguments:
                preferences_updates["training_frequency"] = arguments["training_frequency"]
            
            if preferences_updates:
                updates["preferences"] = preferences_updates
            
            profile = update_user_profile(user_id, updates)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "updated_profile": profile,
                    "message": "Fitness goals and preferences updated successfully"
                }, indent=2)
            )]
        
        elif name == "set_dietary_restrictions":
            user_id = arguments["user_id"]
            
            health_updates = {}
            if "dietary_restrictions" in arguments:
                health_updates["dietary_restrictions"] = arguments["dietary_restrictions"]
            if "allergies" in arguments:
                health_updates["allergies"] = arguments["allergies"]
            if "injuries" in arguments:
                health_updates["injuries"] = arguments["injuries"]
            
            updates = {"health_info": health_updates}
            profile = update_user_profile(user_id, updates)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "updated_health_info": profile["health_info"],
                    "message": "Health information updated successfully"
                }, indent=2)
            )]
        
        elif name == "get_exercise_recommendations":
            user_id = arguments["user_id"]
            recommendations = generate_exercise_recommendations(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2)
            )]
        
        elif name == "calculate_nutrition_needs":
            user_id = arguments["user_id"]
            nutrition = calculate_nutrition_needs(user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(nutrition, indent=2)
            )]
        
        elif name == "update_personal_info":
            user_id = arguments["user_id"]
            
            personal_info_updates = {}
            for field in ["name", "age", "fitness_level", "height_cm", "weight_kg"]:
                if field in arguments:
                    personal_info_updates[field] = arguments[field]
            
            updates = {"personal_info": personal_info_updates}
            profile = update_user_profile(user_id, updates)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "updated_personal_info": profile["personal_info"],
                    "message": "Personal information updated successfully"
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "get_user_preferences",
                        "update_fitness_goals",
                        "set_dietary_restrictions",
                        "get_exercise_recommendations",
                        "calculate_nutrition_needs",
                        "update_personal_info"
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
    logger.info("Starting User Profile MCP Server...")
    logger.info(f"Loaded {len(user_profiles)} user profiles")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="user-profile-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())