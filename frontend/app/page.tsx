import Link from "next/link";

const modules = [
  { name: "🥗 Diet Coach", href: "/diet-coach" },
  { name: "📊 Behavior Risk", href: "/behavior-risk" },
  { name: "💬 Gym Buddy", href: "/gym-buddy" },
  { name: "⌚ Smart Gym", href: "/smart-gym" },
  { name: "🎯 Recommendations", href: "/recommendations" },
  { name: "📈 Session Performance", href: "/session-performance" },
];

export default function Home() {
  return (
    <main className="max-w-4xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold mb-8">
        🏋️ AI Gym & Fitness Assistant — Dashboard
      </h1>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {modules.map((mod) => (
          <Link
            key={mod.href}
            href={mod.href}
            className="block bg-white rounded-xl shadow p-6 text-center font-medium hover:shadow-lg transition"
          >
            {mod.name}
          </Link>
        ))}
      </div>
    </main>
  );
}