"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import {
  fetchDicts,
  fetchJobs,
  type DictSnapshot,
  type JobPage,
} from "@/lib/api";

const PAGE_SIZE = 10;

export default function JobsPage() {
  const [snapshot, setSnapshot] = useState<DictSnapshot | null>(null);
  const [city, setCity] = useState("");
  const [batch, setBatch] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<JobPage | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDicts()
      .then((r) => {
        if (r.snapshot) setSnapshot(r.snapshot);
      })
      .catch(() => setSnapshot(null));
  }, []);

  const load = useCallback(() => {
    setError("");
    fetchJobs({
      city: city || undefined,
      batch: batch || undefined,
      keyword: keyword || undefined,
      page,
      page_size: PAGE_SIZE,
    })
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [city, batch, keyword, page]);

  useEffect(() => {
    load();
  }, [load]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setKeyword(keywordInput.trim());
    setPage(1);
  }

  function onReset() {
    setCity("");
    setBatch("");
    setKeywordInput("");
    setKeyword("");
    setPage(1);
  }

  const enabledItems = (code: string) =>
    snapshot?.types
      .find((t) => t.type_code === code)
      ?.items.filter((i) => i.enabled) ?? [];

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const items = data?.items ?? [];

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-8">
      <h1 className="text-xl font-semibold">校招职位</h1>

      <form
        onSubmit={onSearch}
        className="mt-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="grid gap-1.5 text-sm">
            <span className="text-gray-600">工作地点</span>
            <select
              value={city}
              onChange={(e) => {
                setCity(e.target.value);
                setPage(1);
              }}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">全部城市</option>
              {enabledItems("CITY").map((i) => (
                <option key={i.id} value={i.item_key}>
                  {i.item_value}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-sm">
            <span className="text-gray-600">招聘对象</span>
            <select
              value={batch}
              onChange={(e) => {
                setBatch(e.target.value);
                setPage(1);
              }}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">全部届别</option>
              {enabledItems("BATCH").map((i) => (
                <option key={i.id} value={i.item_key}>
                  {i.item_value}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-sm">
            <span className="text-gray-600">岗位名称</span>
            <input
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              placeholder="搜索职位 / 公司 / 描述"
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </label>
          <div className="flex items-end gap-2">
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <SearchIcon />
              查询
            </button>
            <button
              type="button"
              onClick={onReset}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:border-gray-400"
            >
              重置
            </button>
          </div>
        </div>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">加载失败：{error}</p>}

      <div className="mt-4 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-center gap-2 border-b border-gray-100 py-3 text-sm text-gray-600">
          <UnlockIcon />
          <span>加入会员，即刻解锁全部招聘信息</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">岗位（大都不限专业）</th>
                <th className="px-4 py-3 font-medium">公司名称</th>
                <th className="px-4 py-3 font-medium">工作地点</th>
                <th className="px-4 py-3 font-medium">招聘对象</th>
                <th className="px-4 py-3 font-medium">所属类别</th>
                <th className="px-4 py-3 font-medium">薪资</th>
                <th className="px-4 py-3 font-medium">更新时间</th>
                <th className="px-4 py-3 font-medium">相关链接</th>
              </tr>
            </thead>
            <tbody>
              {items.map((job) => (
                <tr
                  key={job.id}
                  className="border-t border-gray-100 hover:bg-gray-50"
                >
                  <td className="max-w-56 truncate px-4 py-3">
                    <Link
                      href={`/jobs/detail?id=${job.id}`}
                      className="font-medium text-blue-600 hover:text-blue-700"
                    >
                      {job.title}
                    </Link>
                  </td>
                  <td className="max-w-44 truncate px-4 py-3 text-gray-700">
                    {job.company}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{job.city}</td>
                  <td className="px-4 py-3 text-gray-700">{job.batch}</td>
                  <td className="px-4 py-3 text-gray-700">
                    {job.category ?? "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-rose-500">
                    {job.salary_text ?? "面议"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                    {job.published_at.slice(0, 10)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <Link
                      href={`/jobs/detail?id=${job.id}`}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      查看详情
                    </Link>
                  </td>
                </tr>
              ))}
              {data && items.length === 0 && (
                <tr className="border-t border-gray-100">
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-sm text-gray-400"
                  >
                    暂无数据，请调整筛选条件后重试
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && (
          <div className="flex items-center justify-center gap-4 border-t border-gray-100 py-3 text-sm text-gray-500">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              ‹ 上一页
            </button>
            <span>
              共 {data.total} 条记录 · 第 {page} / {totalPages} 页
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              下一页 ›
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

function SearchIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function UnlockIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0 text-rose-500"
      aria-hidden="true"
    >
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 9.9-1" />
    </svg>
  );
}
