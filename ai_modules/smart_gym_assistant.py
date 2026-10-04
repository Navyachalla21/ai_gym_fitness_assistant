import random
import time

def simulate_sensor_reading() -> dict:
    """
    Simulates a reading from IoT-enabled gym equipment.
    NOTE: This is simulated data for demonstration, since physical IoT hardware
    (smart resistance machines) is not available for this project. The interface
    below (sensor reading -> recommendation) is designed to plug into real
    MQTT-based hardware data in a production deployment.
    """
    return {
        "timestamp": time.time(),
        "heart_rate_bpm": random.randint(85, 160),
        "resistance_level": random.randint(1, 10),
        "equipment_status": random.choice(["active", "idle", "cooldown"])
    }


def recommend_adjustment(sensor_data: dict) -> str:
    """Recommends a resistance/rest adjustment based on the (simulated) sensor reading."""
    hr = sensor_data["heart_rate_bpm"]
    resistance = int(sensor_data.get("resistance_level", 5))

    if hr > 150:
        return "Heart rate is high — recommend reducing resistance and taking a short rest."
    elif hr < 100:
        if resistance >= 10:
            return ("Heart rate is low and resistance is already at the maximum — "
                    "try a faster pace or a longer session instead.")
        return "Heart rate is low — you could increase resistance for a more effective session."
    else:
        return "Heart rate is in a healthy training zone — maintain current intensity."


def recommend_adjustment_detailed(sensor_data: dict) -> dict:
    """Structured version of the recommendation: advice text + a concrete new resistance level
    and rest time, so the equipment can be adjusted automatically."""
    hr = sensor_data["heart_rate_bpm"]
    resistance = int(sensor_data["resistance_level"])
    status = sensor_data.get("equipment_status", "active")

    if hr > 150:
        zone, intensity = "High", "Reduce"
        new_resistance, rest_seconds = max(1, resistance - 2), 90
    elif hr < 100:
        zone, intensity = "Low", ("Increase" if resistance < 10 else "Maintain")
        new_resistance, rest_seconds = min(10, resistance + 1), 30
    else:
        zone, intensity = "Target", "Maintain"
        new_resistance, rest_seconds = resistance, 45

    if status == "cooldown":      # cooling down: never push the resistance up
        new_resistance = min(new_resistance, resistance)

    return {
        "advice": recommend_adjustment(sensor_data),
        "heart_rate_zone": zone,
        "intensity_action": intensity,
        "current_resistance": resistance,
        "recommended_resistance": new_resistance,
        "recommended_rest_seconds": rest_seconds,
    }
