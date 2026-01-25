from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    generate_reset_token,
    generate_verification_token
)
from app.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
    InvalidTokenException,
    GoogleAuthException
)
from app.utils.email import send_password_reset_email, send_verification_email
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def register_user(user_data: UserCreate, db: Session) -> Token:
        """Register a new user with email and password"""
        
        logger.info(f"🔍 Checking if user already exists: {user_data.email}")
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"⚠️  User already exists: {user_data.email}")
            raise UserAlreadyExistsException()
        
        logger.info(f"✨ Creating new user account")
        # Create new user
        logger.info(f"🔑 Generating verification token")
        verification_token = generate_verification_token()
        
        logger.info(f"🔐 Hashing password")
        hashed_password = get_password_hash(user_data.password)
        logger.info(f"✅ Password hashed successfully")
        
        logger.info(f"💾 Creating user object")
        new_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            hashed_password=hashed_password,
            is_google_user=False,
            verification_token=verification_token
        )
        
        logger.info(f"💾 Saving user to database")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"✅ User saved with ID: {new_user.id}")
        
        # Send verification email (non-blocking)
        logger.info(f"📧 Attempting to send verification email")
        try:
            send_verification_email(new_user.email, verification_token, new_user.full_name)
            logger.info(f"✅ Verification email sent successfully")
        except Exception as e:
            logger.warning(f"⚠️  Failed to send verification email: {e}")
        
        # Generate tokens
        logger.info(f"🎫 Generating JWT tokens")
        access_token = create_access_token(
            data={"sub": new_user.email, "user_id": new_user.id}
        )
        refresh_token = create_refresh_token(
            data={"sub": new_user.email, "user_id": new_user.id}
        )
        logger.info(f"✅ Tokens generated successfully")
        
        logger.info(f"🎉 Registration complete for: {user_data.email}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_orm(new_user)
        )
    
    @staticmethod
    def login_user(user_data: UserLogin, db: Session) -> Token:
        """Login user with email and password"""
        
        logger.info(f"🔍 Looking up user: {user_data.email}")
        # Find user
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user:
            logger.warning(f"⚠️  User not found: {user_data.email}")
            raise InvalidCredentialsException()
        
        logger.info(f"✅ User found: {user_data.email}")
        
        # Check if user registered with Google
        if user.is_google_user:
            logger.warning(f"⚠️  User registered with Google: {user_data.email}")
            raise InvalidCredentialsException()
        
        # Verify password
        logger.info(f"🔐 Verifying password")
        if not verify_password(user_data.password, user.hashed_password):
            logger.warning(f"⚠️  Invalid password for: {user_data.email}")
            raise InvalidCredentialsException()
        
        logger.info(f"✅ Password verified")
        
        # Generate tokens
        logger.info(f"🎫 Generating JWT tokens")
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        )
        logger.info(f"✅ Tokens generated successfully")
        
        logger.info(f"🎉 Login complete for: {user_data.email}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_orm(user)
        )
    
    @staticmethod
    def google_auth(google_token: str, db: Session) -> Token:
        """Authenticate or register user with Google OAuth"""
        
        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                google_token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            # Extract user info
            google_id = idinfo['sub']
            email = idinfo['email']
            full_name = idinfo.get('name', email.split('@')[0])
            
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # User exists - update Google info if needed
                if not user.is_google_user:
                    user.is_google_user = True
                    user.google_id = google_id
                    db.commit()
                    db.refresh(user)
            else:
                # Create new user
                user = User(
                    full_name=full_name,
                    email=email,
                    is_google_user=True,
                    google_id=google_id,
                    is_verified=True  # Google users are auto-verified
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Generate tokens
            access_token = create_access_token(
                data={"sub": user.email, "user_id": user.id}
            )
            refresh_token = create_refresh_token(
                data={"sub": user.email, "user_id": user.id}
            )
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                user=UserResponse.from_orm(user)
            )
            
        except ValueError as e:
            raise GoogleAuthException(f"Invalid Google token: {str(e)}")
        except Exception as e:
            raise GoogleAuthException(f"Google authentication failed: {str(e)}")
    
    @staticmethod
    def forgot_password(email: str, db: Session) -> dict:
        """Initiate password reset process"""
        
        logger.info(f"🔍 Looking up user for password reset: {email}")
        # Find user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning(f"⚠️  User not found: {email}")
            # Don't reveal if user exists or not for security
            return {"message": "If the email exists, a reset link has been sent"}
        
        logger.info(f"✅ User found: {email}")
        
        # Don't allow password reset for Google users
        if user.is_google_user:
            logger.warning(f"⚠️  User is Google user, cannot reset password: {email}")
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        logger.info(f"🔑 Generating password reset token")
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        logger.info(f"💾 Saving reset token to database")
        db.commit()
        logger.info(f"✅ Reset token saved")
        
        # Send reset email (non-blocking)
        logger.info(f"📧 Attempting to send password reset email")
        try:
            send_password_reset_email(user.email, reset_token, user.full_name)
            logger.info(f"✅ Password reset email sent")
        except Exception as e:
            logger.warning(f"⚠️  Failed to send password reset email: {e}")
        
        return {"message": "If the email exists, a reset link has been sent"}
    
    @staticmethod
    def reset_password(token: str, new_password: str, db: Session) -> dict:
        """Reset user password with token"""
        
        logger.info(f"🔍 Looking up user with reset token")
        # Find user with valid reset token
        user = db.query(User).filter(
            User.reset_token == token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            logger.warning(f"⚠️  Invalid or expired reset token")
            raise InvalidTokenException()
        
        logger.info(f"✅ Valid reset token found for: {user.email}")
        
        # Update password
        logger.info(f"🔐 Hashing new password")
        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        logger.info(f"💾 Saving new password to database")
        db.commit()
        logger.info(f"✅ Password reset successful for: {user.email}")
        
        return {"message": "Password reset successful"}
    
    @staticmethod
    def verify_email(token: str, db: Session) -> dict:
        """Verify user email with token"""
        
        logger.info(f"🔍 Looking up user with verification token")
        # Find user with verification token
        user = db.query(User).filter(User.verification_token == token).first()
        
        if not user:
            logger.warning(f"⚠️  Invalid verification token")
            raise InvalidTokenException()
        
        logger.info(f"✅ Valid verification token found for: {user.email}")
        
        # Mark as verified
        logger.info(f"✅ Marking email as verified")
        user.is_verified = True
        user.verification_token = None
        
        logger.info(f"💾 Saving verification status to database")
        db.commit()
        logger.info(f"🎉 Email verified successfully for: {user.email}")
        
        return {"message": "Email verified successfully"}
