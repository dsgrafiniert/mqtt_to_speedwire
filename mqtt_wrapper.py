import os
import paho.mqtt.client as mqtt
import subprocess
import threading
import time

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_BASE_TOPIC = os.getenv("MQTT_TOPIC", "home/emeter/1")
SUSYID = int(os.getenv("SUSYID", 292))
SERIAL = int(os.getenv("SERIAL", 3000000000))
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", 1.0))  # Sekunden

# 🧠 Gepufferte Messwerte
current_values = {
    "voltage": 230.0,
    "current": 0.0,
    "active_power": 0.0,
    "total_forward_energy": 0.0
}
lock = threading.Lock()

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
        subprocess.run(cmd, check=True)
    except Exception as e:
        print("❌ Fehler beim Emeter-Senden:", e)

# 🔁 1Hz-Loop zum Senden
def broadcast_loop():
    while True:
        with lock:
            values = current_values.copy()
        run_emeter_simulator(values)
        time.sleep(SEND_INTERVAL)

# 📥 MQTT-Callbacks
def on_connect(client, userdata, flags, reasonCode, properties):
    print("✅ MQTT verbunden:", reasonCode)
    client.subscribe(f"{MQTT_BASE_TOPIC}/#")
    print(f"📡 Abonniert: {MQTT_BASE_TOPIC}/#")

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
            print(f"🔄 Aktualisiert: {key_map[subkey]} = {value}")
        else:
            print(f"⚠️ Ignoriert unbekanntes Subtopic: {subkey}")
    except ValueError:
        print(f"⚠️ Ungültiger Wert für {topic}: {value_raw}")

# 🧠 MQTT Setup
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# 🔁 Broadcast starten
threading.Thread(target=broadcast_loop, daemon=True).start()

client.loop_forever()
