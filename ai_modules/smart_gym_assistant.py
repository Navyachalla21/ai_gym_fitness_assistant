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

    if hr > 150:
        return "Heart rate is high — recommend reducing resistance and taking a short rest."
    elif hr < 100:
        return "Heart rate is low — you could increase resistance for a more effective session."
    else:
        return "Heart rate is in a healthy training zone — maintain current intensity."