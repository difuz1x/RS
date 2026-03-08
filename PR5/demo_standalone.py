import json
import time
import random
import threading
from datetime import datetime

ROOMS = ["living_room", "bedroom", "kitchen", "hallway", "bathroom"]

ROOM_LABELS = {
    "living_room": "Living Room",
    "bedroom":     "Bedroom",
    "kitchen":     "Kitchen",
    "hallway":     "Hallway",
    "bathroom":    "Bathroom",
}

DOORS = {
    "front_door":  "Front Door",
    "back_door":   "Back Door",
    "garage_door": "Garage Door",
}


def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")


def log(component, msg):
    print(f"[{get_timestamp()}] [{component}] {msg}")


# =============================================================================
# Mock Message Broker
# =============================================================================

class MockBroker:

    def __init__(self):
        self._subscriptions: dict = {}
        self._lock = threading.Lock()

    def subscribe(self, topic_pattern: str, callback):
        with self._lock:
            self._subscriptions.setdefault(topic_pattern, []).append(callback)

    def publish(self, topic: str, payload: dict):
        with self._lock:
            callbacks = []
            for pattern, cbs in self._subscriptions.items():
                if self._matches(pattern, topic):
                    callbacks.extend(cbs)
        for cb in callbacks:
            threading.Thread(target=cb, args=(topic, payload), daemon=True).start()

    def _matches(self, pattern: str, topic: str) -> bool:
        if pattern == "#":
            return True
        if pattern == topic:
            return True
        if pattern.endswith("/#"):
            return topic.startswith(pattern[:-2] + "/")
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return topic.startswith(prefix + "/") and "/" not in topic[len(prefix) + 1:]
        return False


broker = MockBroker()

# =============================================================================
# System state
# =============================================================================

system_state = {
    "sensors": {
        "motion":      {r: False for r in ROOMS},
        "light":       {r: random.randint(150, 500) for r in ROOMS},
        "temperature": {r: round(random.uniform(20.0, 24.0), 1) for r in ROOMS},
        "doors":       {d: "closed" for d in DOORS},
    },
    "devices": {
        "lamps": {r: {"on": False, "brightness": 0} for r in ROOMS},
        "ac":    {"on": False, "target_temp": 22},
        "alarm": {"armed": True, "triggered": False},
    },
}

# =============================================================================
# Sensor Publisher
# =============================================================================

class SensorPublisher:

    def __init__(self):
        self._running = True
        self._motion_state = {r: False for r in ROOMS}

    def publish_motion(self, room, detected):
        if self._motion_state[room] == detected:
            return
        self._motion_state[room] = detected
        system_state["sensors"]["motion"][room] = detected
        broker.publish(f"home/sensors/motion/{room}", {
            "sensor": "motion", "room": room,
            "detected": detected, "timestamp": get_timestamp(),
        })
        log("MOTION SENSOR", f"Motion {'detected' if detected else 'gone'}: {room}")

    def publish_light(self, room, lux):
        system_state["sensors"]["light"][room] = lux
        broker.publish(f"home/sensors/light/{room}", {
            "sensor": "light", "room": room,
            "lux": lux, "timestamp": get_timestamp(),
        })
        log("LIGHT SENSOR", f"{room}: {lux} lux")

    def publish_door(self, door, door_state):
        if system_state["sensors"]["doors"][door] == door_state:
            return
        system_state["sensors"]["doors"][door] = door_state
        broker.publish(f"home/sensors/door/{door}", {
            "sensor": "door", "door": door,
            "state": door_state, "timestamp": get_timestamp(),
        })
        log("DOOR SENSOR", f"{DOORS[door]}: {door_state}")

    def publish_temperature(self, room, temp):
        system_state["sensors"]["temperature"][room] = temp
        broker.publish(f"home/sensors/temperature/{room}", {
            "sensor": "temperature", "room": room,
            "celsius": temp, "timestamp": get_timestamp(),
        })
        log("TEMP SENSOR", f"{room}: {temp} C")

    def _simulate_motion(self):
        while self._running:
            room = random.choice(ROOMS)
            self.publish_motion(room, True)
            time.sleep(random.uniform(2, 4))
            self.publish_motion(room, False)
            time.sleep(random.uniform(5, 10))

    def _simulate_light(self):
        while self._running:
            for room in ROOMS:
                cur = system_state["sensors"]["light"][room]
                new = max(10, min(1000, cur + random.randint(-80, 80)))
                if abs(new - cur) > 30:
                    self.publish_light(room, new)
            time.sleep(random.uniform(6, 12))

    def _simulate_doors(self):
        while self._running:
            door = random.choice(list(DOORS.keys()))
            self.publish_door(door, "open")
            time.sleep(random.uniform(1, 3))
            self.publish_door(door, "closed")
            time.sleep(random.uniform(12, 20))

    def _simulate_temperature(self):
        while self._running:
            for room in ROOMS:
                cur = system_state["sensors"]["temperature"][room]
                new = round(max(15.0, min(32.0, cur + random.uniform(-0.5, 0.5))), 1)
                self.publish_temperature(room, new)
            time.sleep(random.uniform(8, 14))

    def start(self):
        for target in [self._simulate_motion, self._simulate_light,
                       self._simulate_doors, self._simulate_temperature]:
            threading.Thread(target=target, daemon=True).start()

    def stop(self):
        self._running = False


