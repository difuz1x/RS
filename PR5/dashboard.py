import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
import threading
import paho.mqtt.client as mqtt

from config import BROKER_HOST, BROKER_PORT, ROOMS, ROOM_LABELS

DOOR_LABELS = {
    "front_door":  "Front Door",
    "back_door":   "Back Door",
    "garage_door": "Garage Door",
}

state = {
    "motion":      {r: False for r in ROOMS},
    "light":       {r: 0     for r in ROOMS},
    "temperature": {r: 0.0   for r in ROOMS},
    "doors": {
        "front_door":  "closed",
        "back_door":   "closed",
        "garage_door": "closed",
    },
    "lamps":      {r: {"on": False, "brightness": 0} for r in ROOMS},
    "ac":         {"on": False, "target_temp": 22},
    "alarm":      {"armed": False, "triggered": False},
    "last_rules": [],
    "log":        [],
}

_lock = threading.Lock()


def get_timestamp():
    return time.strftime("%H:%M:%S")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_status():
    clear_screen()
    print("=" * 60)
    print(f"  SMART HOME DASHBOARD  |  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    with _lock:
        print("\n  SENSORS")
        print("-" * 60)
        print(f"  {'Room':<16} {'Motion':<12} {'Light':<12} {'Temperature'}")
        print("-" * 60)
        for r in ROOMS:
            motion = "detected" if state["motion"][r] else "-"
            lux    = f"{state['light'][r]} lux"
            temp   = f"{state['temperature'][r]:.1f} C"
            print(f"  {ROOM_LABELS.get(r, r):<16} {motion:<12} {lux:<12} {temp}")

        print("\n  DOORS")
        print("-" * 60)
        for door, label in DOOR_LABELS.items():
            status = "OPEN" if state["doors"].get(door) == "open" else "closed"
            print(f"  {label:<22} {status}")

        print("\n  LAMPS")
        print("-" * 60)
        for r in ROOMS:
            lamp = state["lamps"][r]
            status = f"ON   brightness={lamp['brightness']}%" if lamp["on"] else "OFF"
            print(f"  {ROOM_LABELS.get(r, r):<16} {status}")

        print("\n  OTHER DEVICES")
        print("-" * 60)
        ac = state["ac"]
        ac_status = f"ON  target={ac['target_temp']} C" if ac["on"] else "OFF"
        print(f"  {'Air conditioner':<22} {ac_status}")

        alarm = state["alarm"]
        if alarm.get("triggered"):
            alarm_status = "*** ALARM ***"
        elif alarm.get("armed"):
            alarm_status = "armed"
        else:
            alarm_status = "off"
        print(f"  {'Alarm system':<22} {alarm_status}")

        print("\n  RECENT AUTOMATION EVENTS")
        print("-" * 60)
        if state["last_rules"]:
            for entry in state["last_rules"]:
                print(f"  [{entry['time']}] [{entry['rule']}] {entry['desc']}")
        else:
            print("  (waiting for events...)")

        print("\n  SYSTEM LOG")
        print("-" * 60)
        if state["log"]:
            for entry in state["log"]:
                print(f"  [{entry['time']}] {entry['msg']}")
        else:
            print("  (waiting for messages...)")

    print("=" * 60)
    print("  Press Ctrl+C to stop")
    print("=" * 60)


def on_connect(client, userdata, flags, rc):
    client.subscribe("home/#", qos=0)
    print(f"[{get_timestamp()}] Dashboard connected to broker")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    topic = msg.topic

    with _lock:
        if topic.startswith("home/sensors/motion/"):
            room = topic.split("/")[-1]
            if room in state["motion"]:
                state["motion"][room] = payload.get("detected", False)

        elif topic.startswith("home/sensors/light/"):
            room = topic.split("/")[-1]
            if room in state["light"]:
                state["light"][room] = payload.get("lux", 0)

        elif topic.startswith("home/sensors/temperature/"):
            room = topic.split("/")[-1]
            if room in state["temperature"]:
                state["temperature"][room] = payload.get("celsius", 0.0)

        elif topic.startswith("home/sensors/door/"):
            door = topic.split("/")[-1]
            state["doors"][door] = payload.get("state", "closed")

        elif topic.startswith("home/devices/lamp/") and topic.endswith("/state"):
            room = topic.split("/")[3]
            if room in state["lamps"]:
                state["lamps"][room] = {
                    "on":         payload.get("on", False),
                    "brightness": payload.get("brightness", 0),
                }

        elif topic == "home/devices/ac/state":
            state["ac"]["on"]          = payload.get("on", False)
            state["ac"]["target_temp"] = payload.get("target_temp", 22)

        elif topic == "home/devices/alarm/state":
            state["alarm"]["armed"]     = payload.get("armed", False)
            state["alarm"]["triggered"] = payload.get("triggered", False)

        elif topic == "home/automation/rule_triggered":
            entry = {
                "time": payload.get("timestamp", ""),
                "rule": payload.get("rule", ""),
                "desc": payload.get("description", ""),
            }
            state["last_rules"].insert(0, entry)
            state["last_rules"] = state["last_rules"][:6]

        elif topic == "home/system/log":
            entry = {
                "time": payload.get("timestamp", ""),
                "msg":  payload.get("message", ""),
            }
            state["log"].insert(0, entry)
            state["log"] = state["log"][:6]


def run_mqtt():
    client = mqtt.Client(client_id="dashboard")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    threading.Thread(target=run_mqtt, daemon=True).start()
    time.sleep(0.8)
    print(f"[{get_timestamp()}] Dashboard started. Waiting for data...")
    try:
        while True:
            print_status()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")