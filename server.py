# server.py

from flask import Flask, jsonify, request
import sqlite3
import time
from datetime import datetime

app = Flask(__name__)
DATABASE = 'agrobox.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                moisture REAL,
                light REAL,
                temperature REAL,
                humidity REAL
            )
        ''')
        db.commit()

@app.route('/api/sensors/current', methods=['GET'])
def get_current_sensor_readings():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT moisture, light, temperature, humidity FROM sensor_readings ORDER BY timestamp DESC LIMIT 1')
    latest_reading = cursor.fetchone()
    db.close()

    if latest_reading:
        return jsonify({
            'moisture': latest_reading['moisture'],
            'light': latest_reading['light'],
            'temperature': latest_reading['temperature'],
            'humidity': latest_reading['humidity']
        })
    else:
        return jsonify({'message': 'No sensor readings available'}), 404

@app.route('/api/sensors/history', methods=['GET'])
def get_historical_sensor_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT timestamp, moisture, light, temperature, humidity FROM sensor_readings ORDER BY timestamp DESC LIMIT 20')
    historical_readings = cursor.fetchall()
    db.close()

    # Reverse the order to show oldest first for charting
    historical_readings.reverse()

    data = {
        'moisture': [],
        'light': [],
        'temperature': [],
        'humidity': [],
        'timestamps': []
    }

    for reading in historical_readings:
        data['timestamps'].append(reading['timestamp'])
        data['moisture'].append(reading['moisture'])
        data['light'].append(reading['light'])
        data['temperature'].append(reading['temperature'])
        data['humidity'].append(reading['humidity'])

    return jsonify(data)

@app.route('/api/controls', methods=['POST'])
def update_controls():
    control_data = request.json
    db = get_db()
    cursor = db.cursor()

    # Assuming control_data contains pump, uvLamp, and peltier states
    # You might want to add more robust validation and error handling here
    pump_state = control_data.get('pump', False)
    uv_lamp_state = control_data.get('uvLamp', False)
    peltier_state = control_data.get('peltier', False)

    cursor.execute('UPDATE controls SET pump = ?, uv_lamp = ?, peltier = ? WHERE id = 1',
                   (pump_state, uv_lamp_state, peltier_state))
    db.commit()
    db.close()
    return jsonify({'message': 'Controls updated successfully'}), 200

def simulate_data_insertion():
    conn = get_db()
    cursor = conn.cursor()
    # Insert dummy data if the table is empty
    cursor.execute('SELECT COUNT(*) FROM sensor_readings')
    if cursor.fetchone()[0] == 0:
        timestamp = datetime.now().isoformat()
        cursor.execute('INSERT INTO sensor_readings (timestamp, moisture, light, temperature, humidity) VALUES (?, ?, ?, ?, ?)', (timestamp, 45.0, 650.0, 24.5, 60.0))
        timestamp = datetime.now().isoformat()
        cursor.execute('INSERT INTO sensor_readings (timestamp, moisture, light, temperature, humidity) VALUES (?, ?, ?, ?, ?)', (timestamp, 46.0, 655.0, 24.7, 61.0))
        timestamp = datetime.now().isoformat()
        cursor.execute('INSERT INTO sensor_readings (timestamp, moisture, light, temperature, humidity) VALUES (?, ?, ?, ?, ?)', (timestamp, 44.0, 645.0, 24.3, 59.0))
        conn.commit()
        print("Dummy sensor data inserted.")
    conn.close()

@app.route('/api/simulate_data', methods=['POST'])
def simulate_data():
    simulate_data_insertion()
    return jsonify({'message': 'Simulated data inserted'}), 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
        simulate_data_insertion() # Insert initial data on startup
    app.run(debug=True)