"""EmailLog model for tracking sent emails (Sprint 6 - Task 6.9)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.company import Company


class EmailLog(Base):
    """Track all sent emails with tokens for public PDF access."""
    
    __tablename__ = "email_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)
    email_type: Mapped[str] = mapped_column(String(32))  # invoice, estimate, payment
    entity_id: Mapped[int] = mapped_column(Integer)  # ID of invoice/estimate/payment
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    company: Mapped["Company | None"] = relationship("Company")
    
    @classmethod
    def validate_token(cls, token: str) -> bool:
        """Check if a token is valid and not expired."""
        # This is a static helper; actual validation happens in the API
        return bool(token and len(token) == 36)  # UUID length
