"""Company endpoints (Sprint 1.7).

Routes follow the reference Laravel shape so the frontend can stay familiar:

    POST /api/v1/companies          → create a company
    GET  /api/v1/companies          → list the current user's companies
    POST /api/v1/companies/delete   → bulk delete by ids
"""

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.company import Company, UserCompany
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyDeleteRequest, CompanyOut
from app.services.company_defaults import setup_default_data

router = APIRouter(prefix="/companies", tags=["companies"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "company"


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Company:
    base_slug = payload.slug or _slugify(payload.name)
    slug = base_slug
    suffix = 1
    while await db.scalar(select(Company).where(Company.slug == slug)):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    company = Company(
        name=payload.name,
        slug=slug,
        unique_hash=secrets.token_hex(16),
        owner_id=current_user.id,
    )
    db.add(company)
    await db.flush()
    db.add(UserCompany(user_id=current_user.id, company_id=company.id))
    await setup_default_data(db, company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("", response_model=list[CompanyOut])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Company]:
    result = await db.scalars(
        select(Company)
        .join(UserCompany, UserCompany.company_id == Company.id)
        .where(UserCompany.user_id == current_user.id)
        .order_by(Company.id)
    )
    return list(result.all())


@router.post("/delete")
async def delete_companies(
    payload: CompanyDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not payload.ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided")
    result = await db.scalars(
        select(Company).where(Company.id.in_(payload.ids), Company.owner_id == current_user.id)
    )
    for company in result.all():
        await db.delete(company)
    await db.commit()
    return {"success": True}
