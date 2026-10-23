from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...infra.db import Base


class JobDraft(Base):
    """采集到的职位草稿，经 AI 抽取后入库，人工审核通过后转为正式职位。"""

    __tablename__ = "job_draft"

    DRAFT = "DRAFT"
    REVIEW = "REVIEW"  # 低置信度，需人工审核
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    salary_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(16))  # text | html | excel | image
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        String(16), default=DRAFT, server_default=DRAFT, index=True
    )
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