# =============================================================================
# Smart Hub
# =============================================================================

class SmartHub:

    def __init__(self):
        self._timers: dict = {}
        self._lock = threading.Lock()
        broker.subscribe("home/sensors/#", self._on_sensor)

    def _on_sensor(self, topic: str, payload: dict):
        parts = topic.split("/")
        sensor_type = parts[2]
        if sensor_type == "motion":
            self._rule_motion(parts[3], payload)
        elif sensor_type == "light":
            self._rule_light(parts[3], payload)
        elif sensor_type == "door":
            self._rule_door(parts[3], payload)
        elif sensor_type == "temperature":
            self._rule_temperature(parts[3], payload)

    def _rule_motion(self, room, data):
        detected = data["detected"]
        lux = system_state["sensors"]["light"][room]
        if detected:
            if lux < 200:
                self._fire("R1", f"Motion detected in dark room [{room}]")
                self._cmd_lamp(room, True, brightness=80)
            self._cancel(f"lamp_off_{room}")
        else:
            if system_state["devices"]["lamps"][room]["on"]:
                self._fire("R2", f"Motion gone [{room}] -> lamp off in 30 s")
                self._delay(f"lamp_off_{room}", 30, lambda r=room: self._cmd_lamp(r, False))

    def _rule_light(self, room, data):
        lux = data["lux"]
        if lux < 100:
            self._fire("R3", f"Low light ({lux} lux) [{room}]")
            self._cmd_lamp(room, True, brightness=60)
        elif lux > 700:
            self._fire("R4", f"Bright light ({lux} lux) [{room}]")
            self._cmd_lamp(room, False)

    def _rule_door(self, door, data):
        door_state = data["state"]
        if door == "front_door":
            if door_state == "open":
                self._fire("R5", "Front door opened -> hallway lamp on")
                self._cmd_lamp("hallway", True, brightness=100)
            else:
                self._fire("R6", "Front door closed -> hallway lamp off in 60 s")
                self._delay("lamp_off_hallway_door", 60, lambda: self._cmd_lamp("hallway", False))
        if door == "back_door" and door_state == "open":
            hour = int(time.strftime("%H"))
            if hour >= 22 or hour < 6:
                self._fire("R9", "Back door opened at night -> ALARM")
                self._cmd_alarm("trigger")

    def _rule_temperature(self, room, data):
        temp = data["celsius"]
        ac_on = system_state["devices"]["ac"]["on"]
        if temp > 26.0 and not ac_on:
            self._fire("R7", f"Temperature {temp} C [{room}] -> AC on")
            self._cmd_ac(True, target=22)
        elif temp < 19.0 and ac_on:
            self._fire("R8", f"Temperature {temp} C -> AC off")
            self._cmd_ac(False)

    def _cmd_lamp(self, room, on, brightness=0):
        broker.publish(f"home/devices/lamp/{room}/command", {
            "action": "on" if on else "off",
            "brightness": brightness, "timestamp": get_timestamp(),
        })

    def _cmd_ac(self, on, target=22):
        broker.publish("home/devices/ac/command", {
            "action": "on" if on else "off",
            "target_temp": target, "timestamp": get_timestamp(),
        })

    def _cmd_alarm(self, action):
        broker.publish("home/devices/alarm/command", {
            "action": action, "timestamp": get_timestamp(),
        })

    def _fire(self, rule_id, desc):
        broker.publish("home/automation/rule_triggered", {
            "rule": rule_id, "description": desc, "timestamp": get_timestamp(),
        })
        log("HUB", f"[{rule_id}] {desc}")

    def _delay(self, key, secs, fn):
        self._cancel(key)
        t = threading.Timer(secs, fn)
        t.daemon = True
        t.start()
        self._timers[key] = t

    def _cancel(self, key):
        t = self._timers.pop(key, None)
        if t:
            t.cancel()


