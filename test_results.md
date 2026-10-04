# Test results — http://127.0.0.1:8000

| # | Module | Test | Input | Expected | Actual | Result |
|---|--------|------|-------|----------|--------|--------|
| 1 | Backend API | Root endpoint availability | GET / | 200 OK | 200 {"message":"AI Gym & Fitness Assistant API is running."} | PASS |
| 2 | AI Dietician | BMI + plan (normal BMI) | 70 kg, 170 cm, weight loss, vegetarian | BMI 24.2 Normal weight, plan returned | BMI 24.2 (Normal weight), plan length 1895 chars | PASS |
| 3 | AI Dietician | BMI category (underweight) | 50 kg, 170 cm, muscle gain | BMI 17.3 Underweight | BMI 17.3 (Underweight) | PASS |
| 4 | Habit Tracker | High-risk profile | 13 days, 1.28/wk, 77% | High risk + light 15-min schedule | High (96%); schedule: Light, 15 min | PASS |
| 5 | Habit Tracker | Low-risk profile (contrast) | 1 day, 6/wk, 95% | Low risk, no nudge | Low (1%); schedule: Progressive, 45 min | PASS |
| 6 | Habit Tracker | Medium-risk profile | 5 days, 3/wk, 60% | Medium risk + moderate schedule | Medium (58%); schedule: Moderate, 30 min | PASS |
| 7 | Gym Buddy | Negative message | I feel tired and stressed today | sentiment negative + reply | sentiment=negative; reply: Man, it sounds like today is just really relentless with the heavy stress. Seriously, let'... | PASS |
| 8 | Gym Buddy | Positive message | I feel great and motivated! | sentiment positive + reply | sentiment=positive; reply: Look at you bouncing right back again! I love this resilient energy. Let’s ride this posit... | PASS |
| 9 | Gym Buddy | Negation handling | I am not happy with my progress | sentiment negative | sentiment=negative; reply: Ah, the fitness rollercoaster is spinning us right back around, and that is totally okay! ... | PASS |
| 10 | Performance Analyzer | Good session | 12 reps, 120 s, 10/12 good | 66.0 / 83.3% / Good | score 66.0, form 83.3%, rating Good | PASS |
| 11 | Performance Analyzer | Poor session (contrast) | 3 reps, 300 s, 1/5 good | Needs Improvement | score 13.6, form 20.0%, rating Needs Improvement | PASS |
| 12 | Smart Gym | Sensor reading + matching advice | GET /api/smart-gym-reading | Advice matches heart-rate zone | HR 160 bpm, resistance 7, status cooldown -> Heart rate is high — recommend reducing resistance and taking a short  | PASS |
| 13 | Gym Recommender | Beginner streak | weight loss, streak 0 | 3-Day Kickstart Challenge | 3 programs, 3 gyms, challenge: 3-Day Kickstart Challenge — build your first habit streak! | PASS |
| 14 | Gym Recommender | Advanced streak | muscle gain, streak 20 | 30-Day Mastery Challenge | 3 programs, 3 gyms, challenge: 30-Day Muscle Gain Mastery Challenge — you're ready for the  | PASS |
| 15 | Weekly Report | Report from saved sessions | GET /api/weekly-report | 200 + report fields | 200; 13 session(s), 153 reps, average score 43.2 — trend: Improving. | PASS |
| 16 | Admin Analytics | Summary endpoint | GET /api/analytics/summary | 200 + totals | 200; sessions=13, risk checks=15 | PASS |
| 17 | Gym Recommender | Location + history aware | muscle gain, city Bengaluru | Level, programs, nearest gyms | level beginner (13 session(s) in the last 30 days, average score 43.2); nearest FitZone Elite 1.6 km | PASS |
| 18 | Gym Recommender | Input validation | latitude 95 | 422 validation error | HTTP 422 for latitude 95 | PASS |
| 19 | AI Dietician | Calorie target estimate | 70 kg, 170 cm, weight loss | About 1,500-1,900 kcal | target 1680 kcal (maintenance 2180) | PASS |
| 20 | AI Dietician | Meal logging + intake summary | log, summarise, delete a meal | Saved, counted, removable | logged -> today 300 kcal, 1400 remaining; then deleted | PASS |
| 21 | AI Dietician | Meal validation | empty meal name | 422 validation error | HTTP 422 for empty meal name | PASS |
| 22 | Smart Gym | Live MQTT / fallback + resistance advice | GET /api/smart-gym-live | Source shown, resistance + rest advice | source=simulated, HR 112 -> Maintain, resistance 10 -> 10, rest 45s, broker connected=False | PASS |
| 23 | Backend API | Input validation | POST /api/diet-plan with {} | 422 validation error | HTTP 422 for empty body | PASS |

**23/23 passed.**
