"""sprint 4: estimates, payments, expenses tables.

Revision ID: 0004_sprint4
Revises: 0003_sprint3
Create Date: 2026-05-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_sprint4"
down_revision: str | None = "0003_sprint3"
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
    # Estimates
    op.create_table(
        "estimates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estimate_number", sa.String(length=255), nullable=True),
        sa.Column("estimate_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sub_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("template_name", sa.String(length=128), nullable=True),
        sa.Column("unique_hash", sa.String(length=255), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamp_cols(),
    )

    # estimate_items (same structure as invoice_items)
    op.create_table(
        "estimate_items",
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
        sa.Column("estimate_id", sa.Integer(), sa.ForeignKey("estimates.id", ondelete="CASCADE"), nullable=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )

    # Payment methods
    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )

    # Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_number", sa.String(length=255), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("unique_hash", sa.String(length=255), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(), nullable=True),
        sa.Column("base_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamp_cols(),
    )

    # Expense categories
    op.create_table(
        "expense_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        *_timestamp_cols(),
    )

    # Expenses
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("expense_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(), nullable=True),
        sa.Column("base_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("currency_id", sa.Integer(), sa.ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expense_category_id", sa.Integer(), sa.ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True),
        *_timestamp_cols(),
    )


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("expense_categories")
    op.drop_table("payments")
    op.drop_table("payment_methods")
    op.drop_table("estimate_items")
    op.drop_table("estimates")
