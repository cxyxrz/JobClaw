"""从纯文本中抽取职位结构化字段（规则 + 正则，零外部依赖）。

优先识别带标签的行（公司：/ 地点：/ 薪资：等），再用正则兜底。
后续可扩展为 LLM 抽取（LitLLM），规则版作为兜底。
"""

import re
from dataclasses import dataclass

CITY_KEYWORDS = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安",
    "苏州", "重庆", "天津", "长沙", "青岛", "厦门", "合肥", "郑州", "福州",
    "济南", "大连", "宁波", "无锡", "东莞", "佛山", "珠海",
]

CATEGORY_KEYWORDS = {
    "技术": ["开发", "工程师", "算法", "前端", "后端", "客户端", "测试", "运维", "数据", "研发"],
    "产品": ["产品经理", "产品"],
    "设计": ["设计", "交互", "视觉", "UI", "UX"],
    "运营": ["运营", "增长", "内容", "用户运营"],
    "市场": ["市场", "品牌", "营销"],
}

SALARY_PATTERNS = [
    re.compile(r"(\d{1,3}[-~]\d{1,3}K(?:·\d{1,2}薪)?)", re.IGNORECASE),
    re.compile(r"(\d{1,3}万(?:[-~]\d{1,3}万)?(?:·\d{1,2}薪)?)"),
    re.compile(r"(面议)"),
]

BATCH_PATTERN = re.compile(r"(20\d{2}届|应届|在校生|实习)")

# 带标签的行
LABEL_PATTERNS = {
    "company": re.compile(r"(?:公司|单位|企业)[:：]\s*(.+)"),
    "city": re.compile(r"(?:工作地|地点|城市|工作城市)[:：]\s*(.+)"),
    "batch": re.compile(r"(?:招聘对象|届别|目标人群)[:：]\s*(.+)"),
    "salary": re.compile(r"(?:薪资|工资|待遇|薪酬)[:：]\s*(.+)"),
    "category": re.compile(r"(?:类别|岗位类型|职位类别)[:：]\s*(.+)"),
}

COMPANY_SUFFIX = re.compile(
    r"(.{2,40}?(?:科技|网络|信息|软件|互联网|股份|集团|有限|公司|银行|大学|实验室|研究院|工作室))"
)


@dataclass
class ExtractedJob:
    title: str | None
    company: str | None
    city: str | None
    batch: str | None
    category: str | None
    salary_text: str | None
    description: str
    confidence: float


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _match_labels(lines: list[str]) -> dict:
    found: dict = {}
    for ln in lines:
        for key, pat in LABEL_PATTERNS.items():
            if key in found:
                continue
            m = pat.search(ln)
            if m:
                found[key] = m.group(1).strip()
    return found


def _pick_city(text: str, lines: list[str], labeled: dict) -> str | None:
    if labeled.get("city"):
        for c in CITY_KEYWORDS:
            if c in labeled["city"]:
                return c
        return labeled["city"][:10]
    for city in CITY_KEYWORDS:
        if city in text:
            return city
    return None


def _pick_category(text: str, labeled: dict) -> str | None:
    if labeled.get("category"):
        return labeled["category"][:20]
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cat
    return None


def _pick_salary(text: str, labeled: dict) -> str | None:
    if labeled.get("salary"):
        return labeled["salary"][:30]
    for pat in SALARY_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def _pick_batch(text: str, labeled: dict) -> str | None:
    if labeled.get("batch"):
        m = BATCH_PATTERN.search(labeled["batch"])
        if m:
            return m.group(1)
        return labeled["batch"][:10]
    m = BATCH_PATTERN.search(text)
    return m.group(1) if m else None


def _pick_company(lines: list[str], labeled: dict, text: str) -> str | None:
    if labeled.get("company"):
        return labeled["company"][:40]
    # 后缀正则
    m = COMPANY_SUFFIX.search(text)
    if m:
        return m.group(1).strip()
    # 启发式：标题行之后的第一行短文本且不含地点/薪资/届别关键词
    if len(lines) >= 2:
        candidate = lines[1]
        if (
            2 <= len(candidate) <= 30
            and not any(k in candidate for k in ("地点", "薪资", "届别", "工作地", "招聘对象", "描述", "职责", "要求"))
        ):
            return candidate
    return None


def _pick_title(lines: list[str]) -> str | None:
    for ln in lines:
        # 跳过明显的标签行
        if 2 <= len(ln) <= 60 and "：" not in ln and ":" not in ln:
            return ln
    return lines[0][:60] if lines else None


def extract_fields(text: str) -> ExtractedJob:
    """从文本中抽取职位字段并计算置信度。"""
    lines = _lines(text)
    labeled = _match_labels(lines)

    city = _pick_city(text, lines, labeled)
    category = _pick_category(text, labeled)
    salary = _pick_salary(text, labeled)
    batch = _pick_batch(text, labeled)
    company = _pick_company(lines, labeled, text)
    title = _pick_title(lines)

    # 置信度：核心字段（title/company/city）权重 2，可选字段权重 1
    core = [title, company, city]
    optional = [category, salary, batch]
    score = (sum(1 for v in core if v) * 2 + sum(1 for v in optional if v)) / (
        len(core) * 2 + len(optional)
    )

    return ExtractedJob(
        title=title,
        company=company,
        city=city,
        batch=batch,
        category=category,
        salary_text=salary,
        description=text,
        confidence=round(score, 3),
    )
