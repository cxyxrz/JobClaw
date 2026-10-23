"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import {
  Bot,
  CheckCircle2,
  FileSpreadsheet,
  Globe,
  ImageIcon,
  Send,
  Type,
} from "lucide-react";

import {
  submitCollect,
  submitCollectFile,
  type CollectResult,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

type SourceType = "text" | "html" | "excel" | "image";

const SOURCE_OPTIONS: Array<{
  value: SourceType;
  label: string;
  icon: typeof Type;
  hint: string;
}> = [
  { value: "text", label: "文本直读", icon: Type, hint: "粘贴职位文本" },
  { value: "html", label: "网页采集", icon: Globe, hint: "输入招聘页 URL" },
  { value: "excel", label: "Excel 导入", icon: FileSpreadsheet, hint: "上传 .xlsx" },
  { value: "image", label: "图片采集", icon: ImageIcon, hint: "需启用 OCR" },
];

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
      <div className="p-6 sm:p-8">
        <div className="h-40 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
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

  const statusStyle: Record<string, string> = {
    DRAFT: "bg-green-50 text-green-600",
    REVIEW: "bg-amber-50 text-amber-600",
    ACCEPTED: "bg-blue-50 text-blue-600",
    REJECTED: "bg-red-50 text-red-500",
    DUPLICATE: "bg-slate-100 text-slate-500",
    ERROR: "bg-red-50 text-red-500",
  };
  const statusLabel: Record<string, string> = {
    DRAFT: "已入库（草稿）",
    REVIEW: "需人工审核",
    ACCEPTED: "已通过",
    REJECTED: "已拒绝",
    DUPLICATE: "重复，已跳过",
    ERROR: "采集失败",
  };

  const inputCls =
    "w-full rounded-md border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

  return (
    <div className="p-6 sm:p-8">
      <div className="mb-6">
        <div className="eyebrow">
          <Bot className="h-3.5 w-3.5 text-blue-500" />
          COLLECT WORKBENCH
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
          新建采集
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          提交来源后，AI 将自动完成解析、字段抽取、校验与去重入库。
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm"
        >
          {/* 来源类型选择 */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {SOURCE_OPTIONS.map(({ value, label, icon: Icon, hint }) => {
              const active = sourceType === value;
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => {
                    setSourceType(value);
                    setResult(null);
                    setError("");
                  }}
                  aria-pressed={active}
                  className={`flex flex-col items-center gap-2 rounded-xl border px-3 py-4 text-center transition ${
                    active
                      ? "border-blue-300 bg-blue-50 text-blue-700 shadow-sm"
                      : "border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:text-slate-800"
                  }`}
                >
                  <Icon className="h-5 w-5" strokeWidth={1.7} />
                  <span className="text-xs font-semibold">{label}</span>
                  <span className="text-[10px] text-slate-400">{hint}</span>
                </button>
              );
            })}
          </div>

          {(sourceType === "text" || sourceType === "html") && (
            <label className="mt-6 grid gap-1.5 text-sm">
              <span className="font-medium text-slate-600">
                {sourceType === "html" ? "网页 URL" : "职位文本"}
              </span>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={sourceType === "text" ? 8 : 2}
                placeholder={
                  sourceType === "html"
                    ? "https://example.com/campus/job-posting"
                    : "后端开发工程师（Python）\n字节跳动\n工作地点：北京\n招聘对象：2026届\n薪资：25-40K·16薪\n…"
                }
                className={inputCls}
              />
            </label>
          )}

          {(sourceType === "excel" || sourceType === "image") && (
            <label className="mt-6 grid gap-1.5 text-sm">
              <span className="font-medium text-slate-600">选择文件</span>
              <input
                type="file"
                accept={sourceType === "excel" ? ".xlsx,.xls" : "image/*"}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="h-11 w-full rounded-md border border-dashed border-slate-300 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-600 file:mr-4 file:cursor-pointer file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-blue-700 hover:border-blue-300"
              />
            </label>
          )}

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-red-100 bg-red-50 px-3.5 py-2.5 text-xs text-red-600"
            >
              {error}
            </p>
          )}

          <div className="mt-6 flex items-center gap-4">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-blue-600 px-6 text-sm font-semibold text-white shadow-md shadow-blue-600/15 transition hover:bg-blue-700 disabled:opacity-60"
            >
              <Send className="h-4 w-4" />
              {loading ? "采集中…" : "开始采集"}
            </button>
            <Link
              href="/admin/drafts"
              className="text-sm text-slate-500 transition hover:text-blue-600"
            >
              前往草稿审核 →
            </Link>
          </div>
        </form>

        {/* 结果面板 */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">采集结果</h2>
          {!result ? (
            <div className="mt-8 flex flex-col items-center py-10 text-center">
              <Bot className="h-9 w-9 text-slate-200" strokeWidth={1.3} />
              <p className="mt-3 text-sm text-slate-400">
                提交来源后，结果将在此展示
              </p>
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1.5 text-xs font-semibold ${
                    statusStyle[result.status] ?? "bg-slate-100 text-slate-600"
                  }`}
                >
                  <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
                  {statusLabel[result.status] ?? result.status}
                </span>
                <span className="text-2xl font-bold text-slate-950">
                  {(result.confidence * 100).toFixed(0)}
                  <span className="text-sm font-medium text-slate-400">%</span>
                </span>
              </div>
              <dl className="space-y-3 border-t border-slate-100 pt-4 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="shrink-0 text-slate-400">职位</dt>
                  <dd className="truncate text-right font-medium text-slate-800">
                    {result.title ?? "—"}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="shrink-0 text-slate-400">公司</dt>
                  <dd className="truncate text-right font-medium text-slate-800">
                    {result.company ?? "—"}
                  </dd>
                </div>
                {result.draft_id && (
                  <div className="flex justify-between gap-4">
                    <dt className="shrink-0 text-slate-400">草稿 ID</dt>
                    <dd className="text-slate-800">#{result.draft_id}</dd>
                  </div>
                )}
                {result.message && (
                  <div className="rounded-lg bg-slate-50 px-3 py-2.5 text-xs leading-5 text-slate-500">
                    {result.message}
                  </div>
                )}
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
