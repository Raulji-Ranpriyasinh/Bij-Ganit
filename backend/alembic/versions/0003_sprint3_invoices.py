"""sprint 3 invoices: invoices + invoice_items tables.

Revision ID: 0003_sprint3
Revises: 0002_sprint2
Create Date: 2026-05-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_sprint3"
down_revision: str | None = "0002_sprint2"
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
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(length=255), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("reference_number", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("paid_status", sa.String(length=32), nullable=False, server_default="UNPAID"),
        sa.Column("tax_per_item", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discount_per_item", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=32), nullable=True),
        sa.Column("discount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("discount_val", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sub_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("due_amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("viewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("overdue", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("template_name", sa.String(length=128), nullable=True),
        sa.Column("unique_hash", sa.String(length=255), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_sequence_number", sa.Integer(), nullable=True),
        sa.Column("exchange_rate", sa.Numeric(), nullable=True),
        sa.Column("base_sub_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_total", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_tax", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("base_discount_val", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "currency_id",
            sa.Integer(),
            sa.ForeignKey("currencies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "creator_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recurring_invoice_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("sales_tax_type", sa.String(length=64), nullable=True),
        sa.Column("sales_tax_address_type", sa.String(length=64), nullable=True),
        *_timestamp_cols(),
    )

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("discount_type", sa.String(length=32), nullable=True),
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
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "recurring_invoice_id",
            sa.Integer(),
            nullable=True,
        ),
        *_timestamp_cols(),
    )


def downgrade() -> None:
    op.drop_table("invoice_items")
    op.drop_table("invoices")
