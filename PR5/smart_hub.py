import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import threading
import paho.mqtt.client as mqtt

from config import (
    BROKER_HOST, BROKER_PORT, ROOMS, ROOM_LABELS,
    topic_motion, topic_light, topic_door, topic_temperature,
    topic_lamp_cmd, topic_lamp_state,
    TOPIC_AC_CMD, TOPIC_AC_STATE,
    TOPIC_ALARM_CMD, TOPIC_ALARM_STATE,
    TOPIC_RULE_FIRED, TOPIC_LOG,
)


def get_timestamp():
    return time.strftime("%H:%M:%S")


class SmartHub:

    def __init__(self):
        self._motion:      dict = {r: False for r in ROOMS}
        self._light:       dict = {r: 300   for r in ROOMS}
        self._temperature: dict = {r: 22.0  for r in ROOMS}
        self._doors:       dict = {}

        self._lamp_state: dict = {r: {"on": False, "brightness": 0} for r in ROOMS}
        self._ac_state    = {"on": False, "target_temp": 22}
        self._alarm_state = {"armed": False, "triggered": False}

        self._pending_timers: dict = {}
        self._lock = threading.Lock()

        self.client = mqtt.Client(client_id="smart_hub")
        self.client.on_connect    = self._on_connect
        self.client.on_message    = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[HUB] Connection error: {rc}")
            return
        print(f"[{get_timestamp()}] Hub connected to broker {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe("home/sensors/#", qos=1)
        client.subscribe("home/devices/#", qos=1)
        self._log("Smart Hub is online. Automation rules are active.")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[{get_timestamp()}] Hub disconnected (rc={rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            return

        topic = msg.topic

        if topic.startswith("home/sensors/motion/"):
            self._handle_motion(topic.split("/")[-1], payload)
        elif topic.startswith("home/sensors/light/"):
            self._handle_light(topic.split("/")[-1], payload)
        elif topic.startswith("home/sensors/door/"):
            self._handle_door(topic.split("/")[-1], payload)
        elif topic.startswith("home/sensors/temperature/"):
            self._handle_temperature(topic.split("/")[-1], payload)
        elif topic.startswith("home/devices/lamp/") and topic.endswith("/state"):
            with self._lock:
                self._lamp_state[topic.split("/")[3]] = payload
        elif topic == TOPIC_AC_STATE:
            with self._lock:
                self._ac_state = payload
        elif topic == TOPIC_ALARM_STATE:
            with self._lock:
                self._alarm_state = payload

    def _handle_motion(self, room: str, data: dict):
        detected = data.get("detected", False)
        with self._lock:
            self._motion[room] = detected
            lux = self._light[room]

        if detected:
            if lux < 200:
                self._fire_rule("R1", f"Motion detected in dark room '{room}'",
                                lambda: self._lamp_on(room, brightness=80))
            self._cancel_timer(f"lamp_off_{room}")
        else:
            if self._lamp_state.get(room, {}).get("on"):
                self._fire_rule("R2", f"Motion gone in '{room}', lamp will turn off in 30 s",
                                lambda r=room: self._schedule_lamp_off(r, delay=30))

    def _handle_light(self, room: str, data: dict):
        lux = data.get("lux", 300)
        with self._lock:
            self._light[room] = lux

        if lux < 100:
            self._fire_rule("R3", f"Low light ({lux} lux) in '{room}'",
                            lambda: self._lamp_on(room, brightness=60))
        elif lux > 700:
            self._fire_rule("R4", f"Bright light ({lux} lux) in '{room}'",
                            lambda: self._lamp_off(room))

    def _handle_door(self, door: str, data: dict):
        door_state = data.get("state", "closed")
        with self._lock:
            self._doors[door] = door_state

        if door == "front_door":
            if door_state == "open":
                self._fire_rule("R5", "Front door opened -> hallway lamp on",
                                lambda: self._lamp_on("hallway", brightness=100))
            else:
                self._fire_rule("R6", "Front door closed -> hallway lamp will turn off in 60 s",
                                lambda: self._schedule_lamp_off("hallway", delay=60))

        if door == "back_door" and door_state == "open":
            hour = int(time.strftime("%H"))
            if hour >= 22 or hour < 6:
                self._fire_rule("R9", "Back door opened at night -> ALARM",
                                self._trigger_alarm)

    def _handle_temperature(self, room: str, data: dict):
        temp = data.get("celsius", 22.0)
        with self._lock:
            self._temperature[room] = temp

        if temp > 26.0 and not self._ac_state.get("on"):
            self._fire_rule("R7", f"Temperature {temp} C in '{room}' -> AC on",
                            lambda: self._ac_on(target=22))
        elif temp < 19.0 and self._ac_state.get("on"):
            self._fire_rule("R8", f"Temperature {temp} C -> AC off", self._ac_off)

    def _lamp_on(self, room: str, brightness: int = 80):
        cmd = {"action": "on", "brightness": brightness, "timestamp": get_timestamp()}
        self.client.publish(topic_lamp_cmd(room), json.dumps(cmd), qos=1)

    def _lamp_off(self, room: str):
        cmd = {"action": "off", "brightness": 0, "timestamp": get_timestamp()}
        self.client.publish(topic_lamp_cmd(room), json.dumps(cmd), qos=1)

    def _schedule_lamp_off(self, room: str, delay: int):
        self._cancel_timer(f"lamp_off_{room}")
        t = threading.Timer(delay, lambda: self._lamp_off(room))
        t.daemon = True
        t.start()
        self._pending_timers[f"lamp_off_{room}"] = t

    def _cancel_timer(self, key: str):
        t = self._pending_timers.pop(key, None)
        if t:
            t.cancel()

    def _ac_on(self, target: int = 22):
        cmd = {"action": "on", "target_temp": target, "timestamp": get_timestamp()}
        self.client.publish(TOPIC_AC_CMD, json.dumps(cmd), qos=1)

    def _ac_off(self):
        cmd = {"action": "off", "timestamp": get_timestamp()}
        self.client.publish(TOPIC_AC_CMD, json.dumps(cmd), qos=1)

    def _trigger_alarm(self):
        cmd = {"action": "trigger", "timestamp": get_timestamp()}
        self.client.publish(TOPIC_ALARM_CMD, json.dumps(cmd), qos=2)

    def _fire_rule(self, rule_id: str, description: str, action=None):
        event = {"rule": rule_id, "description": description, "timestamp": get_timestamp()}
        self.client.publish(TOPIC_RULE_FIRED, json.dumps(event), qos=1)
        print(f"[{get_timestamp()}] [RULE {rule_id}] {description}")
        if action:
            action()

    def _log(self, text: str):
        self.client.publish(TOPIC_LOG, json.dumps({
            "source":    "smart_hub",
            "message":   text,
            "timestamp": get_timestamp(),
        }), qos=0)
        print(f"[{get_timestamp()}] {text}")

    def run(self):
        print("-" * 50)
        print("SMART HOME -- CENTRAL HUB")
        print("-" * 50)
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self._log("Hub stopped")
            self.client.disconnect()
            print("\nHub stopped.")


if __name__ == "__main__":
    SmartHub().run()