"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  ArrowDown,
  ArrowUpRight,
  BriefcaseBusiness,
  Building2,
  LayoutList,
  LockKeyhole,
  MapPin,
  Search,
  Sparkles,
  Table2,
} from "lucide-react";

import {
  fetchDicts,
  fetchJobs,
  type DictSnapshot,
  type JobPage,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const dateLabel = (value?: string | null) =>
  (value ?? "").slice(0, 10) || "日期待补充";

export default function JobsPage() {
  const [snapshot, setSnapshot] = useState<DictSnapshot | null>(null);
  const [city, setCity] = useState("");
  const [batch, setBatch] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [data, setData] = useState<JobPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [view, setView] = useState<"list" | "table">("list");
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
    fetchDicts()
      .then((r) => {
        if (r.snapshot) setSnapshot(r.snapshot);
      })
      .catch(() => setSnapshot(null));
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    fetchJobs({
      city: city || undefined,
      batch: batch || undefined,
      keyword: keyword || undefined,
      page,
      page_size: pageSize,
    })
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [city, batch, keyword, page, pageSize]);

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

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasFilter = Boolean(city || batch || keyword);

  const selectCls =
    "h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

  return (
    <div className="member-workspace py-8 sm:py-12">
      {/* Hero */}
      <section className="mb-8 grid items-center gap-8 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 font-semibold text-blue-700">
              <Sparkles className="h-3.5 w-3.5" /> AI 求职伙伴
            </span>
            <span className="text-slate-500">校园招聘</span>
          </div>
          <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight text-slate-950 sm:text-5xl">
            下一站的机会，
            <br />
            <span className="text-blue-600">和 AI 一起发现。</span>
          </h1>
          <p className="mt-5 max-w-md text-sm leading-7 text-slate-500">
            从梳理求职方向，到发现合适岗位。
            <br className="hidden sm:block" />
            让求职派 Agent，陪你把下一步想清楚。
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              href="/login"
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-blue-600 px-5 text-sm font-medium text-white shadow-md shadow-blue-600/15 transition hover:bg-blue-700"
            >
              <Sparkles className="h-4 w-4" />
              {authed ? "进入个人中心" : "登录解锁全部"}{" "}
              <ArrowUpRight className="h-4 w-4" />
            </Link>
            <a
              href="#recruitment-search"
              className="inline-flex h-11 items-center gap-2 rounded-xl px-4 text-sm text-slate-600 transition hover:text-blue-600"
            >
              自己找机会 <ArrowDown className="h-4 w-4" />
            </a>
          </div>
        </div>
        {/* 装饰图形 */}
        <div
          aria-hidden="true"
          className="relative hidden h-64 lg:block"
        >
          <div className="absolute inset-0 rounded-3xl bg-[radial-gradient(circle_at_70%_30%,rgba(96,165,250,0.25),transparent_55%),radial-gradient(circle_at_25%_75%,rgba(167,139,250,0.18),transparent_50%)]" />
          <div
            className="absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)",
              backgroundSize: "32px 32px",
              maskImage:
                "radial-gradient(ellipse at center, black 30%, transparent 75%)",
              WebkitMaskImage:
                "radial-gradient(ellipse at center, black 30%, transparent 75%)",
            }}
          />
          <div className="absolute left-1/2 top-1/2 flex h-28 w-28 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-3xl border border-blue-100 bg-white/90 shadow-xl backdrop-blur">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
              <BriefcaseBusiness className="h-5 w-5" strokeWidth={1.6} />
            </span>
            <span className="mt-2 text-xs font-bold tracking-widest text-slate-700">
              JobClaw
            </span>
            <span className="text-[9px] tracking-widest text-slate-400">
              YOUR CAREER AGENT
            </span>
          </div>
          <div className="absolute left-8 top-10 flex items-center gap-2.5 rounded-2xl border border-slate-100 bg-white/90 px-4 py-3 shadow-md backdrop-blur">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <MapPin className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-semibold text-slate-800">先认识你</p>
              <p className="text-[11px] text-slate-400">梳理经历与偏好</p>
            </div>
          </div>
          <div className="absolute bottom-10 right-8 flex items-center gap-2.5 rounded-2xl border border-slate-100 bg-white/90 px-4 py-3 shadow-md backdrop-blur">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-500">
              <Building2 className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-semibold text-slate-800">再找机会</p>
              <p className="text-[11px] text-slate-400">探索适合的岗位</p>
            </div>
          </div>
        </div>
      </section>

      {/* 搜索表单 */}
      <form
        id="recruitment-search"
        onSubmit={onSearch}
        className="mb-7 scroll-mt-24 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5"
      >
        <div className="mb-4 flex items-center justify-between gap-3 text-xs">
          <span className="flex items-center gap-2 font-medium text-slate-600">
            <BriefcaseBusiness className="h-4 w-4 text-blue-500" />
            探索招聘机会
          </span>
          <span className="text-slate-400">
            {loading || error ? "—" : total} 条
            {hasFilter ? "匹配招聘" : "招聘信息"}
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1.6fr_1fr_1fr_auto]">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <input
              aria-label="关键词"
              className="h-10 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              placeholder="搜索职位 / 公司 / 描述"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
            />
          </div>
          <select
            aria-label="工作地点"
            className={selectCls}
            value={city}
            onChange={(e) => {
              setCity(e.target.value);
              setPage(1);
            }}
          >
            <option value="">全部城市</option>
            {enabledItems("CITY").map((i) => (
              <option key={i.id} value={i.item_key}>
                {i.item_value}
              </option>
            ))}
          </select>
          <select
            aria-label="招聘对象"
            className={selectCls}
            value={batch}
            onChange={(e) => {
              setBatch(e.target.value);
              setPage(1);
            }}
          >
            <option value="">全部届别</option>
            {enabledItems("BATCH").map((i) => (
              <option key={i.id} value={i.item_key}>
                {i.item_value}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-blue-600 px-7 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
          >
            <Search className="h-4 w-4" />
            查询机会
          </button>
        </div>
        <div className="mt-3 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onReset}
            className="inline-flex h-9 items-center rounded-md px-4 text-sm text-slate-500 transition hover:bg-slate-50 hover:text-slate-800"
          >
            重置
          </button>
        </div>
      </form>

      {/* 列表 / 表格切换 */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold text-slate-900">招聘机会</h2>
          <span className="text-xs text-slate-500">
            {loading ? "正在加载…" : `${total} 条结果`}
          </span>
        </div>
        <div className="flex gap-1 rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          <button
            type="button"
            aria-pressed={view === "list"}
            onClick={() => setView("list")}
            className={`inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition ${
              view === "list"
                ? "bg-slate-100 text-slate-900"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <LayoutList className="h-3.5 w-3.5" />
            列表
          </button>
          <button
            type="button"
            aria-pressed={view === "table"}
            onClick={() => setView("table")}
            className={`inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition ${
              view === "table"
                ? "bg-slate-100 text-slate-900"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <Table2 className="h-3.5 w-3.5" />
            表格
          </button>
        </div>
      </div>

      {/* 内容区 */}
      {error ? (
        <div role="alert" className="empty-panel">
          <p>{error}</p>
          <button
            type="button"
            onClick={load}
            className="mt-4 inline-flex h-10 items-center rounded-md bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-700"
          >
            重新加载
          </button>
        </div>
      ) : loading ? (
        <div aria-label="正在加载招聘信息" className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-2xl border border-slate-100 bg-white"
            />
          ))}
        </div>
      ) : !items.length ? (
        <div className="empty-panel">
          <Search className="mx-auto mb-3 h-8 w-8 text-slate-300" />
          <h3 className="font-medium text-slate-800">暂未找到匹配的招聘</h3>
          <p className="mt-2 text-sm">试着减少筛选条件，看看更多机会。</p>
          <button
            type="button"
            onClick={onReset}
            className="mt-5 inline-flex h-10 items-center rounded-md border border-slate-200 bg-white px-5 text-sm font-medium text-slate-700 shadow-sm hover:border-blue-300 hover:text-blue-600"
          >
            清除筛选
          </button>
        </div>
      ) : (
        <>
          {!authed && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
              <span className="flex items-center gap-2 text-sm text-blue-800">
                <LockKeyhole className="h-4 w-4" />
                登录并开通会员后，可查看完整招聘信息。
              </span>
              <Link
                href="/login"
                className="inline-flex h-8 items-center rounded-md bg-blue-600 px-3 text-xs font-medium text-white hover:bg-blue-700"
              >
                登录查看
              </Link>
            </div>
          )}

          {view === "list" ? (
            <div className="space-y-3">
              {items.map((job) => (
                <article
                  key={job.id}
                  className="group flex flex-col gap-5 rounded-2xl border border-slate-200/80 bg-white p-5 transition-colors hover:border-blue-200 sm:flex-row sm:p-6"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-slate-100 bg-slate-50 text-lg font-semibold text-slate-600">
                    {job.company?.slice(0, 1) || <Building2 />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-lg font-semibold text-slate-950">
                        <Link
                          href={`/jobs/detail?id=${job.id}`}
                          className="transition-colors hover:text-blue-600"
                        >
                          {job.company}
                        </Link>
                      </h3>
                      {job.category && (
                        <span className="soft-tag">{job.category}</span>
                      )}
                      <span className="soft-tag text-blue-700">
                        {job.batch || "招聘中"}
                      </span>
                    </div>
                    <p
                      className="mt-2.5 line-clamp-2 text-sm leading-6 text-slate-600"
                      title={job.title}
                    >
                      {job.title}
                      {job.salary_text ? ` · ${job.salary_text}` : ""}
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500">
                      <span className="inline-flex max-w-full items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 shrink-0" />
                        <span className="truncate">{job.city || "地点待补充"}</span>
                      </span>
                      <span>{job.batch || "招聘对象待补充"}</span>
                      <span>{dateLabel(job.published_at)} 更新</span>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center justify-between gap-4 sm:flex-col sm:items-end sm:justify-center">
                    <span className="text-xs text-slate-500">
                      {job.salary_text || "薪资面议"}
                    </span>
                    <Link
                      href={`/jobs/detail?id=${job.id}`}
                      className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600"
                    >
                      查看招聘 <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
              <table className="w-full min-w-[780px] text-left text-sm">
                <thead className="bg-slate-50 text-xs text-slate-500">
                  <tr>
                    {[
                      "公司 / 届别",
                      "岗位摘要",
                      "工作地点",
                      "薪资",
                      "更新时间",
                      "",
                    ].map((label, i) => (
                      <th key={i} className="px-5 py-4 font-medium">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((job) => (
                    <tr key={job.id} className="border-t border-slate-100">
                      <td className="px-5 py-4">
                        <p className="font-semibold">{job.company}</p>
                        <p className="mt-1 text-xs text-slate-500">{job.batch}</p>
                      </td>
                      <td className="max-w-xs px-5 py-4">
                        <p className="line-clamp-2 leading-6" title={job.title}>
                          {job.title}
                        </p>
                      </td>
                      <td className="max-w-40 px-5 py-4">
                        <p className="line-clamp-2">{job.city}</p>
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-slate-600">
                        {job.salary_text || "面议"}
                      </td>
                      <td className="whitespace-nowrap px-5 py-4 text-xs text-slate-500">
                        {dateLabel(job.published_at)}
                      </td>
                      <td className="px-5 py-4">
                        <Link
                          href={`/jobs/detail?id=${job.id}`}
                          className="whitespace-nowrap text-blue-600 hover:text-blue-700"
                        >
                          详情 ↗
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 分页 */}
          {total > 0 && (
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
              <span className="text-xs text-slate-500">
                共 {total} 条 · 第 {page} / {totalPages} 页
              </span>
              <div className="flex items-center gap-2">
                <select
                  aria-label="每页条数"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="h-9 rounded-md border border-slate-200 bg-white px-2 text-xs text-slate-600 shadow-sm focus:outline-none"
                >
                  {[10, 20, 50].map((s) => (
                    <option key={s} value={s}>
                      {s} 条/页
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="inline-flex h-9 items-center rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 shadow-sm transition hover:border-blue-300 hover:text-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  上一页
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="inline-flex h-9 items-center rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 shadow-sm transition hover:border-blue-300 hover:text-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
