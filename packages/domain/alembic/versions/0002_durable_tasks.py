"""Durable tasks, sessions, revisions, and submission attempts

Revision ID: 0002_durable_tasks
Revises: 99975bc45c5d
Create Date: 2026-08-30 06:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_durable_tasks"
down_revision: str | Sequence[str] | None = "99975bc45c5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. retailer_tasks
    op.create_table(
        "retailer_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="QUEUED"),
        sa.Column("lease_token", sa.String(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["comparison_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retailer_tasks_run_id", "retailer_tasks", ["run_id"])
    op.create_index("ix_retailer_tasks_retailer_id", "retailer_tasks", ["retailer_id"])
    op.create_index("ix_retailer_tasks_status", "retailer_tasks", ["status"])
    op.create_index("ix_retailer_tasks_lease_token", "retailer_tasks", ["lease_token"])
    op.create_index("ix_retailer_tasks_lease_expires_at", "retailer_tasks", ["lease_expires_at"])

    # 2. retailer_sessions
    op.create_table(
        "retailer_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("retailer_id", sa.String(), nullable=False),
        sa.Column("is_authenticated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("user_name", sa.String(), nullable=True),
        sa.Column("requires_action", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("action_type", sa.String(), nullable=True),
        sa.Column("resume_token", sa.String(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retailer_id"),
    )
    op.create_index("ix_retailer_sessions_retailer_id", "retailer_sessions", ["retailer_id"])

    # 3. quote_revisions
    op.create_table(
        "quote_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quote_id", sa.Uuid(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cart_fingerprint", sa.String(), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("gross_total_cents", sa.Integer(), nullable=False),
        sa.Column("selected_delivery_slot_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["store_quotes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_revisions_quote_id", "quote_revisions", ["quote_id"])
    op.create_index("ix_quote_revisions_cart_fingerprint", "quote_revisions", ["cart_fingerprint"])

    # 4. submission_attempts
    op.create_table(
        "submission_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("approval_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("retailer_response", sa.String(), nullable=True),
        sa.Column("error_detail", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approval_id"], ["approvals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submission_attempts_approval_id", "submission_attempts", ["approval_id"])
    op.create_index("ix_submission_attempts_idempotency_key", "submission_attempts", ["idempotency_key"])
    op.create_index("ix_submission_attempts_status", "submission_attempts", ["status"])


def downgrade() -> None:
    op.drop_table("submission_attempts")
    op.drop_table("quote_revisions")
    op.drop_table("retailer_sessions")
    op.drop_table("retailer_tasks")
