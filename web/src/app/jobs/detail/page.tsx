"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  Building2,
  CalendarDays,
  Link2,
  MapPin,
  Users,
} from "lucide-react";

import { fetchJobById, type JobOut } from "@/lib/api";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<JobOut | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobById(Number(params.id))
      .then(setJob)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="member-workspace py-10">
        <div className="h-64 animate-pulse rounded-2xl border border-slate-100 bg-white" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="member-workspace py-10">
        <div className="empty-panel">
          <h2 className="font-medium text-slate-800">
            {error || "职位不存在或已下线"}
          </h2>
          <Link
            href="/jobs"
            className="mt-5 inline-flex h-10 items-center gap-1.5 rounded-md bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-700"
          >
            <ArrowLeft className="h-4 w-4" /> 返回职位列表
          </Link>
        </div>
      </div>
    );
  }

  const dateLabel = (value?: string | null) =>
    (value ?? "").slice(0, 10) || "待补充";

  return (
    <div className="member-workspace py-8">
      <Link
        href="/jobs"
        className="mb-5 inline-flex items-center gap-1.5 text-sm text-slate-500 transition hover:text-blue-600"
      >
        <ArrowLeft className="h-4 w-4" />
        返回职位列表
      </Link>

      <div className="grid gap-6 lg:grid-cols-[1.7fr_1fr]">
        {/* 左侧：职位描述 */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                    <Building2 className="h-5 w-5" strokeWidth={1.7} />
                  </span>
                  <h1 className="truncate text-2xl font-bold text-slate-950">
                    {job.company}
                  </h1>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {job.category && (
                    <span className="soft-tag">{job.category}</span>
                  )}
                  {job.batch && (
                    <span className="soft-tag text-blue-700">{job.batch}</span>
                  )}
                </div>
              </div>
              {job.source_url && (
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hidden h-9 shrink-0 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-4 text-xs font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600 sm:inline-flex"
                >
                  <Link2 className="h-3.5 w-3.5" />
                  原始链接
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
            <div className="mt-6 border-t border-slate-100 pt-6">
              <h2 className="mb-3 text-sm font-semibold text-slate-900">
                岗位描述
              </h2>
              <p className="whitespace-pre-wrap text-sm leading-7 text-slate-600">
                {job.description || job.title}
              </p>
            </div>
          </div>
        </div>

        {/* 右侧：信息侧栏 */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6">
            <h2 className="mb-5 text-sm font-semibold text-slate-900">
              岗位信息
            </h2>
            <dl className="space-y-4 text-sm">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-slate-400">
                  <MapPin className="h-4 w-4" />
                </span>
                <div className="flex-1">
                  <dt className="text-xs text-slate-400">工作地点</dt>
                  <dd className="mt-0.5 text-slate-800">{job.city || "待补充"}</dd>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-slate-400">
                  <Users className="h-4 w-4" />
                </span>
                <div className="flex-1">
                  <dt className="text-xs text-slate-400">招聘对象</dt>
                  <dd className="mt-0.5 text-slate-800">{job.batch || "待补充"}</dd>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-slate-400">
                  <CalendarDays className="h-4 w-4" />
                </span>
                <div className="flex-1">
                  <dt className="text-xs text-slate-400">发布时间</dt>
                  <dd className="mt-0.5 text-slate-800">
                    {dateLabel(job.published_at)}
                  </dd>
                </div>
              </div>
            </dl>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-6">
            <h2 className="mb-2 text-sm font-semibold text-slate-900">
              薪资参考
            </h2>
            <p className="text-xl font-bold text-blue-600">
              {job.salary_text || "面议"}
            </p>
            <p className="mt-2 text-xs text-slate-400">
              薪资信息来源于公开渠道，实际以面试沟通为准
            </p>
          </div>

          <button
            type="button"
            onClick={() => router.push("/jobs")}
            className="w-full rounded-xl border border-slate-200 bg-white py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600"
          >
            查看更多相似机会
          </button>
        </div>
      </div>
    </div>
  );
}
