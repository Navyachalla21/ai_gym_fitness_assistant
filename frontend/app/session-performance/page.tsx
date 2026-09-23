"use client";
import { useState } from "react";
import Link from "next/link";

export default function SessionPerformance() {
  const [reps, setReps] = useState(12);
  const [duration, setDuration] = useState(120);
  const [goodCount, setGoodCount] = useState(10);
  const [totalCount, setTotalCount] = useState(12);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const feedbackList = [
      ...Array(goodCount).fill("Good rep!"),
      ...Array(Math.max(totalCount - goodCount, 0)).fill("Adjust form"),
    ];
    try {
      const res = await fetch("http://localhost:8000/api/analyze-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reps, duration_seconds: duration, form_feedback_list: feedbackList }),
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
      <h1 className="text-2xl font-bold mt-4 mb-6">📈 Pose-to-Performance Analyzer</h1>
      <p className="text-sm text-gray-500 mb-4">Enter results from a completed AI Gym Trainer session.</p>

      <div className="space-y-4 bg-white p-6 rounded-xl shadow">
        <div>
          <label className="block text-sm font-medium mb-1">Reps completed</label>
          <input type="number" value={reps} onChange={(e) => setReps(Number(e.target.value))} className="w-full border rounded-md px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Session duration (seconds)</label>
          <input type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-full border rounded-md px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Number of &apos;Good rep!&apos; feedbacks</label>
          <input type="number" value={goodCount} onChange={(e) => setGoodCount(Number(e.target.value))} className="w-full border rounded-md px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Total feedback events</label>
          <input type="number" value={totalCount} onChange={(e) => setTotalCount(Number(e.target.value))} className="w-full border rounded-md px-3 py-2" />
        </div>

        <button onClick={handleSubmit} disabled={loading} className="w-full bg-black text-white rounded-md py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50">
          {loading ? "Analyzing..." : "Analyze Session"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {result && (
          <div className="mt-6 border-t pt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">Performance Score</p>
              <p className="font-bold">{result.performance_score}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Form Quality</p>
              <p className="font-bold">{result.form_quality_pct}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Rating</p>
              <p className="font-bold">{result.rating}</p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}