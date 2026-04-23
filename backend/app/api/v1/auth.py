"""Auth endpoints (Sprint 1.6).

POST /api/v1/auth/login   → email + password -> JWT
POST /api/v1/auth/logout  → stateless, just 200s (client drops the token)
GET  /api/v1/auth/check   → verify the current token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthCheckResponse, LoginRequest, LogoutResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.password or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The provided credentials are incorrect.",
        )
    return TokenResponse(token=create_access_token(subject=user.id))


@router.post("/logout", response_model=LogoutResponse)
async def logout(_: User = Depends(get_current_user)) -> LogoutResponse:
    # Tokens are stateless JWTs; the client simply discards them.  We still
    # require a valid token here so a random POST can't "succeed".
    return LogoutResponse(success=True)


@router.get("/check", response_model=AuthCheckResponse)
async def check(current_user: User = Depends(get_current_user)) -> AuthCheckResponse:
    return AuthCheckResponse(authenticated=True, user_id=current_user.id)
