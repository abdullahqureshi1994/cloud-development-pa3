"""
Shared utilities for PA3 Cloud Development.
This module is imported by both /app and /functions.
"""

from datetime import datetime, timezone


class SensorReading:
    """Data model representing a sensor reading from the database."""

    def __init__(self, sensor_id: str, location: str, temperature: float,
                 humidity: float, timestamp: str = None):
        self.sensor_id = sensor_id
        self.location = location
        self.temperature = temperature
        self.humidity = humidity
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SensorReading":
        return cls(
            sensor_id=data["sensor_id"],
            location=data["location"],
            temperature=data["temperature"],
            humidity=data["humidity"],
            timestamp=data.get("timestamp"),
        )


def format_response(success: bool, data=None, message: str = "") -> dict:
    """Standard JSON response envelope used by both the app and the function."""
    return {
        "success": success,
        "data": data,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def validate_reading(data: dict) -> tuple[bool, str]:
    """Validate that a sensor reading dict has all required fields."""
    required = ["sensor_id", "location", "temperature", "humidity"]
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"
    if not isinstance(data["temperature"], (int, float)):
        return False, "temperature must be a number"
    if not isinstance(data["humidity"], (int, float)):
        return False, "humidity must be a number"
    if not (0 <= data["humidity"] <= 100):
        return False, "humidity must be between 0 and 100"
    return True, ""
