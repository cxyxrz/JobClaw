"""agent tables: im_binding / chat_message / user_profile / user_behavior / scheduled_task / model_usage

Revision ID: 0004_agent_tables
Revises: 0003_job_draft
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_agent_tables"
down_revision = "0003_job_draft"
branch_labels = None
depends_on = None


def _pk_column():
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        nullable=False,
    )


def _user_fk(nullable=False):
    return sa.Column(
        "user_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=nullable
    )


def _dt_column(name):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    # IM 绑定（渠道用户 ↔ 系统用户）
    op.create_table(
        "im_binding",
        _pk_column(),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("im_user_id", sa.String(length=64), nullable=False),
        _user_fk(),
        _dt_column("created_at"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "im_user_id", name="uq_im_binding"),
    )

    # 会话消息
    op.create_table(
        "chat_message",
        _pk_column(),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        _user_fk(),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("agent", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("intent", sa.String(length=32), nullable=False, server_default=""),
        _dt_column("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_message_session_id", "chat_message", ["session_id"])
    op.create_index("ix_chat_message_user", "chat_message", ["user_id", "created_at"])

    # 用户画像
    op.create_table(
        "user_profile",
        _pk_column(),
        _user_fk(),
        sa.Column("city", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("batch", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("keywords", sa.String(length=200), nullable=False, server_default=""),
        _dt_column("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_profile_user_id", "user_profile", ["user_id"], unique=True)

    # 用户行为
    op.create_table(
        "user_behavior",
        _pk_column(),
        _user_fk(),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        _dt_column("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_behavior_user", "user_behavior", ["user_id", "created_at"])

    # 定时任务
    op.create_table(
        "scheduled_task",
        _pk_column(),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("cron", sa.String(length=32), nullable=False),
        sa.Column("params", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("last_message", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=True),
        _dt_column("created_at"),
        _dt_column("updated_at"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 模型用量
    op.create_table(
        "model_usage",
        _pk_column(),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        _dt_column("created_at"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_usage")
    op.drop_table("scheduled_task")
    op.drop_index("ix_user_behavior_user", table_name="user_behavior")
    op.drop_table("user_behavior")
    op.drop_index("ix_user_profile_user_id", table_name="user_profile")
    op.drop_table("user_profile")
    op.drop_index("ix_chat_message_user", table_name="chat_message")
    op.drop_index("ix_chat_message_session_id", table_name="chat_message")
    op.drop_table("chat_message")
    op.drop_table("im_binding")
