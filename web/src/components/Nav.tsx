"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { clearToken, getToken } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/jobs", label: "校招职位" },
  { href: "/me", label: "个人中心" },
  { href: "/admin", label: "管理端" },
];

export default function Nav() {
  const [authed, setAuthed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, [pathname]);

  function logout() {
    clearToken();
    setAuthed(false);
    router.push("/");
  }

  return (
    <header className="border-b border-gray-100 bg-white">
      <nav className="mx-auto flex w-full max-w-6xl items-center gap-6 px-6 py-3">
        <Link href="/" className="flex shrink-0 items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-base font-bold text-white">
            J
          </span>
          <span className="text-lg font-bold text-blue-600">求职派</span>
        </Link>
        <div className="flex items-center gap-5 text-sm">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  active
                    ? "font-medium text-blue-600"
                    : "text-gray-600 hover:text-gray-900"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </div>
        <div className="ml-auto flex items-center gap-4">
          <button
            type="button"
            aria-label="通知"
            className="text-gray-500 hover:text-gray-700"
          >
            <BellIcon />
          </button>
          {authed ? (
            <button
              type="button"
              onClick={logout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              退出登录
            </button>
          ) : (
            <Link
              href="/login"
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              登录
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}

function BellIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}
