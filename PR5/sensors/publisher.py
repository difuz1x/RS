import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import random
import threading
import paho.mqtt.client as mqtt

from config import (
    BROKER_HOST, BROKER_PORT, ROOMS,
    topic_motion, topic_light, topic_door, topic_temperature,
    TOPIC_LOG,
)

DOOR_LABELS = {
    "front_door":  "Front Door",
    "back_door":   "Back Door",
    "garage_door": "Garage Door",
}

_state = {
    "motion":      {r: False for r in ROOMS},
    "light":       {r: random.randint(100, 600) for r in ROOMS},
    "temperature": {r: round(random.uniform(19.0, 24.0), 1) for r in ROOMS},
    "doors": {
        "front_door":  "closed",
        "back_door":   "closed",
        "garage_door": "closed",
    },
}


def get_timestamp():
    return time.strftime("%H:%M:%S")


class SensorPublisher:

    def __init__(self):
        self.client = mqtt.Client(client_id="sensor_publisher")
        self.client.on_connect = self._on_connect
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.client.loop_start()
        self._lock = threading.Lock()
        self._running = True

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._log("Sensor publisher connected to broker")
        else:
            print(f"[ERROR] Connection failed: code {rc}")

    def publish(self, topic: str, payload: dict, qos: int = 1):
        self.client.publish(topic, json.dumps(payload), qos=qos, retain=False)

    def _log(self, text: str):
        self.client.publish(TOPIC_LOG, json.dumps({
            "source":    "sensor_publisher",
            "message":   text,
            "timestamp": get_timestamp(),
        }), qos=0)
        print(f"[{get_timestamp()}] {text}")

    def publish_motion(self, room: str, detected: bool):
        with self._lock:
            if _state["motion"][room] == detected:
                return
            _state["motion"][room] = detected
        payload = {
            "sensor":    "motion",
            "room":      room,
            "detected":  detected,
            "timestamp": get_timestamp(),
        }
        self.publish(topic_motion(room), payload)
        self._log(f"Motion {'detected' if detected else 'gone'}: {room}")

    def publish_light(self, room: str, lux: int):
        with self._lock:
            _state["light"][room] = lux
        payload = {
            "sensor":    "light",
            "room":      room,
            "lux":       lux,
            "timestamp": get_timestamp(),
        }
        self.publish(topic_light(room), payload, qos=0)
        self._log(f"Light level {room}: {lux} lux")

    def publish_door(self, door: str, door_state: str):
        with self._lock:
            if _state["doors"][door] == door_state:
                return
            _state["doors"][door] = door_state
        payload = {
            "sensor":    "door",
            "door":      door,
            "state":     door_state,
            "timestamp": get_timestamp(),
        }
        self.publish(topic_door(door), payload)
        self._log(f"Door [{DOOR_LABELS[door]}]: {door_state}")

    def publish_temperature(self, room: str, temp: float):
        with self._lock:
            _state["temperature"][room] = temp
        payload = {
            "sensor":    "temperature",
            "room":      room,
            "celsius":   temp,
            "timestamp": get_timestamp(),
        }
        self.publish(topic_temperature(room), payload, qos=0)
        self._log(f"Temperature {room}: {temp} C")

    def _simulate_motion(self):
        while self._running:
            room = random.choice(ROOMS)
            self.publish_motion(room, True)
            time.sleep(random.uniform(2, 5))
            self.publish_motion(room, False)
            time.sleep(random.uniform(4, 10))

    def _simulate_light(self):
        while self._running:
            for room in ROOMS:
                current = _state["light"][room]
                delta = random.randint(-50, 50)
                new_lux = max(10, min(1000, current + delta))
                if abs(new_lux - current) > 20:
                    self.publish_light(room, new_lux)
            time.sleep(random.uniform(5, 12))

    def _simulate_doors(self):
        doors = list(_state["doors"].keys())
        while self._running:
            door = random.choice(doors)
            self.publish_door(door, "open")
            time.sleep(random.uniform(1, 4))
            self.publish_door(door, "closed")
            time.sleep(random.uniform(15, 30))

    def _simulate_temperature(self):
        while self._running:
            for room in ROOMS:
                current = _state["temperature"][room]
                delta = round(random.uniform(-0.3, 0.3), 1)
                new_temp = round(max(15.0, min(32.0, current + delta)), 1)
                self.publish_temperature(room, new_temp)
            time.sleep(random.uniform(8, 15))

    def run(self):
        print("-" * 50)
        print("SMART HOME -- SENSOR PUBLISHER")
        print("-" * 50)
        print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
        print(f"Rooms: {', '.join(ROOMS)}")
        print("-" * 50)
        time.sleep(1)
        threads = [
            threading.Thread(target=self._simulate_motion,      daemon=True),
            threading.Thread(target=self._simulate_light,       daemon=True),
            threading.Thread(target=self._simulate_doors,       daemon=True),
            threading.Thread(target=self._simulate_temperature, daemon=True),
        ]
        for t in threads:
            t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False
            self._log("Sensor publisher stopped")
            self.client.loop_stop()
            self.client.disconnect()
            print("\nPublisher stopped.")


if __name__ == "__main__":
    SensorPublisher().run()