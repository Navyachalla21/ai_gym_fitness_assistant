import winsound
import requests
import cv2
import mediapipe as mp
import numpy as np
import time

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = "ai_modules/pose_landmarker_lite.task"

# Standard 33-point BlazePose landmark indices
RIGHT_SHOULDER = 12
RIGHT_ELBOW = 14
RIGHT_WRIST = 16


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

def check_elbow_drift(shoulder, elbow, w):
    """Returns True if elbow has drifted too far from torso (common curl mistake)."""
    horizontal_distance = abs(elbow[0] - shoulder[0]) * w
    return horizontal_distance > 60  # pixels — adjust based on testing


class BicepCurlCounter:
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.feedback = "Get ready"

    def update(self, elbow_angle, elbow_drifted):
        if elbow_drifted:
            self.feedback = "Keep elbow tucked in!"
            return self.counter, self.stage, self.feedback, True  # True = warning

        if elbow_angle > 160:
            self.stage = "down"
        if elbow_angle < 50 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.feedback = "Good rep!"
            return self.counter, self.stage, self.feedback, False

        return self.counter, self.stage, self.feedback, False


def run_pose_detection():
    """
    Opens the webcam, detects pose landmarks in real time using MediaPipe's
    Tasks API (PoseLandmarker), calculates elbow angle, and counts bicep curl reps.
    Press 'q' to quit.
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

    cv2.namedWindow('AI Gym Trainer - Bicep Curl Counter', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('AI Gym Trainer - Bicep Curl Counter', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            image = frame.copy()
            h, w, _ = image.shape

            try:
                landmarks = result.pose_landmarks[0]  # first detected person

                shoulder = [landmarks[RIGHT_SHOULDER].x, landmarks[RIGHT_SHOULDER].y]
                elbow = [landmarks[RIGHT_ELBOW].x, landmarks[RIGHT_ELBOW].y]
                wrist = [landmarks[RIGHT_WRIST].x, landmarks[RIGHT_WRIST].y]

                angle = calculate_angle(shoulder, elbow, wrist)
                drifted = check_elbow_drift(shoulder, elbow, w)
                count, stage, feedback, is_warning = rep_counter.update(angle, drifted)
                feedback_log.append(feedback)

                if is_warning:
                    winsound.Beep(400, 150)
                elif feedback == "Good rep!":
                    winsound.Beep(1000, 100)
    
                elbow_px = (int(elbow[0] * w), int(elbow[1] * h))
                cv2.putText(image, str(int(angle)), elbow_px,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

                # Draw landmarks as dots
                for lm in landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(image, (cx, cy), 4, (0, 255, 0), -1)

            except (IndexError, AttributeError):
                count, stage, feedback = rep_counter.counter, rep_counter.stage, "No person detected"

            cv2.rectangle(image, (0, 0), (250, 90), (30, 30, 30), -1)
            cv2.putText(image, f"REPS: {count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f"STAGE: {stage}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, feedback, (10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA)

            cv2.imshow('AI Gym Trainer - Bicep Curl Counter', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    session_duration = int(time.time() - start_time)

    print(f"\nSession complete — Reps: {rep_counter.counter}, Duration: {session_duration}s")

    try:
        response = requests.post("http://localhost:8000/api/analyze-session", json={
            "reps": rep_counter.counter,
            "duration_seconds": session_duration,
            "form_feedback_list": feedback_log
        })
        if response.status_code == 200:
            result = response.json()
            print(f"Performance Score: {result['performance_score']}")
            print(f"Form Quality: {result['form_quality_pct']}%")
            print(f"Rating: {result['rating']}")
        else:
            print(f"Backend error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not reach backend — make sure uvicorn is running on port 8000.")

if __name__ == "__main__":
    run_pose_detection()