from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    ForgotPassword,
    ResetPassword,
    GoogleAuthRequest,
    UserResponse
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models.user import User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password
    
    - **full_name**: User's full name
    - **email**: User's email address
    - **password**: User's password (min 8 characters)
    """
    logger.info(f"📝 Registration attempt for email: {user_data.email}")
    logger.info(f"   Full name: {user_data.full_name}")
    try:
        result = AuthService.register_user(user_data, db)
        logger.info(f"✅ Registration successful for: {user_data.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Registration failed for {user_data.email}: {str(e)}")
        raise


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    - **email**: User's email address
    - **password**: User's password
    """
    logger.info(f"🔐 Login attempt for email: {user_data.email}")
    try:
        result = AuthService.login_user(user_data, db)
        logger.info(f"✅ Login successful for: {user_data.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Login failed for {user_data.email}: {str(e)}")
        raise


@router.post("/google", response_model=Token)
async def google_auth(
    auth_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate or register with Google OAuth
    
    - **token**: Google ID token from frontend
    """
    logger.info(f"🔵 Google OAuth authentication attempt")
    try:
        result = AuthService.google_auth(auth_data.token, db)
        logger.info(f"✅ Google OAuth successful")
        return result
    except Exception as e:
        logger.error(f"❌ Google OAuth failed: {str(e)}")
        raise


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPassword,
    db: Session = Depends(get_db)
):
    """
    Request password reset email
    
    - **email**: User's email address
    """
    logger.info(f"🔑 Forgot password request for: {data.email}")
    result = AuthService.forgot_password(data.email, db)
    logger.info(f"✅ Forgot password email sent (if user exists)")
    return result


@router.post("/reset-password")
async def reset_password(
    data: ResetPassword,
    db: Session = Depends(get_db)
):
    """
    Reset password with token from email
    
    - **token**: Reset token from email
    - **new_password**: New password (min 8 characters)
    """
    logger.info(f"🔄 Password reset attempt with token")
    try:
        result = AuthService.reset_password(data.token, data.new_password, db)
        logger.info(f"✅ Password reset successful")
        return result
    except Exception as e:
        logger.error(f"❌ Password reset failed: {str(e)}")
        raise


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify email address with token
    
    - **token**: Verification token from email
    """
    logger.info(f"📧 Email verification attempt")
    try:
        result = AuthService.verify_email(token, db)
        logger.info(f"✅ Email verified successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Email verification failed: {str(e)}")
        raise


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"👤 Get current user info for: {current_user.email}")
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user
    
    Note: Since JWT tokens are stateless, the client must delete the tokens.
    This endpoint confirms the logout action and can be used for logging purposes.
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"🚪 Logout request for: {current_user.email}")
    logger.info(f"✅ User logged out successfully: {current_user.email}")
    
    return {
        "message": "Logged out successfully",
        "user_email": current_user.email
    }
