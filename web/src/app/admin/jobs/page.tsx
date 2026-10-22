"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { api, type JobPage, type UserOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

const EMPTY_FORM = {
  title: "",
  company: "",
  city: "",
  batch: "",
  category: "",
  salary_text: "",
  description: "",
};

export default function AdminJobsPage() {
  const [user, setUser] = useState<UserOut | null>(null);
  const [data, setData] = useState<JobPage | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const routerReady = typeof window !== "undefined";

  const load = useCallback(() => {
    api<JobPage>("/api/v1/admin/jobs?status=ALL&page_size=50")
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!routerReady) return;
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    api<UserOut>("/api/v1/auth/me")
      .then((me) => {
        setUser(me);
        if (me.role === "ADMIN") load();
      })
      .catch((err: Error) => setError(err.message));
  }, [load, routerReady]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      await api("/api/v1/admin/jobs", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          category: form.category || null,
          salary_text: form.salary_text || null,
        }),
      });
      setForm(EMPTY_FORM);
      setMessage("职位已发布");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    }
  }

  async function toggleStatus(id: number, status: string) {
    setError("");
    try {
      await api(`/api/v1/admin/jobs/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    }
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
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-red-600">
        当前账号 {user.username} 无管理权限（需要 ADMIN 角色）。
      </main>
    );
  }

  const fields: Array<[keyof typeof EMPTY_FORM, string, string]> = [
    ["title", "职位标题", "text"],
    ["company", "公司", "text"],
    ["city", "城市", "text"],
    ["batch", "届别", "text"],
    ["category", "类别", "text"],
    ["salary_text", "薪资", "text"],
  ];

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-xl font-semibold">职位管理</h1>

      <form
        onSubmit={onCreate}
        className="mt-4 grid gap-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm sm:grid-cols-3"
      >
        {fields.map(([key, label]) => (
          <label key={key} className="grid gap-1.5 text-sm">
            <span className="text-gray-600">{label}</span>
            <input
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required={key === "title" || key === "company" || key === "city" || key === "batch"}
              className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </label>
        ))}
        <label className="grid gap-1.5 text-sm sm:col-span-3">
          <span className="text-gray-600">职位描述</span>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
            className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          />
        </label>
        <div className="sm:col-span-3">
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            发布职位
          </button>
          {message && (
            <span className="ml-3 text-sm text-blue-600">{message}</span>
          )}
        </div>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">职位</th>
                <th className="px-4 py-3 font-medium">公司</th>
                <th className="px-4 py-3 font-medium">城市/届别</th>
                <th className="px-4 py-3 font-medium">状态</th>
                <th className="px-4 py-3 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((job) => (
                <tr key={job.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{job.id}</td>
                  <td className="px-4 py-3">{job.title}</td>
                  <td className="px-4 py-3">{job.company}</td>
                  <td className="px-4 py-3">
                    {job.city} / {job.batch}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        job.status === "PUBLISHED"
                          ? "text-blue-600"
                          : "text-gray-400"
                      }
                    >
                      {job.status === "PUBLISHED" ? "已发布" : "已下线"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() =>
                        toggleStatus(
                          job.id,
                          job.status === "PUBLISHED" ? "OFFLINE" : "PUBLISHED",
                        )
                      }
                      className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:border-gray-400"
                    >
                      {job.status === "PUBLISHED" ? "下线" : "发布"}
                    </button>
                  </td>
                </tr>
              ))}
              {data && data.items.length === 0 && (
                <tr className="border-t border-gray-100">
                  <td colSpan={6} className="px-4 py-10 text-center text-sm text-gray-400">
                    暂无数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
