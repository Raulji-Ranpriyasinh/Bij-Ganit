"""Expenses endpoints (Sprint 4).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.finance import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/expenses", tags=["expenses"]) 


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
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
    await db.flush()
    await db.commit()
    await db.refresh(exp)
    return exp


@router.get("")
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    stmt = select(Expense).where(Expense.company_id == company.id)
    res = await db.scalars(stmt)
    return {"items": list(res.all())}


@router.get("/{expense_id}", response_model=ExpenseOut)
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
