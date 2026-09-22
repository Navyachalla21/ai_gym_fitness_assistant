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


class BicepCurlCounter:
    """Tracks bicep curl reps using elbow angle transitions."""
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.feedback = "Get ready"

    def update(self, elbow_angle):
        if elbow_angle > 160:
            self.stage = "down"
        if elbow_angle < 50 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.feedback = "Good rep!"
        return self.counter, self.stage, self.feedback


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
                count, stage, feedback = rep_counter.update(angle)

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


if __name__ == "__main__":
    run_pose_detection()