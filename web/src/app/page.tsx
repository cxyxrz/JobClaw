import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-16">
      <p className="text-sm font-medium text-blue-600">JobClaw · 求职派</p>
      <h1 className="mt-3 text-4xl font-bold">校招职位聚合与 AI 采集平台</h1>
      <p className="mt-4 max-w-2xl text-gray-600">
        用户看岗位，管理员管数据，AI 负责采集，支付和字典支撑运营。
        前端为 Next.js 静态站，后端为 FastAPI 模块化单体。
      </p>
      <div className="mt-8 flex flex-wrap gap-4 text-sm">
        <Link
          href="/jobs"
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          浏览职位
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:border-gray-400"
        >
          登录
        </Link>
        <Link
          href="/me"
          className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:border-gray-400"
        >
          个人中心
        </Link>
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:border-gray-400"
        >
          接口文档
        </a>
      </div>
      <p className="mt-10 text-sm text-gray-500">
        职位列表、采集任务、会员与字典页面将随 M1–M5 陆续上线。
      </p>
    </main>
  );
}
