"""
PA3 Cloud Development — Main Web Application
A simple sensor dashboard that reads/writes to PostgreSQL
and calls an Azure Function for data aggregation.
"""

import os
import json
import logging
import requests
import psycopg2
from flask import Flask, jsonify, render_template_string, request

# Import shared module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.models import SensorReading, format_response, validate_reading

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuration from environment variables ──
DATABASE_URL = os.environ.get("DATABASE_URL", "")
FUNCTION_URL = os.environ.get("FUNCTION_URL", "")
FUNCTION_KEY = os.environ.get("FUNCTION_KEY", "")


def get_db_connection():
    """Create a database connection using DATABASE_URL."""
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def init_db():
    """Create the sensor_readings table if it does not exist."""
    conn = get_db_connection()
    if conn is None:
        logger.warning("Database not available — skipping init.")
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id SERIAL PRIMARY KEY,
                sensor_id VARCHAR(50) NOT NULL,
                location VARCHAR(100) NOT NULL,
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.error(f"Database init failed: {e}")


# ── HTML template ──
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PA3 Sensor Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
        h1 { color: #0078d4; }
        .card { background: white; border-radius: 8px; padding: 20px; margin: 16px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { padding: 8px 16px; border-radius: 4px; display: inline-block; margin: 4px; }
        .ok { background: #dff6dd; color: #107c10; }
        .err { background: #fde7e9; color: #d13438; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }
        th { background: #0078d4; color: white; }
        button { background: #0078d4; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 4px; }
        button:hover { background: #005a9e; }
        pre { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>PA3 Sensor Dashboard</h1>
    <div class="card">
        <h2>Status</h2>
        <span class="status {{ 'ok' if db_ok else 'err' }}">Database: {{ 'Connected' if db_ok else 'Not connected' }}</span>
        <span class="status {{ 'ok' if func_ok else 'err' }}">Function: {{ 'Configured' if func_ok else 'Not configured' }}</span>
    </div>
    <div class="card">
        <h2>Add Sensor Reading</h2>
        <form id="addForm">
            <input type="text" id="sensor_id" placeholder="Sensor ID" value="SENSOR-001" />
            <input type="text" id="location" placeholder="Location" value="LabA" />
            <input type="number" id="temperature" placeholder="Temperature" value="22.5" step="0.1" />
            <input type="number" id="humidity" placeholder="Humidity" value="65" step="0.1" />
            <button type="submit">Add Reading</button>
        </form>
        <p id="addResult"></p>
    </div>
    <div class="card">
        <h2>Recent Readings</h2>
        <button onclick="loadReadings()">Refresh</button>
        <table>
            <thead><tr><th>Sensor</th><th>Location</th><th>Temp (°C)</th><th>Humidity (%)</th><th>Time</th></tr></thead>
            <tbody id="readingsBody"><tr><td colspan="5">Click Refresh to load</td></tr></tbody>
        </table>
    </div>
    <div class="card">
        <h2>Function: Aggregate Stats</h2>
        <button onclick="callFunction()">Call Aggregation Function</button>
        <pre id="funcResult">Click the button to call the Azure Function</pre>
    </div>
    <script>
        document.getElementById('addForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const body = {
                sensor_id: document.getElementById('sensor_id').value,
                location: document.getElementById('location').value,
                temperature: parseFloat(document.getElementById('temperature').value),
                humidity: parseFloat(document.getElementById('humidity').value)
            };
            const res = await fetch('/api/readings', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
            const data = await res.json();
            document.getElementById('addResult').textContent = data.message || JSON.stringify(data);
        });
        async function loadReadings() {
            const res = await fetch('/api/readings');
            const data = await res.json();
            const tbody = document.getElementById('readingsBody');
            if (data.success && data.data && data.data.length > 0) {
                tbody.innerHTML = data.data.map(r => `<tr><td>${r.sensor_id}</td><td>${r.location}</td><td>${r.temperature}</td><td>${r.humidity}</td><td>${r.timestamp}</td></tr>`).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="5">No readings found</td></tr>';
            }
        }
        async function callFunction() {
            const res = await fetch('/api/aggregate');
            const data = await res.json();
            document.getElementById('funcResult').textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    db_ok = get_db_connection() is not None
    func_ok = bool(FUNCTION_URL)
    return render_template_string(DASHBOARD_HTML, db_ok=db_ok, func_ok=func_ok)


@app.route("/health")
def health():
    return jsonify(format_response(True, message="Healthy"))


@app.route("/api/readings", methods=["GET"])
def get_readings():
    conn = get_db_connection()
    if conn is None:
        return jsonify(format_response(False, message="Database not connected")), 503
    try:
        cur = conn.cursor()
        cur.execute("SELECT sensor_id, location, temperature, humidity, timestamp FROM sensor_readings ORDER BY timestamp DESC LIMIT 20")
        rows = cur.fetchall()
        readings = [
            SensorReading(r[0], r[1], r[2], r[3], str(r[4])).to_dict()
            for r in rows
        ]
        cur.close()
        conn.close()
        return jsonify(format_response(True, data=readings))
    except Exception as e:
        return jsonify(format_response(False, message=str(e))), 500


@app.route("/api/readings", methods=["POST"])
def add_reading():
    data = request.get_json()
    if not data:
        return jsonify(format_response(False, message="No JSON body")), 400

    valid, msg = validate_reading(data)
    if not valid:
        return jsonify(format_response(False, message=msg)), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify(format_response(False, message="Database not connected")), 503
    try:
        reading = SensorReading.from_dict(data)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sensor_readings (sensor_id, location, temperature, humidity) VALUES (%s, %s, %s, %s)",
            (reading.sensor_id, reading.location, reading.temperature, reading.humidity),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(format_response(True, message="Reading added successfully"))
    except Exception as e:
        return jsonify(format_response(False, message=str(e))), 500


@app.route("/api/aggregate")
def aggregate():
    """Calls the Azure Function to get aggregated sensor stats."""
    if not FUNCTION_URL:
        return jsonify(format_response(False, message="FUNCTION_URL not configured")), 503

    try:
        headers = {}
        if FUNCTION_KEY:
            headers["x-functions-key"] = FUNCTION_KEY

        # Fetch recent readings to send to the function for aggregation
        conn = get_db_connection()
        readings_data = []
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT sensor_id, location, temperature, humidity, timestamp FROM sensor_readings ORDER BY timestamp DESC LIMIT 100")
            rows = cur.fetchall()
            readings_data = [
                SensorReading(r[0], r[1], r[2], r[3], str(r[4])).to_dict()
                for r in rows
            ]
            cur.close()
            conn.close()

        resp = requests.post(
            FUNCTION_URL,
            json={"readings": readings_data},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.RequestException as e:
        return jsonify(format_response(False, message=f"Function call failed: {e}")), 502


# ── Initialise DB on startup (runs under both gunicorn and direct python) ──
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
