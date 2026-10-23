"""Agent 相关 ORM 模型：IM 绑定 / 会话消息 / 用户画像 / 行为 / 调度任务 / 模型用量。

注意：MySQL 的 TEXT 列禁止 server_default（M0 教训）。
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...infra.db import Base


def _pk():
    return mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


def _fk_user(nullable: bool = False):
    return mapped_column(BigInteger().with_variant(Integer, "sqlite"), nullable=nullable)


class ImBinding(Base):
    """IM 用户 ↔ 系统用户 映射（消息网关层）。"""

    __tablename__ = "im_binding"
    __table_args__ = (UniqueConstraint("channel", "im_user_id", name="uq_im_binding"),)

    id: Mapped[int] = _pk()
    channel: Mapped[str] = mapped_column(String(16))  # wechat | feishu | dingtalk
    im_user_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[int] = _fk_user()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ChatMessage(Base):
    """对话消息落库（会话历史）。"""

    __tablename__ = "chat_message"
    __table_args__ = (Index("ix_chat_message_user", "user_id", "created_at"),)

    id: Mapped[int] = _pk()
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = _fk_user()
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text, default="")
    agent: Mapped[str] = mapped_column(String(32), default="")
    intent: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserProfile(Base):
    """用户画像：求职偏好（推荐 Agent 的召回依据）。"""

    __tablename__ = "user_profile"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = _fk_user()
    city: Mapped[str] = mapped_column(String(50), default="")
    batch: Mapped[str] = mapped_column(String(20), default="")
    category: Mapped[str] = mapped_column(String(50), default="")
    keywords: Mapped[str] = mapped_column(String(200), default="")  # 空格分隔
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserBehavior(Base):
    """用户行为记录：聊天 / 推荐 / 偏好更新等事件。"""

    __tablename__ = "user_behavior"
    __table_args__ = (Index("ix_user_behavior_user", "user_id", "created_at"),)

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = _fk_user()
    action: Mapped[str] = mapped_column(String(32))  # chat | recommend | profile_update | view
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScheduledTask(Base):
    """定时任务（任务调度 Agent）。"""

    __tablename__ = "scheduled_task"

    TASK_TYPES = ("collect_url", "expire_cleanup", "dedupe", "recommend_push")

    id: Mapped[int] = _pk()
    name: Mapped[str] = mapped_column(String(100))
    task_type: Mapped[str] = mapped_column(String(32))
    cron: Mapped[str] = mapped_column(String(32))  # 标准 5 段 crontab
    params: Mapped[str] = mapped_column(Text, default="")  # JSON
    enabled: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str] = mapped_column(String(16), default="")  # SUCCESS | FAILED
    last_message: Mapped[str] = mapped_column(String(500), default="")
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = _fk_user(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ModelUsage(Base):
    """模型调用用量统计（模型路由 Agent）。"""

    __tablename__ = "model_usage"

    id: Mapped[int] = _pk()
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(64))
    task_type: Mapped[str] = mapped_column(String(32))  # intent | chat | extract ...
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
