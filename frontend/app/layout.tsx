import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Gym & Fitness Assistant",
  description: "AI-powered fitness ecosystem",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">{children}</body>
    </html>
  );
}