"""Shared FastAPI dependencies (Sprint 1.5/1.8).

* `get_current_user` resolves the bearer token into a concrete `User`.
* `get_current_company` is the multi-tenancy guard used by every tenant-scoped
  route.  It reads `X-Company` from the request headers, verifies the user is
  a member of that company and returns the `Company` object, which routes can
  inject and use to scope their queries (equivalent to the Laravel
  `scopeWhereCompany` pattern).
"""

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.database import get_db
from app.models.company import Company, UserCompany
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = verify_token(token)
    if not claims or "sub" not in claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        user_id = int(claims["sub"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from exc
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_company(
    company_header: str | None = Header(default=None, alias="company"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Company:
    """Validate the `company` request header and return the Company.

    Every tenant-scoped endpoint should `Depends(get_current_company)` and use
    the returned company's id (or the dependency's returned object) to scope
    its queries so tenants cannot see each other's data.
    """
    if not company_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'company' header",
        )
    try:
        company_id = int(company_header)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'company' header",
        ) from exc

    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    membership = await db.scalar(
        select(UserCompany).where(
            UserCompany.user_id == current_user.id,
            UserCompany.company_id == company.id,
        )
    )
    if not membership and company.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this company",
        )
    return company
