"""
Voice coach for the AI Gym Trainer (college extension).

Turns what the webcam trainer shows on screen into spoken coaching:
  * "Up" (arm extended, curl now) and "Down" (rep done, lower) pace cues
  * rep counts
  * form corrections ("Correct your form. Keep your elbow tucked in.")
  * short motivation lines while the user is working
  * celebration lines at rep milestones ("Boom! 10 perfect reps crushed!")

Design rules
  * Speech never blocks the video loop: all talking happens in a background thread that
    speaks each sentence through Windows' built-in System.Speech (no pip install needed).
  * One speech queue shared by every feature, so voices never overlap. Higher-priority
    lines (form warnings, celebrations, heart-rate alerts later) interrupt lower ones.
  * The coach speaks on CHANGES only (stage change, new rep, new warning), with
    cooldowns, so it never chatters frame after frame.
  * If speech is unavailable the coach prints the lines instead; the trainer keeps working.

Self-test (speaks sample lines):   python voice_coach.py
Dry run (prints, no audio):        python voice_coach.py --dry
"""
import base64
import os
import queue
import random
import subprocess
import sys
import threading
import time

# Priorities: a higher number may interrupt a lower one.
P_PACE = 0         # "Up" / "Down"
P_INFO = 1         # rep count, motivation
P_FORM = 2         # form corrections
P_URGENT = 3       # celebrations, heart-rate alerts

# Each sentence is spoken by its own short PowerShell call. (A long-lived PowerShell process that
# we fed through a pipe stayed silent on some Windows laptops; one call per sentence works everywhere.)
_PS_ONE = ("Add-Type -AssemblyName System.Speech; "
           "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
           "$s.Rate = {rate}; $s.Volume = 100; $s.Speak('{text}')")


def _clean(text):
    """The speech call reads plain ASCII; strip anything else (emoji etc.)."""
    return "".join(ch for ch in text if 32 <= ord(ch) < 127).replace("|", " ").strip()


class Speaker:
    """Background speech queue. Safe to call from the video loop: say() returns instantly."""

    def __init__(self, dry=False, rate=None):
        self.dry = dry
        self.rate = int(os.getenv("VOICE_RATE", rate if rate is not None else 1))
        self.muted = False
        self._q = queue.Queue()
        self._proc = None              # the PowerShell call that is speaking right now
        self._thread = None
        self._busy_until = 0.0
        self._current_priority = -1
        self._lock = threading.Lock()
        self.backend = "print"

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        if not self.dry and sys.platform.startswith("win"):
            self.backend = "windows-sapi"
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        return self

    def close(self, wait=True):
        """Finish the current sentence, then stop."""
        self._q.put(None)
        if self._thread:
            self._thread.join(timeout=12 if wait else 0.5)
        self._kill()

    # -- public API --------------------------------------------------------
    def say(self, text, priority=P_INFO, force=False):
        """Queue a line. Returns True if it was accepted, False if dropped (muted / busy with
        something more important / too soon)."""
        if self.muted:
            return False
        now = time.time()
        with self._lock:
            if (not force) and now < self._busy_until and priority <= self._current_priority:
                return False          # already talking, and this is not more important
            words = max(1, len(text.split()))
            self._busy_until = now + 0.9 + 0.38 * words     # ~0.9 s for PowerShell to start
            self._current_priority = priority
        self._q.put((priority, text))
        return True

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self._kill()
        return self.muted

    # -- internals ---------------------------------------------------------
    def _kill(self):
        p = self._proc
        if p is not None and p.poll() is None:
            try:
                p.kill()
            except Exception:  # noqa: BLE001
                pass

    def _speak(self, text):
        """Start speaking `text`; returns False if speech is not available."""
        if self.backend != "windows-sapi":
            return False
        script = _PS_ONE.format(rate=self.rate, text=text.replace("'", "''"))
        try:
            self._proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-Command", script],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as exc:  # noqa: BLE001 - voice must never break the trainer
            print(f"[voice] speech unavailable ({exc}); printing instead")
            self.backend = "print"
            return False

    def _wait_current(self, timeout=15.0):
        p = self._proc
        if p is None:
            return
        try:
            p.wait(timeout=timeout)
        except Exception:  # noqa: BLE001
            self._kill()

    def _worker(self):
        while True:
            item = self._q.get()
            if item is None:
                self._wait_current(8.0)       # let the last sentence finish
                return
            priority, text = item
            text = _clean(text)
            if not text:
                continue
            if self._proc is not None and self._proc.poll() is None:
                if priority >= P_FORM:
                    self._kill()              # important line: cut off what is playing
                else:
                    self._wait_current()      # normal line: wait for the current one
            if self.muted:
                continue
            if not self._speak(text):
                print(f"[voice] {text}")


