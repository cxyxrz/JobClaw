"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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

  const rows: Array<[string, string]> = [
    ["用户 ID", String(user.id)],
    ["用户名", user.username],
    ["角色", user.role],
    ["VIP 等级", String(user.vip_level)],
    ["VIP 到期", user.vip_expires_at ?? "—"],
  ];

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-xl font-semibold">个人中心</h1>
      <dl className="mt-6 grid max-w-md gap-3 rounded-lg border border-gray-200 bg-white p-6 text-sm shadow-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4">
            <dt className="text-gray-500">{label}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-4 text-sm text-gray-500">
        职位列表、收藏职位与投递记录将在 M1 之后接入。
      </p>
    </main>
  );
}
