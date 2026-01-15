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

@router.post(
    "/register", 
    response_model=UserResponse, 
    summary="Register a new user",
    description="Creates a new user account with the provided details. Hashes the password before storage."
)
async def register(user: UserCreate, controller: AuthController = Depends(get_auth_controller)):
    """
    Register a new user with the following information:
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **email**: Valid email address (must be unique)
    - **mobile**: Mobile number
    - **city**: User's city
    - **dob**: Date of birth
    - **password**: Strong password
    """
    created_user = await controller.create_user(user)
    return created_user

@router.post(
    "/login", 
    response_model=Token,
    summary="Login for access token",
    description="Authenticate user with email (username) and password to obtain an OAuth2 access token."
)
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
        subject=user.email, 
        expires_delta=access_token_expires,
        extra_claims={
            "id": str(user.id),
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "role": "user" # Example role
        }
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "Bearer"
    }

# Alternative JSON login if preferred strictly over Form
@router.post(
    "/login/json", 
    response_model=Token,
    summary="Login with JSON body",
    description="Alternative login endpoint accepting a JSON body instead of form data."
)
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
        subject=user.email, 
        expires_delta=access_token_expires,
        extra_claims={
            "id": str(user.id),
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "role": "user"
        }
    )
    refresh_token = create_refresh_token(
        subject=user.email
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "Bearer"
    }

@router.post(
    "/refresh", 
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
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
        "token_type": "Bearer"
    }

@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve details of the currently authenticated user."
)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Returns the user object for the authenticated user context.
    Requires a valid Bearer token in the Authorization header.
    """
    return current_user
