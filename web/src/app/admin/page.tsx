"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, type PingData, type UserOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

const MODULES: Array<{ name: string; note: string; href?: string }> = [
  { name: "采集任务", note: "提交文本/网页/Excel/图片采集，AI 自动抽取字段", href: "/admin/collect" },
  { name: "草稿审核", note: "审核采集草稿，通过则转为正式职位", href: "/admin/drafts" },
  { name: "职位管理", note: "草稿审核与发布、职位查询", href: "/admin/jobs" },
  { name: "字典管理", note: "城市/届别/会员价格等字典与版本同步" },
  { name: "会员订单", note: "微信支付订单与 VIP 发放（M4）" },
];

export default function AdminPage() {
  const [user, setUser] = useState<UserOut | null>(null);
  const [ping, setPing] = useState<PingData | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<UserOut>("/api/v1/auth/me")
      .then((me) => {
        setUser(me);
        if (me.role === "ADMIN") {
          api<PingData>("/api/v1/admin/ping").then(setPing).catch(() => setPing(null));
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [router]);

  if (error) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-red-600">
        加载失败：{error}
      </main>
    );
  }
  if (!user) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-gray-500">
        加载中…
      </main>
    );
  }
  if (user.role !== "ADMIN") {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <h1 className="text-xl font-semibold">管理端</h1>
        <p className="mt-4 text-sm text-red-600">
          当前账号 {user.username} 无管理权限（需要 ADMIN 角色）。
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-xl font-semibold">管理端</h1>
      <p className="mt-2 text-sm text-gray-500">
        当前登录：{user.username}（ADMIN）· 后端连通性：
        {ping ? `ping=${ping.pong}` : "检测中…"}
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {MODULES.map((m) => {
          const inner = (
            <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:border-blue-300 hover:shadow-md">
              <h2 className="font-medium text-gray-900">{m.name}</h2>
              <p className="mt-2 text-sm text-gray-500">{m.note}</p>
              {m.href && (
                <span className="mt-3 inline-block text-sm text-blue-600">进入 →</span>
              )}
            </section>
          );
          return m.href ? (
            <Link key={m.name} href={m.href}>
              {inner}
            </Link>
          ) : (
            <div key={m.name}>{inner}</div>
          );
        })}
      </div>
    </main>
  );
}
