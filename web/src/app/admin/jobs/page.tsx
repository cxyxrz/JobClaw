"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { BriefcaseBusiness, Plus } from "lucide-react";

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
      <div className="p-6 sm:p-8">
        <div className="h-40 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
    );
  }
  if (user.role !== "ADMIN") {
    return (
      <div className="p-6 sm:p-8">
        <div className="empty-panel">
          当前账号 {user.username} 无管理权限（需要 ADMIN 角色）。
        </div>
      </div>
    );
  }

  const fields: Array<[keyof typeof EMPTY_FORM, string, boolean]> = [
    ["title", "职位标题", true],
    ["company", "公司", true],
    ["city", "城市", true],
    ["batch", "届别", true],
    ["category", "类别", false],
    ["salary_text", "薪资", false],
  ];

  const inputCls =
    "h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

  return (
    <div className="p-6 sm:p-8">
      <div className="mb-6">
        <div className="eyebrow">
          <BriefcaseBusiness className="h-3.5 w-3.5 text-blue-500" />
          JOB LIBRARY
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
          职位库管理
        </h1>
      </div>

      <form
        onSubmit={onCreate}
        className="mb-6 grid gap-4 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm sm:grid-cols-3"
      >
        <h2 className="text-sm font-semibold text-slate-900 sm:col-span-3">
          创建职位
        </h2>
        {fields.map(([key, label, required]) => (
          <label key={key} className="grid gap-1.5 text-sm">
            <span className="font-medium text-slate-600">{label}</span>
            <input
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required={required}
              className={inputCls}
            />
          </label>
        ))}
        <label className="grid gap-1.5 text-sm sm:col-span-3">
          <span className="font-medium text-slate-600">职位描述</span>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </label>
        <div className="flex items-center gap-3 sm:col-span-3">
          <button
            type="submit"
            className="inline-flex h-10 items-center gap-2 rounded-md bg-blue-600 px-5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            发布职位
          </button>
          {message && (
            <span className="text-sm font-medium text-green-600">{message}</span>
          )}
        </div>
      </form>

      {error && (
        <p
          role="alert"
          className="mb-4 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50/80 text-xs text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">ID</th>
              <th className="px-5 py-4 font-medium">职位</th>
              <th className="px-5 py-4 font-medium">公司</th>
              <th className="px-5 py-4 font-medium">城市 / 届别</th>
              <th className="px-5 py-4 font-medium">状态</th>
              <th className="px-5 py-4 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items ?? []).map((job) => (
              <tr
                key={job.id}
                className="border-t border-slate-100 hover:bg-slate-50/60"
              >
                <td className="px-5 py-3.5 text-slate-400">{job.id}</td>
                <td className="max-w-56 truncate px-5 py-3.5 font-medium text-slate-900">
                  {job.title}
                </td>
                <td className="max-w-44 truncate px-5 py-3.5">{job.company}</td>
                <td className="whitespace-nowrap px-5 py-3.5 text-slate-600">
                  {job.city} / {job.batch}
                </td>
                <td className="px-5 py-3.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${
                      job.status === "PUBLISHED"
                        ? "bg-green-50 text-green-600"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {job.status === "PUBLISHED" ? "已发布" : "已下线"}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  <button
                    type="button"
                    onClick={() =>
                      toggleStatus(
                        job.id,
                        job.status === "PUBLISHED" ? "OFFLINE" : "PUBLISHED",
                      )
                    }
                    className="inline-flex h-8 items-center rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600"
                  >
                    {job.status === "PUBLISHED" ? "下线" : "发布"}
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr className="border-t border-slate-100">
                <td
                  colSpan={6}
                  className="px-5 py-10 text-center text-sm text-slate-400"
                >
                  暂无数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
