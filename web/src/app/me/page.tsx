"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BadgeCheck,
  BriefcaseBusiness,
  CalendarClock,
  IdCard,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { api, type UserOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function MePage() {
  const [user, setUser] = useState<UserOut | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<UserOut>("/api/v1/auth/me")
      .then(setUser)
      .catch((err: Error) => setError(err.message));
  }, [router]);

  if (error) {
    return (
      <div className="member-workspace py-12">
        <div className="empty-panel">加载失败：{error}</div>
      </div>
    );
  }
  if (!user) {
    return (
      <div className="member-workspace py-12">
        <div className="h-40 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
    );
  }

  const isVip = user.vip_level > 0;

  const infos = [
    {
      icon: IdCard,
      label: "用户名",
      value: user.username,
    },
    {
      icon: ShieldCheck,
      label: "角色",
      value: user.role === "ADMIN" ? "管理员" : "普通用户",
    },
    {
      icon: BadgeCheck,
      label: "会员状态",
      value: isVip ? `VIP ${user.vip_level}` : "普通用户",
    },
    {
      icon: CalendarClock,
      label: "会员到期",
      value: user.vip_expires_at
        ? user.vip_expires_at.slice(0, 10)
        : "—",
    },
  ];

  return (
    <div className="member-workspace py-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="eyebrow">
            <Sparkles className="h-3.5 w-3.5 text-blue-500" />
            YOUR CAREER AGENT
          </div>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
            你好，{user.username}
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            管理你的账号信息与求职偏好
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold ${
            isVip
              ? "bg-blue-50 text-blue-700"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          <BadgeCheck className="h-3.5 w-3.5" />
          {isVip ? `VIP ${user.vip_level}` : "普通用户"}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {infos.map(({ icon: Icon, label, value }) => (
          <div
            key={label}
            className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                <Icon className="h-5 w-5" strokeWidth={1.7} />
              </span>
              <div className="min-w-0">
                <p className="text-xs text-slate-400">{label}</p>
                <p className="mt-0.5 truncate text-lg font-semibold text-slate-900">
                  {value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-2xl border border-dashed border-blue-200 bg-blue-50/50 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-blue-600 shadow-sm">
              <BriefcaseBusiness className="h-5 w-5" strokeWidth={1.7} />
            </span>
            <div>
              <h2 className="font-semibold text-slate-900">
                更多求职能力建设中
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                职位收藏、投递记录、AI 求职助手即将上线，敬请期待。
              </p>
            </div>
          </div>
          <span className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-500 shadow-sm">
            M3–M5 规划中
          </span>
        </div>
      </div>
    </div>
  );
}
