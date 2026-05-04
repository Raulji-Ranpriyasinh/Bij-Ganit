"""Expenses + Expense Categories endpoints (Sprint 4).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.finance import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseCategoryCreate, ExpenseCategoryOut

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ── Expense Categories ────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[ExpenseCategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    res = await db.scalars(select(ExpenseCategory).where(ExpenseCategory.company_id == company.id))
    return list(res.all())


@router.post("/categories", response_model=ExpenseCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = ExpenseCategory(name=payload.name, description=payload.description, company_id=company.id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/categories/{category_id}", response_model=ExpenseCategoryOut)
async def update_category(
    category_id: int,
    payload: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = await db.get(ExpenseCategory, category_id)
    if not cat or cat.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    cat.name = payload.name
    cat.description = payload.description
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = await db.get(ExpenseCategory, category_id)
    if not cat or cat.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await db.delete(cat)
    await db.commit()
    return {"success": True}


# ── Expenses ──────────────────────────────────────────────────────────────────

@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Expense:
    exp = Expense(
        expense_date=payload.expense_date,
        amount=payload.amount,
        notes=payload.notes,
        expense_category_id=payload.expense_category_id,
        payment_method_id=payload.payment_method_id,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


@router.get("/expenses")
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    res = await db.scalars(select(Expense).where(Expense.company_id == company.id))
    return {"items": list(res.all())}


@router.get("/expenses/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    e = await db.get(Expense, expense_id)
    if not e or e.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return e

    categories_router = APIRouter(prefix="/categories", tags=["expense-categories"])


@categories_router.get("", )
async def list_categories(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    res = await db.scalars(select(ExpenseCategory).where(ExpenseCategory.company_id == company.id))
    return list(res.all())


@categories_router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = ExpenseCategory(
        name=payload["name"],
        description=payload.get("description"),
        company_id=company.id,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@categories_router.put("/{category_id}")
async def update_category(
    category_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = await db.get(ExpenseCategory, category_id)
    if not cat or cat.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    cat.name = payload.get("name", cat.name)
    cat.description = payload.get("description", cat.description)
    await db.commit()
    await db.refresh(cat)
    return cat


@categories_router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    cat = await db.get(ExpenseCategory, category_id)
    if not cat or cat.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await db.delete(cat)
    await db.commit()
    return {"success": True}