"""Unit CRUD (Sprint 2.6)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.unit import Unit
from app.models.user import User
from app.schemas.unit import UnitCreate, UnitOut, UnitUpdate

router = APIRouter(prefix="/units", tags=["units"])


@router.get("", response_model=list[UnitOut])
async def list_units(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> list[Unit]:
    result = await db.scalars(
        select(Unit).where(Unit.company_id == company.id).order_by(Unit.id)
    )
    return list(result.all())


@router.post("", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> Unit:
    unit = Unit(name=payload.name, company_id=company.id)
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


@router.put("/{unit_id}", response_model=UnitOut)
async def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> Unit:
    unit = await db.get(Unit, unit_id)
    if not unit or unit.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(unit, k, v)
    await db.commit()
    await db.refresh(unit)
    return unit


@router.delete("/{unit_id}")
async def delete_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    unit = await db.get(Unit, unit_id)
    if not unit or unit.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    await db.delete(unit)
    await db.commit()
    return {"success": True}
