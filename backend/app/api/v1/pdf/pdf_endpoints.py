"""PDF API endpoints for invoices, estimates, and payments (Sprint 6 - Task 6.5, 6.9)."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.invoice import Invoice
from app.models.finance import Estimate, Payment
from app.models.email_log import EmailLog
from app.services.pdf_service import generate_pdf, render_html, get_available_templates


router = APIRouter(prefix="/pdf", tags=["pdf"])


def _get_invoice_context(invoice: Invoice) -> dict:
    """Build context dictionary for invoice PDF templates."""
    company = invoice.company
    customer = invoice.customer
    
    return {
        "invoice": invoice,
        "company": company,
        "customer": customer,
        "items": invoice.items,
    }


def _get_estimate_context(estimate: Estimate) -> dict:
    """Build context dictionary for estimate PDF templates."""
    company = estimate.company
    customer = estimate.customer
    
    return {
        "estimate": estimate,
        "company": company,
        "customer": customer,
        "items": estimate.items,
    }


def _get_payment_context(payment: Payment) -> dict:
    """Build context dictionary for payment PDF templates."""
    company = payment.company
    customer = payment.customer
    payment_method = None  # Would need to load from relationship
    
    return {
        "payment": payment,
        "company": company,
        "customer": customer,
        "payment_method": payment_method,
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice_pdf(
    invoice_id: int,
    preview: bool = Query(default=False),
    template: str = Query(default="invoice1"),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Generate PDF for an invoice.
    
    Args:
        invoice_id: Invoice ID
        preview: If True, return HTML instead of PDF
        template: Template name to use (default: invoice1)
    """
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    template_name = f"{template}.html"
    context = _get_invoice_context(invoice)
    
    if preview:
        # Return rendered HTML for preview
        html_content = render_html(template_name, context)
        return Response(content=html_content, media_type="text/html")
    
    # Generate PDF
    pdf_bytes = generate_pdf(template_name, context)
    
    filename = f"Invoice_{invoice.invoice_number}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/estimates/{estimate_id}")
async def get_estimate_pdf(
    estimate_id: int,
    preview: bool = Query(default=False),
    template: str = Query(default="estimate1"),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Generate PDF for an estimate."""
    estimate = await db.get(Estimate, estimate_id)
    if not estimate or estimate.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
    
    template_name = f"{template}.html"
    context = _get_estimate_context(estimate)
    
    if preview:
        html_content = render_html(template_name, context)
        return Response(content=html_content, media_type="text/html")
    
    pdf_bytes = generate_pdf(template_name, context)
    
    filename = f"Estimate_{estimate.estimate_number}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/payments/{payment_id}")
async def get_payment_pdf(
    payment_id: int,
    preview: bool = Query(default=False),
    template: str = Query(default="payment1"),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    """Generate PDF for a payment receipt."""
    payment = await db.get(Payment, payment_id)
    if not payment or payment.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    template_name = f"{template}.html"
    context = _get_payment_context(payment)
    
    if preview:
        html_content = render_html(template_name, context)
        return Response(content=html_content, media_type="text/html")
    
    pdf_bytes = generate_pdf(template_name, context)
    
    filename = f"Payment_{payment.payment_number}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/public/{token}")
async def get_public_pdf(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public PDF access via email token (Task 6.9).
    
    This endpoint allows customers to access PDFs without login
    by validating the unique token sent via email.
    """
    # Find email log by token
    stmt = select(EmailLog).where(EmailLog.token == token)
    result = await db.execute(stmt)
    email_log = result.scalar_one_or_none()
    
    if not email_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")
    
    # Check expiry
    if email_log.is_expired or email_log.token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token has expired")
    
    # Determine entity type and get PDF
    entity_id = email_log.entity_id
    email_type = email_log.email_type
    
    if email_type == "invoice":
        invoice = await db.get(Invoice, entity_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        template_name = f"{invoice.template_name or 'invoice1'}.html"
        context = _get_invoice_context(invoice)
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        
    elif email_type == "estimate":
        estimate = await db.get(Estimate, entity_id)
        if not estimate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
        
        template_name = f"{estimate.template_name or 'estimate1'}.html"
        context = _get_estimate_context(estimate)
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Estimate_{estimate.estimate_number}.pdf"
        
    elif email_type == "payment":
        payment = await db.get(Payment, entity_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        template_name = f"payment1.html"
        context = _get_payment_context(payment)
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Payment_{payment.payment_number}.pdf"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email type")
    
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/templates/list")
async def list_templates():
    """List available PDF templates (Task 6.6)."""
    return {"templates": get_available_templates()}
