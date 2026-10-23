"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  Database,
  FileSearch,
  LayoutDashboard,
  ShieldAlert,
  Wallet,
} from "lucide-react";

import { api, type PingData, type UserOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

const MODULES: Array<{
  name: string;
  note: string;
  href?: string;
  icon: typeof Bot;
  live?: boolean;
}> = [
  {
    name: "采集工作台",
    note: "提交文本 / 网页 / Excel / 图片，AI 自动抽取字段入库",
    href: "/admin/collect",
    icon: Bot,
    live: true,
  },
  {
    name: "草稿审核",
    note: "低置信度草稿人工复核，通过后一键转为正式职位",
    href: "/admin/drafts",
    icon: FileSearch,
    live: true,
  },
  {
    name: "职位库管理",
    note: "职位创建、发布与下线，全状态查询",
    href: "/admin/jobs",
    icon: BriefcaseBusiness,
    live: true,
  },
  {
    name: "字典管理",
    note: "城市 / 届别 / 会员价格等字典与版本同步（接口已就绪）",
    icon: Database,
  },
  {
    name: "会员订单",
    note: "微信支付订单与 VIP 发放",
    icon: Wallet,
  },
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
      <div className="p-6 sm:p-8">
        <div className="empty-panel">加载失败：{error}</div>
      </div>
    );
  }
  if (!user) {
    return (
      <div className="p-6 sm:p-8">
        <div className="h-40 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
    );
  }
  if (user.role !== "ADMIN") {
    return (
      <div className="p-6 sm:p-8">
        <div className="empty-panel">
          <ShieldAlert className="mx-auto mb-3 h-8 w-8 text-amber-400" />
          <h2 className="font-medium text-slate-800">无管理权限</h2>
          <p className="mt-2 text-sm">
            当前账号 {user.username} 需要 ADMIN 角色才能进入管理后台。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 sm:p-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="eyebrow">
            <LayoutDashboard className="h-3.5 w-3.5 text-blue-500" />
            ADMIN CONSOLE
          </div>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
            管理总览
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            欢迎回来，{user.username} · 数据服务
            {ping
              ? "运行正常"
              : "状态检测中…"}
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold ${
            ping
              ? "bg-green-50 text-green-600"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              ping ? "bg-green-500" : "bg-slate-400"
            }`}
          />
          API {ping ? "在线" : "…"}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {MODULES.map(({ name, note, href, icon: Icon, live }) => {
          const inner = (
            <section className="flex h-full flex-col rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:border-blue-200 hover:shadow-md">
              <div className="flex items-center justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </span>
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                    live
                      ? "bg-green-50 text-green-600"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {live ? "可用" : "规划中"}
                </span>
              </div>
              <h2 className="mt-4 font-semibold text-slate-900">{name}</h2>
              <p className="mt-2 flex-1 text-sm leading-6 text-slate-500">
                {note}
              </p>
              {href && (
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-blue-600">
                  进入 <ArrowUpRight className="h-4 w-4" />
                </span>
              )}
            </section>
          );
          return href ? (
            <Link key={name} href={href}>
              {inner}
            </Link>
          ) : (
            <div key={name}>{inner}</div>
          );
        })}
      </div>
    </div>
  );
}
