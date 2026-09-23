"use client";
import { useState } from "react";
import Link from "next/link";

type Message = { sender: "You" | "Buddy"; text: string; sentiment?: string };

export default function GymBuddy() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages((prev) => [...prev, { sender: "You", text: userMsg }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/gym-buddy-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { sender: "Buddy", text: data.reply, sentiment: data.sentiment }]);
    } catch {
      setMessages((prev) => [...prev, { sender: "Buddy", text: "Error reaching backend.", sentiment: "error" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-2xl mx-auto py-12 px-6">
      <Link href="/" className="text-sm text-blue-600 hover:underline">← Back to Dashboard</Link>
      <h1 className="text-2xl font-bold mt-4 mb-6">💬 Virtual Gym Buddy</h1>

      <div className="bg-white p-6 rounded-xl shadow space-y-4">
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {messages.map((m, i) => (
            <p key={i} className="text-sm">
              {m.sender === "You" ? (
                <span><strong>You:</strong> {m.text}</span>
              ) : (
                <span><strong>Buddy</strong> <em>(mood: {m.sentiment})</em>: {m.text}</span>
              )}
            </p>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Talk to your gym buddy..."
            className="flex-1 border rounded-md px-3 py-2"
          />
          <button onClick={handleSend} disabled={loading} className="bg-black text-white rounded-md px-4 py-2 font-medium hover:bg-gray-800 transition disabled:opacity-50">
            {loading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </main>
  );
}