# app/auth/router.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import settings
from .schemas import UserCreate, User, LoginRequest, Token
from .models import User as UserModel
from .utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_user_by_email
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user