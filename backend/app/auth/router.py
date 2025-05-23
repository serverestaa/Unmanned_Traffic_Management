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
from ..utils.logger import setup_logger

logger = setup_logger("utm.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(db, user.email)
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        logger.info(f"Creating new user: {user.email}")
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
        logger.info(f"User created successfully: {user.email}")
        return db_user
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}", exc_info=True)
        raise


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Login attempt for user: {login_data.email}")
        user = await authenticate_user(db, login_data.email, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}
        )
        logger.info(f"Successful login for user: {login_data.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        raise


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    try:
        logger.debug(f"User info requested for: {current_user.email}")
        return current_user
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}", exc_info=True)
        raise