# =============================================================================
# Device Controller
# =============================================================================

class DeviceController:

    def __init__(self):
        broker.subscribe("home/devices/#", self._on_command)

    def _on_command(self, topic, payload):
        if topic.startswith("home/devices/lamp/") and topic.endswith("/command"):
            self._exec_lamp(topic.split("/")[3], payload)
        elif topic == "home/devices/ac/command":
            self._exec_ac(payload)
        elif topic == "home/devices/alarm/command":
            self._exec_alarm(payload)

    def _exec_lamp(self, room, cmd):
        on = cmd["action"] == "on"
        br = cmd.get("brightness", 0)
        system_state["devices"]["lamps"][room] = {"on": on, "brightness": br}
        label = ROOM_LABELS.get(room, room)
        log("LAMP", f"ON  [{label}]  {br}%" if on else f"OFF [{label}]")

    def _exec_ac(self, cmd):
        on = cmd["action"] == "on"
        system_state["devices"]["ac"]["on"] = on
        if on:
            t = cmd.get("target_temp", 22)
            system_state["devices"]["ac"]["target_temp"] = t
            log("AC", f"ON  target={t} C")
        else:
            log("AC", "OFF")

    def _exec_alarm(self, cmd):
        action = cmd["action"]
        if action == "trigger":
            system_state["devices"]["alarm"]["triggered"] = True
            log("ALARM", "*** TRIGGERED *** TRIGGERED *** TRIGGERED ***")
            threading.Timer(8, self._reset_alarm).start()
        elif action == "arm":
            system_state["devices"]["alarm"] = {"armed": True, "triggered": False}
            log("ALARM", "Armed")
        elif action == "disarm":
            system_state["devices"]["alarm"] = {"armed": False, "triggered": False}
            log("ALARM", "Disarmed")

    def _reset_alarm(self):
        system_state["devices"]["alarm"]["triggered"] = False
        log("ALARM", "Reset")


# =============================================================================
# Status report
# =============================================================================

def print_status(cycle: int):
    print()
    print("=" * 55)
    print(f"  SYSTEM STATE  (cycle {cycle})")
    print("=" * 55)
    s = system_state

    print(f"\n  {'Room':<16} {'Motion':<12} {'Light':<10} {'Temp'}")
    print("  " + "-" * 50)
    for r in ROOMS:
        motion = "detected" if s["sensors"]["motion"][r] else "-"
        print(f"  {ROOM_LABELS.get(r, r):<16} {motion:<12} {s['sensors']['light'][r]:<10} {s['sensors']['temperature'][r]:.1f} C")

    print("\n  Doors:")
    for door, label in DOORS.items():
        print(f"  {label:<22} {s['sensors']['doors'].get(door, 'closed')}")

    print("\n  Lamps:")
    for r in ROOMS:
        lamp = s["devices"]["lamps"][r]
        status = f"ON  {lamp['brightness']}%" if lamp["on"] else "OFF"
        print(f"  {ROOM_LABELS.get(r, r):<16} {status}")

    ac    = s["devices"]["ac"]
    alarm = s["devices"]["alarm"]
    print(f"\n  Air conditioner: {'ON  target=' + str(ac['target_temp']) + ' C' if ac['on'] else 'OFF'}")
    print(f"  Alarm system:    {'*** ALARM ***' if alarm.get('triggered') else 'armed' if alarm.get('armed') else 'off'}")
    print()


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    print("-" * 55)
    print("SMART HOME -- Standalone Demo")
    print("-" * 55)
    print("Components:")
    print("  SensorPublisher  -- simulates sensor data")
    print("  SmartHub         -- applies automation rules")
    print("  DeviceController -- executes device commands")
    print("  MockBroker       -- in-process pub/sub broker")
    print()
    print("System state is printed every 15 seconds.")
    print("Press Ctrl+C to stop.")
    print("-" * 55)

    hub       = SmartHub()
    devices   = DeviceController()
    publisher = SensorPublisher()

    time.sleep(0.3)
    print(f"\n[{get_timestamp()}] System started.")
    publisher.start()

    try:
        cycle = 0
        while True:
            time.sleep(15)
            cycle += 1
            print_status(cycle)
    except KeyboardInterrupt:
        publisher.stop()
        print(f"\n[{get_timestamp()}] System stopped.")
        print_status(cycle)