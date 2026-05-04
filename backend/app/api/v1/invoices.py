"""Invoice create endpoint (Sprint 3).

Implements POST /invoices to create an invoice with items and taxes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_company, get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.invoice import Invoice, InvoiceItem
from app.models.tax import Tax, TaxType
from app.models.customer import Customer
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceItemInput, InvoiceItemOut
from app.schemas.tax import TaxInput
from app.services.serial_number import generate_invoice_number
from app.core.hashids import encode_id

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    # minimal validations
    invoice = Invoice(
        customer_id=payload.customer_id,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(invoice)
    await db.flush()

    # generate sequence + invoice_number
    invoice_number, seq = await generate_invoice_number(db, company.id)
    invoice.invoice_number = invoice_number
    invoice.sequence_number = seq

    # items
    sub_total = 0
    for item_payload in payload.items:
        ii = InvoiceItem(
            name=item_payload.name,
            description=item_payload.description,
            price=item_payload.price,
            quantity=item_payload.quantity,
            discount=item_payload.discount,
            discount_val=item_payload.discount_val,
            company_id=company.id,
            invoice_id=invoice.id,
            item_id=item_payload.item_id,
            unit_name=item_payload.unit_name,
        )
        # simple totals
        line_total = (ii.price * ii.quantity) - ii.discount_val
        ii.total = line_total
        ii.base_price = ii.price
        ii.base_total = ii.total
        sub_total += ii.total
        db.add(ii)
        await db.flush()
        # taxes per line
        for tax_payload in item_payload.taxes:
            tax_type = await db.get(TaxType, tax_payload.tax_type_id)
            if not tax_type or tax_type.company_id != company.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tax_type_id {tax_payload.tax_type_id}")
            db.add(
                Tax(
                    name=tax_type.name,
                    amount=tax_payload.amount,
                    percent=tax_payload.percent,
                    compound_tax=tax_payload.compound_tax,
                    tax_type_id=tax_payload.tax_type_id,
                    item_id=ii.id,
                    company_id=company.id,
                    invoice_id=invoice.id,
                )
            )

    invoice.sub_total = sub_total
    invoice.total = sub_total + payload.discount
    invoice.due_amount = invoice.total

    # invoice-level taxes
    for t in payload.taxes:
        tax_type = await db.get(TaxType, t.tax_type_id)
        if not tax_type or tax_type.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tax_type_id {t.tax_type_id}")
        db.add(
            Tax(
                name=tax_type.name,
                amount=t.amount,
                percent=t.percent,
                compound_tax=t.compound_tax,
                tax_type_id=t.tax_type_id,
                invoice_id=invoice.id,
                company_id=company.id,
            )
        )

    # compute unique_hash
    await db.flush()
    invoice.unique_hash = encode_id("invoice", invoice.id)
    await db.commit()
    await db.refresh(invoice)
    return invoice

@router.get("/templates")
async def invoice_templates() -> list[dict]:
    # static list for now
    return [
        {"name": "default", "preview": "/static/templates/default.png"},
        {"name": "modern", "preview": "/static/templates/modern.png"},
    ]

@router.put("/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: int,
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    # payments existence guard: if invoice has payments (not implemented) disallow customer change
    paid_amount = (invoice.total or 0) - (invoice.due_amount or 0)
    if payload.customer_id and payload.customer_id != invoice.customer_id and paid_amount > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change customer when payments exist")

    # remove old items and taxes
    await db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id))
    await db.execute(delete(Tax).where(Tax.invoice_id == invoice.id))

    # update some fields
    invoice.customer_id = payload.customer_id
    invoice.invoice_date = payload.invoice_date
    invoice.due_date = payload.due_date

    # recreate items
    sub_total = 0
    for item_payload in payload.items:
        ii = InvoiceItem(
            name=item_payload.name,
            description=item_payload.description,
            price=item_payload.price,
            quantity=item_payload.quantity,
            discount=item_payload.discount,
            discount_val=item_payload.discount_val,
            company_id=company.id,
            invoice_id=invoice.id,
            item_id=item_payload.item_id,
            unit_name=item_payload.unit_name,
        )
        line_total = (ii.price * ii.quantity) - ii.discount_val
        ii.total = line_total
        ii.base_price = ii.price
        ii.base_total = ii.total
        sub_total += ii.total
        db.add(ii)
        await db.flush()
        for tax_payload in item_payload.taxes:
            tax_type = await db.get(TaxType, tax_payload.tax_type_id)
            if not tax_type or tax_type.company_id != company.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tax_type_id {tax_payload.tax_type_id}")
            db.add(
                Tax(
                    name=tax_type.name,
                    amount=tax_payload.amount,
                    percent=tax_payload.percent,
                    compound_tax=tax_payload.compound_tax,
                    tax_type_id=tax_payload.tax_type_id,
                    item_id=ii.id,
                    company_id=company.id,
                    invoice_id=invoice.id,
                )
            )

    invoice.sub_total = sub_total
    invoice.total = sub_total + payload.discount

    # recreate invoice-level taxes
    for t in payload.taxes:
        tax_type = await db.get(TaxType, t.tax_type_id)
        if not tax_type or tax_type.company_id != company.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tax_type_id {t.tax_type_id}")
        db.add(
            Tax(
                name=tax_type.name,
                amount=t.amount,
                percent=t.percent,
                compound_tax=t.compound_tax,
                tax_type_id=t.tax_type_id,
                invoice_id=invoice.id,
                company_id=company.id,
            )
        )

    # recalc due_amount and paid_status
    paid_amount = paid_amount
    invoice.due_amount = max(0, invoice.total - paid_amount)
    if paid_amount >= invoice.total and invoice.total > 0:
        invoice.paid_status = "PAID"
    elif paid_amount > 0:
        invoice.paid_status = "PARTIALLY_PAID"
    else:
        invoice.paid_status = "UNPAID"

    await db.commit()
    await db.refresh(invoice)
    return invoice



@router.get("")
async def list_invoices(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    paid_status: str | None = Query(default=None),
    invoice_number: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    order_by: str | None = Query(default="id"),
    order_dir: str | None = Query(default="desc"),
    page: int = Query(default=1),
    per_page: int = Query(default=25),
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> list[Invoice]:
    stmt = select(Invoice).where(Invoice.company_id == company.id)
    if search:
        # join customers
        stmt = stmt.join(Customer).where(Customer.name.ilike(f"%{search}%"))
    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
    if paid_status:
        stmt = stmt.where(Invoice.paid_status == paid_status)
    if invoice_number:
        stmt = stmt.where(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    if from_date:
        stmt = stmt.where(Invoice.invoice_date >= from_date)
    if to_date:
        stmt = stmt.where(Invoice.invoice_date <= to_date)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    # ordering
    order_col = getattr(Invoice, order_by, Invoice.id)
    if order_dir and order_dir.lower() == "desc":
        stmt = stmt.order_by(order_col.desc())
    else:
        stmt = stmt.order_by(order_col.asc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)
    result = await db.scalars(stmt)
    items = list(result.all())
    return {"items": items, "meta": {"total": int(total or 0), "page": page, "per_page": per_page}}



@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> Invoice:
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice



@router.post("/delete")
async def bulk_delete_invoices(
    ids: list[int],
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No ids provided")
    await db.execute(delete(Tax).where(Tax.invoice_id.in_(ids)))
    await db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id.in_(ids)))
    await db.execute(delete(Invoice).where(Invoice.id.in_(ids), Invoice.company_id == company.id))
    await db.commit()
    return {"success": True}



@router.post("/{invoice_id}/status")
async def change_invoice_status(
    invoice_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: User = Depends(get_current_user),
) -> dict[str, bool]:
    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status required")
    invoice.status = new_status
    if new_status.upper() == "SENT":
        invoice.sent = True
    await db.commit()
    return {"success": True}



@router.post("/{invoice_id}/clone", response_model=InvoiceOut)
async def clone_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    company: Company = Depends(get_current_company),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    src = await db.get(Invoice, invoice_id)
    if not src or src.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    # create new invoice
    new = Invoice(
        invoice_date=src.invoice_date,
        due_date=src.due_date,
        reference_number=src.reference_number,
        status="DRAFT",
        paid_status="UNPAID",
        tax_per_item=src.tax_per_item,
        discount_per_item=src.discount_per_item,
        notes=src.notes,
        discount=src.discount,
        discount_val=src.discount_val,
        sub_total=src.sub_total,
        total=src.total,
        tax=src.tax,
        due_amount=src.total,
        template_name=src.template_name,
        company_id=company.id,
        creator_id=current_user.id,
    )
    db.add(new)
    await db.flush()
    invoice_number, seq = await generate_invoice_number(db, company.id)
    new.invoice_number = invoice_number
    new.sequence_number = seq
    # clone items
    for it in src.items:
        ni = InvoiceItem(
            name=it.name,
            description=it.description,
            price=it.price,
            quantity=it.quantity,
            discount=it.discount,
            discount_val=it.discount_val,
            tax=it.tax,
            total=it.total,
            unit_name=it.unit_name,
            base_price=it.base_price,
            base_total=it.base_total,
            company_id=company.id,
            invoice_id=new.id,
            item_id=it.item_id,
        )
        db.add(ni)
    # clone taxes
    taxes = await db.scalars(select(Tax).where(Tax.invoice_id == src.id))
    for t in taxes.all():
        db.add(
            Tax(
                name=t.name,
                amount=t.amount,
                percent=t.percent,
                compound_tax=t.compound_tax,
                tax_type_id=t.tax_type_id,
                invoice_id=new.id,
                company_id=company.id,
            )
        )
    await db.flush()
    new.unique_hash = encode_id("invoice", new.id)
    await db.commit()
    await db.refresh(new)
    return new

