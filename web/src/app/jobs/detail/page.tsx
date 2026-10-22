"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, type JobOut } from "@/lib/api";

export default function JobDetailPage() {
  const [job, setJob] = useState<JobOut | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
      setError("缺少职位 ID（用法：/jobs/detail?id=1）");
      return;
    }
    api<JobOut>(`/api/v1/jobs/${id}`)
      .then(setJob)
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <p className="text-sm text-red-600">{error}</p>
        <Link href="/jobs" className="mt-4 inline-block text-sm text-blue-600">
          返回职位列表
        </Link>
      </main>
    );
  }
  if (!job) {
    return (
      <main className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-gray-500">
        加载中…
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <Link href="/jobs" className="text-sm text-blue-600 hover:text-blue-700">
        ← 返回职位列表
      </Link>
      <div className="mt-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold">{job.title}</h1>
        <p className="mt-2 text-gray-600">
          {job.company} ·{" "}
          <span className="font-medium text-rose-500">
            {job.salary_text ?? "面议"}
          </span>
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-gray-500">
          <span className="rounded bg-gray-100 px-2 py-1">{job.city}</span>
          <span className="rounded bg-gray-100 px-2 py-1">{job.batch}</span>
          {job.category && (
            <span className="rounded bg-gray-100 px-2 py-1">{job.category}</span>
          )}
        </div>
        <section className="mt-6 whitespace-pre-wrap border-t border-gray-100 pt-6 text-sm leading-6 text-gray-700">
          {job.description || "暂无职位描述"}
        </section>
        {job.source_url && (
          <a
            href={job.source_url}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-block text-sm text-blue-600 underline hover:text-blue-700"
          >
            查看原始来源
          </a>
        )}
      </div>
    </main>
  );
}
