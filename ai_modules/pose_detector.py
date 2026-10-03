try:
    import winsound
except ImportError:
    winsound = None

import requests
import cv2
import mediapipe as mp
import numpy as np
import time
import os
import threading

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "pose_landmarker_lite.task")

# Standard 33-point BlazePose landmark indices
RIGHT_SHOULDER = 12
RIGHT_ELBOW = 14
RIGHT_WRIST = 16
LEFT_SHOULDER = 11

MIN_VISIBILITY = 0.6   # ignore landmarks the model is not confident about
DRIFT_RATIO = 0.5      # elbow may sit up to 50% of the shoulder width away from the shoulder

WINDOW_NAME = 'AI Gym Trainer - Bicep Curl Counter'


def beep(freq, ms):
    """Plays a short beep without blocking the video loop (Windows only; silent elsewhere)."""
    if winsound is None:
        return

    def _play():
        try:
            winsound.Beep(freq, ms)
        except RuntimeError:
            pass  # another beep was still playing - skip this one

    threading.Thread(target=_play, daemon=True).start()


def calculate_angle(a, b, c):
    """Calculates the angle at point 'b', formed by points a-b-c."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

def check_elbow_drift(shoulder, elbow, w, shoulder_width_px=None):
    """Returns True if the elbow has drifted too far from the torso (common curl mistake).

    The limit scales with the user's shoulder width, so it works the same whether the
    user is near or far from the camera. Falls back to a fixed pixel limit if the
    shoulder width is unknown."""
    horizontal_distance = abs(elbow[0] - shoulder[0]) * w
    if shoulder_width_px and shoulder_width_px > 20:
        limit = DRIFT_RATIO * shoulder_width_px
    else:
        limit = 60 * (w / 640)  # old fixed limit, scaled to the frame width
    return horizontal_distance > limit


def visibility(landmark):
    """Model confidence that a landmark is really visible (1.0 if the model gives none)."""
    v = getattr(landmark, "visibility", None)
    return 1.0 if v is None else v


class ArmNotVisible(Exception):
    """Raised when the right arm is not clearly in view, so the frame is skipped."""


class BicepCurlCounter:
    """Counts bicep curls. Robust against jitter: a position must be held for a few
    consecutive frames to count, and reps cannot follow each other faster than a human can curl."""
    CONFIRM_DOWN = 3        # frames the arm must stay extended (> 160 deg) to arm the next rep
    CONFIRM_UP = 2          # frames the arm must stay fully curled (< 50 deg) to complete a rep
    MIN_REP_SECONDS = 0.8   # minimum time between two reps

    def __init__(self):
        self.counter = 0
        self.stage = None
        self.feedback = "Get ready"
        self._down_frames = 0
        self._up_frames = 0
        self._last_rep_time = float("-inf")

    def update(self, elbow_angle, elbow_drifted, now=None):
        now = time.time() if now is None else now

        if elbow_drifted:
            self._down_frames = 0
            self._up_frames = 0
            self.feedback = "Keep elbow tucked in!"
            return self.counter, self.stage, self.feedback, True  # True = warning

        self._down_frames = self._down_frames + 1 if elbow_angle > 160 else 0
        self._up_frames = self._up_frames + 1 if elbow_angle < 50 else 0

        if self._down_frames >= self.CONFIRM_DOWN:
            self.stage = "down"
            self.feedback = "Clear extension. Curl up."
        if (self._up_frames >= self.CONFIRM_UP and self.stage == "down"
                and now - self._last_rep_time >= self.MIN_REP_SECONDS):
            self.stage = "up"
            self.counter += 1
            self._last_rep_time = now
            self.feedback = "Good rep!"
            return self.counter, self.stage, self.feedback, False

        if self.stage == "up" and elbow_angle > 70:
            self.feedback = "Lower down smoothly."

        return self.counter, self.stage, self.feedback, False


def send_session(reps, duration, feedback_log):
    """Posts the finished session to the backend (Module 1 -> Module 6 integration)."""
    print(f"\nSession complete — Reps: {reps}, Duration: {duration}s")
    if reps == 0 and not feedback_log:
        print("No reps or form events were recorded, so this session was not saved.")
        return
    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    try:
        response = requests.post(f"{backend_url}/api/analyze-session", json={
            "reps": reps,
            "duration_seconds": duration,
            "form_feedback_list": feedback_log
        }, timeout=60)  # Render's free tier can take ~50s to wake up
        if response.status_code == 200:
            result = response.json()
            print(f"Performance Score: {result.get('performance_score', 'N/A')}")
            print(f"Form Quality: {result.get('form_quality_pct', 'N/A')}%")
            print(f"Rating: {result.get('rating', 'N/A')}")
        else:
            print(f"Backend error: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Could not reach backend at {backend_url} — make sure uvicorn is running on port 8000.")
    except requests.exceptions.Timeout:
        print("Backend took too long to respond (it may be waking up) — session not saved.")


def run_pose_detection():
    """
    Opens the webcam, detects pose landmarks in real time using MediaPipe's
    Tasks API (PoseLandmarker), calculates elbow angle, and counts bicep curl reps.
    Press 'q' or Esc in the video window to quit (Ctrl+C in the terminal also works
    and still saves the session).
    """
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1
    )

    rep_counter = BicepCurlCounter()
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    feedback_log = []

    # State tracking so each rep / each form warning is logged once, not once per frame
    last_count = 0
    warning_active = False
    last_timestamp_ms = -1

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 540)

    count, stage = 0, None
    landmarker = PoseLandmarker.create_from_options(options)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            # VIDEO mode needs strictly increasing timestamps
            timestamp_ms = max(last_timestamp_ms + 1, int((time.time() - start_time) * 1000))
            last_timestamp_ms = timestamp_ms

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            image = frame.copy()
            h, w, _ = image.shape

            try:
                landmarks = result.pose_landmarks[0]  # first detected person

                arm = (landmarks[RIGHT_SHOULDER], landmarks[RIGHT_ELBOW], landmarks[RIGHT_WRIST])
                if min(visibility(lm) for lm in arm) < MIN_VISIBILITY:
                    raise ArmNotVisible

                shoulder_width_px = None
                left_sh = landmarks[LEFT_SHOULDER]
                if visibility(left_sh) >= MIN_VISIBILITY:
                    shoulder_width_px = abs(left_sh.x - landmarks[RIGHT_SHOULDER].x) * w

                shoulder = [landmarks[RIGHT_SHOULDER].x, landmarks[RIGHT_SHOULDER].y]
                elbow = [landmarks[RIGHT_ELBOW].x, landmarks[RIGHT_ELBOW].y]
                wrist = [landmarks[RIGHT_WRIST].x, landmarks[RIGHT_WRIST].y]

                angle = calculate_angle(shoulder, elbow, wrist)
                drifted = check_elbow_drift(shoulder, elbow, w, shoulder_width_px)
                count, stage, feedback, is_warning = rep_counter.update(angle, drifted)

                # Log + beep only when something CHANGES (not on every frame)
                if count > last_count:
                    feedback_log.append("Good rep!")
                    last_count = count
                    warning_active = False
                    beep(1000, 100)
                elif is_warning and not warning_active:
                    feedback_log.append("Keep elbow tucked in!")
                    warning_active = True
                    beep(400, 150)
                elif not is_warning and warning_active:
                    warning_active = False  # form corrected

                elbow_px = (int(elbow[0] * w), int(elbow[1] * h))
                cv2.putText(image, str(int(angle)), elbow_px,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

                # Draw landmarks as dots
                for lm in landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(image, (cx, cy), 4, (0, 255, 0), -1)

            except ArmNotVisible:
                count, stage, feedback = rep_counter.counter, rep_counter.stage, "Arm not fully visible - step back"
            except (IndexError, AttributeError):
                count, stage, feedback = rep_counter.counter, rep_counter.stage, "No person detected"

            cv2.rectangle(image, (0, 0), (250, 90), (30, 30, 30), -1)
            cv2.putText(image, f"REPS: {count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f"STAGE: {stage}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, feedback, (10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA)

            cv2.imshow(WINDOW_NAME, image)

            key = cv2.waitKey(10) & 0xFF
            if key in (ord('q'), 27):  # q or Esc
                break
    except KeyboardInterrupt:
        print("\nStopped with Ctrl+C — saving the session so far...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    # Send the results BEFORE closing the landmarker, so a slow/stuck shutdown can't lose the session
    send_session(rep_counter.counter, int(time.time() - start_time), feedback_log)

    try:
        landmarker.close()
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    run_pose_detection()