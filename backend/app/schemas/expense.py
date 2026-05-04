"""Schemas for Expenses + Expense Categories (Sprint 4).
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ExpenseCategoryCreate(BaseModel):
    name: str
    description: str | None = None


class ExpenseCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    company_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ExpenseCreate(BaseModel):
    expense_date: date | None = None
    amount: int
    notes: str | None = None
    expense_category_id: int | None = None
    payment_method_id: int | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_date: date | None = None
    amount: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime