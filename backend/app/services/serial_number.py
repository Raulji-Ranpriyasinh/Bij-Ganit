"""Serial number formatter service (Sprint 3).

Simple parser for format strings like: {{SERIES:INV}}{{DELIMITER:-}}{{SEQUENCE:6}}
This module provides `generate_invoice_number(db, company)` which computes
the next sequence for the company and returns a formatted string and the
numeric sequence.
"""

import re
from typing import Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice


_TOKEN_RE = re.compile(r"\{\{([A-Z]+):?([^}]*)\}\}")


async def generate_invoice_number(db: AsyncSession, company_id: int, fmt: str | None = None) -> Tuple[str, int]:
    """Return (invoice_number, sequence_number).

    fmt: format string; if None use default.
    This implementation is intentionally simple: it selects max(sequence_number)
    for the company and adds one. In a high-concurrency environment a
    dedicated sequences table or DB sequence is recommended.
    """
    if not fmt:
        fmt = "{{SERIES:INV}}{{DELIMITER:-}}{{SEQUENCE:6}}"

    # compute next sequence atomically-ish by reading max + 1
    stmt = select(func.coalesce(func.max(Invoice.sequence_number), 0)).where(Invoice.company_id == company_id)
    result = await db.scalar(stmt)
    next_seq = int(result) + 1

    # parse tokens
    tokens = {m.group(1): m.group(2) for m in _TOKEN_RE.finditer(fmt)}
    series = tokens.get("SERIES", "")
    delimiter = tokens.get("DELIMITER", "")
    seq_spec = tokens.get("SEQUENCE", "0")
    try:
        width = int(seq_spec)
    except Exception:
        width = 0

    seq_str = str(next_seq).zfill(width) if width > 0 else str(next_seq)
    parts = []
    if series:
        parts.append(series)
    if delimiter:
        parts.append(delimiter)
    parts.append(seq_str)
    invoice_number = "".join(parts)
    return invoice_number, next_seq
