import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET

CONFIG_PATH = "config.xml"

def load_config():
    """Return dict from XML or defaults if file missing."""
    try:
        tree = ET.parse(CONFIG_PATH)
        root = tree.getroot()
        targets = root.find("targets")
        uv = root.find("uv")
        return {
            "temperature": float(targets.find("temperature").text),
            "light": float(targets.find("light").text),
            "soil_moisture": float(targets.find("soil_moisture").text),
            "uv_start": int(uv.find("start_hour").text),
            "uv_end": int(uv.find("end_hour").text)
        }
    except Exception:
        return {
            "temperature": 26.0,
            "light": 300.0,
            "soil_moisture": 45.0,
            "uv_start": 9,
            "uv_end": 16
        }

def save_config(data):
    """Write dict to XML."""
    root = ET.Element("config")
    targets = ET.SubElement(root, "targets")
    ET.SubElement(targets, "temperature").text = str(data["temperature"])
    ET.SubElement(targets, "light").text = str(data["light"])
    ET.SubElement(targets, "soil_moisture").text = str(data["soil_moisture"])
    uv = ET.SubElement(root, "uv")
    ET.SubElement(uv, "start_hour").text = str(data["uv_start"])
    ET.SubElement(uv, "end_hour").text = str(data["uv_end"])
    tree = ET.ElementTree(root)
    tree.write(CONFIG_PATH)
    messagebox.showinfo("Saved", "Configuration updated successfully")

def open_editor():
    cfg = load_config()

    root = tk.Tk()
    root.title("Plant System Configuration")
    root.geometry("300x260")
    frm = ttk.Frame(root, padding=15)
    frm.pack(fill="both", expand=True)

    vars = {k: tk.StringVar(value=str(v)) for k, v in cfg.items()}

    labels = {
        "temperature": "Temperature °C (max)",
        "light": "Light threshold (lux)",
        "soil_moisture": "Soil moisture (%)",
        "uv_start": "UV start hour (0-23)",
        "uv_end": "UV end hour (0-23)"
    }

    row = 0
    for key, label in labels.items():
        ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=vars[key]).grid(row=row, column=1, pady=3)
        row += 1

    def save_and_exit():
        try:
            data = {k: float(v.get()) if "uv" not in k else int(v.get()) for k, v in vars.items()}
            save_config(data)
            root.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")

    ttk.Button(frm, text="Save", command=save_and_exit).grid(row=row, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    open_editor()
