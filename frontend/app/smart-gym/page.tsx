"use client";
import { useState } from "react";
import Link from "next/link";

export default function SmartGym() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFetch = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/smart-gym-reading");
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
      <h1 className="text-2xl font-bold mt-4 mb-6">⌚ Smart Gym Assistant (Simulated IoT)</h1>
      <p className="text-sm text-gray-500 mb-4">Simulated sensor data — demonstrates the AI+IoT integration layer.</p>

      <div className="bg-white p-6 rounded-xl shadow space-y-4">
        <button onClick={handleFetch} disabled={loading} className="w-full bg-black text-white rounded-md py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50">
          {loading ? "Reading..." : "Get Live Sensor Reading"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {result && (
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500">Heart Rate</p>
              <p className="font-bold">{result.reading.heart_rate_bpm} bpm</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Resistance Level</p>
              <p className="font-bold">{result.reading.resistance_level}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Equipment Status</p>
              <p className="font-bold">{result.reading.equipment_status}</p>
            </div>
            <div className="col-span-3 mt-2 text-sm bg-blue-50 border border-blue-200 rounded-md p-3 text-left">
              {result.advice}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}