"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchDrafts, reviewDraft, type DraftOut } from "@/lib/api";
import { getToken } from "@/lib/auth";

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "草稿",
  REVIEW: "待审核",
  ACCEPTED: "已通过",
  REJECTED: "已拒绝",
};
const STATUS_COLOR: Record<string, string> = {
  DRAFT: "text-blue-600",
  REVIEW: "text-amber-600",
  ACCEPTED: "text-green-600",
  REJECTED: "text-red-500",
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
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-gray-500">
        加载中…
      </main>
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / 20));

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">草稿审核</h1>
        <Link
          href="/admin/collect"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          ← 新建采集
        </Link>
      </div>

      <div className="mt-4 flex gap-3 text-sm">
        {["", "REVIEW", "DRAFT", "ACCEPTED", "REJECTED"].map((s) => (
          <button
            key={s}
            onClick={() => {
              setStatus(s);
              setPage(1);
            }}
            className={
              status === s
                ? "rounded-md bg-blue-600 px-3 py-1.5 text-white"
                : "rounded-md border border-gray-300 px-3 py-1.5 text-gray-700 hover:border-gray-400"
            }
          >
            {s ? STATUS_LABEL[s] : "全部"}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">职位</th>
                <th className="px-4 py-3 font-medium">公司</th>
                <th className="px-4 py-3 font-medium">城市/届别</th>
                <th className="px-4 py-3 font-medium">置信度</th>
                <th className="px-4 py-3 font-medium">来源</th>
                <th className="px-4 py-3 font-medium">状态</th>
                <th className="px-4 py-3 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => (
                <tr key={d.id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="max-w-44 truncate px-4 py-3 font-medium">
                    {d.title ?? "—"}
                  </td>
                  <td className="max-w-40 truncate px-4 py-3">{d.company ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {d.city ?? "—"} / {d.batch ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        d.confidence >= 0.6 ? "text-green-600" : "text-amber-600"
                      }
                    >
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{d.source_type}</td>
                  <td className={`px-4 py-3 ${STATUS_COLOR[d.status] ?? ""}`}>
                    {STATUS_LABEL[d.status] ?? d.status}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => onReview(d.id, "accept")}
                        className="rounded-md bg-blue-600 px-2.5 py-1 text-xs text-white hover:bg-blue-700"
                      >
                        通过
                      </button>
                      <button
                        onClick={() => onReview(d.id, "reject")}
                        className="rounded-md border border-gray-300 px-2.5 py-1 text-xs text-gray-700 hover:border-gray-400"
                      >
                        拒绝
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr className="border-t border-gray-100">
                  <td colSpan={7} className="px-4 py-10 text-center text-sm text-gray-400">
                    暂无草稿
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-center gap-4 border-t border-gray-100 py-3 text-sm text-gray-500">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            ‹ 上一页
          </button>
          <span>
            共 {total} 条 · 第 {page} / {totalPages} 页
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            下一页 ›
          </button>
        </div>
      </div>
    </main>
  );
}
