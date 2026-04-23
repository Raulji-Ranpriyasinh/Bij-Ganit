"""Customer CRUD (Sprint 2.4).

The reference Laravel controller defined a handful of bulk-tuned behaviours
(whereCompany scope, search filter, bulk delete, per-customer stats).  We
mirror those with idiomatic SQLAlchemy 2.0 async queries.
"""

from datetime import date, datetime, time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.models.address import Address
from app.models.company import Company
from app.models.customer import Customer
from app.models.user import User
from app.schemas.address import AddressInput, AddressOut
from app.schemas.customer import (
    CustomerCreate,
    CustomerDeleteRequest,
    CustomerOut,
    CustomerStats,
    CustomerUpdate,
)

router = APIRouter(prefix="/customers", tags=["customers"])


def _pick_address(customer: Customer, type_: str) -> Address | None:
    return next((a for a in customer.addresses if a.type == type_), None)


def _serialize_customer(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "contact_name": customer.contact_name,
        "company_name": customer.company_name,
        "website": customer.website,
        "enable_portal": customer.enable_portal,
        "currency_id": customer.currency_id,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "billing": (
            AddressOut.model_validate(_pick_address(customer, "billing"))
            if _pick_address(customer, "billing")
            else None
        ),
        "shipping": (
            AddressOut.model_validate(_pick_address(customer, "shipping"))
            if _pick_address(customer, "shipping")
            else None
        ),
    }


def _apply_address(customer: Customer, type_: str, payload: AddressInput | None) -> None:
    existing = _pick_address(customer, type_)
    if payload is None:
        return
    if existing is None:
        customer.addresses.append(
            Address(
                type=type_,
                company_id=customer.company_id,
                **payload.model_dump(),
            )
        )
        return
    for k, v in payload.model_dump().items():
        setattr(existing, k, v)


@router.get("", response_model=list[CustomerOut])
async def list_customers(
    search: str | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from_date"),
    to_date: date | None = Query(default=None, alias="to_date"),
    order_by: Literal["name", "created_at", "id"] = Query(default="id"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> list[dict]:
    stmt = select(Customer).where(Customer.company_id == company.id)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Customer.name.ilike(pattern),
                Customer.contact_name.ilike(pattern),
                Customer.company_name.ilike(pattern),
            )
        )
    if from_date:
        stmt = stmt.where(Customer.created_at >= datetime.combine(from_date, time.min))
    if to_date:
        stmt = stmt.where(Customer.created_at <= datetime.combine(to_date, time.max))

    col = {
        "name": Customer.name,
        "created_at": Customer.created_at,
        "id": Customer.id,
    }[order_by]
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc())

    result = await db.scalars(stmt)
    return [_serialize_customer(c) for c in result.all()]


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> dict:
    customer = Customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        contact_name=payload.contact_name,
        company_name=payload.company_name,
        website=payload.website,
        enable_portal=payload.enable_portal,
        currency_id=payload.currency_id,
        password=hash_password(payload.password) if payload.password else None,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(customer)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
        ) from exc
    _apply_address(customer, "billing", payload.billing)
    _apply_address(customer, "shipping", payload.shipping)
    await db.commit()
    await db.refresh(customer)
    return _serialize_customer(customer)


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict:
    customer = await db.get(Customer, customer_id)
    if not customer or customer.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return _serialize_customer(customer)


@router.put("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict:
    customer = await db.get(Customer, customer_id)
    if not customer or customer.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    data = payload.model_dump(exclude_unset=True)
    billing = data.pop("billing", None)
    shipping = data.pop("shipping", None)
    if "password" in data:
        pw = data.pop("password")
        if pw:
            customer.password = hash_password(pw)
    for k, v in data.items():
        setattr(customer, k, v)
    if billing is not None:
        _apply_address(customer, "billing", AddressInput(**billing))
    if shipping is not None:
        _apply_address(customer, "shipping", AddressInput(**shipping))
    await db.commit()
    await db.refresh(customer)
    return _serialize_customer(customer)


@router.post("/delete")
async def bulk_delete_customers(
    payload: CustomerDeleteRequest,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided"
        )
    result = await db.scalars(
        select(Customer).where(
            Customer.id.in_(payload.ids), Customer.company_id == company.id
        )
    )
    for c in result.all():
        await db.delete(c)
    await db.commit()
    return {"success": True}


@router.get("/{customer_id}/stats", response_model=CustomerStats)
async def customer_stats(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> CustomerStats:
    customer = await db.get(Customer, customer_id)
    if not customer or customer.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    total_customers = await db.scalar(
        select(func.count()).select_from(Customer).where(Customer.company_id == company.id)
    )
    return CustomerStats(
        customer_id=customer.id,
        total_customers=int(total_customers or 0),
    )
