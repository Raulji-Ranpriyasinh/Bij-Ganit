"""PDF generation endpoints for invoices, estimates and payments (Sprint 6).

Provides:
- GET /invoices/{id}/pdf - Download or preview invoice PDF
- GET /estimates/{id}/pdf - Download or preview estimate PDF  
- GET /payments/{id}/pdf - Download or preview payment PDF
- GET /invoices/templates - List available invoice templates
- GET /estimates/templates - List available estimate templates
- GET /payments/templates - List available payment templates
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.invoice import Invoice
from app.models.estimate import Estimate
from app.models.finance import Payment
from app.services.pdf_service import (
    generate_pdf,
    generate_pdf_preview,
    list_templates,
    save_pdf_to_disk,
)
from io import BytesIO


router = APIRouter(tags=["pdf"])


def _format_currency(amount: float, currency_code: str = "USD") -> str:
    """Format amount as currency string."""
    return f"{currency_code} {amount:,.2f}"


def _prepare_invoice_context(invoice: Invoice, company: Company) -> dict:
    """Prepare context dictionary for invoice PDF template."""
    # Build company address
    company_address = ""
    if company.name:
        company_address += f"<b>{company.name}</b><br>"
    if company.address:
        company_address += f"{company.address}<br>"
    if company.city:
        company_address += f"{company.city}, "
    if company.state:
        company_address += f"{company.state} "
    if company.country_id:
        company_address += f"{company.country_id}<br>"
    if company.phone:
        company_address += f"Phone: {company.phone}<br>"
    if company.email:
        company_address += f"Email: {company.email}"

    # Build billing address
    billing_address = ""
    if invoice.customer:
        if invoice.customer.name:
            billing_address += f"<b>{invoice.customer.name}</b><br>"
        if invoice.customer.contact_name:
            billing_address += f"{invoice.customer.contact_name}<br>"
        if invoice.customer.email:
            billing_address += f"Email: {invoice.customer.email}<br>"
        if invoice.customer.phone:
            billing_address += f"Phone: {invoice.customer.phone}<br>"
        if invoice.customer.address:
            billing_address += f"{invoice.customer.address}<br>"

    # Build shipping address (same as billing if not specified)
    shipping_address = billing_address

    # Format dates
    formatted_invoice_date = ""
    formatted_due_date = ""
    if invoice.invoice_date:
        formatted_invoice_date = invoice.invoice_date.strftime("%Y-%m-%d")
    if invoice.due_date:
        formatted_due_date = invoice.due_date.strftime("%Y-%m-%d")

    # Prepare items with custom fields
    items_data = []
    for item in invoice.items:
        items_data.append({
            "name": item.name,
            "description": item.description or "",
            "quantity": item.quantity,
            "price": item.price,
            "discount": item.discount,
            "discount_val": item.discount_val,
            "discount_type": item.discount_type,
            "tax": item.tax,
            "total": item.total,
            "unit_name": item.unit_name,
            "custom_fields": {},
        })

    # Get currency code
    currency_code = "USD"
    if invoice.currency and invoice.currency.code:
        currency_code = invoice.currency.code

    return {
        "invoice": type('obj', (object,), {
            "invoice_number": invoice.invoice_number or "",
            "formatted_invoice_date": formatted_invoice_date,
            "formatted_due_date": formatted_due_date,
            "notes": invoice.notes or "",
            "discount_per_item": invoice.discount_per_item,
            "tax_per_item": invoice.tax_per_item,
            "discount_type": invoice.discount_type,
            "discount": invoice.discount,
            "discount_val": invoice.discount_val,
            "sub_total": invoice.sub_total,
            "total": invoice.total,
            "items": items_data,
            "taxes": [{"name": t.name, "percent": t.percent, "amount": t.amount} for t in (invoice.taxes or [])],
            "customer": type('obj', (object,), {
                "company": type('obj', (object,), {"name": company.name or ""}) if company else None
            })() if invoice.customer else None,
        })(),
        "company_address": company_address,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "logo": None,  # Could be company logo URL
        "currency_code": currency_code,
        "custom_fields": [],
        "format_currency": _format_currency,
        "taxes": [{"name": t.name, "percent": t.percent, "amount": t.amount} for t in (invoice.taxes or [])],
    }


def _prepare_estimate_context(estimate: Estimate, company: Company) -> dict:
    """Prepare context dictionary for estimate PDF template."""
    # Similar to invoice but with estimate-specific fields
    company_address = ""
    if company.name:
        company_address += f"<b>{company.name}</b><br>"
    if company.address:
        company_address += f"{company.address}<br>"

    billing_address = ""
    if estimate.customer:
        if estimate.customer.name:
            billing_address += f"<b>{estimate.customer.name}</b><br>"
        if estimate.customer.email:
            billing_address += f"Email: {estimate.customer.email}<br>"

    formatted_estimate_date = ""
    formatted_expiry_date = ""
    if estimate.estimate_date:
        formatted_estimate_date = estimate.estimate_date.strftime("%Y-%m-%d")
    if estimate.expiry_date:
        formatted_expiry_date = estimate.expiry_date.strftime("%Y-%m-%d")

    items_data = []
    for item in estimate.items:
        items_data.append({
            "name": item.name,
            "description": item.description or "",
            "quantity": item.quantity,
            "price": item.price,
            "discount": item.discount,
            "discount_val": item.discount_val,
            "discount_type": item.discount_type,
            "tax": item.tax,
            "total": item.total,
            "unit_name": item.unit_name,
            "custom_fields": {},
        })

    currency_code = "USD"
    if estimate.currency and estimate.currency.code:
        currency_code = estimate.currency.code

    return {
        "estimate": type('obj', (object,), {
            "estimate_number": estimate.estimate_number or "",
            "formatted_estimate_date": formatted_estimate_date,
            "formatted_expiry_date": formatted_expiry_date,
            "notes": estimate.notes or "",
            "discount_per_item": estimate.discount_per_item,
            "tax_per_item": estimate.tax_per_item,
            "discount_type": estimate.discount_type,
            "discount": estimate.discount,
            "discount_val": estimate.discount_val,
            "sub_total": estimate.sub_total,
            "total": estimate.total,
            "items": items_data,
            "taxes": [{"name": t.name, "percent": t.percent, "amount": t.amount} for t in (estimate.taxes or [])],
            "customer": type('obj', (object,), {
                "company": type('obj', (object,), {"name": company.name or ""}) if company else None
            })() if estimate.customer else None,
        })(),
        "company_address": company_address,
        "billing_address": billing_address,
        "shipping_address": billing_address,
        "logo": None,
        "currency_code": currency_code,
        "custom_fields": [],
        "format_currency": _format_currency,
        "taxes": [{"name": t.name, "percent": t.percent, "amount": t.amount} for t in (estimate.taxes or [])],
    }


def _prepare_payment_context(payment: Payment, company: Company) -> dict:
    """Prepare context dictionary for payment PDF template."""
    company_address = ""
    if company.name:
        company_address += f"<b>{company.name}</b><br>"
    if company.address:
        company_address += f"{company.address}<br>"

    formatted_payment_date = ""
    if payment.payment_date:
        formatted_payment_date = payment.payment_date.strftime("%Y-%m-%d")

    currency_code = "USD"
    if payment.currency and payment.currency.code:
        currency_code = payment.currency.code

    return {
        "payment": type('obj', (object,), {
            "payment_number": payment.payment_number or "",
            "formatted_payment_date": formatted_payment_date,
            "notes": payment.notes or "",
            "total_amount": payment.amount,
            "payment_method": payment.payment_method or "",
            "invoice_payments": [],
        })(),
        "company_address": company_address,
        "logo": None,
        "currency_code": currency_code,
        "format_currency": _format_currency,
    }


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: int,
    preview: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
):
    """Get invoice as PDF download or HTML preview."""
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    template_name = f"invoice/{invoice.template_name or 'invoice1'}.html"
    context = _prepare_invoice_context(invoice, company)

    if preview:
        html_content = generate_pdf_preview(template_name, context)
        return HTMLResponse(content=html_content)

    pdf_bytes = generate_pdf(template_name, context)

    filename = f"Invoice-{invoice.invoice_number or invoice_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/estimates/{estimate_id}/pdf")
async def get_estimate_pdf(
    estimate_id: int,
    preview: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
):
    """Get estimate as PDF download or HTML preview."""
    estimate = await db.get(Estimate, estimate_id)
    if not estimate or estimate.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")

    template_name = f"estimate/{estimate.template_name or 'estimate1'}.html"
    context = _prepare_estimate_context(estimate, company)

    if preview:
        html_content = generate_pdf_preview(template_name, context)
        return HTMLResponse(content=html_content)

    pdf_bytes = generate_pdf(template_name, context)

    filename = f"Estimate-{estimate.estimate_number or estimate_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/payments/{payment_id}/pdf")
async def get_payment_pdf(
    payment_id: int,
    preview: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
):
    """Get payment as PDF download or HTML preview."""
    payment = await db.get(Payment, payment_id)
    if not payment or payment.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    template_name = f"payment/{'payment1'}.html"
    context = _prepare_payment_context(payment, company)

    if preview:
        html_content = generate_pdf_preview(template_name, context)
        return HTMLResponse(content=html_content)

    pdf_bytes = generate_pdf(template_name, context)

    filename = f"Payment-{payment.payment_number or payment_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/invoices/templates")
async def list_invoice_templates():
    """List available invoice templates."""
    return list_templates("invoice")


@router.get("/estimates/templates")
async def list_estimate_templates():
    """List available estimate templates."""
    return list_templates("estimate")


@router.get("/payments/templates")
async def list_payment_templates():
    """List available payment templates."""
    return list_templates("payment")
