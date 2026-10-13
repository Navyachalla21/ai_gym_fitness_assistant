"""
Heart-rate monitor with on-screen display and voice alerts (college extension, Smart Gym).

The heart-rate SOURCE is pluggable, the alert logic and the screen stay the same:
  --source sim      simulated workout (works anywhere; press w / s to push the rate up / down)
  --source manual   you set the value with the w / s keys (start at 75)
  --source ble      a Bluetooth heart-rate device (strap, armband, or a watch that broadcasts
                    the standard Heart Rate service 0x180D). Needs:  pip install bleak

Run:  python ai_modules/heart_monitor.py --source sim --age 20
Keys (click the window first):  w = +5 bpm   s = -5 bpm   m = mute voice   q / Esc = quit

Alerts are based on a rough maximum heart rate (220 - age). This is a fitness aid for a demo,
NOT a medical device.
"""
import argparse
import asyncio
import collections
import math
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_coach import Speaker, P_INFO, P_URGENT  # noqa: E402

# (lower bound as a fraction of max HR, name, BGR colour)
ZONES = [
    (0.00, "Rest", (200, 200, 200)),
    (0.50, "Warm-up", (255, 200, 0)),
    (0.60, "Fat burn", (0, 200, 0)),
    (0.70, "Cardio", (0, 220, 220)),
    (0.80, "Hard", (0, 140, 255)),
    (0.90, "Peak", (0, 0, 255)),
]


def zone_of(pct):
    z = ZONES[0]
    for item in ZONES:
        if pct >= item[0]:
            z = item
    return z


class HeartAlerts:
    """Turns a stream of bpm readings into zone changes and spoken alerts. Pure logic, no I/O."""
    HIGH_PCT, HIGH_FOR = 0.90, 8.0        # 90% of max for 8 s  -> "slow down"
    MAX_PCT, MAX_FOR = 1.00, 4.0          # 100% of max for 4 s -> "stop and rest"
    ZONE_FOR = 5.0                        # a new zone must hold 5 s before it is announced
    LOST_AFTER = 10.0                     # no reading for 10 s  -> "no signal"

    def __init__(self, speaker=None, age=20, now=time.time):
        self.speaker = speaker
        self.age = age
        self.max_hr = 220 - age
        self._now = now
        self.last_reading_at = None
        self.zone_name = "Rest"
        self._cand = None
        self._cand_since = 0.0
        self._high_since = None
        self._max_since = None
        self._was_high = False
        self._cool = {}
        self.spoken = []
        self.status = "Waiting for heart rate..."

    def _say(self, key, text, cooldown, priority=P_INFO):
        now = self._now()
        if now - self._cool.get(key, -999.0) < cooldown:
            return
        self._cool[key] = now
        self.spoken.append((now, text))
        if self.speaker is not None:
            self.speaker.say(text, priority, force=priority >= P_URGENT)

    def update(self, bpm, now=None):
        now = self._now() if now is None else now
        self.last_reading_at = now
        if bpm < 35 or bpm > 230:
            self.status = "Reading looks wrong - check the watch fit"
            self._say("bad", "Heart rate reading looks wrong. Check how the device fits.", 30.0)
            return self.zone_name
        pct = bpm / self.max_hr
        name = zone_of(pct)[1]

        # zone changes (announced once they hold for a few seconds)
        if name != self.zone_name:
            if self._cand != name:
                self._cand, self._cand_since = name, now
            elif now - self._cand_since >= self.ZONE_FOR:
                self.zone_name = name
                self._cand = None
                if name != "Rest":
                    self._say("zone", f"{name} zone.", 8.0)
        else:
            self._cand = None

        # danger: too high for too long
        self._max_since = (self._max_since or now) if pct >= self.MAX_PCT else None
        self._high_since = (self._high_since or now) if pct >= self.HIGH_PCT else None
        if self._max_since and now - self._max_since >= self.MAX_FOR:
            self.status = "TOO HIGH - STOP AND REST"
            self._was_high = True
            self._say("max", "Heart rate is too high. Stop and rest now.", 20.0, P_URGENT)
        elif self._high_since and now - self._high_since >= self.HIGH_FOR:
            self.status = "HIGH - slow down"
            self._was_high = True
            self._say("high", f"Heart rate is high, {int(bpm)}. Slow down and breathe.", 30.0, P_URGENT)
        elif self._was_high and pct < 0.80:
            self._was_high = False
            self.status = "Recovering"
            self._say("recover", "Good. Your heart rate is coming down.", 30.0)
        elif not (self._high_since or self._max_since):
            self.status = f"{self.zone_name} zone"
        return self.zone_name

    def check_signal(self, now=None):
        now = self._now() if now is None else now
        if self.last_reading_at is not None and now - self.last_reading_at > self.LOST_AFTER:
            self.status = "No heart-rate signal"
            self._say("lost", "No heart rate signal. Check the connection.", 30.0)


