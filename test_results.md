# Test results — https://ai-gym-backend-bwiz.onrender.com

| # | Module | Test | Input | Expected | Actual | Result |
|---|--------|------|-------|----------|--------|--------|
| 1 | Backend API | Root endpoint availability | GET / | 200 OK | 200 {"message":"AI Gym & Fitness Assistant API is running."} | PASS |
| 2 | AI Dietician | BMI + plan (normal BMI) | 70 kg, 170 cm, weight loss, vegetarian | BMI 24.2 Normal weight, plan returned | BMI 24.2 (Normal weight), plan length 2347 chars | PASS |
| 3 | AI Dietician | BMI category (underweight) | 50 kg, 170 cm, muscle gain | BMI 17.3 Underweight | BMI 17.3 (Underweight) | PASS |
| 4 | Habit Tracker | High-risk profile | 13 days, 1.28/wk, 77% | High risk + light 15-min schedule | High (94%); schedule: Light, 15 min | PASS |
| 5 | Habit Tracker | Low-risk profile (contrast) | 1 day, 6/wk, 95% | Low risk, no nudge | Low (0%); schedule: Progressive, 45 min | PASS |
| 6 | Habit Tracker | Medium-risk profile | 5 days, 3/wk, 60% | Medium risk + moderate schedule | High (100%); schedule: Light, 15 min | FAIL |
| 7 | Gym Buddy | Negative message | I feel tired and stressed today | sentiment negative + reply | sentiment=negative; reply: Oh man, I totally get that—some days just hit extra hard. Take all the pressure off for to... | PASS |
| 8 | Gym Buddy | Positive message | I feel great and motivated! | sentiment positive + reply | sentiment=positive; reply: Look at that 180-degree turn! I love that energy so much, especially after dealing with al... | PASS |
| 9 | Gym Buddy | Negation handling | I am not happy with my progress | sentiment negative | sentiment=negative; reply: Hey, I totally feel you—progress can be so frustratingly slow sometimes, especially after ... | PASS |
| 10 | Performance Analyzer | Good session | 12 reps, 120 s, 10/12 good | 66.0 / 83.3% / Good | score 66.0, form 83.3%, rating Good | PASS |
| 11 | Performance Analyzer | Poor session (contrast) | 3 reps, 300 s, 1/5 good | Needs Improvement | score 13.6, form 20.0%, rating Needs Improvement | PASS |
| 12 | Smart Gym | Sensor reading + matching advice | GET /api/smart-gym-reading | Advice matches heart-rate zone | HR 119 bpm, resistance 6, status active -> Heart rate is in a healthy training zone — maintain current intensity. | PASS |
| 13 | Gym Recommender | Beginner streak | weight loss, streak 0 | 3-Day Kickstart Challenge | 3 programs, 3 gyms, challenge: 3-Day Kickstart Challenge — build your first habit streak! | PASS |
| 14 | Gym Recommender | Advanced streak | muscle gain, streak 20 | 30-Day Mastery Challenge | 3 programs, 3 gyms, challenge: 30-Day Muscle Gain Mastery Challenge — you're ready for the  | PASS |
| 15 | Weekly Report | Report from saved sessions | GET /api/weekly-report | 200 + report fields | 200; 2 session(s), 15 reps, average score 39.8 — trend: Declining. | PASS |
| 16 | Admin Analytics | Summary endpoint | GET /api/analytics/summary | 200 + totals | 200; sessions=2, risk checks=3 | PASS |
| 17 | Gym Recommender | Location + history aware | muscle gain, city Bengaluru | Level, programs, nearest gyms | Error: 'nearby_gyms' | FAIL |
| 18 | Gym Recommender | Input validation | latitude 95 | 422 validation error | HTTP 404 for latitude 95 | FAIL |
| 19 | AI Dietician | Calorie target estimate | 70 kg, 170 cm, weight loss | About 1,500-1,900 kcal | Error: 'target_calories' | FAIL |
| 20 | AI Dietician | Meal logging + intake summary | log, summarise, delete a meal | Saved, counted, removable | Error: 'id' | FAIL |
| 21 | AI Dietician | Meal validation | empty meal name | 422 validation error | HTTP 404 for empty meal name | FAIL |
| 22 | Smart Gym | Live MQTT / fallback + resistance advice | GET /api/smart-gym-live | Source shown, resistance + rest advice | Error: 'analysis' | FAIL |
| 23 | Backend API | Input validation | POST /api/diet-plan with {} | 422 validation error | HTTP 422 for empty body | PASS |

**16/23 passed.**