class VoiceCoach:
    """Turns per-frame trainer state into spoken cues. Call update() once per frame."""

    MILESTONES = (5, 10, 15, 20, 25, 30, 40, 50)
    MOTIVATION = (
        "Nice pace, keep going.",
        "You are doing great.",
        "Strong and steady. Keep it up.",
        "Breathe and keep moving.",
        "Stay focused. You've got this.",
        "Looking good. Do not stop now.",
    )

    def __init__(self, speaker=None, pace_cues=True, motivation_every=25.0, now=time.time):
        self.speaker = speaker or Speaker()
        self.pace_cues = pace_cues
        self.motivation_every = motivation_every
        self._now = now
        self.reset()

    def reset(self):
        self.last_count = 0
        self.last_stage = None
        self.was_warning = False
        self.clean_streak = 0          # reps since the last form warning
        self.warned_since_rep = False
        self.last_warning_at = -99.0
        self.warn_repeats = 0          # spoken warnings in the current continuous warning episode
        self.notice_times = {}         # key -> last time a one-off hint was spoken
        self.last_lower_at = -99.0
        self.last_motivation_at = self._now()
        self.last_line = None
        self.spoken = []               # (time, priority, text), handy for tests and the report

    # -- lifecycle ---------------------------------------------------------
    def start(self, greet=True):
        self.speaker.start()
        self.last_motivation_at = self._now()
        if greet:
            self._say("Get ready. Let's start your curls.", P_INFO)
        return self

    def finish(self, reps, wait=True):
        self.announce_end(reps)
        self.close(wait=wait)

    def toggle_mute(self):
        return self.speaker.toggle_mute()

    @property
    def muted(self):
        return self.speaker.muted

    def notice(self, key, text, cooldown=15.0, priority=P_INFO):
        """One-off spoken hint (for example 'step back'), at most once per `cooldown` seconds."""
        now = self._now()
        if now - self.notice_times.get(key, -999.0) < cooldown:
            return False
        if self._say(text, priority):
            self.notice_times[key] = now
            return True
        return False

    def announce_end(self, reps):
        """Queue the closing line (speech continues in the background)."""
        if reps > 0:
            self._say(f"Session complete. {reps} reps. Great work.", P_URGENT)
        else:
            self._say("Session complete.", P_URGENT)

    def close(self, wait=True):
        """Let the current sentence finish, then stop the speech process."""
        self.speaker.close(wait=wait)

    # -- per-frame ---------------------------------------------------------
    def update(self, count, stage, feedback="", is_warning=False):
        """count: total reps. stage: 'up' / 'down' / None. feedback: the on-screen text.
        is_warning: True while the elbow-drift warning is showing."""
        now = self._now()

        # 1. Form correction: speak when a warning STARTS, repeat only every 10 s, and never more
        #    than 3 times in one continuous episode (so a user who keeps the elbow out is not nagged).
        if is_warning:
            self.warned_since_rep = True
            first = not self.was_warning
            if first:
                self.warn_repeats = 0
            if (first or now - self.last_warning_at > 10.0) and self.warn_repeats < 3:
                if self._say("Correct your form. Keep your elbow tucked in.", P_FORM):
                    self.last_warning_at = now
                    self.warn_repeats += 1
        self.was_warning = bool(is_warning)

        # 2. New rep: count it, or celebrate at milestones.
        new_rep = count > self.last_count
        if new_rep:
            for n in range(self.last_count + 1, count + 1):
                if self.warned_since_rep:
                    self.clean_streak = 0
                else:
                    self.clean_streak += 1
                self.warned_since_rep = False
                self._on_rep(n)
            self.last_count = count
            self.last_motivation_at = now
        elif count < self.last_count:     # counter was reset
            self.last_count = count

        # 3. "Up" cue when the arm is fully extended (time to curl). The "Down" cue comes with
        #    the rep count (see _on_rep), because the trainer flips to 'up' on the same frame a
        #    rep is counted.
        if stage != self.last_stage:
            if self.pace_cues and stage == "down" and not is_warning and not new_rep:
                self._say("Up", P_PACE)
            self.last_stage = stage

        # 4. Slow-down hint when the trainer says to lower smoothly.
        if feedback and "lower" in feedback.lower() and now - self.last_lower_at > 6.0:
            if self._say("Lower slowly.", P_INFO):
                self.last_lower_at = now

        # 5. Motivation while the user is active but things have been quiet.
        if self.motivation_every and now - self.last_motivation_at > self.motivation_every \
                and self.last_count > 0:
            if self._say(self._pick_motivation(), P_INFO):
                self.last_motivation_at = now

    # -- helpers -----------------------------------------------------------
    def _on_rep(self, n):
        if n in self.MILESTONES:
            if self.clean_streak >= n:
                self._say(f"Boom! {n} perfect reps crushed!", P_URGENT)
            else:
                self._say(f"Boom! {n} reps crushed!", P_URGENT)
        elif self.clean_streak and self.clean_streak % 5 == 0:
            self._say(f"{self.clean_streak} clean reps in a row. Beautiful form!", P_URGENT)
        else:
            self._say(f"{n}. Down" if self.pace_cues else str(n), P_INFO)

    def _pick_motivation(self):
        options = [m for m in self.MOTIVATION if m != self.last_line] or list(self.MOTIVATION)
        return random.choice(options)

    def _say(self, text, priority):
        ok = self.speaker.say(text, priority)
        if ok:
            self.last_line = text
            self.spoken.append((self._now(), priority, text))
        return ok


