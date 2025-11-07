from gpiozero import OutputDevice
import sqlite3
from datetime import datetime

ACTUATORS = {
    "uv_light": 17,
    "pump": 27,
    "cooler": 23
}

_relays = {}
_status = {}
_db = None

# ---------- Database ----------
def _init_db(db_path="actuator_status.db"):
    global _db
    _db = sqlite3.connect(db_path)
    cur = _db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS actuator_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            name TEXT NOT NULL,
            state INTEGER NOT NULL
        );
    """)
    _db.commit()

def _log(name, state):
    if _db:
        with _db:
            _db.execute(
                "INSERT INTO actuator_log(timestamp, name, state) VALUES (?, ?, ?)",
                (datetime.now().isoformat(timespec="seconds"), name, int(state))
            )

# ---------- Setup ----------
def init_actuators():
    global _relays, _status
    _init_db()
    for name, pin in ACTUATORS.items():
        r = OutputDevice(pin, active_high=False, initial_value=False)
        _relays[name] = r
        _status[name] = 0

def set_actuator(name, on: bool):
    """Turn actuator on/off and log state."""
    if name not in _relays:
        raise ValueError(f"No actuator {name}")
    relay = _relays[name]
    relay.on() if on else relay.off()
    _status[name] = int(on)
    _log(name, on)

def get_status():
    return dict(_status)

def shutdown_actuators():
    for name in _relays:
        set_actuator(name, False)
    if _db:
        _db.close()
