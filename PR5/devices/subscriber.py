import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
import paho.mqtt.client as mqtt

from config import (
    BROKER_HOST, BROKER_PORT, ROOMS, ROOM_LABELS,
    topic_lamp_cmd, topic_lamp_state,
    TOPIC_AC_CMD, TOPIC_AC_STATE,
    TOPIC_ALARM_CMD, TOPIC_ALARM_STATE,
    TOPIC_LOG,
)


def get_timestamp():
    return time.strftime("%H:%M:%S")


class DeviceSubscriber:

    def __init__(self):
        self._lamps: dict = {r: {"on": False, "brightness": 0} for r in ROOMS}
        self._ac    = {"on": False, "target_temp": 22, "current_temp": 22.0}
        self._alarm = {"armed": True, "triggered": False}
        self._lock  = threading.Lock()

        self.client = mqtt.Client(client_id="device_subscriber")
        self.client.on_connect    = self._on_connect
        self.client.on_message    = self._on_message
        self.client.on_disconnect = lambda c, u, rc: print(
            f"[{get_timestamp()}] Disconnected (rc={rc})"
        )

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[DEVICES] Connection error: {rc}")
            return
        print(f"[{get_timestamp()}] Device controller connected")
        for room in ROOMS:
            client.subscribe(topic_lamp_cmd(room), qos=1)
        client.subscribe(TOPIC_AC_CMD,    qos=1)
        client.subscribe(TOPIC_ALARM_CMD, qos=2)
        self._log("Device controller is online. Waiting for commands.")
        self._publish_all_states()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            return

        topic = msg.topic

        if topic.startswith("home/devices/lamp/") and topic.endswith("/command"):
            self._exec_lamp(topic.split("/")[3], payload)
        elif topic == TOPIC_AC_CMD:
            self._exec_ac(payload)
        elif topic == TOPIC_ALARM_CMD:
            self._exec_alarm(payload)

    def _exec_lamp(self, room: str, cmd: dict):
        action     = cmd.get("action", "off")
        brightness = cmd.get("brightness", 80)
        label      = ROOM_LABELS.get(room, room)
        with self._lock:
            if action == "on":
                self._lamps[room] = {"on": True, "brightness": brightness}
                print(f"[{get_timestamp()}] LAMP ON  [{label}] brightness={brightness}%")
            else:
                self._lamps[room] = {"on": False, "brightness": 0}
                print(f"[{get_timestamp()}] LAMP OFF [{label}]")
            state = dict(self._lamps[room])
        self.client.publish(
            topic_lamp_state(room),
            json.dumps({**state, "room": room, "timestamp": get_timestamp()}),
            qos=1, retain=True,
        )

    def _exec_ac(self, cmd: dict):
        action = cmd.get("action", "off")
        with self._lock:
            if action == "on":
                target = cmd.get("target_temp", 22)
                self._ac = {"on": True, "target_temp": target, "current_temp": self._ac["current_temp"]}
                print(f"[{get_timestamp()}] AC ON  target={target} C")
            else:
                self._ac["on"] = False
                print(f"[{get_timestamp()}] AC OFF")
            state = dict(self._ac)
        self.client.publish(
            TOPIC_AC_STATE,
            json.dumps({**state, "timestamp": get_timestamp()}),
            qos=1, retain=True,
        )

    def _exec_alarm(self, cmd: dict):
        action = cmd.get("action", "arm")
        with self._lock:
            if action == "trigger":
                self._alarm = {"armed": True, "triggered": True}
                print(f"[{get_timestamp()}] *** ALARM TRIGGERED ***")
                threading.Timer(10, self._reset_alarm).start()
            elif action == "arm":
                self._alarm = {"armed": True, "triggered": False}
                print(f"[{get_timestamp()}] Alarm armed")
            elif action == "disarm":
                self._alarm = {"armed": False, "triggered": False}
                print(f"[{get_timestamp()}] Alarm disarmed")
            state = dict(self._alarm)
        self.client.publish(
            TOPIC_ALARM_STATE,
            json.dumps({**state, "timestamp": get_timestamp()}),
            qos=2, retain=True,
        )

    def _reset_alarm(self):
        with self._lock:
            self._alarm["triggered"] = False
        self.client.publish(
            TOPIC_ALARM_STATE,
            json.dumps({**self._alarm, "timestamp": get_timestamp()}),
            qos=1, retain=True,
        )
        print(f"[{get_timestamp()}] Alarm reset")

    def _publish_all_states(self):
        for room in ROOMS:
            self.client.publish(
                topic_lamp_state(room),
                json.dumps({**self._lamps[room], "room": room, "timestamp": get_timestamp()}),
                qos=1, retain=True,
            )
        self.client.publish(TOPIC_AC_STATE,
                            json.dumps({**self._ac, "timestamp": get_timestamp()}),
                            qos=1, retain=True)
        self.client.publish(TOPIC_ALARM_STATE,
                            json.dumps({**self._alarm, "timestamp": get_timestamp()}),
                            qos=1, retain=True)

    def _log(self, text: str):
        self.client.publish(TOPIC_LOG, json.dumps({
            "source":    "device_subscriber",
            "message":   text,
            "timestamp": get_timestamp(),
        }), qos=0)
        print(f"[{get_timestamp()}] {text}")

    def run(self):
        print("-" * 50)
        print("SMART HOME -- DEVICE CONTROLLER")
        print("-" * 50)
        print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
        print("-" * 50)
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self._log("Device controller stopped")
            self.client.disconnect()
            print("\nDevice controller stopped.")


if __name__ == "__main__":
    DeviceSubscriber().run()