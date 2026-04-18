"""
PA3 Cloud Development — Skeleton Azure Function
Students: Implement your aggregation logic here.

This function receives a JSON payload with a list of sensor readings
from the web app and should return aggregated statistics.

Expected input (POST body):
{
    "readings": [
        {
            "sensor_id": "SENSOR-001",
            "location": "LabA",
            "temperature": 22.5,
            "humidity": 65.0,
            "timestamp": "2026-04-09T10:00:00+00:00"
        },
        ...
    ]
}

Expected output (your aggregation results), for example:
{
    "success": true,
    "data": {
        "total_readings": 10,
        "per_sensor": {
            "SENSOR-001": {
                "count": 5,
                "avg_temperature": 22.3,
                "avg_humidity": 64.5,
                "min_temperature": 20.1,
                "max_temperature": 24.0
            }
        }
    },
    "message": "Aggregation complete"
}
"""

import json
import logging
import azure.functions as func
import sys
import os

# Import shared module from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.models import SensorReading, format_response, validate_reading


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Aggregate function triggered.")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps(format_response(False, message="Invalid JSON body")),
            mimetype="application/json",
            status_code=400,
        )

    readings_raw = body.get("readings", [])

    # ----------------------------------------------------------------
    # TODO: Students — implement your aggregation logic below.
    #
    # You have access to:
    #   - readings_raw: list of dicts (each matches SensorReading.to_dict())
    #   - SensorReading, format_response, validate_reading from shared module
    #
    # Suggested aggregations:
    #   - Total reading count
    #   - Per-sensor: count, avg/min/max temperature, avg/min/max humidity
    #   - Per-location: count of readings
    #
    # Replace the placeholder result below with your real implementation.
    # ----------------------------------------------------------------

    # Placeholder — replace this with your aggregation logic
    result = format_response(
        success=True,
        data={
            "total_readings": len(readings_raw),
            "message": "Replace this with your aggregation logic",
        },
        message="Function executed successfully",
    )

    return func.HttpResponse(
        json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )
