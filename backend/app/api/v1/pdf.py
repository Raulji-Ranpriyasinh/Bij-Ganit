"""PDF and Email endpoints for invoices, estimates, and payments (Sprint 6 - Tasks 6.5, 6.8, 6.9).

Provides endpoints to generate PDF documents from templates and send them via email.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.invoice import Invoice
from app.models.estimate import Estimate
from app.models.payment import Payment
from app.models.company import Company
from app.models.customer import Customer
from app.services.pdf_service import generate_pdf, render_template, get_available_templates
from app.services.email_service import (
    send_email,
    validate_email_token,
    get_invoice_email_subject,
    get_invoice_email_body,
    get_estimate_email_subject,
    get_estimate_email_body,
    get_payment_email_body,
)


class SendEmailRequest(BaseModel):
    """Request model for sending email."""
    to: str | list[str]
    subject: str
    body: str
    attach_pdf: bool = True


class EmailPreviewResponse(BaseModel):
    """Response model for email preview."""
    subject: str
    body: str
    placeholders: dict[str, str]


router = APIRouter(prefix="/invoices", tags=["invoices-pdf"])


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    preview: bool = Query(False, description="If true, return HTML instead of PDF"),
    db: AsyncSession = Depends(get_db),
):
    """Get invoice as PDF or HTML preview.
    
    Args:
        invoice_id: The invoice ID
        preview: If true, returns HTML; otherwise returns PDF
        db: Database session
        
    Returns:
        PDF file or HTML content
    """
    # Fetch invoice
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Prepare template context
    company_address = ""
    if invoice.company:
        lines = []
        if invoice.company.name:
            lines.append(invoice.company.name)
        if invoice.company.address:
            lines.append(invoice.company.address)
        if invoice.company.city:
            lines.append(f"{invoice.company.city}, {invoice.company.state} {invoice.company.zip}")
        if invoice.company.country:
            lines.append(invoice.company.country)
        company_address = "<br>".join(lines)
    
    billing_address = ""
    shipping_address = ""
    if invoice.customer:
        if invoice.customer.billing_address:
            lines = []
            if invoice.customer.name:
                lines.append(invoice.customer.name)
            if invoice.customer.billing_address:
                lines.append(invoice.customer.billing_address)
            if invoice.customer.billing_city:
                lines.append(f"{invoice.customer.billing_city}, {invoice.customer.billing_state} {invoice.customer.billing_zip}")
            if invoice.customer.billing_country:
                lines.append(invoice.customer.billing_country)
            billing_address = "<br>".join(lines)
        
        if invoice.customer.shipping_address:
            lines = []
            if invoice.customer.name:
                lines.append(invoice.customer.name)
            if invoice.customer.shipping_address:
                lines.append(invoice.customer.shipping_address)
            if invoice.customer.shipping_city:
                lines.append(f"{invoice.customer.shipping_city}, {invoice.customer.shipping_state} {invoice.customer.shipping_zip}")
            if invoice.customer.shipping_country:
                lines.append(invoice.customer.shipping_country)
            shipping_address = "<br>".join(lines)
    
    # Format dates
    formatted_invoice_date = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else ""
    formatted_due_date = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else ""
    
    # Build invoice data structure for template
    invoice_data = {
        "invoice_number": invoice.invoice_number or "",
        "formatted_invoice_date": formatted_invoice_date,
        "formatted_due_date": formatted_due_date,
        "status": invoice.status,
        "paid_status": invoice.paid_status,
        "tax_per_item": invoice.tax_per_item,
        "discount_per_item": invoice.discount_per_item,
        "notes": invoice.notes or "",
        "discount_type": invoice.discount_type or "",
        "discount": invoice.discount or 0,
        "discount_val": invoice.discount_val or 0,
        "sub_total": invoice.sub_total or 0,
        "total": invoice.total or 0,
        "tax": invoice.tax or 0,
        "items": [
            {
                "name": item.name,
                "description": item.description or "",
                "quantity": item.quantity,
                "price": item.price,
                "discount": item.discount or 0,
                "discount_val": item.discount_val or 0,
                "discount_type": item.discount_type or "",
                "tax": item.tax or 0,
                "total": item.total,
                "unit_name": item.unit_name or "",
            }
            for item in invoice.items
        ],
        "taxes": [
            {
                "name": tax.name,
                "percent": float(tax.percent) if tax.percent else 0,
                "amount": tax.amount or 0,
            }
            for tax in invoice.taxes
        ],
    }
    
    currency_symbol = "$"
    if invoice.currency and invoice.currency.symbol:
        currency_symbol = invoice.currency.symbol
    
    logo = None  # Could be base64 encoded image or URL
    
    context = {
        "invoice": invoice_data,
        "company": {"name": invoice.company.name} if invoice.company else None,
        "company_address": company_address,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "currency_symbol": currency_symbol,
        "logo": logo,
        "taxes": invoice_data["taxes"],
    }
    
    # Determine template
    template_name = f"invoice/{invoice.template_name or 'invoice1'}.html"
    
    if preview:
        # Return HTML preview
        html_content = render_template(template_name, context)
        return Response(content=html_content, media_type="text/html")
    else:
        # Generate PDF
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Invoice-{invoice.invoice_number}.pdf"
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.get("/templates")
async def list_invoice_templates():
    """List available invoice templates.
    
    Returns:
        List of template metadata
    """
    templates = get_available_templates("invoice")
    return {"templates": templates}


def _build_invoice_context(invoice: Invoice) -> dict[str, Any]:
    """Build context dictionary for invoice email/PDF."""
    company_address = ""
    if invoice.company:
        lines = []
        if invoice.company.name:
            lines.append(invoice.company.name)
        if invoice.company.address:
            lines.append(invoice.company.address)
        if invoice.company.city:
            lines.append(f"{invoice.company.city}, {invoice.company.state} {invoice.company.zip}")
        if invoice.company.country:
            lines.append(invoice.company.country)
        company_address = "<br>".join(lines)
    
    billing_address = ""
    shipping_address = ""
    customer_name = ""
    if invoice.customer:
        customer_name = invoice.customer.name or ""
        if invoice.customer.billing_address:
            lines = []
            if invoice.customer.name:
                lines.append(invoice.customer.name)
            if invoice.customer.billing_address:
                lines.append(invoice.customer.billing_address)
            if invoice.customer.billing_city:
                lines.append(f"{invoice.customer.billing_city}, {invoice.customer.billing_state} {invoice.customer.billing_zip}")
            if invoice.customer.billing_country:
                lines.append(invoice.customer.billing_country)
            billing_address = "<br>".join(lines)
        
        if invoice.customer.shipping_address:
            lines = []
            if invoice.customer.name:
                lines.append(invoice.customer.name)
            if invoice.customer.shipping_address:
                lines.append(invoice.customer.shipping_address)
            if invoice.customer.shipping_city:
                lines.append(f"{invoice.customer.shipping_city}, {invoice.customer.shipping_state} {invoice.customer.shipping_zip}")
            if invoice.customer.shipping_country:
                lines.append(invoice.customer.shipping_country)
            shipping_address = "<br>".join(lines)
    
    formatted_invoice_date = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else ""
    formatted_due_date = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else ""
    
    invoice_data = {
        "invoice_number": invoice.invoice_number or "",
        "formatted_invoice_date": formatted_invoice_date,
        "formatted_due_date": formatted_due_date,
        "status": invoice.status,
        "paid_status": invoice.paid_status,
        "tax_per_item": invoice.tax_per_item,
        "discount_per_item": invoice.discount_per_item,
        "notes": invoice.notes or "",
        "discount_type": invoice.discount_type or "",
        "discount": invoice.discount or 0,
        "discount_val": invoice.discount_val or 0,
        "sub_total": invoice.sub_total or 0,
        "total": invoice.total or 0,
        "tax": invoice.tax or 0,
        "items": [
            {
                "name": item.name,
                "description": item.description or "",
                "quantity": item.quantity,
                "price": item.price,
                "discount": item.discount or 0,
                "discount_val": item.discount_val or 0,
                "discount_type": item.discount_type or "",
                "tax": item.tax or 0,
                "total": item.total,
                "unit_name": item.unit_name or "",
            }
            for item in invoice.items
        ],
        "taxes": [
            {
                "name": tax.name,
                "percent": float(tax.percent) if tax.percent else 0,
                "amount": tax.amount or 0,
            }
            for tax in invoice.taxes
        ],
    }
    
    currency_symbol = "$"
    if invoice.currency and invoice.currency.symbol:
        currency_symbol = invoice.currency.symbol
    
    return {
        "invoice": invoice_data,
        "company_name": invoice.company.name if invoice.company else "",
        "company_address": company_address,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "customer_name": customer_name,
        "currency_symbol": currency_symbol,
        "invoice_number": invoice.invoice_number or "",
        "invoice_date": formatted_invoice_date,
        "due_date": formatted_due_date,
        "status": invoice.status,
        "total_amount": invoice.total or 0,
        "notes": invoice.notes or "",
        "items": invoice_data["items"],
    }


@router.post("/{invoice_id}/send")
async def send_invoice_email(
    invoice_id: int,
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send invoice via email with optional PDF attachment.
    
    Args:
        invoice_id: The invoice ID
        request: Email request with to, subject, body, attach_pdf
        db: Database session
        
    Returns:
        Email send status
    """
    # Fetch invoice
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Get PDF bytes if attachment requested
    attachments = None
    attachment_names = None
    if request.attach_pdf:
        context = _build_invoice_context(invoice)
        template_name = f"invoice/{invoice.template_name or 'invoice1'}.html"
        pdf_bytes = generate_pdf(template_name, context)
        attachments = [pdf_bytes]
        attachment_names = [f"Invoice-{invoice.invoice_number}.pdf"]
    
    # Send email
    result_data = await send_email(
        to=request.to,
        subject=request.subject,
        body=request.body,
        db=db,
        entity_type="invoice",
        entity_id=invoice_id,
        attachments=attachments,
        attachment_names=attachment_names,
    )
    
    return result_data


@router.get("/{invoice_id}/send/preview")
async def preview_invoice_email(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Preview email content for invoice with placeholders.
    
    Args:
        invoice_id: The invoice ID
        db: Database session
        
    Returns:
        Email preview with subject and body
    """
    # Fetch invoice
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    context = _build_invoice_context(invoice)
    company_name = context["company_name"]
    invoice_number = context["invoice_number"]
    
    subject = get_invoice_email_subject(invoice_number, company_name)
    body = get_invoice_email_body(context)
    
    placeholders = {
        "{{company_name}}": company_name,
        "{{invoice_number}}": invoice_number,
        "{{customer_name}}": context["customer_name"],
        "{{total_amount}}": str(context["total_amount"]),
        "{{invoice_date}}": context["invoice_date"],
        "{{due_date}}": context["due_date"],
    }
    
    return {
        "subject": subject,
        "body": body,
        "placeholders": placeholders,
    }


# Public PDF access endpoint (Task 6.9)
public_router = APIRouter(tags=["public-pdf"])


@public_router.get("/pdf/{token}")
async def get_public_pdf(token: str, db: AsyncSession = Depends(get_db)):
    """Get PDF via public token (no authentication required).
    
    Args:
        token: Unique token from email log
        db: Database session
        
    Returns:
        PDF file stream
    """
    # Validate token
    email_log = await validate_email_token(token, db)
    
    if not email_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )
    
    entity_type = email_log.entity_type
    entity_id = email_log.entity_id
    
    # Fetch the entity and generate PDF
    if entity_type == "invoice":
        result = await db.execute(select(Invoice).where(Invoice.id == entity_id))
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        context = _build_invoice_context(invoice)
        template_name = f"invoice/{invoice.template_name or 'invoice1'}.html"
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Invoice-{invoice.invoice_number}.pdf"
        
    elif entity_type == "estimate":
        result = await db.execute(select(Estimate).where(Estimate.id == entity_id))
        estimate = result.scalar_one_or_none()
        if not estimate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
        
        # Build estimate context (similar to invoice)
        context = _build_estimate_context(estimate)
        template_name = f"estimate/{estimate.template_name or 'estimate1'}.html"
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Estimate-{estimate.estimate_number}.pdf"
        
    elif entity_type == "payment":
        result = await db.execute(select(Payment).where(Payment.id == entity_id))
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        context = _build_payment_context(payment)
        template_name = f"payment/{payment.template_name or 'payment1'}.html"
        pdf_bytes = generate_pdf(template_name, context)
        filename = f"Payment-{payment.payment_number}.pdf"
        
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity type")
    
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _build_estimate_context(estimate: Estimate) -> dict[str, Any]:
    """Build context dictionary for estimate email/PDF."""
    company_name = estimate.company.name if estimate.company else ""
    customer_name = estimate.customer.name if estimate.customer else ""
    
    formatted_estimate_date = estimate.estimate_date.strftime("%Y-%m-%d") if estimate.estimate_date else ""
    formatted_expiry_date = estimate.expiry_date.strftime("%Y-%m-%d") if estimate.expiry_date else ""
    
    currency_symbol = "$"
    if estimate.currency and estimate.currency.symbol:
        currency_symbol = estimate.currency.symbol
    
    items = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price,
            "total": item.total,
        }
        for item in estimate.items
    ]
    
    return {
        "company_name": company_name,
        "customer_name": customer_name,
        "estimate_number": estimate.estimate_number or "",
        "estimate_date": formatted_estimate_date,
        "expiry_date": formatted_expiry_date,
        "status": estimate.status,
        "total_amount": estimate.total or 0,
        "currency_symbol": currency_symbol,
        "notes": estimate.notes or "",
        "items": items,
    }


def _build_payment_context(payment: Payment) -> dict[str, Any]:
    """Build context dictionary for payment email/PDF."""
    company_name = payment.company.name if payment.company else ""
    customer_name = payment.customer.name if payment.customer else ""
    
    formatted_payment_date = payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else ""
    
    currency_symbol = "$"
    if payment.currency and payment.currency.symbol:
        currency_symbol = payment.currency.symbol
    
    return {
        "company_name": company_name,
        "customer_name": customer_name,
        "payment_number": payment.payment_number or "",
        "payment_date": formatted_payment_date,
        "payment_method": payment.payment_method or "",
        "reference": payment.reference or "",
        "total_amount": payment.amount or 0,
        "currency_symbol": currency_symbol,
        "notes": payment.notes or "",
    }
