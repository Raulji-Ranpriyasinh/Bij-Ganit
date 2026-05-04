"""Estimates, Payments, Expenses models (Sprint 4).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.currency import Currency


class Estimate(Base):
    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(primary_key=True)
    estimate_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimate_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sub_total: Mapped[int] = mapped_column(BigInteger, default=0)
    total: Mapped[int] = mapped_column(BigInteger, default=0)
    tax: Mapped[int] = mapped_column(BigInteger, default=0)

    template_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    unique_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, default=0)

    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["EstimateItem"]] = relationship("EstimateItem", back_populates="estimate", lazy="selectin")
    customer: Mapped["Customer | None"] = relationship("Customer", lazy="selectin")
    company: Mapped["Company | None"] = relationship("Company", lazy="selectin")


class EstimateItem(Base):
    __tablename__ = "estimate_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    price: Mapped[int] = mapped_column(BigInteger, default=0)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    discount: Mapped[int] = mapped_column(BigInteger, default=0)
    discount_val: Mapped[int] = mapped_column(BigInteger, default=0)
    tax: Mapped[int] = mapped_column(BigInteger, default=0)
    total: Mapped[int] = mapped_column(BigInteger, default=0)

    unit_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    base_price: Mapped[int] = mapped_column(BigInteger, default=0)
    base_discount_val: Mapped[int] = mapped_column(BigInteger, default=0)
    base_tax: Mapped[int] = mapped_column(BigInteger, default=0)
    base_total: Mapped[int] = mapped_column(BigInteger, default=0)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    estimate_id: Mapped[int | None] = mapped_column(ForeignKey("estimates.id", ondelete="CASCADE"), nullable=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    estimate: Mapped["Estimate | None"] = relationship("Estimate", back_populates="items")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    unique_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    base_amount: Mapped[int] = mapped_column(BigInteger, default=0)

    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    invoice: Mapped["Invoice | None"] = relationship("Invoice", lazy="selectin")


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    base_amount: Mapped[int] = mapped_column(BigInteger, default=0)

    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True)
    expense_category_id: Mapped[int | None] = mapped_column(ForeignKey("expense_categories.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
