from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
from app.database import get_db, init_db, User
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from app.oauth import facebook_oauth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    init_db()
    yield


app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)
security = HTTPBearer()


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


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
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Auth Service API", "version": "1.0.0"}


# Facebook OAuth Endpoints

@app.get("/auth/facebook")
def facebook_login():
    """Redirect to Facebook login page."""
    authorization_url = facebook_oauth.get_authorization_url()
    return RedirectResponse(authorization_url)


@app.get("/auth/facebook/callback")
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
