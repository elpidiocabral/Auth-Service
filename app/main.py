from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from app.database import get_db, init_db, User
from app.schemas import UserCreate, UserLogin, UserResponse, Token, GoogleLoginRequest
from app.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from app.oauth import oauth_manager
import secrets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
security = HTTPBearer()

# Store OAuth states temporarily (in production, use Redis)
oauth_states = {}


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with username and password."""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
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


@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user with username and password, return JWT token."""
    # Find user by username
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not user.hashed_password or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.get("/auth/google/login")
async def google_login():
    """Initiate Google OAuth2 flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True
    
    auth_url = await oauth_manager.get_authorization_url("google", state)
    return RedirectResponse(url=auth_url)


@app.post("/auth/google/callback", response_model=Token)
async def google_callback(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Handle Google OAuth2 callback.
    
    Expected request body:
    {
        "code": "authorization_code_from_google",
        "state": "state_from_google_callback"
    }
    """
    # Verify state
    if request.state and request.state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )
    
    # Remove state from dictionary
    if request.state:
        del oauth_states[request.state]
    
    try:
        # Get user info from Google
        user_info = await oauth_manager.get_user_info("google", request.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user info from Google: {str(e)}"
        )
    
    # Check if user exists
    user = db.query(User).filter(
        User.provider_user_id == user_info["provider_user_id"],
        User.provider == user_info["provider"]
    ).first()
    
    if not user:
        # Create new user if not exists
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
        # Update user info
        user.first_name = user_info.get("first_name")
        user.last_name = user_info.get("last_name")
        user.picture_url = user_info.get("picture_url")
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}


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


@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Auth Service"}


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Auth Service API", "version": "1.0.0"}
