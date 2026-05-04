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

    # if attached to invoice, adjust invoice due_amount
    if payload.invoice_id:
        inv = await db.get(Invoice, payload.invoice_id)
        if not inv or inv.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        inv.due_amount = max(0, (inv.due_amount or inv.total or 0) - payload.amount)
        if inv.due_amount <= 0 and (inv.total or 0) > 0:
            inv.paid_status = "PAID"
        elif inv.due_amount < (inv.total or 0):
            inv.paid_status = "PARTIALLY_PAID"
        else:
            inv.paid_status = "UNPAID"

    await db.commit()
    await db.refresh(payment)
    return payment


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
