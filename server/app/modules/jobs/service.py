from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Job

SAMPLE_JOBS: list[dict] = [
    {
        "title": "后端开发工程师（Python）",
        "company": "字节跳动",
        "city": "北京",
        "batch": "2026届",
        "category": "技术",
        "salary_text": "25-40K·16薪",
        "description": "负责服务端业务系统设计与开发，参与高并发架构演进。要求熟悉 Python/Go，掌握 MySQL、Redis 等常用中间件。",
    },
    {
        "title": "算法工程师（推荐方向）",
        "company": "腾讯",
        "city": "深圳",
        "batch": "2026届",
        "category": "技术",
        "salary_text": "30-50K·16薪",
        "description": "参与推荐系统模型迭代与特征体系建设，要求扎实的机器学习基础与工程落地能力。",
    },
    {
        "title": "前端开发工程师",
        "company": "阿里巴巴",
        "city": "杭州",
        "batch": "2026届",
        "category": "技术",
        "salary_text": "22-38K·16薪",
        "description": "负责电商核心链路前端研发，熟悉 React/TypeScript，有性能优化经验者优先。",
    },
    {
        "title": "产品经理（校园社区）",
        "company": "美团",
        "city": "北京",
        "batch": "2027届",
        "category": "产品",
        "salary_text": "18-28K·15薪",
        "description": "负责校园社区产品规划与迭代，输出 PRD 并推动跨团队落地。",
    },
    {
        "title": "交互设计师",
        "company": "网易",
        "city": "杭州",
        "batch": "2027届",
        "category": "设计",
        "salary_text": "16-26K·14薪",
        "description": "负责游戏社区产品交互设计，输出高质量原型与设计规范。",
    },
    {
        "title": "运营管培生",
        "company": "拼多多",
        "city": "上海",
        "batch": "2026届",
        "category": "运营",
        "salary_text": "15-25K·16薪",
        "description": "轮岗培养，参与活动策划、用户增长与商家运营。",
    },
    {
        "title": "数据分析师",
        "company": "京东",
        "city": "北京",
        "batch": "2026届",
        "category": "技术",
        "salary_text": "20-32K·15薪",
        "description": "负责零售业务数据指标体系建设与专题分析，熟练使用 SQL。",
    },
    {
        "title": "客户端开发工程师（iOS）",
        "company": "小红书",
        "city": "上海",
        "batch": "2026届",
        "category": "技术",
        "salary_text": "25-40K·16薪",
        "description": "参与社区 App iOS 端功能研发与体验优化，熟悉 Swift/UIKit。",
    },
    {
        "title": "测试开发工程师",
        "company": "华为",
        "city": "深圳",
        "batch": "2027届",
        "category": "技术",
        "salary_text": "18-30K·14薪",
        "description": "负责自动化测试平台建设与质量保障体系落地。",
    },
    {
        "title": "用户增长产品经理",
        "company": "哔哩哔哩",
        "city": "上海",
        "batch": "2026届",
        "category": "产品",
        "salary_text": "18-30K·15薪",
        "description": "负责新用户转化链路优化，通过实验驱动增长。",
    },
    {
        "title": "视觉设计师",
        "company": "米哈游",
        "city": "上海",
        "batch": "2027届",
        "category": "设计",
        "salary_text": "17-28K·14薪",
        "description": "参与游戏宣发物料与活动视觉设计。",
    },
    {
        "title": "内容运营",
        "company": "快手",
        "city": "北京",
        "batch": "2027届",
        "category": "运营",
        "salary_text": "14-22K·15薪",
        "description": "负责垂类内容生态运营与创作者维护。",
    },
]


async def query_jobs(
    session: AsyncSession,
    *,
    city: str | None = None,
    batch: str | None = None,
    keyword: str | None = None,
    status: str = "PUBLISHED",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Job], int]:
    stmt = select(Job).where(Job.status == status)
    if city:
        stmt = stmt.where(Job.city == city)
    if batch:
        stmt = stmt.where(Job.batch == batch)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Job.title.like(like), Job.company.like(like), Job.description.like(like))
        )
    total = (
        await session.scalars(select(func.count()).select_from(stmt.subquery()))
    ).one()
    stmt = (
        stmt.order_by(Job.published_at.desc(), Job.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await session.scalars(stmt)).all())
    return items, total


async def ensure_seed_jobs(session: AsyncSession) -> int:
    existing = (await session.scalars(select(func.count()).select_from(Job))).one()
    if existing:
        return 0
    now = datetime.now(timezone.utc)
    for row in SAMPLE_JOBS:
        session.add(Job(**row, published_at=now))
    return len(SAMPLE_JOBS)
