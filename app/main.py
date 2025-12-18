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


@app.post("/forgot-password", tags=["Password Reset"])
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset. Sends an email with a reset link.
    
    - **email**: User's email address
    
    Returns a generic message for security reasons.
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        return {
            "message": "Se o email existir em nossa base de dados, você receberá um link para redefinir a senha."
        }
    
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário foi registrado via OAuth. Por favor, use o login OAuth correspondente."
        )
    
    reset_token = create_reset_password_token(data={"sub": user.email})
    
    import hashlib
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    
    user.reset_token_hash = token_hash
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    
    email_sent = await send_reset_password_email(user.email, reset_token)
    
    if not email_sent:
        user.reset_token_hash = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao enviar email de redefinição de senha. Tente novamente mais tarde."
        )
    
    return {
        "message": "Se o email existir em nossa base de dados, você receberá um link para redefinir a senha."
    }


@app.post("/reset-password", response_model=ResetPasswordResponse, tags=["Password Reset"])
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset user password using the reset token.
    
    - **token**: JWT token received in email
    - **new_password**: New password for the user
    
    Returns success message if password is reset.
    """
    payload = decode_reset_password_token(request.token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não encontrado"
        )
    
    if not user.reset_token_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma solicitação de redefinição de senha ativa"
        )
    
    import hashlib
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    
    if token_hash != user.reset_token_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )
    
    if user.reset_token_expires < datetime.utcnow():
        user.reset_token_hash = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado"
        )
    
    hashed_password = get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    
    await send_password_changed_email(user.email)
    
    return {
        "message": "Senha redefinida com sucesso. Você pode agora fazer login com sua nova senha."
    }


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


@app.get("/routes", tags=["Documentation"])
def list_routes():
    """
    List all available routes in the API.
    
    Returns a comprehensive documentation of all endpoints.
    """
    return {
        "message": "Auth Service API Routes",
        "version": "1.0.0",
        "routes": {
            "Authentication": [
                {
                    "method": "POST",
                    "path": "/register",
                    "description": "Register a new user",
                    "body": {
                        "username": "string",
                        "email": "string",
                        "password": "string"
                    }
                },
                {
                    "method": "POST",
                    "path": "/login",
                    "description": "Login user with username and password",
                    "body": {
                        "username": "string",
                        "password": "string"
                    }
                }
            ],
            "Password Reset": [
                {
                    "method": "POST",
                    "path": "/forgot-password",
                    "description": "Request password reset. Sends email with reset link",
                    "body": {
                        "email": "string"
                    }
                },
                {
                    "method": "POST",
                    "path": "/reset-password",
                    "description": "Reset password using token from email",
                    "body": {
                        "token": "string (JWT token from email)",
                        "new_password": "string"
                    }
                }
            ],
            "User Profile": [
                {
                    "method": "GET",
                    "path": "/me",
                    "description": "Get current user information",
                    "auth": "Bearer token required"
                },
                {
                    "method": "GET",
                    "path": "/profile",
                    "description": "Get current user profile",
                    "auth": "Bearer token required"
                }
            ],
            "OAuth - Google": [
                {
                    "method": "GET",
                    "path": "/auth/google/login",
                    "description": "Initiate Google OAuth2 flow"
                },
                {
                    "method": "GET",
                    "path": "/auth/google/callback",
                    "description": "Handle Google OAuth2 callback",
                    "params": {
                        "code": "string",
                        "state": "string"
                    }
                }
            ],
            "OAuth - Facebook": [
                {
                    "method": "GET",
                    "path": "/auth/facebook",
                    "description": "Redirect to Facebook login page"
                },
                {
                    "method": "GET",
                    "path": "/auth/facebook/callback",
                    "description": "Handle Facebook OAuth callback",
                    "params": {
                        "code": "string (optional)",
                        "error": "string (optional)"
                    }
                }
            ],
            "Health": [
                {
                    "method": "GET",
                    "path": "/health",
                    "description": "Health check endpoint"
                },
                {
                    "method": "GET",
                    "path": "/",
                    "description": "Root endpoint"
                }
            ]
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }