import os
import json
import paho.mqtt.client as mqtt
import subprocess
import threading
import time

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/emeter")
SUSYID = int(os.getenv("SUSYID", 292))
SERIAL = int(os.getenv("SERIAL", 3000000000))
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", 1.0))  # seconds

# 🔁 Aktuelle Werte werden hier gepuffert
current_values = {
    "active_power": 0.0,
    "total_forward_energy": 0.0,
    "voltage": 230.0,
    "current": 0.0
}
lock = threading.Lock()

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
        subprocess.run(cmd, check=True)
    except Exception as e:
        print("❌ Error running simulator:", e)

# 🔁 Loop, das jede Sekunde einen Broadcast sendet
def broadcast_loop():
    while True:
        with lock:
            values = current_values.copy()
        run_emeter_simulator(values)
        time.sleep(SEND_INTERVAL)

# 📥 MQTT-Callback
def on_connect(client, userdata, flags, reasonCode, properties):
    print("✅ Connected to MQTT")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, message):
    global current_values
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        print(f"📨 MQTT: {payload}")
        with lock:
            current_values.update({
                "active_power": float(payload.get("active_power", current_values["active_power"])),
                "total_forward_energy": float(payload.get("total_forward_energy", current_values["total_forward_energy"])),
                "voltage": float(payload.get("voltage", current_values["voltage"])),
                "current": float(payload.get("current", current_values["current"]))
            })
    except Exception as e:
        print("❌ Error in MQTT payload:", e)

# 🧠 MQTT Setup
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# 🔁 Starte Hintergrund-Broadcast-Thread
threading.Thread(target=broadcast_loop, daemon=True).start()

client.loop_forever()
