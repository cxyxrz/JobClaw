"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BriefcaseBusiness,
  FilePlus2,
  Files,
  LayoutDashboard,
  type LucideIcon,
} from "lucide-react";

interface AdminMenuItem {
  label: string;
  path: string;
  icon: LucideIcon;
}

const MENU: AdminMenuItem[] = [
  { label: "新建采集", path: "/admin/collect", icon: FilePlus2 },
  { label: "草稿审核", path: "/admin/drafts", icon: Files },
  { label: "职位库", path: "/admin/jobs", icon: BriefcaseBusiness },
  { label: "管理总览", path: "/admin", icon: LayoutDashboard },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-[calc(100svh-4rem)] flex-col md:h-[calc(100svh-4rem)] md:flex-row md:overflow-hidden">
      <aside className="flex shrink-0 flex-col border-b border-slate-200/80 bg-white md:w-52 md:border-b-0 md:border-r">
        <nav
          aria-label="后台页面"
          className="flex gap-1 overflow-x-auto p-3 md:flex-col md:px-3 md:py-5"
        >
          {MENU.map((item) => {
            const Icon = item.icon;
            const active =
              item.path === "/admin"
                ? pathname === "/admin"
                : pathname === item.path || pathname?.startsWith(`${item.path}/`);
            return (
              <Link
                key={item.path}
                href={item.path}
                aria-current={active ? "page" : undefined}
                className={`flex shrink-0 items-center gap-3 rounded-lg px-3 py-3 text-[13px] transition-colors ${
                  active
                    ? "bg-blue-50 font-semibold text-blue-700"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon className="h-[17px] w-[17px]" />
                {item.label}
                {active && (
                  <span className="ml-auto hidden h-1.5 w-1.5 rounded-full bg-blue-600 md:block" />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto hidden px-6 py-5 md:block">
          <Link href="/" className="text-xs text-slate-400 hover:text-blue-600">
            浏览用户端 ↗
          </Link>
        </div>
      </aside>
      <main className="admin-workspace min-h-0 min-w-0 flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
