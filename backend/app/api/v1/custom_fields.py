"""Custom Fields CRUD (Sprint 5)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.custom_field import CustomField
from app.models.user import User

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])


@router.get("")
async def list_custom_fields(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    res = await db.scalars(select(CustomField).where(CustomField.company_id == company.id))
    return list(res.all())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", payload.get("name", "").lower()).strip("_")
    cf = CustomField(
        name=payload["name"],
        slug=slug,
        model_type=payload.get("model_type", "Invoice"),
        type=payload.get("type", "Text"),
        placeholder=payload.get("placeholder"),
        is_required=payload.get("is_required", False),
        order=payload.get("order"),
        company_id=company.id,
    )
    db.add(cf)
    await db.commit()
    await db.refresh(cf)
    return cf


@router.put("/{field_id}")
async def update_custom_field(
    field_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cf = await db.get(CustomField, field_id)
    if not cf or cf.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found")
    for k, v in payload.items():
        if hasattr(cf, k):
            setattr(cf, k, v)
    await db.commit()
    await db.refresh(cf)
    return cf


@router.delete("/{field_id}")
async def delete_custom_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cf = await db.get(CustomField, field_id)
    if not cf or cf.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found")
    await db.delete(cf)
    await db.commit()
    return {"success": True}