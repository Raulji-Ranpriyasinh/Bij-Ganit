"""Cron endpoints for background tasks (Sprint 5).

Provides a simple HTTP-triggered task to generate invoices from recurring
definitions. This is synchronous and intended for development/testing; in
production run via scheduler or background worker.
"""

from datetime import datetime, timedelta, date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.deps import get_current_company, get_current_user
from app.models.recurring import RecurringInvoice, RecurringInvoiceItem
from app.models.invoice import Invoice, InvoiceItem
from app.services.serial_number import generate_invoice_number

router = APIRouter(prefix="/cron", tags=["cron"])


def _advance_next_date(current: date | datetime | None, freq: str | None) -> datetime | None:
    if not current or not freq:
        return None
    if isinstance(current, datetime):
        base = current
    else:
        base = datetime.combine(current, datetime.min.time())
    f = freq.lower()
    if f == "daily":
        return base + timedelta(days=1)
    if f == "weekly":
        return base + timedelta(weeks=1)
    if f == "monthly":
        # naive month increment
        month = base.month + 1
        year = base.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        return base.replace(year=year, month=month)
    if f == "yearly":
        return base.replace(year=base.year + 1)
    return None


@router.post("/run-recurring")
async def run_recurring(
    db: AsyncSession = Depends(get_db),
    company = Depends(get_current_company),
    user = Depends(get_current_user),
):
    now = datetime.utcnow()
    stmt = select(RecurringInvoice).where(RecurringInvoice.company_id == company.id, RecurringInvoice.status == "ACTIVE")
    rows = (await db.scalars(stmt)).all()
    created: List[int] = []
    for r in rows:
        should = False
        if r.next_invoice_at and r.next_invoice_at <= now:
            should = True
        elif r.starts_at and datetime.combine(r.starts_at, datetime.min.time()) <= now and not r.next_invoice_at:
            should = True

        if not should:
            continue

        # generate invoice number
        number, seq = await generate_invoice_number(db, company.id)

        inv = Invoice(
            invoice_number=number,
            invoice_date=datetime.utcnow(),
            due_date=None,
            status="DRAFT",
            paid_status="UNPAID",
            tax_per_item=r.tax_per_item,
            discount_per_item=r.discount_per_item,
            notes=r.notes,
            discount_type=r.discount_type,
            discount=r.discount,
            discount_val=r.discount_val,
            sub_total=r.sub_total,
            total=r.total,
            tax=r.tax,
            due_amount=r.total,
            sent=False,
            viewed=False,
            overdue=False,
            template_name=r.template_name,
            unique_hash=None,
            sequence_number=seq,
            base_sub_total=r.sub_total,
            base_total=r.total,
            base_tax=r.tax,
            base_discount_val=r.discount_val,
            currency_id=r.currency_id,
            customer_id=r.customer_id,
            company_id=company.id,
            creator_id=user.id,
            recurring_invoice_id=r.id,
        )
        db.add(inv)
        await db.flush()

        # copy items
        for it in r.items:
            ni = InvoiceItem(
                name=it.name,
                description=it.description,
                price=it.price,
                quantity=it.quantity,
                discount=it.discount,
                discount_val=it.discount_val,
                tax=it.tax,
                total=it.total,
                unit_name=it.unit_name,
                base_price=it.base_price,
                base_discount_val=it.base_discount_val,
                base_tax=it.base_tax,
                base_total=it.base_total,
                exchange_rate=it.exchange_rate,
                invoice_id=inv.id,
                company_id=company.id,
                recurring_invoice_id=r.id,
            )
            db.add(ni)

        # advance next run
        nxt = _advance_next_date(r.next_invoice_at or r.starts_at, r.frequency)
        r.next_invoice_at = nxt
        created.append(inv.id)

    await db.commit()
    return {"created_invoice_ids": created}
