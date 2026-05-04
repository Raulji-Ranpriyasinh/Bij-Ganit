"""sprint 5: dashboard helpers, recurring_invoices, recurring_items, custom_fields.

Revision ID: 0005_sprint5
Revises: 0004_sprint4_estimates_payments_expenses
Create Date: 2026-05-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_sprint5"
down_revision: str | None = "0004_sprint4_estimates_payments_expenses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp_cols() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    # recurring_invoices
    op.create_table(
        "recurring_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("starts_at", sa.Date(), nullable=True),
        sa.Column("frequency", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("send_automatically", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("next_invoice_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("limit_by", sa.String(length=16), nullable=True),
        sa.Column("limit_count", sa.Integer(), nullable=True),
        sa.Column("limit_date", sa.Date(), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(), nullable=True),
        sa.Column("tax_per_item", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discount_per_item", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discount_type", sa.String(length=32), nullable=True),
        sa.Column("discount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("discount_val", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sub_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("due_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("template_name", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamp_cols(),
    )

    # recurring_invoice_items
    op.create_table(
        "recurring_invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("price", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("discount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("discount_val", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("unit_name", sa.String(length=128), nullable=True),
        sa.Column("base_price", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_discount_val", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("exchange_rate", sa.Numeric(), nullable=True),
        sa.Column("recurring_invoice_id", sa.Integer(), sa.ForeignKey("recurring_invoices.id", ondelete="CASCADE"), nullable=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )

    # custom_fields
    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("placeholder", sa.String(length=255), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )

    # custom_field_values
    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("custom_field_id", sa.Integer(), sa.ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("valuable_type", sa.String(length=64), nullable=False),
        sa.Column("valuable_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("boolean_answer", sa.Boolean(), nullable=True),
        sa.Column("date_answer", sa.Date(), nullable=True),
        sa.Column("time_answer", sa.Time(), nullable=True),
        sa.Column("string_answer", sa.String(length=1024), nullable=True),
        sa.Column("number_answer", sa.Numeric(), nullable=True),
        sa.Column("datetime_answer", sa.DateTime(timezone=True), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )


def downgrade() -> None:
    op.drop_table("custom_field_values")
    op.drop_table("custom_fields")
    op.drop_table("recurring_invoice_items")
    op.drop_table("recurring_invoices")
