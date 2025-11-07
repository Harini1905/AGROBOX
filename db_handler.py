import sqlite3
from datetime import datetime

con = None
cur = None

def create_database(db_name="agrobox.db"):
    """Create SQLite database with sensors + actuator states."""
    global con, cur
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            moisture REAL,
            light REAL,
            temperature REAL,
            humidity REAL
        );
    """)
    con.commit()
    return con


def insert_data(moisture, light, temperature, humidity):
    """Insert one complete data row."""
    global con, cur
    if con is None:
        raise RuntimeError("Database not initialized. Call create_database() first.")
    ts = datetime.now().isoformat(timespec='seconds')
    cur.execute("""
        INSERT INTO sensor_readings(
            timestamp, moisture, light, temperature, humidity
        ) VALUES (?, ?, ?, ?, ?);
    """, (ts, moisture, light, temperature, humidity))
    con.commit()


def read_recent(limit=20):
    """Fetch recent system data."""
    global cur
    if cur is None:
        raise RuntimeError("Database not initialized.")
    cur.execute("SELECT timestamp, moisture, light, temperature, humidity FROM sensor_readings ORDER BY id DESC LIMIT ?;", (limit,))
    return cur.fetchall()


def close_database():
    global con
    if con:
        con.close()
        con = None

