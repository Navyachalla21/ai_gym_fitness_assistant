# 🏋️ AI Gym & Fitness Assistant

An AI-powered fitness ecosystem that unifies workout detection, diet planning, behavior tracking, IoT-based smart gym assistance, and conversational AI into a single intelligent platform — built as part of an internship project for Unlox Academy / Trivion.

## 🔗 Live Demo

- **Dashboard (Streamlit):** https://aigymfitnessassistant-sqktqokhufhzdfac6pdefs.streamlit.app
- **Backend API (Render):** https://ai-gym-backend-bwiz.onrender.com
- **API Docs (Swagger):** https://ai-gym-backend-bwiz.onrender.com/docs

> Note: The backend runs on Render's free tier, which spins down after periods of inactivity. The first request after idle time may take 30–50 seconds to respond while the server wakes up.

## 📖 Project Overview

The AI Gym & Fitness Assistant integrates seven core AI modules into one ecosystem that understands, adapts, and enhances a user's fitness journey — acting as a smart personal trainer, dietician, motivator, and data-driven fitness manager.

## 🧠 Core AI Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | **AI Gym Trainer** | Real-time webcam pose detection (MediaPipe) that counts bicep curl reps, tracks elbow angle, detects poor form (elbow drift), and gives audio + visual feedback. Runs as a standalone script due to webcam/real-time hardware requirements. |
| 2 | **AI Dietician & Calorie Coach** | Calculates BMI and generates a personalized diet plan, grocery list, and calorie target using Google Gemini (LLM), based on weight, height, goal, and dietary preferences. |
| 3 | **Smart Gym Assistant (AI + IoT)** | Simulates IoT gym equipment sensor data (heart rate, resistance level, equipment status) and gives real-time intensity/rest advice. |
| 4 | **AI Fitness Habit Tracker** | Uses a trained logistic regression model to predict workout skip risk based on recent engagement patterns, and sends motivational nudges. |
| 5 | **Virtual Gym Buddy** | A conversational AI companion (Gemini-powered) with keyword-based sentiment detection that responds supportively based on the user's detected mood. |
| 6 | **Pose-to-Performance Analyzer** | Scores a completed workout session (reps, duration, form feedback) into a Performance Score, Form Quality %, and Rating. |
| 7 | **Gym Recommender & Planner** | Recommends workout programs, nearby gyms (demo data), and fitness challenges based on the user's goal and current streak. |

### 🔄 Module Integration

Module 1 (AI Gym Trainer) automatically sends its session results (reps, duration, form feedback) to the backend's `/api/analyze-session` endpoint the moment a webcam session ends — directly feeding Module 6 (Pose-to-Performance Analyzer) without any manual data entry. This is the core "integration layer" connecting real-time detection to performance scoring.

The remaining modules (2, 3, 4, 5, 7) each operate as independent tools within the same dashboard and backend, per the system's modular design.

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend (Dashboard) | Streamlit (deployed), React.js / Next.js (built, local) |
| Backend | Python, FastAPI |
| AI/ML | Google Gemini API (LangChain), MediaPipe (Pose Landmarker Tasks API), OpenCV, scikit-learn |
| Deployment | Render (backend), Streamlit Community Cloud (dashboard), Docker (containerized setup available) |
| Version Control | Git / GitHub |

## 📁 Project Structure

ai_gym_fitness_assistant/
├── ai_modules/
│ ├── pose_detector.py # Module 1: AI Gym Trainer (webcam)
│ ├── diet_coach.py # Module 2: Diet Coach
│ ├── smart_gym_assistant.py # Module 3: Smart Gym (IoT simulation)
│ ├── behavior_predictor.py # Module 4: Habit Tracker
│ ├── gym_buddy_chat.py # Module 5: Gym Buddy Chat
│ ├── performance_analyzer.py # Module 6: Performance Analyzer
│ ├── gym_recommender.py # Module 7: Recommender
│ └── pose_landmarker_lite.task # MediaPipe pose model
├── backend/
│ ├── app.py # FastAPI app + routes
│ ├── Dockerfile
│ └── requirements.txt
├── frontend/ # React/Next.js dashboard
│ ├── app/
│ │ ├── page.tsx # Dashboard home
│ │ ├── diet-coach/
│ │ ├── behavior-risk/
│ │ ├── gym-buddy/
│ │ ├── smart-gym/
│ │ ├── recommendations/
│ │ └── session-performance/
│ └── Dockerfile
├── streamlit_dashboard/
│ └── app.py # Streamlit dashboard (deployed)
├── docker-compose.yml
└── README.md

## 🚀 Running Locally

### Option 1: Manual (Python + Node)

**Backend:**
```bash
backend\venv\Scripts\activate
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

**Streamlit Dashboard:**
```bash
streamlit run streamlit_dashboard/app.py
```

**React Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:3000`

**AI Gym Trainer (webcam):**
```bash
python ai_modules/pose_detector.py
```
Press `q` to quit and auto-send session results to the backend.

### Option 2: Docker (containerized)

```bash
docker compose up --build
```
This builds and runs both the backend and frontend containers together. Requires Docker Desktop installed and running.

> Docker configuration is included in this repository for containerized deployment. Due to time constraints, the primary deployed demo uses Streamlit Community Cloud + Render (see Live Demo links above); Docker deployment will be fully tested and used post-submission.

### Environment Variables

Create a `.env` file in the project root and in `backend/` with:

GOOGLE_API_KEY=your_gemini_api_key_here

## ✅ Testing Summary

The following was manually tested and verified working:

- **Diet Coach:** Verified correct BMI calculation, category classification, and AI-generated meal plans across multiple goals (muscle gain, weight loss).
- **Behavior Risk:** Verified skip-risk predictions and nudges across low/medium/high risk scenarios.
- **Gym Buddy Chat:** Verified sentiment detection (positive/neutral/negative) and contextual AI replies across a multi-turn conversation.
- **Smart Gym:** Verified simulated sensor readings and matching advice (e.g., high heart rate → rest recommendation).
- **Recommendations:** Verified goal-based program suggestions, demo gym listings, and challenge suggestions.
- **Session Performance:** Verified performance score, form quality %, and rating calculations from sample session data.
- **AI Gym Trainer (Module 1):** Tested live with webcam and physical dumbbells — verified real-time rep counting, elbow angle tracking, form-drift warning (audio beep), and good-rep confirmation (audio beep).
- **Module 1 → Module 6 Integration:** Verified that ending a live webcam session automatically POSTs session data to the backend and returns a live performance score — no manual re-entry required.
- **Deployment:** Verified the live Streamlit Cloud dashboard successfully communicates with the live Render-hosted backend end-to-end, including real Gemini AI responses, from a public URL (not localhost).
- **Cross-platform parity:** Verified all 6 dashboard modules produce consistent results across both the Streamlit dashboard and the React/Next.js frontend.

## 📌 Notes & Known Limitations

- The AI Gym Trainer (Module 1) runs as a standalone Python script rather than a web page, due to the real-time webcam access and frame-processing requirements of MediaPipe/OpenCV, which are better suited to a native script than a browser environment. It integrates with the rest of the system via the backend API.
- Render's free-tier backend spins down after 15 minutes of inactivity; the first request after idle time will be slower (~30–50s) while it restarts.
- Docker containerization is complete and available in the repository but not yet used as the primary deployment method, due to project timeline constraints.

## 👩‍💻 Author

Navyashree K N — Project Intern, Unlox Academy