# ---------------------------------------------------------------- sources
class ManualSource:
    """The value is whatever you set with the w / s keys."""
    label = "MANUAL"

    def __init__(self, start=75):
        self.value = start

    def nudge(self, delta):
        self.value = max(30, min(220, self.value + delta))

    def read(self):
        return self.value

    def close(self):
        pass


class SimulatedSource:
    """A fake workout: rests, ramps up to a hard effort, then recovers (4-minute cycle).
    w / s add an offset on top, so you can push it into the danger zone on demand."""
    label = "SIMULATED"

    def __init__(self, max_hr=200):
        self.t0 = time.time()
        self.offset = 0
        self.max_hr = max_hr

    def nudge(self, delta):
        self.offset += delta

    def read(self):
        t = (time.time() - self.t0) % 240.0
        base = 72 + 0.80 * self.max_hr * 0.6 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 240.0))
        return max(30, min(220, base + self.offset + 1.5 * math.sin(t * 1.7)))

    def close(self):
        pass


class BleSource:
    """Standard Bluetooth Heart Rate service (0x180D, characteristic 0x2A37) via bleak.
    NOT TESTED against the boAt watch: whether it works depends on the device exposing the
    standard service (check with the nRF Connect phone app)."""
    label = "BLUETOOTH"
    HR_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
    HR_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"

    def __init__(self, name_hint=None):
        self.name_hint = (name_hint or "").lower()
        self.value = None
        self.status = "scanning..."
        self._stop = threading.Event()
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    @staticmethod
    def parse(data):
        flags = data[0]
        return int.from_bytes(data[1:3], "little") if flags & 0x01 else data[1]

    async def _run(self):
        try:
            from bleak import BleakScanner, BleakClient
        except ImportError:
            self.status = "bleak not installed (pip install bleak)"
            return
        while not self._stop.is_set():
            try:
                found = await BleakScanner.discover(timeout=8.0, return_adv=True)
                target = None
                for addr, (dev, adv) in found.items():
                    uuids = [u.lower() for u in (adv.service_uuids or [])]
                    name = (dev.name or adv.local_name or "").lower()
                    if self.HR_SERVICE in uuids or (self.name_hint and self.name_hint in name):
                        target = dev
                        break
                if target is None:
                    self.status = "no heart-rate device found; retrying..."
                    continue
                self.status = f"connecting to {target.name or target.address}"
                async with BleakClient(target) as client:
                    await client.start_notify(
                        self.HR_CHAR, lambda _c, data: setattr(self, "value", self.parse(bytes(data))))
                    self.status = f"connected: {target.name or target.address}"
                    while client.is_connected and not self._stop.is_set():
                        await asyncio.sleep(0.5)
            except Exception as exc:  # noqa: BLE001
                self.status = f"bluetooth error: {exc}"
                await asyncio.sleep(3.0)

    def nudge(self, delta):
        pass

    def read(self):
        return self.value

    def close(self):
        self._stop.set()


