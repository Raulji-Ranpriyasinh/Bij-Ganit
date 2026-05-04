"""CustomField + CustomFieldValue models (Sprint 5).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from app.models.company import Company


class CustomField(Base):
    __tablename__ = "custom_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    model_type: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(32))
    placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    options: Mapped[dict | None] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    values: Mapped[list["CustomFieldValue"]] = relationship("CustomFieldValue", back_populates="field", lazy="selectin")


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    custom_field_id: Mapped[int] = mapped_column(ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False)
    valuable_type: Mapped[str] = mapped_column(String(64))
    valuable_id: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(32))
    boolean_answer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    date_answer: Mapped[Date | None] = mapped_column(Date, nullable=True)
    time_answer: Mapped[str | None] = mapped_column(String(32), nullable=True)
    string_answer: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    number_answer: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    datetime_answer: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    field: Mapped["CustomField"] = relationship("CustomField", back_populates="values")
