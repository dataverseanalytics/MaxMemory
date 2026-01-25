from fastapi import APIRouter, Depends, status, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.profile import ProfileUpdate, ChangePassword, ProfileResponse
from app.services.profile_service import ProfileService
from app.core.dependencies import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"👤 Get profile request for: {current_user.email}")
    return ProfileService.get_profile(current_user)


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    - **full_name**: New full name (optional)
    - **email**: New email address (optional, will require re-verification)
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"✏️ Update profile request for: {current_user.email}")
    try:
        result = ProfileService.update_profile(current_user, profile_data, db)
        logger.info(f"✅ Profile updated successfully for: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Profile update failed for {current_user.email}: {str(e)}")
        raise


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    - **current_password**: Current password
    - **new_password**: New password (min 8 characters)
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"🔐 Change password request for: {current_user.email}")
    try:
        result = ProfileService.change_password(current_user, password_data, db)
        logger.info(f"✅ Password changed successfully for: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Password change failed for {current_user.email}: {str(e)}")
        raise


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account (soft delete - deactivates account)
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"🗑️ Delete account request for: {current_user.email}")
    try:
        result = ProfileService.delete_account(current_user, db)
        logger.info(f"✅ Account deleted successfully for: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Account deletion failed for {current_user.email}: {str(e)}")
        raise


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload user avatar/profile image
    
    - **file**: Image file (JPG, PNG, GIF, WEBP - max 5MB)
    
    Requires: Bearer token in Authorization header
    """
    from fastapi import HTTPException
    from app.utils.file_upload import validate_image_file, save_upload_file
    
    logger.info(f"🖼️ Avatar upload request for: {current_user.email}")
    
    # Validate file
    if not validate_image_file(file):
        logger.error(f"❌ Invalid image file for {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Allowed formats: JPG, PNG, GIF, WEBP"
        )
    
    try:
        # Save file
        avatar_url = await save_upload_file(file, current_user.id)
        
        # Update user profile
        result = await ProfileService.upload_avatar(current_user, avatar_url, db)
        logger.info(f"✅ Avatar uploaded successfully for: {current_user.email}")
        return result
    except ValueError as e:
        logger.error(f"❌ File validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Avatar upload failed for {current_user.email}: {str(e)}")
        raise


@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user avatar/profile image
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"🗑️ Delete avatar request for: {current_user.email}")
    try:
        result = ProfileService.delete_avatar(current_user, db)
        logger.info(f"✅ Avatar deleted successfully for: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Avatar deletion failed for {current_user.email}: {str(e)}")
        raise


@router.get("/account-details")
async def get_account_details(
    current_user: User = Depends(get_current_user)
):
    """
    Get account details
    
    Returns:
    - **member_since**: Account creation date
    - **member_since_formatted**: Formatted as "Month Year" (e.g., "January 2024")
    - **account_status**: "Active" or "Inactive"
    - **total_days**: Total days since account creation
    - **is_verified**: Email verification status
    - **is_google_user**: Whether user signed up with Google
    
    Requires: Bearer token in Authorization header
    """
    logger.info(f"📊 Account details request for: {current_user.email}")
    try:
        result = ProfileService.get_account_details(current_user)
        logger.info(f"✅ Account details retrieved for: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get account details for {current_user.email}: {str(e)}")
        raise
