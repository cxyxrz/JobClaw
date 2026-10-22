import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import Nav from "@/components/Nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "JobClaw 求职派",
  description: "校招职位聚合与 AI 采集平台",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6,#fb7185)] text-gray-900">
        <div className="mx-auto my-4 max-w-6xl px-3 sm:my-6 sm:px-4">
          <div className="flex min-h-[calc(100vh-2rem)] flex-col overflow-hidden rounded-2xl bg-white shadow-xl sm:min-h-[calc(100vh-3rem)]">
            <Nav />
            <div className="flex-1">{children}</div>
            <footer className="border-t border-gray-100 px-6 py-3 text-right text-xs text-gray-400">
              © 2026 JobClaw 求职派 · 版权所有
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
