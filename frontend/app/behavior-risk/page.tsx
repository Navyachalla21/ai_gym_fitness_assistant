"use client";
import { useState } from "react";
import Link from "next/link";

export default function BehaviorRisk() {
  const [days, setDays] = useState(2);
  const [weekly, setWeekly] = useState(4);
  const [completion, setCompletion] = useState(85);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/behavior-risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          days_since_last_workout: days,
          weekly_avg_sessions: weekly,
          avg_session_completion_pct: completion,
        }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-2xl mx-auto py-12 px-6">
      <Link href="/" className="text-sm text-blue-600 hover:underline">← Back to Dashboard</Link>
      <h1 className="text-2xl font-bold mt-4 mb-6">📊 AI Fitness Habit Tracker</h1>

      <div className="space-y-4 bg-white p-6 rounded-xl shadow">
        <div>
          <label className="block text-sm font-medium mb-1">Days since last workout: {days}</label>
          <input type="range" min={0} max={14} value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-full" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Average sessions per week: {weekly}</label>
          <input type="range" min={0} max={7} step={0.5} value={weekly} onChange={(e) => setWeekly(Number(e.target.value))} className="w-full" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Average session completion %: {completion}</label>
          <input type="range" min={0} max={100} value={completion} onChange={(e) => setCompletion(Number(e.target.value))} className="w-full" />
        </div>

        <button onClick={handleSubmit} disabled={loading} className="w-full bg-black text-white rounded-md py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50">
          {loading ? "Predicting..." : "Predict Skip Risk"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {result && (
          <div className="mt-6 border-t pt-4 space-y-2">
            <p className="font-semibold">Skip Risk: {result.risk_level} ({(result.skip_probability * 100).toFixed(0)}%)</p>
            {result.nudge && <p className="text-sm bg-blue-50 border border-blue-200 rounded-md p-3">{result.nudge}</p>}
          </div>
        )}
      </div>
    </main>
  );
}