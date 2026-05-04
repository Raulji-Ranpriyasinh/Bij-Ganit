"""Payments endpoints (Sprint 4).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.finance import Payment, PaymentMethod
from app.models.user import User
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, PaymentOut
from app.core.hashids import encode_id

router = APIRouter(prefix="/payments", tags=["payments"])


def _update_invoice_due(inv: Invoice, amount_delta: int) -> None:
    """Add amount_delta to invoice due_amount and recalculate paid_status."""
    inv.due_amount = max(0, (inv.due_amount or 0) + amount_delta)
    total = inv.total or 0
    if inv.due_amount <= 0 and total > 0:
        inv.paid_status = "PAID"
    elif inv.due_amount < total:
        inv.paid_status = "PARTIALLY_PAID"
    else:
        inv.paid_status = "UNPAID"


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Payment:
    payment = Payment(
        payment_date=payload.payment_date,
        amount=payload.amount,
        notes=payload.notes,
        company_id=company.id,
        creator_id=current_user.id,
        payment_method_id=payload.payment_method_id,
        invoice_id=payload.invoice_id,
    )
    db.add(payment)
    await db.flush()
    payment.unique_hash = encode_id("payment", payment.id)

    if payload.invoice_id:
        inv = await db.get(Invoice, payload.invoice_id)
        if not inv or inv.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        _update_invoice_due(inv, -payload.amount)

    await db.commit()
    await db.refresh(payment)
    return payment


@router.put("/{payment_id}", response_model=PaymentOut)
async def update_payment(
    payment_id: int,
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Payment:
    payment = await db.get(Payment, payment_id)
    if not payment or payment.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    old_invoice_id = payment.invoice_id
    old_amount = payment.amount

    # Case 1 & 2: had an old invoice — restore its due_amount
    if old_invoice_id:
        old_inv = await db.get(Invoice, old_invoice_id)
        if old_inv and old_inv.company_id == company.id:
            _update_invoice_due(old_inv, old_amount)

    # Apply new values
    payment.amount = payload.amount
    payment.payment_date = payload.payment_date
    payment.notes = payload.notes
    payment.payment_method_id = payload.payment_method_id
    payment.invoice_id = payload.invoice_id

    # Case 1: invoice changed OR Case 3: same invoice — subtract new amount
    if payload.invoice_id:
        new_inv = await db.get(Invoice, payload.invoice_id)
        if not new_inv or new_inv.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        _update_invoice_due(new_inv, -payload.amount)

    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/delete")
async def delete_payments(
    ids: list[int],
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided")
    result = await db.scalars(
        select(Payment).where(Payment.id.in_(ids), Payment.company_id == company.id)
    )
    for p in result.all():
        if p.invoice_id:
            inv = await db.get(Invoice, p.invoice_id)
            if inv and inv.company_id == company.id:
                _update_invoice_due(inv, p.amount)
        await db.delete(p)
    await db.commit()
    return {"success": True}


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    p = await db.get(Payment, payment_id)
    if not p or p.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return p


@router.get("")
async def list_payments(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    stmt = select(Payment).where(Payment.company_id == company.id)
    res = await db.scalars(stmt)
    return {"items": list(res.all())}