class GuidedCounter:
    """Trainer-led curls: the voice tells you what to do, like a real gym trainer.

      "Up"   -> you curl the weight up   (elbow angle below CURL_ANGLE)
      "Down" -> you lower it             (elbow angle above EXTEND_ANGLE)
    One full Up + Down = one rep. If you do not respond, it nudges you
    ("Raise your arm up." / "Lower your arm down."). It has the same update() signature as
    BicepCurlCounter, so the trainer can use either one."""

    CURL_ANGLE = 60.0
    EXTEND_ANGLE = 150.0
    CONFIRM = 2              # frames a position must be held
    START_DELAY = 4.0        # seconds after the first frame before the first command (greeting plays)
    NUDGE_AFTER = 6.0        # seconds without a response before a reminder
    NUDGE_EVERY = 6.0
    MAX_NUDGES = 3
    MILESTONES = (5, 10, 15, 20, 25, 30, 40, 50)

    def __init__(self, speaker=None, now=time.time):
        self.speaker = speaker
        self._now = now
        self.counter = 0
        self.stage = None            # 'up' (curled) or 'down' (extended)
        self.feedback = "Get ready"
        self.target = "up"           # what the trainer is asking for next
        self._confirm = 0
        self._t_first = None
        self._started = False
        self._cmd_at = 0.0
        self._nudges = 0
        self._last_nudge_at = 0.0
        self._last_warn_at = -99.0
        self.had_warning = False
        self.clean_streak = 0
        self.spoken = []

    def _say(self, text, priority=P_URGENT, force=True):
        self.spoken.append((self._now(), text))
        if self.speaker is not None:
            self.speaker.say(text, priority, force=force)

    def _command(self, text, now):
        self._say(text)
        self._cmd_at = now
        self._nudges = 0
        self._last_nudge_at = now
        self._confirm = 0

    def update(self, elbow_angle, elbow_drifted, now=None):
        now = self._now() if now is None else now
        if self._t_first is None:
            self._t_first = now

        # Wait for the greeting to finish, then give the first command.
        if not self._started:
            self.feedback = "Get ready"
            if now - self._t_first >= self.START_DELAY:
                self._started = True
                self.feedback = "Curl UP"
                self._command("Up", now)
            return self.counter, self.stage, self.feedback, False

        # Elbow drifting away from the body: correct the form (no counting while it drifts).
        if elbow_drifted:
            self._confirm = 0
            self.had_warning = True
            self.feedback = "Keep elbow tucked in!"
            if now - self._last_warn_at > 8.0:
                self._last_warn_at = now
                self._say("Keep your elbow tucked in.", P_FORM, force=False)
            return self.counter, self.stage, self.feedback, True

        if self.target == "up":
            self.feedback = "Curl UP"
            self._confirm = self._confirm + 1 if elbow_angle < self.CURL_ANGLE else 0
            if self._confirm >= self.CONFIRM:
                self.stage = "up"
                self.target = "down"
                self.feedback = "Now lower DOWN"
                self._command("Down", now)
        else:
            self.feedback = "Now lower DOWN"
            self._confirm = self._confirm + 1 if elbow_angle > self.EXTEND_ANGLE else 0
            if self._confirm >= self.CONFIRM:
                self.stage = "down"
                self.counter += 1
                self.clean_streak = 0 if self.had_warning else self.clean_streak + 1
                self.had_warning = False
                self.target = "up"
                self.feedback = "Good rep! Curl UP"
                n = self.counter
                if n in self.MILESTONES:
                    word = "perfect " if self.clean_streak >= n else ""
                    self._command(f"Boom! {n} {word}reps crushed! Up", now)
                else:
                    self._command(f"{n}. Up", now)
                return self.counter, self.stage, self.feedback, False

        # No response to the command: nudge, like a trainer would.
        if (now - self._cmd_at > self.NUDGE_AFTER and now - self._last_nudge_at > self.NUDGE_EVERY
                and self._nudges < self.MAX_NUDGES):
            self._nudges += 1
            self._last_nudge_at = now
            if self.target == "up":
                self._say("Raise your arm up.", P_FORM, force=False)
            else:
                self._say("Lower your arm down slowly.", P_FORM, force=False)
        return self.counter, self.stage, self.feedback, False


