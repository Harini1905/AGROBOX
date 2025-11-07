import serial
import time
import adafruit_dht, board

# ---------- Configuration ----------
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
STARTUP_DELAY = 5          # time to let Arduino start fully
DHT_PIN = board.D4
MAX_WAIT_FOR_ARDUINO = 15  # seconds to wait for first valid data

ser = None
_dht = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)


# ---------- Serial ----------
def connect_serial(port=SERIAL_PORT, baud=BAUD_RATE):
    """Connect to Arduino and wait until it's ready to send data."""
    global ser
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"🔌 Serial connected to {port} at {baud} baud. Waiting {STARTUP_DELAY}s for Arduino...")
        time.sleep(STARTUP_DELAY)
        ser.reset_input_buffer()

        # Wait for first valid line
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_FOR_ARDUINO:
            test = read_serial_line()
            if test and all(v is not None for v in test):
                print(f"✅ Arduino ready after {round(time.time() - start_time, 1)} s")
                return True
            time.sleep(0.5)
        print("⚠️ Arduino did not send valid data within wait window.")
        return True  # still allow program to run
    except serial.SerialException as e:
        print(f"❌ Serial connection failed: {e}")
        return False


def read_serial_line():
    """Read one CSV line like 'soil,light' from Arduino."""
    global ser
    if ser is None or not ser.is_open:
        return None
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            return None
        parts = line.split(",")
        if len(parts) >= 2:
            return [float(parts[0]), float(parts[1])]
        return None
    except Exception:
        return None


def close_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("🔌 Serial connection closed.")


# ---------- DHT22 ----------
def read_dht22():
    """Return temperature (°C) and humidity (%) with stable reading."""
    try:
        time.sleep(0.5)
        _ = _dht.temperature
        time.sleep(0.5)
        t = _dht.temperature
        h = _dht.humidity
        if t is not None and h is not None:
            return round(t, 1), round(h, 1)
        return None, None
    except RuntimeError:
        return None, None


# ---------- Combined ----------
def get_all_data():
    """Return [soil_moisture, light_intensity, temperature, humidity]."""
    data = read_serial_line()
    if data is None:
        data = [None, None]
    t, h = read_dht22()
    return [data[0], data[1], t, h]


# ---------- Stand-alone Test ----------
if __name__ == "__main__":
    if not connect_serial():
        exit(1)
    try:
        while True:
            soil, lux, t, h = get_all_data()
            print(f"Soil:{soil}  Lux:{lux}  Temp:{t}°C  Hum:{h}%")
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        close_serial()

