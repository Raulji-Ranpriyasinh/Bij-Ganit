"""Item CRUD (Sprint 2.6).

`Items` are company-scoped.  Per-item taxes live in the `taxes` table with
`item_id` set, so creating / updating an item replaces its tax rows in one
transaction to keep the API idempotent.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.item import Item
from app.models.tax import Tax, TaxType
from app.models.user import User
from app.schemas.item import ItemCreate, ItemDeleteRequest, ItemOut, ItemUpdate
from app.schemas.tax import TaxInput

router = APIRouter(prefix="/items", tags=["items"])


async def _replace_taxes(
    db: AsyncSession,
    item: Item,
    company_id: int,
    tax_inputs: list[TaxInput],
) -> None:
    """Clear an item's tax rows and insert the provided ones."""
    await db.execute(delete(Tax).where(Tax.item_id == item.id))
    for payload in tax_inputs:
        tax_type = await db.get(TaxType, payload.tax_type_id)
        if not tax_type or tax_type.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown tax_type_id {payload.tax_type_id}",
            )
        db.add(
            Tax(
                tax_type_id=payload.tax_type_id,
                item_id=item.id,
                name=tax_type.name,
                amount=payload.amount,
                percent=payload.percent,
                compound_tax=payload.compound_tax,
                company_id=company_id,
            )
        )


@router.get("", response_model=list[ItemOut])
async def list_items(
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> list[Item]:
    stmt = select(Item).where(Item.company_id == company.id)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Item.name.ilike(pattern), Item.description.ilike(pattern)))
    result = await db.scalars(stmt.order_by(Item.id.desc()))
    return list(result.all())


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Item:
    item = Item(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        tax_per_item=payload.tax_per_item,
        unit_id=payload.unit_id,
        currency_id=payload.currency_id,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(item)
    await db.flush()
    await _replace_taxes(db, item, company.id, payload.taxes)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> Item:
    item = await db.get(Item, item_id)
    if not item or item.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> Item:
    item = await db.get(Item, item_id)
    if not item or item.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    data = payload.model_dump(exclude_unset=True)
    taxes = data.pop("taxes", None)
    for k, v in data.items():
        setattr(item, k, v)
    if taxes is not None:
        await _replace_taxes(
            db, item, company.id, [TaxInput(**t) for t in taxes]
        )
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/delete")
async def bulk_delete_items(
    payload: ItemDeleteRequest,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided"
        )
    result = await db.scalars(
        select(Item).where(Item.id.in_(payload.ids), Item.company_id == company.id)
    )
    for item in result.all():
        await db.delete(item)
    await db.commit()
    return {"success": True}
