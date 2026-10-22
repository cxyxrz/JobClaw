"""initial user table

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("union_id", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=16), server_default="USER", nullable=False),
        sa.Column("vip_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("vip_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("union_id"),
    )
    op.create_index("ix_user_username", "user", ["username"])


def downgrade() -> None:
    op.drop_index("ix_user_username", table_name="user")
    op.drop_table("user")
