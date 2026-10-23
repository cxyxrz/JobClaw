import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  FileSearch,
  LayoutGrid,
  Sparkles,
} from "lucide-react";

const FEATURES = [
  {
    icon: Bot,
    title: "AI 采集 Agent",
    desc: "文本、网页、Excel、图片四类来源自动解析，字段抽取、去重一步到位。",
    tag: "已上线",
  },
  {
    icon: BriefcaseBusiness,
    title: "校招职位聚合",
    desc: "城市、届别、关键词多维筛选，最新校园招聘信息一站浏览。",
    tag: "已上线",
  },
  {
    icon: FileSearch,
    title: "草稿人工审核",
    desc: "低置信度草稿自动标记，管理员审核通过后一键转为正式职位。",
    tag: "已上线",
  },
  {
    icon: LayoutGrid,
    title: "异步任务与会员",
    desc: "任务池进度推送、微信支付与 VIP 解锁即将到来。",
    tag: "规划中",
  },
];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="member-workspace pt-16 sm:pt-24">
        <div className="grid items-center gap-12 lg:grid-cols-[1.3fr_1fr]">
          <div>
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 font-semibold text-blue-700">
                <Sparkles className="h-3.5 w-3.5" /> AI 求职伙伴
              </span>
              <span className="text-slate-500">校招职位聚合与 AI 采集平台</span>
            </div>
            <h1 className="mt-6 text-4xl font-semibold leading-[1.15] tracking-tight text-slate-950 sm:text-6xl">
              下一站的机会，
              <br />
              <span className="text-blue-600">和 AI 一起发现。</span>
            </h1>
            <p className="mt-6 max-w-lg text-base leading-8 text-slate-500">
              用户看岗位，管理员管数据，AI 负责采集。
              <br className="hidden sm:block" />
              求职派把校园招聘信息收集、整理、审核的每一步都变得简单。
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link
                href="/jobs"
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-blue-600 px-6 text-sm font-medium text-white shadow-md shadow-blue-600/15 transition hover:bg-blue-700"
              >
                浏览校招职位
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex h-11 items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 text-sm font-medium text-slate-700 shadow-sm transition hover:border-blue-300 hover:text-blue-600"
              >
                登录 / 注册
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>
            <dl className="mt-12 grid max-w-md grid-cols-3 gap-6 text-sm">
              {[
                ["4 类", "采集来源"],
                ["1 步", "草稿转正"],
                ["0 门槛", "浏览职位"],
              ].map(([value, label]) => (
                <div key={label}>
                  <dt className="text-2xl font-bold text-slate-950">{value}</dt>
                  <dd className="mt-1 text-xs text-slate-400">{label}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* 装饰图形 */}
          <div aria-hidden="true" className="relative hidden h-80 lg:block">
            <div className="absolute inset-0 rounded-[2rem] bg-[radial-gradient(circle_at_70%_30%,rgba(96,165,250,0.25),transparent_55%),radial-gradient(circle_at_25%_75%,rgba(167,139,250,0.18),transparent_50%)]" />
            <div
              className="absolute inset-0 opacity-40"
              style={{
                backgroundImage:
                  "linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)",
                backgroundSize: "36px 36px",
                maskImage:
                  "radial-gradient(ellipse at center, black 30%, transparent 75%)",
                WebkitMaskImage:
                  "radial-gradient(ellipse at center, black 30%, transparent 75%)",
              }}
            />
            <div className="absolute left-1/2 top-1/2 flex h-32 w-32 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-3xl border border-blue-100 bg-white/90 shadow-xl backdrop-blur">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-white">
                <Bot className="h-6 w-6" strokeWidth={1.5} />
              </span>
              <span className="mt-2.5 text-sm font-bold tracking-widest text-slate-700">
                JobClaw
              </span>
              <span className="mt-0.5 text-[9px] tracking-widest text-slate-400">
                YOUR CAREER AGENT
              </span>
            </div>
            <div className="absolute left-6 top-8 flex items-center gap-2.5 rounded-2xl border border-slate-100 bg-white/90 px-4 py-3 shadow-md backdrop-blur">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <FileSearch className="h-4 w-4" />
              </span>
              <div>
                <p className="text-xs font-semibold text-slate-800">先认识你</p>
                <p className="text-[11px] text-slate-400">梳理经历与偏好</p>
              </div>
            </div>
            <div className="absolute bottom-8 right-6 flex items-center gap-2.5 rounded-2xl border border-slate-100 bg-white/90 px-4 py-3 shadow-md backdrop-blur">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-500">
                <BriefcaseBusiness className="h-4 w-4" />
              </span>
              <div>
                <p className="text-xs font-semibold text-slate-800">再找机会</p>
                <p className="text-[11px] text-slate-400">探索适合的岗位</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 功能矩阵 */}
      <section className="member-workspace py-16 sm:py-24">
        <div className="flex items-end justify-between">
          <div>
            <div className="eyebrow">
              <Sparkles className="h-3.5 w-3.5 text-blue-500" />
              PLATFORM
            </div>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              一个平台，覆盖采集到发布全链路
            </h2>
          </div>
          <Link
            href="/jobs"
            className="hidden items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 sm:inline-flex"
          >
            查看全部职位 <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, desc, tag }) => (
            <section
              key={title}
              className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:border-blue-200 hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </span>
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                    tag === "已上线"
                      ? "bg-green-50 text-green-600"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {tag}
                </span>
              </div>
              <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{desc}</p>
            </section>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="member-workspace pb-20">
        <div className="relative overflow-hidden rounded-3xl bg-blue-600 px-8 py-14 text-center shadow-lg shadow-blue-600/20 sm:px-12">
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-15"
            style={{
              backgroundImage:
                "radial-gradient(circle at 20% 30%, white 1px, transparent 1px), radial-gradient(circle at 80% 70%, white 1px, transparent 1px)",
              backgroundSize: "64px 64px",
            }}
          />
          <h2 className="relative text-2xl font-bold text-white sm:text-3xl">
            准备好开始你的校招之旅了吗？
          </h2>
          <p className="relative mx-auto mt-3 max-w-md text-sm leading-7 text-blue-100">
            现在登录，即刻解锁完整招聘信息与 AI 采集能力。
          </p>
          <div className="relative mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/login"
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-white px-6 text-sm font-semibold text-blue-700 shadow-sm transition hover:bg-blue-50"
            >
              立即登录 <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/jobs"
              className="inline-flex h-11 items-center gap-2 rounded-xl border border-white/40 px-6 text-sm font-medium text-white transition hover:bg-white/10"
            >
              先逛逛职位
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
