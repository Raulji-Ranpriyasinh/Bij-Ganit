"""Estimates endpoints (Sprint 4).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.finance import Estimate, EstimateItem
from app.models.tax import Tax, TaxType
from app.models.user import User
from app.schemas.estimate import EstimateCreate, EstimateOut, EstimateItemInput
from app.services.serial_number import generate_invoice_number
from app.core.hashids import encode_id
from app.models.invoice import Invoice, InvoiceItem
from app.schemas.invoice import InvoiceOut

router = APIRouter(prefix="/estimates", tags=["estimates"]) 


@router.post("", response_model=EstimateOut, status_code=status.HTTP_201_CREATED)
async def create_estimate(
    payload: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Estimate:
    est = Estimate(
        estimate_date=payload.estimate_date,
        expiry_date=payload.expiry_date,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(est)
    await db.flush()

    sub_total = 0
    for item_payload in payload.items:
        ei = EstimateItem(
            name=item_payload.name,
            description=item_payload.description,
            price=item_payload.price,
            quantity=item_payload.quantity,
            discount=item_payload.discount,
            discount_val=item_payload.discount_val,
            company_id=company.id,
            estimate_id=est.id,
            item_id=item_payload.item_id,
            unit_name=item_payload.unit_name,
        )
        ei.total = (ei.price * ei.quantity) - ei.discount_val
        ei.base_price = ei.price
        ei.base_total = ei.total
        sub_total += ei.total
        db.add(ei)
        await db.flush()
        for tax_payload in item_payload.taxes:
            tax_type = await db.get(TaxType, tax_payload.tax_type_id)
            if not tax_type or tax_type.company_id != company.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tax_type_id {tax_payload.tax_type_id}")
            db.add(
                Tax(
                    name=tax_type.name,
                    amount=tax_payload.amount,
                    percent=tax_payload.percent,
                    compound_tax=tax_payload.compound_tax,
                    tax_type_id=tax_payload.tax_type_id,
                    item_id=ei.id,
                    company_id=company.id,
                    estimate_id=est.id,
                )
            )

    est.sub_total = sub_total
    est.total = sub_total

    await db.flush()
    est.unique_hash = encode_id("estimate", est.id)
    await db.commit()
    await db.refresh(est)
    return est


@router.get("")
async def list_estimates(
    page: int = Query(default=1),
    per_page: int = Query(default=25),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    stmt = select(Estimate).where(Estimate.company_id == company.id).offset((page - 1) * per_page).limit(per_page)
    res = await db.scalars(stmt)
    items = list(res.all())
    return {"items": items, "meta": {"total": len(items), "page": page, "per_page": per_page}}


@router.get("/{estimate_id}", response_model=EstimateOut)
async def get_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    est = await db.get(Estimate, estimate_id)
    if not est or est.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
    return est


@router.post("/delete")
async def bulk_delete_estimates(
    ids: list[int],
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided")
    await db.execute(delete(Tax).where(Tax.estimate_id.in_(ids)))
    await db.execute(delete(EstimateItem).where(EstimateItem.estimate_id.in_(ids)))
    await db.execute(delete(Estimate).where(Estimate.id.in_(ids), Estimate.company_id == company.id))
    await db.commit()
    return {"success": True}

@router.post("/{estimate_id}/convert-to-invoice", response_model=InvoiceOut)

async def convert_estimate_to_invoice(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
):
    est = await db.get(Estimate, estimate_id)
    if not est or est.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estimate not found")
    inv = Invoice(
        invoice_date=est.estimate_date,
        due_date=None,
        status="DRAFT",
        paid_status="UNPAID",
        notes=est.notes,
        sub_total=est.sub_total,
        total=est.total,
        tax=est.tax,
        due_amount=est.total,
        template_name=est.template_name,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(inv)
    await db.flush()
    invoice_number, seq = await generate_invoice_number(db, company.id)
    inv.invoice_number = invoice_number
    inv.sequence_number = seq
    # copy items
    for it in est.items:
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
            base_total=it.base_total,
            company_id=company.id,
            invoice_id=inv.id,
            item_id=it.item_id,
        )
        db.add(ni)
    await db.flush()
    inv.unique_hash = encode_id("invoice", inv.id)
    await db.commit()
    await db.refresh(inv)
    return inv
