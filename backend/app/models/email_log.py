"""Email log model for tracking sent emails (Sprint 6 - Task 6.8).

This model stores email logs with expirable tokens for public PDF access.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class EmailLog(Base):
    """Model for tracking sent emails."""
    
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=False, index=True)  # invoice, estimate, payment
    entity_id = Column(Integer, nullable=False, index=True)
    token = Column(String(36), unique=True, index=True, nullable=True)  # UUID for public access
    token_expiry = Column(DateTime, nullable=True)
    status = Column(String(50), default="sent")  # sent, failed, pending
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships could be added here if needed
    # For now, we keep it simple with just entity_type and entity_id
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, recipient={self.recipient_email}, entity={self.entity_type}:{self.entity_id})>"
