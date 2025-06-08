import os
import paho.mqtt.client as mqtt
import subprocess
import threading
import time
from datetime import datetime

# 🌐 Konfiguration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_BASE_TOPIC = os.getenv("MQTT_TOPIC", "home/emeter/1")
SUSYID = int(os.getenv("SUSYID", 292))
SERIAL = int(os.getenv("SERIAL", 3000000000))
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", 1.0))  # Sekunden

# 🔐 Messwert-Puffer
current_values = {
    "voltage": 230.0,
    "current": 0.0,
    "active_power": 0.0,
    "total_forward_energy": 0.0
}
lock = threading.Lock()

def debug(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    color = {
        "INFO": "\033[92m",   # Grün
        "WARN": "\033[93m",   # Gelb
        "ERR":  "\033[91m",   # Rot
        "DBG":  "\033[94m",   # Blau
    }.get(level, "\033[0m")
    print(f"{color}[{level}] {ts} | {msg}\033[0m")

# 🚀 Emeter UDP-Simulator aufrufen
def run_emeter_simulator(payload: dict):
    try:
        cmd = [
            "python3", "simulator/send_emeter_data.py",
            "--susy-id", str(SUSYID),
            "--serial", str(SERIAL),
            "--active-power", str(payload["active_power"]),
            "--total-forward-energy", str(payload["total_forward_energy"]),
            "--voltage", str(payload["voltage"]),
            "--current", str(payload["current"])
        ]
        debug(f"Sende UDP-Emeter-Daten: {cmd}", "DBG")
        subprocess.run(cmd, check=True)
    except Exception as e:
        debug(f"Fehler beim Emeter-Senden: {e}", "ERR")

# 🔁 Wiederholte Emeter-Broadcasts
def broadcast_loop():
    debug("Starte UDP-Broadcast-Loop mit 1Hz", "INFO")
    while True:
        with lock:
            values = current_values.copy()
        debug(f"Broadcast-Werte: {values}", "DBG")
        run_emeter_simulator(values)
        time.sleep(SEND_INTERVAL)

# 📥 MQTT-Callbacks
def on_connect(client, userdata, flags, reasonCode, properties):
    debug(f"MQTT verbunden mit Code: {reasonCode}", "INFO")
    topic = f"{MQTT_BASE_TOPIC}/#"
    client.subscribe(topic)
    debug(f"MQTT Subscribed to: {topic}", "INFO")

def on_message(client, userdata, message):
    topic = message.topic
    value_raw = message.payload.decode("utf-8")
    try:
        value = float(value_raw)
        subkey = topic.split("/")[-1]  # z.B. 'voltage'

        key_map = {
            "voltage": "voltage",
            "current": "current",
            "power": "active_power",
            "yieldtotal": "total_forward_energy"
        }

        if subkey in key_map:
            with lock:
                current_values[key_map[subkey]] = value
            debug(f"MQTT {subkey} → {key_map[subkey]}: {value}", "DBG")
        else:
            debug(f"Ignoriertes Subtopic: {subkey}", "WARN")
    except ValueError:
        debug(f"Ungültiger Wert für {topic}: {value_raw}", "ERR")

# 🔧 MQTT Setup
debug(f"Starte Emeter-Simulator für SERIAL={SERIAL}, SUSYID={SUSYID}", "INFO")
debug(f"MQTT: {MQTT_BROKER}:{MQTT_PORT}, Topic: {MQTT_BASE_TOPIC}/#", "INFO")
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# 🧵 Hintergrundthread starten
threading.Thread(target=broadcast_loop, daemon=True).start()

# 🚦 Starte MQTT-Loop
client.loop_forever()
