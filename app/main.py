from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db, init_db, User
from app.schemas import UserCreate, UserLogin, UserResponse, Token, GoogleLoginRequest, ForgotPasswordRequest, ResetPasswordRequest, ResetPasswordResponse
from app.auth import get_password_hash, verify_password, create_access_token, decode_access_token, create_reset_password_token, decode_reset_password_token
from app.oauth import oauth_manager, facebook_oauth
from app.email_service import send_reset_password_email, send_password_changed_email
import secrets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    init_db()
    yield


app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

oauth_states = {}


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        provider="local"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token, tags=["Authentication"])
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user with username and password, return JWT token."""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not user.hashed_password or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.get("/auth/google/login", tags=["OAuth - Google"])
async def google_login():
    """Initiate Google OAuth2 flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True
    
    auth_url = await oauth_manager.get_authorization_url("google", state)
    return RedirectResponse(url=auth_url)


@app.get("/auth/google/callback", response_model=Token, tags=["OAuth - Google"])
async def google_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth2 callback (GET).
    Google redirects with query params:
    /auth/google/callback?code=...&state=...
    """

    if state and state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )

    if state:
        del oauth_states[state]

    try:
        user_info = await oauth_manager.get_user_info("google", code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user info from Google: {str(e)}"
        )

    user = db.query(User).filter(
        User.provider_user_id == user_info["provider_user_id"],
        User.provider == user_info["provider"]
    ).first()

    if not user:
        user = User(
            email=user_info["email"],
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            picture_url=user_info.get("picture_url"),
            provider=user_info["provider"],
            provider_user_id=user_info["provider_user_id"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.first_name = user_info.get("first_name")
        user.last_name = user_info.get("last_name")
        user.picture_url = user_info.get("picture_url")
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@app.get("/auth/facebook", tags=["OAuth - Facebook"])
def facebook_login():
    """Redirect to Facebook login page."""
    authorization_url = facebook_oauth.get_authorization_url()
    return RedirectResponse(authorization_url)


@app.get("/auth/facebook/callback", tags=["OAuth - Facebook"])
async def facebook_callback(code: Optional[str] = None, error: Optional[str] = None, db: Session = Depends(get_db)):
    """Handle Facebook OAuth callback."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Facebook authentication failed: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    token_data = await facebook_oauth.get_access_token(code)
    if not token_data or "access_token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from Facebook"
        )
    
    user_info = await facebook_oauth.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Facebook"
        )
    
    facebook_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name", "")
    
    if not facebook_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook ID not provided"
        )
    
    user = db.query(User).filter(User.facebook_id == facebook_id).first()
    
    if not user:
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.facebook_id = facebook_id
                user.provider = "facebook"
                db.commit()
                db.refresh(user)
            else:
                username = email.split("@")[0] if email else f"facebook_{facebook_id}"
                
                existing_user = db.query(User).filter(User.username == username).first()
                if existing_user:
                    username = f"{username}_{facebook_id[:8]}"
                
                user = User(
                    username=username,
                    email=email or f"{facebook_id}@facebook.com",
                    facebook_id=facebook_id,
                    provider="facebook",
                    hashed_password=None  
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        else:
            username = f"facebook_{facebook_id}"
            user = User(
                username=username,
                email=f"{facebook_id}@facebook.com",
                facebook_id=facebook_id,
                provider="facebook",
                hashed_password=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "provider": user.provider
        }
    }


@app.get("/profile", response_model=UserResponse, tags=["User Profile"])
def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Auth Service"}


@app.get("/me", response_model=UserResponse, tags=["User Profile"])
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/", tags=["Health"])
def root():
    """Root endpoint."""
    return {"message": "Auth Service API", "version": "1.0.0"}