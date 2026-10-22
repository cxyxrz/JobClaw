"""job and dict tables

Revision ID: 0002_jobs_dicts
Revises: 0001_initial
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_jobs_dicts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _pk_column():
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        nullable=False,
    )


def _timestamps():
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "job",
        _pk_column(),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=50), nullable=False),
        sa.Column("batch", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("salary_text", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="PUBLISHED", nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_city", "job", ["city"])
    op.create_index("ix_job_batch", "job", ["batch"])
    op.create_index("ix_job_status", "job", ["status"])
    op.create_index("ix_job_query", "job", ["status", "city", "batch", "published_at"])

    op.create_table(
        "dict_type",
        _pk_column(),
        sa.Column("type_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type_code"),
    )
    op.create_index("ix_dict_type_type_code", "dict_type", ["type_code"])

    op.create_table(
        "dict_item",
        _pk_column(),
        sa.Column("type_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("item_key", sa.String(length=100), nullable=False),
        sa.Column("item_value", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["type_id"], ["dict_type.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("type_id", "item_key", name="uq_dict_item_type_key"),
    )
    op.create_index("ix_dict_item_type_id", "dict_item", ["type_id"])


def downgrade() -> None:
    op.drop_index("ix_dict_item_type_id", table_name="dict_item")
    op.drop_table("dict_item")
    op.drop_index("ix_dict_type_type_code", table_name="dict_type")
    op.drop_table("dict_type")
    op.drop_index("ix_job_query", table_name="job")
    op.drop_index("ix_job_status", table_name="job")
    op.drop_index("ix_job_batch", table_name="job")
    op.drop_index("ix_job_city", table_name="job")
    op.drop_table("job")
