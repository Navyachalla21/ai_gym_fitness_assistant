"""
Simulated IoT gym machine (stand-in for a real smart treadmill / resistance bike).

Publishes telemetry to an MQTT broker every few seconds and obeys resistance commands sent by the
backend. Run it on any computer while the backend is running:

    python ai_modules/iot_simulator.py            # runs until Ctrl+C
    python ai_modules/iot_simulator.py --count 30 # publish 30 readings, then stop

Requires:  pip install paho-mqtt
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mqtt_bridge as mb  # noqa: E402  (same settings as the backend: broker, port, topics)


class SimulatedMachine:
    """A workout that cycles warm-up -> work -> peak -> cool-down (about 2 minutes per cycle)."""
    CYCLE_SECONDS = 120

    def __init__(self, resistance: int = 5):
        self.resistance = resistance
        self.t = 0.0

    def apply_command(self, resistance_level: int):
        self.resistance = max(1, min(10, int(resistance_level)))

    def reading(self, dt: float = 2.0) -> dict:
        self.t += dt
        phase = (self.t % self.CYCLE_SECONDS) / self.CYCLE_SECONDS            # 0..1 through the cycle
        effort = 0.5 - 0.5 * math.cos(2 * math.pi * phase)                      # 0 -> 1 -> 0
        hr = 85 + effort * 80 + (self.resistance - 5) * 3 + 2 * math.sin(self.t)  # higher resistance -> higher HR
        status = "cooldown" if phase > 0.8 else "active" if phase > 0.1 else "idle"
        return {"heart_rate_bpm": int(round(max(40, min(200, hr)))), "resistance_level": self.resistance,
                "equipment_status": status, "timestamp": time.time()}


def main():
    ap = argparse.ArgumentParser(description="Simulated IoT gym machine")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between readings (default 2)")
    ap.add_argument("--count", type=int, default=0, help="stop after this many readings (default: run forever)")
    args = ap.parse_args()

    machine = SimulatedMachine()
    client = mb.make_client(f"aigym-simulator-{os.getpid()}")

    def on_connect(c, userdata, flags, rc, *a):
        if mb.connect_ok(rc):
            c.subscribe(mb.COMMAND_TOPIC)
            print(f"Connected to {mb.BROKER}:{mb.PORT} - publishing to {mb.TELEMETRY_TOPIC}")
        else:
            print(f"Broker refused connection: {rc}")

    def on_message(c, userdata, msg):
        try:
            level = int(json.loads(msg.payload)["resistance_level"])
        except (ValueError, KeyError, TypeError):
            return
        machine.apply_command(level)
        print(f"<- command received: resistance set to {machine.resistance}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mb.BROKER, mb.PORT, keepalive=30)
    client.loop_start()

    sent = 0
    try:
        while not args.count or sent < args.count:
            r = machine.reading(args.interval)
            client.publish(mb.TELEMETRY_TOPIC, json.dumps(r))
            sent += 1
            print(f"-> HR {r['heart_rate_bpm']} bpm | resistance {r['resistance_level']} | {r['equipment_status']}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
