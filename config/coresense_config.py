"""
CoreSense Platform Configuration
"""

PLATFORM_CONFIG = {
    'name': 'CoreSense AI Platform',
    'version': '1.0.0', 
    'hardware_mode': 'simulation',
    'sensor_type': 'fabric_pressure_array',
    'deployment': {
        'environment': 'hackathon_demo',
        'mode': 'simulation',
        'future_hardware': 'compression_band_v1'
    }
}

SENSOR_ZONES = {
    'upper_rectus': 'Upper Abdominals',
    'lower_rectus': 'Lower Abdominals',
    'right_oblique': 'Right Oblique', 
    'left_oblique': 'Left Oblique',
    'transverse': 'Deep Core (Transverse Abdominis)',
    'lumbar': 'Lower Back (Lumbar)'
}

MUSCLE_ACTIVATION_THRESHOLDS = {
    'optimal': 0.60,
    'moderate': 0.40,
    'low': 0.20
}

COMPENSATION_PATTERNS = {
    'lower_back_dominance': {
        'indicator': 'lumbar > 0.50 AND transverse < 0.40',
        'coaching': 'Engage deep core, reduce lower back tension'
    },
    'lateral_imbalance': {
        'indicator': 'abs(right_oblique - left_oblique) > 0.20',
        'coaching': 'Balance left and right side engagement'
    }
}

EXERCISE_CONFIGS = {
    'plank': {
        'primary_muscles': ['upper_rectus', 'lower_rectus', 'transverse'],
        'secondary_muscles': ['right_oblique', 'left_oblique'],
        'form_cues': [
            'Keep body straight from head to heels',
            'Engage core muscles',
            'Breathe steadily'
        ]
    },
    'side_plank': {
        'primary_muscles': ['right_oblique', 'left_oblique', 'transverse'],
        'secondary_muscles': ['upper_rectus', 'lower_rectus'],
        'form_cues': [
            'Keep body in straight line',
            'Engage side core muscles',
            'Maintain steady breathing'
        ]
    },
    'dead_bug': {
        'primary_muscles': ['transverse', 'lower_rectus'],
        'secondary_muscles': ['upper_rectus'],
        'form_cues': [
            'Keep lower back pressed to floor',
            'Move slowly and controlled',
            'Coordinate opposite arm and leg'
        ]
    },
    'bird_dog': {
        'primary_muscles': ['transverse', 'lumbar'],
        'secondary_muscles': ['upper_rectus', 'lower_rectus'],
        'form_cues': [
            'Keep hips level',
            'Extend fully but controlled',
            'Maintain neutral spine'
        ]
    }
}

AI_COACHING_CONFIG = {
    'feedback_frequency': 2.0,  # seconds
    'confidence_threshold': 0.85,
    'coaching_modes': {
        'encouraging': {
            'messages': [
                "Great job! Keep that form strong!",
                "You're doing excellent! Hold steady!",
                "Perfect engagement! Stay focused!"
            ]
        },
        'corrective': {
            'messages': [
                "Adjust your form slightly",
                "Focus on your core engagement", 
                "Check your breathing pattern"
            ]
        },
        'motivational': {
            'messages': [
                "You've got this! Push through!",
                "Strong work! Almost there!",
                "Excellent effort! Stay consistent!"
            ]
        }
    }
}

# CoreSense Hardware Simulation Parameters
SIMULATION_CONFIG = {
    'noise_level': 0.05,
    'response_time': 0.1,  # seconds
    'calibration_time': 2.0,  # seconds
    'sensor_sensitivity': 0.95,
    'default_baseline': 0.15
}

# Export configuration objects
__all__ = [
    'PLATFORM_CONFIG',
    'SENSOR_ZONES', 
    'MUSCLE_ACTIVATION_THRESHOLDS',
    'COMPENSATION_PATTERNS',
    'EXERCISE_CONFIGS',
    'AI_COACHING_CONFIG',
    'SIMULATION_CONFIG'
]