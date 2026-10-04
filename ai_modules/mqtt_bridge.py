"""
MQTT bridge for the Smart Gym Assistant (Module 3).

Equipment (or iot_simulator.py) publishes JSON telemetry to a topic on an MQTT broker; this bridge
subscribes in a background thread and keeps the most recent reading. The backend serves that
reading, and can publish a resistance command back to the equipment.

    equipment --publish--> [MQTT broker] --subscribe--> backend (this file) --> dashboard
    equipment <--command-- [MQTT broker] <--publish---- backend

Settings (environment variables):
    MQTT_BROKER   default broker.hivemq.com   (a free PUBLIC broker - anyone can read/write topics,
                                               so keep the topic name private and non-sensitive)
    MQTT_PORT     default 1883
    MQTT_TOPIC    default aigym-nk-7f3a9c/equipment/01   (telemetry goes to <topic>/telemetry,
                                                          commands to <topic>/command)
"""
import json
import os
import threading
import time

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "1883"))
BASE_TOPIC = os.getenv("MQTT_TOPIC", "aigym-nk-7f3a9c/equipment/01")
TELEMETRY_TOPIC = f"{BASE_TOPIC}/telemetry"
COMMAND_TOPIC = f"{BASE_TOPIC}/command"

VALID_STATUS = {"active", "idle", "cooldown"}


def make_client(client_id: str):
    """Creates a paho-mqtt client for both paho 1.x and 2.x."""
    import paho.mqtt.client as mqtt
    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    return mqtt.Client(client_id=client_id)


def connect_ok(rc) -> bool:
    """True if a paho connect result code means success (works for paho 1.x ints and 2.x ReasonCode)."""
    failure = getattr(rc, "is_failure", None)
    return (not failure) if failure is not None else rc == 0


def parse_reading(payload: bytes | str):
    """Validates one telemetry message. Returns a clean dict, or None if it is not usable."""
    try:
        data = json.loads(payload)
        hr = int(data["heart_rate_bpm"])
        res = int(data["resistance_level"])
        status = str(data.get("equipment_status", "active"))
    except (ValueError, KeyError, TypeError):
        return None
    if not (30 <= hr <= 230 and 1 <= res <= 10 and status in VALID_STATUS):
        return None
    return {"heart_rate_bpm": hr, "resistance_level": res, "equipment_status": status,
            "timestamp": float(data.get("timestamp", time.time()))}


class MqttBridge:
    def __init__(self):
        self._lock = threading.Lock()
        self._started = False
        self._client = None
        self._latest = None
        self._received_at = 0.0
        self.connected = False
        self.error = None

    # ------------------------------------------------------------- lifecycle
    def start(self):
        """Starts the background subscriber once. Safe to call on every request."""
        with self._lock:
            if self._started:
                return
            self._started = True
        try:
            client = make_client(f"aigym-backend-{os.getpid()}-{int(time.time())}")
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message
            client.reconnect_delay_set(min_delay=1, max_delay=30)
            client.connect_async(BROKER, PORT, keepalive=30)
            client.loop_start()           # network loop runs in its own thread
            self._client = client
        except ImportError:
            self.error = "paho-mqtt is not installed (pip install paho-mqtt)"
        except Exception as exc:  # noqa: BLE001
            self.error = f"could not start MQTT client: {exc}"

    # ------------------------------------------------------------- callbacks
    def _on_connect(self, client, userdata, flags, rc, *args):
        if connect_ok(rc):
            self.connected = True
            self.error = None
            client.subscribe(TELEMETRY_TOPIC, qos=0)   # (re)subscribe after every reconnect
        else:
            self.connected = False
            self.error = f"broker refused the connection (code {rc})"

    def _on_disconnect(self, client, userdata, *args):
        self.connected = False

    def _on_message(self, client, userdata, msg):
        reading = parse_reading(msg.payload)
        if reading is None:
            return                      # ignore malformed / out-of-range messages
        with self._lock:
            self._latest = reading
            self._received_at = time.time()

    # --------------------------------------------------------------- access
    def latest(self, max_age_seconds: float = 15.0):
        """Most recent valid reading if it is fresh enough, else None."""
        with self._lock:
            if self._latest and time.time() - self._received_at <= max_age_seconds:
                return dict(self._latest)
        return None

    def publish_command(self, resistance_level: int) -> bool:
        """Asks the equipment to change its resistance."""
        if not (self._client and self.connected):
            return False
        payload = json.dumps({"resistance_level": int(resistance_level), "timestamp": time.time()})
        info = self._client.publish(COMMAND_TOPIC, payload, qos=0)
        return getattr(info, "rc", 0) == 0

    def status(self) -> dict:
        return {"connected": self.connected, "broker": f"{BROKER}:{PORT}", "topic": TELEMETRY_TOPIC,
                "error": self.error}


bridge = MqttBridge()
