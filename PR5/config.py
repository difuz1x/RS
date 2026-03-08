# MQTT broker settings
BROKER_HOST = "localhost"
BROKER_PORT = 1883

# List of rooms in the house
ROOMS = ["living_room", "bedroom", "kitchen", "hallway", "bathroom"]

ROOM_LABELS = {
    "living_room": "Living Room",
    "bedroom":     "Bedroom",
    "kitchen":     "Kitchen",
    "hallway":     "Hallway",
    "bathroom":    "Bathroom",
}

def topic_motion(room: str)      -> str: return f"home/sensors/motion/{room}"
def topic_light(room: str)       -> str: return f"home/sensors/light/{room}"
def topic_door(door: str)        -> str: return f"home/sensors/door/{door}"
def topic_temperature(room: str) -> str: return f"home/sensors/temperature/{room}"

def topic_lamp_cmd(room: str)   -> str: return f"home/devices/lamp/{room}/command"
def topic_lamp_state(room: str) -> str: return f"home/devices/lamp/{room}/state"

TOPIC_AC_CMD      = "home/devices/ac/command"
TOPIC_AC_STATE    = "home/devices/ac/state"
TOPIC_ALARM_CMD   = "home/devices/alarm/command"
TOPIC_ALARM_STATE = "home/devices/alarm/state"

TOPIC_RULE_FIRED = "home/automation/rule_triggered"
TOPIC_LOG        = "home/system/log"