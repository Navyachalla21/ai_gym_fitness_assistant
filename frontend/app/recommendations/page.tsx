"use client";
import { useState } from "react";
import Link from "next/link";

export default function Recommendations() {
  const [goal, setGoal] = useState("weight loss");
  const [streak, setStreak] = useState(5);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, current_streak_days: streak }),
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
      <h1 className="text-2xl font-bold mt-4 mb-6">🎯 Gym Recommender & Planner</h1>

      <div className="space-y-4 bg-white p-6 rounded-xl shadow">
        <div>
          <label className="block text-sm font-medium mb-1">Your goal</label>
          <select value={goal} onChange={(e) => setGoal(e.target.value)} className="w-full border rounded-md px-3 py-2">
            <option>weight loss</option>
            <option>muscle gain</option>
            <option>endurance</option>
            <option>general fitness</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Current streak (days)</label>
          <input type="number" value={streak} onChange={(e) => setStreak(Number(e.target.value))} className="w-full border rounded-md px-3 py-2" />
        </div>

        <button onClick={handleSubmit} disabled={loading} className="w-full bg-black text-white rounded-md py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50">
          {loading ? "Loading..." : "Get Recommendations"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {result && (
          <div className="mt-6 border-t pt-4 space-y-3 text-sm">
            <div>
              <p className="font-semibold">Recommended Programs:</p>
              <ul className="list-disc ml-5">
                {result.programs.map((p: string, i: number) => <li key={i}>{p}</li>)}
              </ul>
            </div>
            <div>
              <p className="font-semibold">Nearby Gyms (demo data):</p>
              <ul className="list-disc ml-5">
                {result.nearby_gyms.map((g: any, i: number) => (
                  <li key={i}>{g.name} — {g.distance_km} km — ⭐ {g.rating}</li>
                ))}
              </ul>
            </div>
            <p><span className="font-semibold">Suggested Challenge:</span> {result.challenge}</p>
          </div>
        )}
      </div>
    </main>
  );
}