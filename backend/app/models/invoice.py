"""Invoice + InvoiceItem models (Sprint 3).
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
    from app.models.customer import Customer
    from app.models.currency import Currency


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    paid_status: Mapped[str] = mapped_column(String(32), default="UNPAID")
    tax_per_item: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_per_item: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    discount: Mapped[int] = mapped_column(BigInteger, default=0)
    discount_val: Mapped[int] = mapped_column(BigInteger, default=0)
    sub_total: Mapped[int] = mapped_column(BigInteger, default=0)
    total: Mapped[int] = mapped_column(BigInteger, default=0)
    tax: Mapped[int] = mapped_column(BigInteger, default=0)
    due_amount: Mapped[int] = mapped_column(BigInteger, default=0)

    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    viewed: Mapped[bool] = mapped_column(Boolean, default=False)
    overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    template_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    unique_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sequence_number: Mapped[int] = mapped_column(Integer, default=0)
    customer_sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    base_sub_total: Mapped[int] = mapped_column(BigInteger, default=0)
    base_total: Mapped[int] = mapped_column(BigInteger, default=0)
    base_tax: Mapped[int] = mapped_column(BigInteger, default=0)
    base_discount_val: Mapped[int] = mapped_column(BigInteger, default=0)

    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recurring_invoice_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", lazy="selectin")
    taxes: Mapped[list["Tax"]] = relationship("Tax", primaryjoin="Invoice.id==foreign(app.models.tax.Tax.invoice_id)", lazy="selectin")
    customer: Mapped["Customer | None"] = relationship("Customer", lazy="selectin")
    currency: Mapped["Currency | None"] = relationship("Currency", lazy="selectin")
    company: Mapped["Company | None"] = relationship("Company", lazy="selectin")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    discount_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

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

    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    recurring_invoice_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    invoice: Mapped["Invoice | None"] = relationship("Invoice", back_populates="items")
