"""Email service using FastAPI-Mail (Sprint 6 - Task 6.7).

This service handles sending emails with PDF attachments for invoices,
estimates, and payments. Supports SMTP, Mailgun, SES, and Sendmail drivers.
"""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from enum import Enum

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.database import get_db
from app.models.email_log import EmailLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class EmailDriver(str, Enum):
    """Supported email drivers."""
    SMTP = "smtp"
    MAILGUN = "mailgun"
    SES = "ses"
    SENDMAIL = "sendmail"


# Email templates directory
EMAIL_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


def get_jinja_env() -> Environment:
    """Create and configure Jinja2 environment for email templates."""
    return Environment(
        loader=FileSystemLoader(EMAIL_TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_email_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 email template with the given context.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice_email.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML string
    """
    env = get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


def create_connection_config(
    driver: str,
    mail_from: str,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_tls: bool = True,
    mailgun_api_key: Optional[str] = None,
    mailgun_domain: Optional[str] = None,
    ses_access_key: Optional[str] = None,
    ses_secret_key: Optional[str] = None,
    ses_region: Optional[str] = None,
) -> ConnectionConfig:
    """Create FastAPI-Mail connection configuration based on driver.
    
    Args:
        driver: Email driver (smtp, mailgun, ses, sendmail)
        mail_from: From email address
        smtp_host: SMTP server host (for SMTP driver)
        smtp_port: SMTP server port (for SMTP driver)
        smtp_user: SMTP username (for SMTP driver)
        smtp_password: SMTP password (for SMTP driver)
        smtp_tls: Use TLS for SMTP (default True)
        mailgun_api_key: Mailgun API key (for Mailgun driver)
        mailgun_domain: Mailgun domain (for Mailgun driver)
        ses_access_key: AWS SES access key (for SES driver)
        ses_secret_key: AWS SES secret key (for SES driver)
        ses_region: AWS SES region (for SES driver)
        
    Returns:
        Configured ConnectionConfig instance
    """
    if driver == EmailDriver.SMTP:
        return ConnectionConfig(
            MAIL_FROM=mail_from,
            MAIL_SERVER=smtp_host or "smtp.gmail.com",
            MAIL_PORT=smtp_port or 587,
            MAIL_USERNAME=smtp_user,
            MAIL_PASSWORD=smtp_password,
            MAIL_STARTTLS=smtp_tls,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    elif driver == EmailDriver.MAILGUN:
        # FastAPI-Mail doesn't have built-in Mailgun support
        # We'll use SMTP interface for Mailgun
        return ConnectionConfig(
            MAIL_FROM=mail_from,
            MAIL_SERVER="smtp.mailgun.org",
            MAIL_PORT=587,
            MAIL_USERNAME=f"postmaster@{mailgun_domain}",
            MAIL_PASSWORD=mailgun_api_key,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    elif driver == EmailDriver.SES:
        # FastAPI-Mail doesn't have built-in SES support
        # We'll use SMTP interface for SES
        return ConnectionConfig(
            MAIL_FROM=mail_from,
            MAIL_SERVER=f"email-smtp.{ses_region or 'us-east-1'}.amazonaws.com",
            MAIL_PORT=587,
            MAIL_USERNAME=ses_access_key,
            MAIL_PASSWORD=ses_secret_key,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    elif driver == EmailDriver.SENDMAIL:
        return ConnectionConfig(
            MAIL_FROM=mail_from,
            MAIL_SERVER="localhost",
            MAIL_PORT=25,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=False,
            VALIDATE_CERTS=False,
        )
    else:
        raise ValueError(f"Unsupported email driver: {driver}")


async def send_email(
    to: list[str] | str,
    subject: str,
    body: str,
    driver: str = "smtp",
    mail_from: str = "noreply@example.com",
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    attachments: Optional[list[bytes]] = None,
    attachment_names: Optional[list[str]] = None,
    db: Optional[AsyncSession] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
) -> dict[str, Any]:
    """Send an email with optional attachments.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        body: Email body (HTML)
        driver: Email driver to use
        mail_from: From email address
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        attachments: List of attachment bytes
        attachment_names: List of attachment filenames
        db: Database session for logging
        entity_type: Type of entity (invoice, estimate, payment)
        entity_id: ID of the entity
        
    Returns:
        Dict with status and email log info
    """
    # Create connection config
    config = create_connection_config(
        driver=driver,
        mail_from=mail_from,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
    )
    
    # Prepare recipients
    recipients = [to] if isinstance(to, str) else to
    
    # Prepare attachments
    attachment_files = []
    if attachments and attachment_names:
        for att_bytes, att_name in zip(attachments, attachment_names):
            attachment_files.append({
                "file": att_bytes,
                "name": att_name,
            })
    
    # Create message schema
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html,
        attachments=attachment_files if attachment_files else None,
    )
    
    # Send email
    fm = FastMail(config)
    await fm.send_message(message)
    
    # Generate token for public PDF access
    token = str(uuid.uuid4())
    token_expiry = datetime.utcnow() + timedelta(days=7)  # 7 days expiry
    
    # Log email if database session provided
    email_log_data = None
    if db and entity_type and entity_id:
        email_log = EmailLog(
            recipient_email=recipients[0],
            subject=subject,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            token=token,
            token_expiry=token_expiry,
            status="sent",
        )
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)
        email_log_data = {
            "id": email_log.id,
            "token": token,
            "token_expiry": token_expiry.isoformat(),
        }
    
    return {
        "status": "sent",
        "recipients": recipients,
        "subject": subject,
        "email_log": email_log_data,
    }


async def generate_email_token(
    entity_type: str,
    entity_id: int,
    db: AsyncSession,
    expiry_days: int = 7,
) -> str:
    """Generate a unique token for public PDF access.
    
    Args:
        entity_type: Type of entity (invoice, estimate, payment)
        entity_id: ID of the entity
        db: Database session
        expiry_days: Number of days until token expires
        
    Returns:
        Generated token string
    """
    token = str(uuid.uuid4())
    token_expiry = datetime.utcnow() + timedelta(days=expiry_days)
    
    email_log = EmailLog(
        recipient_email="",  # No specific recipient for token-only generation
        subject="",
        body="",
        entity_type=entity_type,
        entity_id=entity_id,
        token=token,
        token_expiry=token_expiry,
        status="pending",
    )
    db.add(email_log)
    await db.commit()
    await db.refresh(email_log)
    
    return token


async def validate_email_token(token: str, db: AsyncSession) -> Optional[EmailLog]:
    """Validate an email token and check expiry.
    
    Args:
        token: Token to validate
        db: Database session
        
    Returns:
        EmailLog if valid and not expired, None otherwise
    """
    result = await db.execute(
        select(EmailLog).where(EmailLog.token == token)
    )
    email_log = result.scalar_one_or_none()
    
    if not email_log:
        return None
    
    if email_log.token_expiry < datetime.utcnow():
        return None  # Token expired
    
    return email_log


def get_invoice_email_subject(invoice_number: str, company_name: str) -> str:
    """Generate default invoice email subject."""
    return f"Invoice {invoice_number} from {company_name}"


def get_invoice_email_body(context: dict[str, Any]) -> str:
    """Generate default invoice email body."""
    return render_email_template("invoice_email.html", context)


def get_estimate_email_subject(estimate_number: str, company_name: str) -> str:
    """Generate default estimate email subject."""
    return f"Estimate {estimate_number} from {company_name}"


def get_estimate_email_body(context: dict[str, Any]) -> str:
    """Generate default estimate email body."""
    return render_email_template("estimate_email.html", context)


def get_payment_email_body(context: dict[str, Any]) -> str:
    """Generate default payment email body."""
    return render_email_template("payment_email.html", context)
