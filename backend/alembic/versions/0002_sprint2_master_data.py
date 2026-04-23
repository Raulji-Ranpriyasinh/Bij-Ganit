"""sprint 2 master data: currencies, countries, addresses, customers, units,
items, tax_types, taxes (and seed data for currencies + countries).

Revision ID: 0002_sprint2
Revises: 0001_initial
Create Date: 2026-04-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.seed_data.countries import COUNTRIES
from app.seed_data.currencies import CURRENCIES

revision: str = "0002_sprint2"
down_revision: str | None = "0001_initial"
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
    # --- lookup tables -------------------------------------------------------
    currencies = op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=True),
        sa.Column("precision", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "thousand_separator", sa.String(length=4), nullable=False, server_default=","
        ),
        sa.Column(
            "decimal_separator", sa.String(length=4), nullable=False, server_default="."
        ),
        sa.Column(
            "swap_currency_symbol",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    countries = op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phonecode", sa.Integer(), nullable=False, server_default="0"),
    )

    # --- domain tables -------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column(
            "enable_portal", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "currency_id",
            sa.Integer(),
            sa.ForeignKey("currencies.id", ondelete="SET NULL"),
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
        *_timestamp_cols(),
    )

    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("address_street_1", sa.String(length=255), nullable=True),
        sa.Column("address_street_2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=255), nullable=True),
        sa.Column("zip", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("fax", sa.String(length=64), nullable=True),
        sa.Column("type", sa.String(length=16), nullable=True),
        sa.Column(
            "country_id",
            sa.Integer(),
            sa.ForeignKey("countries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        *_timestamp_cols(),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        *_timestamp_cols(),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("price", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "tax_per_item", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "unit_id",
            sa.Integer(),
            sa.ForeignKey("units.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "currency_id",
            sa.Integer(),
            sa.ForeignKey("currencies.id", ondelete="SET NULL"),
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
        *_timestamp_cols(),
    )

    op.create_table(
        "tax_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column(
            "compound_tax", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "collective_tax", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("type", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        *_timestamp_cols(),
    )

    op.create_table(
        "taxes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column(
            "compound_tax", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "tax_type_id",
            sa.Integer(),
            sa.ForeignKey("tax_types.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # invoice/estimate FKs are added in a later sprint when those tables
        # exist.  Keep the columns here now so the polymorphic contract is
        # stable and the model can already use them.
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("estimate_id", sa.Integer(), nullable=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        *_timestamp_cols(),
    )

    # --- seed static lookup data --------------------------------------------
    if CURRENCIES:
        op.bulk_insert(currencies, CURRENCIES)
    if COUNTRIES:
        op.bulk_insert(countries, COUNTRIES)


def downgrade() -> None:
    op.drop_table("taxes")
    op.drop_table("tax_types")
    op.drop_table("items")
    op.drop_table("units")
    op.drop_table("addresses")
    op.drop_table("customers")
    op.drop_table("countries")
    op.drop_table("currencies")