class NullCoach:
    """Used when voice can't be loaded, so pose_detector.py needs no special cases."""

    def start(self, *a, **k):
        return self

    def update(self, *a, **k):
        pass

    muted = False

    def finish(self, *a, **k):
        pass

    def announce_end(self, *a, **k):
        pass

    def close(self, *a, **k):
        pass

    def notice(self, *a, **k):
        return False

    def toggle_mute(self):
        return False


def _selftest(dry):
    print("Voice self-test ({}).".format("dry run, printing only" if dry else "you should hear speech"))
    coach = VoiceCoach(Speaker(dry=dry), motivation_every=0).start()
    print("Voice engine:", coach.speaker.backend)
    time.sleep(2.5)
    count = 0
    coach.update(0, "down", "Get ready", False)
    for rep in range(1, 6):
        time.sleep(1.2)
        coach.update(count, "up", "", False)
        time.sleep(1.0)
        coach.update(count, "down", "", False)
        time.sleep(0.4)
        count += 1
        coach.update(count, "up", "Good rep!", False)
        if rep == 3:
            time.sleep(1.0)
            coach.update(count, "up", "Keep elbow tucked in!", True)
        time.sleep(1.5)
        coach.update(count, "down", "", False)
    coach.finish(count)
    print("Spoken lines:")
    for _, p, t in coach.spoken:
        print("  [p{}] {}".format(p, t))


if __name__ == "__main__":
    _selftest("--dry" in sys.argv)
