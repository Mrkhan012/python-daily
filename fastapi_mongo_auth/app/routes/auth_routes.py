from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.connection import get_database
from app.controllers.auth_controller import AuthController
from app.models.user import UserCreate, UserResponse, UserLogin, UserInDB
from app.models.token import Token
from app.core.security import create_access_token, create_refresh_token
from app.core.deps import get_current_user
from app.core.config import settings
from jose import jwt, JWTError
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_controller(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthController:
    return AuthController(db)

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, controller: AuthController = Depends(get_auth_controller)):
    created_user = await controller.create_user(user)
    return created_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), controller: AuthController = Depends(get_auth_controller)):
    # Note: OAuth2PasswordRequestForm expects username, so we map email to it if needed or use custom body
    # Standard OAuth2 uses 'username' and 'password' form fields.
    # The user asked for "login with password in sign with passwrd alo do".
    # We will assume they might want a JSON body (UserLogin) or Form. 
    # Usually standard /token endpoint uses Form. But let's support a JSON endpoint too or just use the Form for swagger UI compatibility.
    # I will stick to OAuth2PasswordRequestForm for Swagger UI support, treating 'username' as 'email'.
    
    user = await controller.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

# Alternative JSON login if preferred strictly over Form
@router.post("/login/json", response_model=Token)
async def login_json(user_login: UserLogin, controller: AuthController = Depends(get_auth_controller)):
    user = await controller.authenticate_user(user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        email: str = payload.get("sub")
        if email is None:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=email, expires_delta=access_token_expires
    )
    # Optionally rotate refresh token
    new_refresh_token = create_refresh_token(subject=email)

    return {
        "access_token": access_token, 
        "refresh_token": new_refresh_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user
