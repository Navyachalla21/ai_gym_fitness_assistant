"use client";

import { useState } from "react";
import Link from "next/link";

export default function DietCoach() {
  const [weight, setWeight] = useState(70);
  const [height, setHeight] = useState(170);
  const [goal, setGoal] = useState("weight loss");
  const [preferences, setPreferences] = useState("no restrictions");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/diet-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weight_kg: weight,
          height_cm: height,
          goal,
          preferences,
        }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-2xl mx-auto py-12 px-6">
      <Link href="/" className="text-sm text-blue-600 hover:underline">
        ← Back to Dashboard
      </Link>
      <h1 className="text-2xl font-bold mt-4 mb-6">
        🥗 AI Dietician & Calorie Coach
      </h1>

      <div className="space-y-4 bg-white p-6 rounded-xl shadow">
        <div>
          <label className="block text-sm font-medium mb-1">Weight (kg)</label>
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(Number(e.target.value))}
            className="w-full border rounded-md px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Height (cm)</label>
          <input
            type="number"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            className="w-full border rounded-md px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Goal</label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full border rounded-md px-3 py-2"
          >
            <option>weight loss</option>
            <option>muscle gain</option>
            <option>endurance</option>
            <option>general fitness</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Dietary preferences
          </label>
          <input
            type="text"
            value={preferences}
            onChange={(e) => setPreferences(e.target.value)}
            className="w-full border rounded-md px-3 py-2"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-black text-white rounded-md py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate Diet Plan"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {result && (
          <div className="mt-6 border-t pt-4">
            <p className="font-semibold">
              BMI: {result.bmi} ({result.category})
            </p>
            <div className="mt-3 whitespace-pre-wrap text-sm text-gray-800">
              {result.plan}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}