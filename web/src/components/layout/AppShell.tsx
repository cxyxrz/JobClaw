"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Bell, ChevronDown, LayoutGrid, ScanSearch, User } from "lucide-react";

import { clearToken, getRole, getToken, getUsername } from "@/lib/auth";

const USER_NAV = [
  { label: "校招职位", href: "/jobs" },
  { label: "个人中心", href: "/me" },
];

const ADMIN_DOMAINS = [
  { label: "管理总览", href: "/admin", exact: true },
  { label: "采集工作台", href: "/admin/collect", exact: false },
];

function Logo({ wordmark = true }: { wordmark?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/logo.svg" alt="求职派" className="h-9 w-9 shrink-0" />
      {wordmark && (
        <span className="text-2xl font-bold text-blue-600">求职派</span>
      )}
    </span>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [username, setUsername] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    setAuthed(Boolean(getToken()));
    setUsername(getUsername() ?? "");
    setIsAdmin(getRole() === "ADMIN");
  }, [pathname]);

  const onAdmin = pathname?.startsWith("/admin");

  function logout() {
    clearToken();
    setMenuOpen(false);
    router.push("/");
  }

  const adminDomainActive = (d: (typeof ADMIN_DOMAINS)[number]) =>
    d.exact ? pathname === d.href : pathname?.startsWith(d.href);

  return (
    <div className="flex min-h-screen flex-col bg-[#f7f8fa]">
      {/* 顶部导航栏 */}
      <header className="fixed left-0 right-0 top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur-xl">
        <div className="px-4 sm:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex min-w-0 items-center gap-4 sm:gap-8">
              <div className="flex shrink-0 items-center">
                <Link
                  href="/"
                  className="inline-flex items-center rounded-md transition-opacity hover:opacity-80"
                >
                  <Logo wordmark={onAdmin ? false : true} />
                  {onAdmin && (
                    <span className="ml-2 hidden whitespace-nowrap text-sm font-medium text-slate-500 sm:inline">
                      管理后台
                    </span>
                  )}
                </Link>
              </div>
              {onAdmin ? (
                <nav className="flex min-w-0 items-center gap-1 overflow-x-auto whitespace-nowrap rounded-xl bg-slate-100/70 p-1">
                  {ADMIN_DOMAINS.map((d) => {
                    const active = adminDomainActive(d);
                    return (
                      <Link
                        key={d.href}
                        href={d.href}
                        className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                          active
                            ? "bg-white text-blue-600 shadow-sm"
                            : "text-gray-600 hover:bg-white hover:text-blue-600"
                        }`}
                      >
                        {d.label}
                      </Link>
                    );
                  })}
                </nav>
              ) : (
                <nav className="flex items-center gap-4 text-sm sm:gap-7">
                  {USER_NAV.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={
                        pathname?.startsWith(item.href)
                          ? "font-medium text-blue-600"
                          : "text-gray-700 hover:text-blue-600"
                      }
                    >
                      {item.label}
                    </Link>
                  ))}
                </nav>
              )}
            </div>
            <div className="ml-3 flex shrink-0 items-center gap-3">
              {!onAdmin && (
                <span className="hidden text-xs text-slate-400 lg:block">
                  让每一步求职更清晰
                </span>
              )}
              <button
                type="button"
                aria-label="通知"
                className="hidden h-9 w-9 items-center justify-center rounded-md text-slate-500 hover:text-slate-800 sm:inline-flex"
              >
                <Bell className="h-4 w-4" />
              </button>
              {mounted && authed ? (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setMenuOpen((v) => !v)}
                    className="flex cursor-pointer items-center rounded-full border border-slate-200 bg-white py-1 pl-1 pr-2"
                  >
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                      {username.slice(0, 1).toUpperCase() || "U"}
                    </span>
                    <ChevronDown className="ml-1 h-4 w-4 text-gray-500" />
                  </button>
                  {menuOpen && (
                    <>
                      <button
                        type="button"
                        aria-label="关闭菜单"
                        className="fixed inset-0 z-10 cursor-default"
                        onClick={() => setMenuOpen(false)}
                      />
                      <div className="absolute right-0 z-20 mt-2 w-44 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg">
                        <div className="px-3 py-2">
                          <div className="font-medium">{username || "已登录"}</div>
                          <div className="text-xs text-gray-500">
                            {isAdmin ? "管理员" : "普通用户"}
                          </div>
                        </div>
                        <div className="my-1 h-px bg-slate-100" />
                        <Link
                          href="/me"
                          onClick={() => setMenuOpen(false)}
                          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                        >
                          <User className="h-4 w-4" />
                          个人信息
                        </Link>
                        {isAdmin && (
                          <Link
                            href="/admin"
                            onClick={() => setMenuOpen(false)}
                            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          >
                            <LayoutGrid className="h-4 w-4" />
                            管理后台
                          </Link>
                        )}
                        <div className="my-1 h-px bg-slate-100" />
                        <button
                          type="button"
                          onClick={logout}
                          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
                        >
                          退出
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                mounted && (
                  <Link
                    href="/login"
                    className="inline-flex h-9 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600"
                  >
                    <User className="h-4 w-4" />
                    登录
                  </Link>
                )
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 正文内容 */}
      <main className="flex-grow pt-16">{children}</main>

      {!onAdmin && (
        <footer className="mt-auto border-t border-slate-200/70 py-7">
          <div className="px-4 sm:px-8">
            <p className="text-center text-sm text-gray-500">
              © {new Date().getFullYear()} 求职派 - 专注于校园招聘信息
            </p>
          </div>
        </footer>
      )}
    </div>
  );
}
