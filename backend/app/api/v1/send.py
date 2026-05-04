"""Invoice send email endpoint (Sprint 6 - Task 6.8)."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.invoice import Invoice
from app.models.email_log import EmailLog
from app.models.finance import Estimate, Payment
from app.services.pdf_service import generate_pdf, render_html
from app.services.email_service import (
    send_email,
    generate_email_token,
    get_token_expiry,
    render_email_template,
    get_invoice_email_subject,
    get_estimate_email_subject,
    get_payment_email_subject,
    get_invoice_email_body,
)


router = APIRouter(tags=["send"])


@router.post("/invoices/{invoice_id}/send")
async def send_invoice_email(
    invoice_id: int,
    to: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    attach_pdf: bool = True,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Send invoice via email (Task 6.8).
    
    Args:
        invoice_id: Invoice ID
        to: Recipient email address
        subject: Email subject (optional, uses default if not provided)
        body: Email body (optional, uses default if not provided)
        attach_pdf: Whether to attach PDF (default True)
    """
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Generate PDF attachment
    pdf_bytes = None
    attachment_name = None
    if attach_pdf:
        template_name = f"{invoice.template_name or 'invoice1'}.html"
        from app.services.pdf_service import _get_invoice_context
        context = _get_invoice_context(invoice)
        pdf_bytes = generate_pdf(template_name, context)
        attachment_name = f"Invoice_{invoice.invoice_number}.pdf"
    
    # Get SMTP config from settings (would come from DB in production)
    smtp_config = {
        "mail_server": "smtp.example.com",
        "mail_port": 587,
        "mail_username": "user@example.com",
        "mail_password": "password",
        "mail_from": "noreply@example.com",
        "mail_from_name": company.name if company else "Company",
        "use_tls": True,
    }
    
    # Prepare email content
    if not subject:
        subject = get_invoice_email_subject(invoice.invoice_number)
    
    # Generate token for public access
    token = generate_email_token()
    token_expires = get_token_expiry(days=7)
    
    # Create public PDF link
    pdf_link = f"/api/v1/pdf/public/{token}"
    
    # Render email HTML
    customer_name = invoice.customer.name if invoice.customer else "Valued Customer"
    amount = (invoice.total or 0) / 100
    due_date = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else None
    
    email_html = render_email_template("invoice.html", {
        "invoice_number": invoice.invoice_number,
        "customer_name": customer_name,
        "amount": amount,
        "due_date": due_date,
        "company_name": company.name if company else "Company",
        "company_logo": company.logo if company else None,
        "company_address": company.address.street if company and company.address else "",
        "pdf_link": pdf_link,
    })
    
    # Send email
    try:
        await send_email(
            to=[to],
            subject=subject,
            body=email_html,
            html=True,
            attachments=[pdf_bytes] if pdf_bytes else None,
            attachment_names=[attachment_name] if attachment_name else None,
            smtp_config=smtp_config,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {str(e)}")
    
    # Log email
    email_log = EmailLog(
        recipient=to,
        subject=subject,
        body=email_html,
        token=token,
        token_expires_at=token_expires,
        email_type="invoice",
        entity_id=invoice.id,
        company_id=company.id,
    )
    db.add(email_log)
    
    # Mark invoice as sent
    invoice.sent = True
    
    await db.commit()
    
    return {"success": True, "message": "Email sent successfully", "token": token}


@router.get("/invoices/{invoice_id}/send/preview")
async def preview_invoice_email(
    invoice_id: int,
    to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Preview invoice email before sending (Task 6.8)."""
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    customer_name = invoice.customer.name if invoice.customer else "Valued Customer"
    amount = (invoice.total or 0) / 100
    due_date = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else None
    
    email_html = render_email_template("invoice.html", {
        "invoice_number": invoice.invoice_number,
        "customer_name": customer_name,
        "amount": amount,
        "due_date": due_date,
        "company_name": company.name if company else "Company",
        "company_logo": company.logo if company else None,
        "company_address": company.address.street if company and company.address else "",
        "pdf_link": "#",
    })
    
    return {
        "to": to or (invoice.customer.email if invoice.customer else ""),
        "subject": get_invoice_email_subject(invoice.invoice_number),
        "body": email_html,
    }


@router.post("/estimates/{estimate_id}/send")
async def send_estimate_email(
    estimate_id: int,
    to: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    attach_pdf: bool = True,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Send estimate via email."""
    estimate = await db.get(Estimate, estimate_id)
    if not estimate or estimate.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
    
    # Generate PDF
    pdf_bytes = None
    attachment_name = None
    if attach_pdf:
        template_name = f"{estimate.template_name or 'estimate1'}.html"
        from app.services.pdf_service import _get_estimate_context
        context = _get_estimate_context(estimate)
        pdf_bytes = generate_pdf(template_name, context)
        attachment_name = f"Estimate_{estimate.estimate_number}.pdf"
    
    smtp_config = {
        "mail_server": "smtp.example.com",
        "mail_port": 587,
        "mail_username": "user@example.com",
        "mail_password": "password",
        "mail_from": "noreply@example.com",
        "mail_from_name": company.name if company else "Company",
        "use_tls": True,
    }
    
    if not subject:
        subject = get_estimate_email_subject(estimate.estimate_number)
    
    token = generate_email_token()
    token_expires = get_token_expiry(days=7)
    pdf_link = f"/api/v1/pdf/public/{token}"
    
    customer_name = estimate.customer.name if estimate.customer else "Valued Customer"
    amount = (estimate.total or 0) / 100
    expiry_date = estimate.expiry_date.strftime("%Y-%m-%d") if estimate.expiry_date else None
    
    email_html = render_email_template("estimate.html", {
        "estimate_number": estimate.estimate_number,
        "customer_name": customer_name,
        "amount": amount,
        "expiry_date": expiry_date,
        "company_name": company.name if company else "Company",
        "company_logo": company.logo if company else None,
        "company_address": company.address.street if company and company.address else "",
        "pdf_link": pdf_link,
    })
    
    try:
        await send_email(
            to=[to],
            subject=subject,
            body=email_html,
            html=True,
            attachments=[pdf_bytes] if pdf_bytes else None,
            attachment_names=[attachment_name] if attachment_name else None,
            smtp_config=smtp_config,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {str(e)}")
    
    email_log = EmailLog(
        recipient=to,
        subject=subject,
        body=email_html,
        token=token,
        token_expires_at=token_expires,
        email_type="estimate",
        entity_id=estimate.id,
        company_id=company.id,
    )
    db.add(email_log)
    
    await db.commit()
    
    return {"success": True, "message": "Email sent successfully", "token": token}


@router.post("/payments/{payment_id}/send")
async def send_payment_email(
    payment_id: int,
    to: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    attach_pdf: bool = True,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Send payment receipt via email."""
    payment = await db.get(Payment, payment_id)
    if not payment or payment.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    pdf_bytes = None
    attachment_name = None
    if attach_pdf:
        template_name = "payment1.html"
        from app.services.pdf_service import _get_payment_context
        context = _get_payment_context(payment)
        pdf_bytes = generate_pdf(template_name, context)
        attachment_name = f"Payment_{payment.payment_number}.pdf"
    
    smtp_config = {
        "mail_server": "smtp.example.com",
        "mail_port": 587,
        "mail_username": "user@example.com",
        "mail_password": "password",
        "mail_from": "noreply@example.com",
        "mail_from_name": company.name if company else "Company",
        "use_tls": True,
    }
    
    if not subject:
        subject = get_payment_email_subject(payment.payment_number)
    
    token = generate_email_token()
    token_expires = get_token_expiry(days=7)
    pdf_link = f"/api/v1/pdf/public/{token}"
    
    customer_name = payment.customer.name if payment.customer else "Valued Customer"
    amount = (payment.amount or 0) / 100
    payment_date = payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else None
    invoice_number = payment.invoice.invoice_number if payment.invoice else None
    
    email_html = render_email_template("payment.html", {
        "payment_number": payment.payment_number,
        "customer_name": customer_name,
        "amount": amount,
        "payment_date": payment_date,
        "invoice_number": invoice_number,
        "payment_method": None,
        "company_name": company.name if company else "Company",
        "company_logo": company.logo if company else None,
        "company_address": company.address.street if company and company.address else "",
        "pdf_link": pdf_link,
    })
    
    try:
        await send_email(
            to=[to],
            subject=subject,
            body=email_html,
            html=True,
            attachments=[pdf_bytes] if pdf_bytes else None,
            attachment_names=[attachment_name] if attachment_name else None,
            smtp_config=smtp_config,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {str(e)}")
    
    email_log = EmailLog(
        recipient=to,
        subject=subject,
        body=email_html,
        token=token,
        token_expires_at=token_expires,
        email_type="payment",
        entity_id=payment.id,
        company_id=company.id,
    )
    db.add(email_log)
    
    await db.commit()
    
    return {"success": True, "message": "Email sent successfully", "token": token}
