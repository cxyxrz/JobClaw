"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Files, ThumbsDown, ThumbsUp } from "lucide-react";

import { fetchDrafts, reviewDraft, type DraftOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

const STATUS_TABS: Array<{ value: string; label: string }> = [
  { value: "", label: "全部" },
  { value: "REVIEW", label: "待审核" },
  { value: "DRAFT", label: "草稿" },
  { value: "ACCEPTED", label: "已通过" },
  { value: "REJECTED", label: "已拒绝" },
];

const STATUS_BADGE: Record<string, string> = {
  DRAFT: "bg-blue-50 text-blue-600",
  REVIEW: "bg-amber-50 text-amber-600",
  ACCEPTED: "bg-green-50 text-green-600",
  REJECTED: "bg-slate-100 text-slate-500",
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "草稿",
  REVIEW: "待审核",
  ACCEPTED: "已通过",
  REJECTED: "已拒绝",
};

export default function DraftsPage() {
  const [authed, setAuthed] = useState(false);
  const [items, setItems] = useState<DraftOut[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<string>("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setAuthed(true);
  }, [router]);

  useEffect(() => {
    if (!authed) return;
    fetchDrafts(status || undefined, page)
      .then((d) => {
        setItems(d.items);
        setTotal(d.total);
      })
      .catch((err: Error) => setError(err.message));
  }, [authed, status, page]);

  async function onReview(id: number, action: "accept" | "reject") {
    setError("");
    try {
      await reviewDraft(id, action);
      setItems((prev) => prev.filter((d) => d.id !== id));
      setTotal((t) => t - 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    }
  }

  if (!authed) {
    return (
      <div className="p-6 sm:p-8">
        <div className="h-40 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / 20));

  return (
    <div className="p-6 sm:p-8">
      <div className="mb-6">
        <div className="eyebrow">
          <Files className="h-3.5 w-3.5 text-blue-500" />
          DRAFT REVIEW
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
          草稿审核
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          审核通过后草稿将自动转为正式职位发布。
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {STATUS_TABS.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => {
                setStatus(t.value);
                setPage(1);
              }}
              aria-pressed={status === t.value}
              className={`h-8 rounded-lg px-3.5 text-xs font-medium transition ${
                status === t.value
                  ? "bg-slate-900 text-white shadow-sm"
                  : "bg-white text-slate-500 shadow-sm ring-1 ring-slate-200 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400">共 {total} 条</span>
      </div>

      {error && (
        <p
          role="alert"
          className="mb-4 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {error}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="bg-slate-50/80 text-xs text-slate-500">
            <tr>
              <th className="px-5 py-4 font-medium">职位 / 公司</th>
              <th className="px-5 py-4 font-medium">城市 / 届别</th>
              <th className="px-5 py-4 font-medium">置信度</th>
              <th className="px-5 py-4 font-medium">来源</th>
              <th className="px-5 py-4 font-medium">状态</th>
              <th className="px-5 py-4 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((d) => (
              <tr
                key={d.id}
                className="border-t border-slate-100 hover:bg-slate-50/60"
              >
                <td className="max-w-56 px-5 py-3.5">
                  <p className="truncate font-medium text-slate-900">
                    {d.title ?? "—"}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-slate-500">
                    {d.company ?? "—"}
                  </p>
                </td>
                <td className="whitespace-nowrap px-5 py-3.5 text-slate-600">
                  {d.city ?? "—"} / {d.batch ?? "—"}
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-14 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full ${
                          d.confidence >= 0.6 ? "bg-green-400" : "bg-amber-400"
                        }`}
                        style={{ width: `${Math.round(d.confidence * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-5 py-3.5">
                  <span className="soft-tag">{d.source_type}</span>
                </td>
                <td className="px-5 py-3.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${
                      STATUS_BADGE[d.status] ?? "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {STATUS_LABEL[d.status] ?? d.status}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => onReview(d.id, "accept")}
                      className="inline-flex h-8 items-center gap-1.5 rounded-md bg-blue-600 px-3 text-xs font-medium text-white shadow-sm transition hover:bg-blue-700"
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                      通过
                    </button>
                    <button
                      type="button"
                      onClick={() => onReview(d.id, "reject")}
                      className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-900"
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                      拒绝
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr className="border-t border-slate-100">
                <td
                  colSpan={6}
                  className="px-5 py-10 text-center text-sm text-slate-400"
                >
                  暂无草稿
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="flex items-center justify-center gap-4 border-t border-slate-100 py-3.5 text-sm text-slate-500">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ‹ 上一页
          </button>
          <span className="text-xs">
            第 {page} / {totalPages} 页
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            下一页 ›
          </button>
        </div>
      </div>
    </div>
  );
}