# ---------------------------------------------------------------- screen
def run(args):
    import cv2
    import numpy as np

    max_hr = 220 - args.age
    if args.source == "ble":
        source = BleSource(args.ble_name)
    elif args.source == "manual":
        source = ManualSource()
    else:
        source = SimulatedSource(max_hr)

    speaker = None if args.no_voice else Speaker().start()
    alerts = HeartAlerts(speaker, age=args.age)
    if speaker:
        speaker.say("Heart rate monitor started.", P_INFO)

    history = collections.deque(maxlen=120)
    last_sample = 0.0
    win = "AI Gym - Heart Rate Monitor"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 760, 440)

    try:
        while True:
            bpm = source.read()
            now = time.time()
            if bpm is not None:
                alerts.update(bpm, now)
                if now - last_sample >= 1.0:
                    history.append(bpm)
                    last_sample = now
            alerts.check_signal(now)

            img = np.zeros((440, 760, 3), np.uint8)
            pct = (bpm / max_hr) if bpm else 0
            _, zname, color = zone_of(pct)
            cv2.putText(img, "HEART RATE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2)
            cv2.putText(img, f"{int(bpm)}" if bpm else "--", (20, 170), cv2.FONT_HERSHEY_SIMPLEX,
                        4.2, color, 8, cv2.LINE_AA)
            cv2.putText(img, "bpm", (330, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (200, 200, 200), 2)
            cv2.putText(img, f"Zone: {zname}  ({int(pct * 100)}% of max {max_hr})", (20, 215),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
            bad = alerts.status.startswith(("TOO", "HIGH", "No ", "Reading"))
            cv2.putText(img, alerts.status, (20, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 0, 255) if bad else (0, 255, 0), 2, cv2.LINE_AA)
            # zone bar
            x0, x1 = 20, 740
            for lo, _n, col in ZONES:
                xs = int(x0 + (x1 - x0) * lo)
                cv2.rectangle(img, (xs, 275), (min(x1, xs + (x1 - x0) // 8), 290), col, -1)
            if bpm:
                mx = int(x0 + (x1 - x0) * min(1.0, pct))
                cv2.line(img, (mx, 268), (mx, 297), (255, 255, 255), 3)
            # trend (last 2 minutes)
            if len(history) > 1:
                pts = []
                for i, v in enumerate(history):
                    px = int(20 + 720 * i / max(1, history.maxlen - 1))
                    py = int(420 - (min(max(v, 40), max_hr + 10) - 40) * 110 / (max_hr - 30))
                    pts.append((px, py))
                for a, b in zip(pts, pts[1:]):
                    cv2.line(img, a, b, (255, 255, 255), 2)
            ble_status = f"  [{source.status}]" if hasattr(source, "status") else ""
            muted = bool(speaker and speaker.muted)
            cv2.putText(img, f"Source: {source.label}{ble_status}   Voice: "
                        f"{'MUTED' if (muted or not speaker) else 'ON'}", (20, 305),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            cv2.putText(img, "w = +5 bpm   s = -5 bpm   m = mute   q = quit", (20, 430),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            cv2.imshow(win, img)

            key = cv2.waitKey(50) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("w"):
                source.nudge(5)
            elif key == ord("s"):
                source.nudge(-5)
            elif key == ord("m") and speaker:
                speaker.toggle_mute()
    except KeyboardInterrupt:
        pass
    finally:
        source.close()
        cv2.destroyAllWindows()
        if speaker:
            speaker.close(wait=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Heart-rate monitor with voice alerts")
    ap.add_argument("--source", choices=["sim", "manual", "ble"], default="sim")
    ap.add_argument("--age", type=int, default=20, help="used for max heart rate = 220 - age")
    ap.add_argument("--ble-name", default="", help="part of the Bluetooth device name, e.g. 'boat'")
    ap.add_argument("--no-voice", action="store_true")
    run(ap.parse_args())
