from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import secrets
import logging

logger = logging.getLogger(__name__)

# Password hashing context - using argon2 for better compatibility
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    logger.debug(f"🔍 Verifying password")
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"{'✅' if result else '❌'} Password verification: {result}")
    return result


def get_password_hash(password: str) -> str:
    """Hash a password"""
    if not password:
        raise ValueError("Password cannot be empty")
    logger.debug(f"🔐 Hashing password (length: {len(password)})")
    hashed = pwd_context.hash(password)
    logger.debug(f"✅ Password hashed successfully")
    return hashed


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    logger.debug(f"🎫 Creating access token for user: {data.get('sub')}")
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"✅ Access token created (expires: {expire})")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    logger.debug(f"🎫 Creating refresh token for user: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"✅ Refresh token created (expires: {expire})")
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    logger.debug(f"🔍 Decoding JWT token")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug(f"✅ Token decoded successfully")
        return payload
    except JWTError as e:
        logger.warning(f"❌ Token decode failed: {e}")
        return None


def generate_reset_token() -> str:
    """Generate a secure random token for password reset"""
    logger.debug(f"🔑 Generating password reset token")
    token = secrets.token_urlsafe(32)
    logger.debug(f"✅ Reset token generated")
    return token


def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    logger.debug(f"🔑 Generating email verification token")
    token = secrets.token_urlsafe(32)
    logger.debug(f"✅ Verification token generated")
    return token
