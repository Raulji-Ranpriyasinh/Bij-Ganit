"""Dashboard endpoint (Sprint 5).
"""

from datetime import datetime
from calendar import monthrange
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.finance import Expense
from app.models.finance import Payment
from app.models.customer import Customer
from app.models.recurring import RecurringInvoice
from app.models.custom_field import CustomField
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _month_start_year(month_index: int, year_start_month: int, year: int) -> tuple[int, int]:
    # month_index 0..11 -> month number adjusted by fiscal start
    month = ((year_start_month - 1) + month_index) % 12 + 1
    year_offset = ((year_start_month - 1) + month_index) // 12
    return year + year_offset, month


@router.get("")
async def get_dashboard(
    previous_year: bool | None = Query(default=False),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
):
    # fiscal year start read from company settings; default Jan
    # For now read from company_defaults constant via settings in service; default month=1
    fiscal_start_month = 1
    now = datetime.utcnow()
    year = now.year - 1 if previous_year else now.year

    months = []
    invoice_totals = []
    expense_totals = []
    receipt_totals = []
    net_income = []

    for i in range(12):
        y, m = _month_start_year(i, fiscal_start_month, year)
        months.append(f"{y}-{m:02d}")
        # invoices base_total per month
        inv_stmt = select(func.coalesce(func.sum(Invoice.base_total), 0)).where(
            Invoice.company_id == company.id,
            extract("year", Invoice.created_at) == y,
            extract("month", Invoice.created_at) == m,
        )
        inv_total = int(await db.scalar(inv_stmt) or 0)
        invoice_totals.append(inv_total)

        exp_stmt = select(func.coalesce(func.sum(Expense.base_amount), 0)).where(
            Expense.company_id == company.id,
            extract("year", Expense.created_at) == y,
            extract("month", Expense.created_at) == m,
        )
        exp_total = int(await db.scalar(exp_stmt) or 0)
        expense_totals.append(exp_total)

        pay_stmt = select(func.coalesce(func.sum(Payment.base_amount), 0)).where(
            Payment.company_id == company.id,
            extract("year", Payment.created_at) == y,
            extract("month", Payment.created_at) == m,
        )
        pay_total = int(await db.scalar(pay_stmt) or 0)
        receipt_totals.append(pay_total)

        net_income.append(pay_total - exp_total)

    total_sales = sum(invoice_totals)
    total_receipts = sum(receipt_totals)
    total_expenses = sum(expense_totals)
    total_net = total_receipts - total_expenses

    total_customers = int(await db.scalar(select(func.count()).select_from(Customer).where(Customer.company_id == company.id)) or 0)
    total_invoices = int(await db.scalar(select(func.count()).select_from(Invoice).where(Invoice.company_id == company.id)) or 0)
    total_estimates = int(await db.scalar(select(func.count()).select_from(RecurringInvoice).where(RecurringInvoice.company_id == company.id)) or 0)

    # amount due
    amount_due = int(await db.scalar(select(func.coalesce(func.sum(Invoice.due_amount), 0)).where(Invoice.company_id == company.id)) or 0)

    # recent due invoices
    recent_due_stmt = select(Invoice).where(Invoice.company_id == company.id, Invoice.due_amount > 0).order_by(Invoice.created_at.desc()).limit(5)
    recent_due = (await db.scalars(recent_due_stmt)).all()

    # recent estimates (represented here by recurring invoices placeholder)
    recent_est_stmt = select(RecurringInvoice).where(RecurringInvoice.company_id == company.id).order_by(RecurringInvoice.created_at.desc()).limit(5)
    recent_est = (await db.scalars(recent_est_stmt)).all()

    return {
        "chart": {
            "months": months,
            "invoice_totals": invoice_totals,
            "expense_totals": expense_totals,
            "receipt_totals": receipt_totals,
            "net_income": net_income,
        },
        "summary": {
            "total_sales": total_sales,
            "total_receipts": total_receipts,
            "total_expenses": total_expenses,
            "total_net_income": total_net,
            "total_customer_count": total_customers,
            "total_invoice_count": total_invoices,
            "total_estimate_count": total_estimates,
            "total_amount_due": amount_due,
        },
        "recent_due_invoices": recent_due,
        "recent_estimates": recent_est,
    }
