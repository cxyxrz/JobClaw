"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ArrowRight, Sparkles } from "lucide-react";

import { api, ApiError, type LoginData } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api<LoginData>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
        auth: false,
      });
      setToken(data.access_token, data.user.username);
      router.push(data.user.role === "ADMIN" ? "/admin" : "/me");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "登录失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }

  const inputCls =
    "h-11 w-full rounded-md border border-slate-200 bg-white px-3.5 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

  return (
    <main className="member-workspace flex min-h-[calc(100svh-4rem-72px)] items-center justify-center py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            <Sparkles className="h-3.5 w-3.5" /> AI 求职伙伴
          </span>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-950">
            欢迎回到求职派
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            登录后解锁完整招聘信息与 AI 采集能力
          </p>
        </div>

        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-slate-200/80 bg-white p-7 shadow-sm"
        >
          <div className="space-y-4">
            <label className="grid gap-1.5 text-sm">
              <span className="font-medium text-slate-700">账号</span>
              <input
                className={inputCls}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin / demo"
                autoComplete="username"
                required
              />
            </label>
            <label className="grid gap-1.5 text-sm">
              <span className="font-medium text-slate-700">密码</span>
              <input
                className={inputCls}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                autoComplete="current-password"
                required
              />
            </label>
          </div>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-red-100 bg-red-50 px-3 py-2.5 text-xs text-red-600"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 text-sm font-semibold text-white shadow-md shadow-blue-600/15 transition hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "登录中…" : "登录"}
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>

          <p className="mt-5 text-center text-xs text-slate-400">
            测试账号：admin / admin123（管理员）· demo / demo123（用户）
          </p>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          还没有账号？
          <Link href="/jobs" className="text-blue-600 hover:text-blue-700">
            先逛逛职位
          </Link>
        </p>
      </div>
    </main>
  );
}
