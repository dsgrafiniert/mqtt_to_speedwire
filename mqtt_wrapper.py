import os
import paho.mqtt.client as mqtt
import subprocess
import json

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "home/power/emeter")
SUSYID = os.getenv("SUSYID", "12345")
SERIAL = os.getenv("SERIAL", "10001")

def on_connect(client, userdata, flags, reasonCode, properties):
    print("Connected with reasonCode", reasonCode)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Message received on {msg.topic}: {msg.payload}")

    try:
        payload = json.loads(msg.payload)
        power = int(payload.get("power", 0))
        voltage = float(payload.get("voltage", 230.0))
        current = float(payload.get("current", 0.0))

        print(f"[{MQTT_TOPIC}] Power={power}W Voltage={voltage}V Current={current}A")

        subprocess.Popen([
            "python", "/app/simulator/sma_emeter_simulator.py",
            "--host", "239.12.255.254",
            "--port", "9522",
            "--power", str(power),
            "--voltage", str(voltage),
            "--current", str(current),
            "--susyid", SUSYID,
            "--serial", SERIAL
        ])
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print(f"[INFO] Subscribed to {MQTT_TOPIC} on {MQTT_BROKER}:{MQTT_PORT}")
    client.loop_forever()

if __name__ == "__main__":
    main()
