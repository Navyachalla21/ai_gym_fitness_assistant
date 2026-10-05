# AI Gym & Fitness Assistant — Testing Report

## 1. Testing Approach
Two kinds of testing were done:

1. **Automated API tests** — `run_tests.py` sends 23 requests to the backend and compares each response with an expected value. It writes the real results to `test_results.md`. Run it with `python run_tests.py <base_url>`.
   - Local backend (`http://127.0.0.1:8000`): **23/23 passed**
   - Live backend on Render (`https://ai-gym-backend-bwiz.onrender.com`): **23/23 passed** (after the final deployment)
2. **Manual tests** — the parts that need a webcam, a browser or a second terminal (Module 1, the dashboard tabs, MQTT with the simulator) were run by hand and are listed in section 3.

Every module has at least one contrasting test (for example high-risk and low-risk habit profiles, a good and a poor session) so the logic is shown to respond to different inputs, not just to run.

## 2. Automated API Test Results (local run, 23/23)

| # | Module | Test | Input | Expected | Actual | Result |
|---|--------|------|-------|----------|--------|--------|
| 1 | Backend API | Root endpoint | GET / | 200 OK | 200, "API is running" | PASS |
| 2 | AI Dietician | BMI + plan (normal BMI) | 70 kg, 170 cm, weight loss, vegetarian | BMI 24.2 Normal weight, plan returned | BMI 24.2 (Normal weight), plan 1889 chars | PASS |
| 3 | AI Dietician | BMI category (underweight) | 50 kg, 170 cm, muscle gain | BMI 17.3 Underweight | BMI 17.3 (Underweight) | PASS |
| 4 | Habit Tracker | High-risk profile | 13 days, 1.28/wk, 77% | High risk + light 15-min schedule | High (96%); Light, 15 min | PASS |
| 5 | Habit Tracker | Low-risk profile | 1 day, 6/wk, 95% | Low risk, no nudge | Low (1%); Progressive, 45 min | PASS |
| 6 | Habit Tracker | Medium-risk profile | 5 days, 3/wk, 60% | Medium risk + moderate schedule | Medium (58%); Moderate, 30 min | PASS |
| 7 | Gym Buddy | Negative message | "I feel tired and stressed today" | negative + reply | negative; supportive reply | PASS |
| 8 | Gym Buddy | Positive message | "I feel great and motivated!" | positive + reply | positive; energetic reply | PASS |
| 9 | Gym Buddy | Negation | "I am not happy with my progress" | negative | negative; encouraging reply | PASS |
| 10 | Performance Analyzer | Good session | 12 reps, 120 s, 10/12 good | 66.0 / 83.3% / Good | 66.0 / 83.3% / Good | PASS |
| 11 | Performance Analyzer | Poor session | 3 reps, 300 s, 1/5 good | Needs Improvement | 13.6 / 20.0% / Needs Improvement | PASS |
| 12 | Smart Gym | Sensor reading + advice | GET /api/smart-gym-reading | Advice matches heart-rate zone | HR 153 → "reduce resistance, short rest" | PASS |
| 13 | Gym Recommender | Beginner streak | weight loss, streak 0 | 3-Day Kickstart Challenge | 3 programs, 3 gyms, Kickstart challenge | PASS |
| 14 | Gym Recommender | Advanced streak | muscle gain, streak 20 | 30-Day Mastery Challenge | 3 programs, 3 gyms, Mastery challenge | PASS |
| 15 | Weekly Report | Report from saved sessions | GET /api/weekly-report | 200 + report fields | 200; 9 sessions, 102 reps, avg 42.8, Stable | PASS |
| 16 | Admin Analytics | Summary | GET /api/analytics/summary | 200 + totals | 200; 9 sessions, 9 risk checks | PASS |
| 17 | Gym Recommender | Location + history aware | muscle gain, Bengaluru | Level, programs, nearest gyms | beginner (9 sessions, avg 42.8); nearest 1.6 km | PASS |
| 18 | Gym Recommender | Validation | latitude 95 | 422 | 422 | PASS |
| 19 | AI Dietician | Calorie target | 70 kg, 170 cm, weight loss | About 1,500–1,900 kcal | 1680 kcal (maintenance 2180) | PASS |
| 20 | AI Dietician | Meal log + summary + delete | log, summarise, delete | Saved, counted, removable | 300 kcal logged, 1400 remaining, deleted | PASS |
| 21 | AI Dietician | Meal validation | empty meal name | 422 | 422 | PASS |
| 22 | Smart Gym | Live MQTT / fallback + advice | GET /api/smart-gym-live | Source shown, resistance + rest advice | source=simulated, HR 116 → Maintain, rest 45 s | PASS |
| 23 | Backend API | Validation | POST /api/diet-plan {} | 422 | 422 | PASS |

