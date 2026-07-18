"""
Auth API router — register and login.

Endpoints:
  POST /api/v1/auth/register
  POST /api/v1/auth/login
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.core.database import get_db
from app.models.auth import LoginRequest, RegisterRequest, TokenResponse
from app.models.database import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates an Inspector or QA Manager account and returns a JWT access token.",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user and return an access token."""
    if body.role not in ("INSPECTOR", "QA_MANAGER"):
        raise HTTPException(status_code=400, detail="Role must be INSPECTOR or QA_MANAGER.")

    existing = db.query(User).filter(
        (User.username == body.username) | (User.email == body.email)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already registered.")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(username=user.username, role=user.role)
    logger.info("New user registered: %s (%s)", user.username, user.role)

    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
        expires_in=int(settings.JWT_EXPIRE_MINUTES) * 60,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
    description="Authenticate with username and password to receive a Bearer JWT token.",
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return a JWT access token."""
    user = db.query(User).filter_by(username=body.username).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token(username=user.username, role=user.role)
    logger.info("User logged in: %s (%s)", user.username, user.role)

    return TokenResponse(
        access_token=token,
        username=user.username,
        role=user.role,
        expires_in=int(settings.JWT_EXPIRE_MINUTES) * 60,
    )
