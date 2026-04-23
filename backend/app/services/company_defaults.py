"""Default data seeded when a new company is created (Sprint 1.9).

The Laravel reference seeds three sets of defaults on company creation:

* Payment methods (Cash, Check, Credit Card, Bank Transfer)
* Units (box, cm, dz, ft, g, in, kg, km, lb, mg, pc)
* 50+ `company_settings` rows (email templates, number formats, date formats,
  currency, language, etc.)

We do NOT yet have tables for those domain entities in this sprint — they
will be introduced in later sprints (4, 6, 12, …).  To keep the interface
stable, this module exposes the data + a `setup_default_data` function that
will loop over these lists and insert them once the target tables exist.
The shape of the data deliberately matches the reference so the next intern
only has to wire it to actual models.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company

DEFAULT_PAYMENT_METHODS: list[str] = ["Cash", "Check", "Credit Card", "Bank Transfer"]

DEFAULT_UNITS: list[str] = [
    "box",
    "cm",
    "dz",
    "ft",
    "g",
    "in",
    "kg",
    "km",
    "lb",
    "mg",
    "pc",
]

# Subset of the 50+ settings from the reference Company model.  Add more as
# the corresponding features land.  Values are strings to match the key/value
# shape of the reference `company_settings` table.
DEFAULT_COMPANY_SETTINGS: dict[str, str] = {
    "invoice_auto_generate": "YES",
    "estimate_auto_generate": "YES",
    "payment_auto_generate": "YES",
    "save_pdf_to_disk": "NO",
    "tax_per_item": "NO",
    "discount_per_item": "NO",
    "retrospective_edits": "allow",
    "invoice_email_attachment": "NO",
    "estimate_email_attachment": "NO",
    "payment_email_attachment": "NO",
    "notify_invoice_viewed": "NO",
    "notify_estimate_viewed": "NO",
    "time_zone": "Asia/Kolkata",
    "language": "en",
    "fiscal_year": "1-12",
    "carbon_date_format": "Y/m/d",
    "moment_date_format": "YYYY/MM/DD",
    "notification_email": "noreply@bijganit.local",
    "invoice_number_format": "{{SERIES:INV}}{{DELIMITER:-}}{{SEQUENCE:6}}",
    "estimate_number_format": "{{SERIES:EST}}{{DELIMITER:-}}{{SEQUENCE:6}}",
    "payment_number_format": "{{SERIES:PAY}}{{DELIMITER:-}}{{SEQUENCE:6}}",
    "expense_number_format": "{{SERIES:EXP}}{{DELIMITER:-}}{{SEQUENCE:6}}",
    "invoice_mail_body": (
        "You have received a new invoice from <b>{COMPANY_NAME}</b>."
        "<br/>Please download using the button below."
    ),
    "estimate_mail_body": (
        "You have received a new estimate from <b>{COMPANY_NAME}</b>."
        "<br/>Please download using the button below."
    ),
    "payment_mail_body": (
        "Thank you for the payment."
        "<br/>Please download your payment receipt using the button below."
    ),
}


async def setup_default_data(db: AsyncSession, company: Company) -> None:
    """Seed a freshly-created company with its defaults.

    In this sprint the target tables (payment_methods, units, company_settings)
    do not exist yet, so this is a safe no-op that later sprints will flesh
    out.  It is still called from the `POST /companies` endpoint so the call
    site is stable and tests can assert it is invoked.
    """
    # Intentional no-op — see docstring.
    _ = (db, company, DEFAULT_PAYMENT_METHODS, DEFAULT_UNITS, DEFAULT_COMPANY_SETTINGS)
