"""Email service using FastAPI-Mail (Sprint 6 - Task 6.7).

This service handles sending emails via SMTP, Mailgun, SES, or Sendmail.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, FileSystemLoader


class EmailDriver(str, Enum):
    SMTP = "smtp"
    MAILGUN = "mailgun"
    SES = "ses"
    SENDMAIL = "sendmail"


EMAIL_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


def _get_jinja_env() -> Environment:
    """Create Jinja2 environment pointing to email templates directory."""
    return Environment(
        loader=FileSystemLoader(EMAIL_TEMPLATE_DIR),
        autoescape=False,
    )


def render_email_template(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 email template with the given context.
    
    Args:
        template_name: Name of the template file (e.g., 'invoice.html')
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML string
    """
    env = _get_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)


async def send_email(
    to: list[str],
    subject: str,
    body: str,
    html: bool = True,
    attachments: list[bytes] | None = None,
    attachment_names: list[str] | None = None,
    smtp_config: dict | None = None,
) -> bool:
    """Send an email using the configured SMTP settings.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body (HTML or plain text)
        html: Whether the body is HTML (default True)
        attachments: List of attachment bytes
        attachment_names: List of attachment filenames
        smtp_config: SMTP configuration dict with keys:
            - mail_server: SMTP server hostname
            - mail_port: SMTP port
            - mail_username: SMTP username
            - mail_password: SMTP password
            - mail_from: Sender email address
            - mail_from_name: Sender name
            - use_tls: Use TLS (default True)
            - use_ssl: Use SSL (default False)
            
    Returns:
        True if email was sent successfully
        
    Raises:
        Exception: If email sending fails
    """
    if not smtp_config:
        raise ValueError("SMTP configuration is required")
    
    conf = ConnectionConfig(
        MAIL_SERVER=smtp_config.get("mail_server", "localhost"),
        MAIL_PORT=smtp_config.get("mail_port", 587),
        MAIL_USERNAME=smtp_config.get("mail_username"),
        MAIL_PASSWORD=smtp_config.get("mail_password"),
        MAIL_FROM=smtp_config.get("mail_from", "noreply@example.com"),
        MAIL_FROM_NAME=smtp_config.get("mail_from_name", "Application"),
        MAIL_STARTTLS=smtp_config.get("use_tls", True),
        MAIL_SSL_TLS=smtp_config.get("use_ssl", False),
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    
    # Prepare attachments
    attachment_files = []
    if attachments and attachment_names:
        for att_bytes, att_name in zip(attachments, attachment_names):
            attachment_files.append({
                "file": att_bytes,
                "filename": att_name,
            })
    
    message = MessageSchema(
        subject=subject,
        recipients=to,
        body=body,
        subtype=MessageType.html if html else MessageType.plain,
        attachments=attachment_files if attachment_files else None,
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    return True


def generate_email_token() -> str:
    """Generate a unique UUID token for email tracking.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_token_expiry(days: int = 7) -> datetime:
    """Calculate token expiry datetime.
    
    Args:
        days: Number of days until expiry (default 7)
        
    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(days=days)


# Email template content helpers
def get_invoice_email_subject(invoice_number: str) -> str:
    """Get default email subject for invoice."""
    return f"Invoice {invoice_number} from Your Company"


def get_estimate_email_subject(estimate_number: str) -> str:
    """Get default email subject for estimate."""
    return f"Estimate {estimate_number} from Your Company"


def get_payment_email_subject(payment_number: str) -> str:
    """Get default email subject for payment receipt."""
    return f"Payment Receipt {payment_number}"


def get_invoice_email_body(invoice_number: str, amount: float, due_date: str | None = None) -> str:
    """Get default email body for invoice."""
    body = f"""Dear Valued Customer,

Thank you for your business. Please find attached invoice {invoice_number} for the amount of ${amount:.2f}.

"""
    if due_date:
        body += f"Payment is due by {due_date}.\n\n"
    
    body += """If you have any questions regarding this invoice, please don't hesitate to contact us.

Best regards,
Your Company Team"""
    return body
