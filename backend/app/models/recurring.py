"""RecurringInvoice and RecurringInvoiceItem models (Sprint 5).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
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


class RecurringInvoice(Base):
    __tablename__ = "recurring_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[Date | None] = mapped_column(Date, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    send_automatically: Mapped[bool] = mapped_column(Boolean, default=False)
    next_invoice_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    limit_by: Mapped[str | None] = mapped_column(String(16), nullable=True)
    limit_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    tax_per_item: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_per_item: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    discount: Mapped[int] = mapped_column(BigInteger, default=0)
    discount_val: Mapped[int] = mapped_column(BigInteger, default=0)
    sub_total: Mapped[int] = mapped_column(BigInteger, default=0)
    total: Mapped[int] = mapped_column(BigInteger, default=0)
    tax: Mapped[int] = mapped_column(BigInteger, default=0)
    due_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    template_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["RecurringInvoiceItem"]] = relationship("RecurringInvoiceItem", back_populates="recurring_invoice", lazy="selectin")


class RecurringInvoiceItem(Base):
    __tablename__ = "recurring_invoice_items"

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

    recurring_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("recurring_invoices.id", ondelete="CASCADE"), nullable=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    recurring_invoice: Mapped["RecurringInvoice | None"] = relationship("RecurringInvoice", back_populates="items")
