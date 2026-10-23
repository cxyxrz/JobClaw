"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import {
  submitCollect,
  submitCollectFile,
  type CollectResult,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

type SourceType = "text" | "html" | "excel" | "image";

export default function CollectPage() {
  const [authed, setAuthed] = useState(false);
  const [sourceType, setSourceType] = useState<SourceType>("text");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CollectResult | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setAuthed(true);
  }, [router]);

  if (!authed) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-gray-500">
        加载中…
      </main>
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      let res: CollectResult;
      if (sourceType === "excel" || sourceType === "image") {
        if (!file) {
          setError("请选择文件");
          setLoading(false);
          return;
        }
        res = await submitCollectFile(sourceType, file);
      } else {
        if (!content.trim()) {
          setError("请输入文本内容或 URL");
          setLoading(false);
          return;
        }
        res = await submitCollect(sourceType, content);
      }
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "采集失败");
    } finally {
      setLoading(false);
    }
  }

  const statusColor: Record<string, string> = {
    DRAFT: "text-blue-600",
    REVIEW: "text-amber-600",
    ACCEPTED: "text-green-600",
    REJECTED: "text-red-500",
    DUPLICATE: "text-gray-500",
    ERROR: "text-red-500",
  };
  const statusLabel: Record<string, string> = {
    DRAFT: "已入库（草稿）",
    REVIEW: "需人工审核",
    ACCEPTED: "已通过",
    REJECTED: "已拒绝",
    DUPLICATE: "重复，跳过",
    ERROR: "采集失败",
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">采集任务</h1>
        <Link
          href="/admin/drafts"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          查看草稿 →
        </Link>
      </div>

      <form
        onSubmit={onSubmit}
        className="mt-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
      >
        <label className="grid gap-1.5 text-sm">
          <span className="text-gray-600">来源类型</span>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as SourceType)}
            className="w-48 rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          >
            <option value="text">文本直读</option>
            <option value="html">网页 URL</option>
            <option value="excel">Excel 文件</option>
            <option value="image">图片（需 paddleocr）</option>
          </select>
        </label>

        {(sourceType === "text" || sourceType === "html") && (
          <label className="mt-4 grid gap-1.5 text-sm">
            <span className="text-gray-600">
              {sourceType === "html" ? "网页 URL" : "职位文本"}
            </span>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              placeholder={
                sourceType === "html"
                  ? "https://example.com/job-posting"
                  : "后端开发工程师（Python）\n字节跳动\n工作地点：北京\n招聘对象：2026届\n薪资：25-40K·16薪\n..."
              }
              className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </label>
        )}

        {(sourceType === "excel" || sourceType === "image") && (
          <label className="mt-4 grid gap-1.5 text-sm">
            <span className="text-gray-600">选择文件</span>
            <input
              type="file"
              accept={sourceType === "excel" ? ".xlsx,.xls" : "image/*"}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
        )}

        <div className="mt-4 flex items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "采集中…" : "开始采集"}
          </button>
          {error && <span className="text-sm text-red-600">{error}</span>}
        </div>
      </form>

      {result && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="font-medium">采集结果</h2>
          <dl className="mt-3 grid max-w-md gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">状态</dt>
              <dd className={statusColor[result.status] ?? "text-gray-700"}>
                {statusLabel[result.status] ?? result.status}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">置信度</dt>
              <dd>{(result.confidence * 100).toFixed(1)}%</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">职位</dt>
              <dd>{result.title ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">公司</dt>
              <dd>{result.company ?? "—"}</dd>
            </div>
            {result.draft_id && (
              <div className="flex justify-between">
                <dt className="text-gray-500">草稿 ID</dt>
                <dd>{result.draft_id}</dd>
              </div>
            )}
            {result.message && (
              <div className="flex justify-between">
                <dt className="text-gray-500">说明</dt>
                <dd className="text-gray-600">{result.message}</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </main>
  );
}