Note on row 22: `source=simulated` and `broker connected=False` is the expected answer when no simulator is publishing. With `iot_simulator.py` running, the same endpoint returns `source=mqtt` (see manual test M6).

## 3. Manual Tests

| # | Module | Test | Result |
|---|--------|------|--------|
| M1 | AI Gym Trainer | Live webcam bicep curls with dumbbells. After the counter was made stricter (confirmation frames, minimum rep time, landmark visibility filter), standing still produced no phantom reps and a 26-rep session was counted correctly. Form warning and good-rep beeps work without freezing the video. | PASS |
| M2 | Module 1 → 6 | Ending a webcam session posts reps, duration and form feedback to `/api/analyze-session` and prints the score, form % and rating. The session is saved to the database. | PASS |
| M3 | Streamlit dashboard | All 7 tabs load and talk to the backend (with `API_URL` set for a local backend). | PASS |
| M4 | Habit Tracker | Schedule adjustment (light / moderate / progressive) shown after a risk check. | PASS |
| M5 | Admin Analytics | Charts for sessions per week, scores, risk and mood read the stored data. | PASS |
| M6 | Smart Gym (MQTT) | With `iot_simulator.py` running, `/api/smart-gym-live` returned `source=mqtt`. Pressing Apply published a resistance command and the simulator printed `command received: resistance set to 3`. | PASS |
| M7 | Deployment | Streamlit Cloud dashboard works against the Render backend over public URLs. | PASS |

## 4. Defects Found During Testing and Fixed
- **Module 1 froze the video** when a beep played. Beeps now run in a background thread.
- **Module 1 counted phantom reps** while the user stood still, because of landmark jitter. Fixed with confirmation frames, a minimum rep time, a visibility filter and a scale-aware elbow-drift check.
- **Sentiment missed "don't have mood"**. Added negative phrases and negation/filler handling.
- **Duplicate demo data** when several dashboard tabs loaded at once. Fixed with a lock in the seeding code (27 duplicated sessions without the lock, 11 with it).
- **Dashboard showed "simulated"** because `API_URL` was not set. Documented in the README.
- **First test run had 0/17** because the wrong URL was used (`onrender.com` instead of the service URL). Not a product defect.

## 5. Known Limitations
- Nearby gyms are **sample data** placed around real city centres, not live map data.
- Render's free tier sleeps after about 15 minutes, and its disk resets on redeploy, so saved history and meals are not permanent there.
- The MQTT broker (`broker.hivemq.com`) is public; the topic name is unique but not secret.
- The Next.js frontend does not have the newest features (analytics, nutrition tracker, live MQTT). The Streamlit dashboard does.
- The performance score weights pace heavily, so slow, controlled sets score low. The recommender therefore rates the demo user as "beginner" (average score about 43, below the 45 threshold).
- Gym Buddy replies come from Gemini and vary between runs; only the sentiment label is asserted in the tests.
- The unit tests of the AI logic were run against stand-ins for FastAPI, Streamlit, paho and Gemini. The 23 API tests above are the ones that ran against the real stack.
