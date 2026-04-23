"""TaxType CRUD (Sprint 2.8)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.tax import TaxType
from app.models.user import User
from app.schemas.tax import (
    TaxTypeCreate,
    TaxTypeDeleteRequest,
    TaxTypeOut,
    TaxTypeUpdate,
)

router = APIRouter(prefix="/tax-types", tags=["tax-types"])


@router.get("", response_model=list[TaxTypeOut])
async def list_tax_types(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> list[TaxType]:
    result = await db.scalars(
        select(TaxType).where(TaxType.company_id == company.id).order_by(TaxType.id)
    )
    return list(result.all())


@router.post("", response_model=TaxTypeOut, status_code=status.HTTP_201_CREATED)
async def create_tax_type(
    payload: TaxTypeCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> TaxType:
    tax = TaxType(**payload.model_dump(), company_id=company.id)
    db.add(tax)
    await db.commit()
    await db.refresh(tax)
    return tax


@router.get("/{tax_type_id}", response_model=TaxTypeOut)
async def get_tax_type(
    tax_type_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> TaxType:
    tax = await db.get(TaxType, tax_type_id)
    if not tax or tax.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tax type not found"
        )
    return tax


@router.put("/{tax_type_id}", response_model=TaxTypeOut)
async def update_tax_type(
    tax_type_id: int,
    payload: TaxTypeUpdate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> TaxType:
    tax = await db.get(TaxType, tax_type_id)
    if not tax or tax.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tax type not found"
        )
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(tax, k, v)
    await db.commit()
    await db.refresh(tax)
    return tax


@router.delete("/{tax_type_id}")
async def delete_tax_type(
    tax_type_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    tax = await db.get(TaxType, tax_type_id)
    if not tax or tax.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tax type not found"
        )
    await db.delete(tax)
    await db.commit()
    return {"success": True}


@router.post("/delete")
async def bulk_delete_tax_types(
    payload: TaxTypeDeleteRequest,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided"
        )
    result = await db.scalars(
        select(TaxType).where(
            TaxType.id.in_(payload.ids), TaxType.company_id == company.id
        )
    )
    for tax in result.all():
        await db.delete(tax)
    await db.commit()
    return {"success": True}
