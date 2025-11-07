from db_handler import create_database, insert_data, read_all, close_database
from sensor_module import connect_serial, close_serial, get_all_data  # your previous file
import time 
if __name__ == "__main__":
    create_database("agrobox.db")
    if connect_serial("/dev/ttyACM0", 9600):
        try:
            while True:
                data = get_all_data()  # [soil, light, temp, hum]
                if all(v is not None for v in data):
                    insert_data(data[0], data[1], data[2], data[3])
                time.sleep(2)
        except KeyboardInterrupt:
            print(read_all()[:5])  # print latest 5 for quick check
        finally:
            close_serial()
            close_database()
