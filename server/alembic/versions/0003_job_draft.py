"""job_draft table for collected drafts

Revision ID: 0003_job_draft
Revises: 0002_jobs_dicts
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_job_draft"
down_revision = "0002_jobs_dicts"
branch_labels = None
depends_on = None


def _pk_column():
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "job_draft",
        _pk_column(),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("city", sa.String(length=50), nullable=True),
        sa.Column("batch", sa.String(length=20), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("salary_text", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="DRAFT",
            nullable=False,
        ),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=True),
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
    )
    op.create_index("ix_job_draft_status", "job_draft", ["status"])
    op.create_index("ix_job_draft_source_type", "job_draft", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_job_draft_source_type", table_name="job_draft")
    op.drop_index("ix_job_draft_status", table_name="job_draft")
    op.drop_table("job_draft")
