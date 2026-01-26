from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.profile import ProfileUpdate, ChangePassword
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
import logging

logger = logging.getLogger(__name__)


class ProfileService:
    """Service class for user profile operations"""
    
    @staticmethod
    def get_profile(user: User) -> User:
        """Get user profile"""
        logger.info(f"📋 Fetching profile for: {user.email}")
        return user
    
    @staticmethod
    def update_profile(user: User, profile_data: ProfileUpdate, db: Session) -> User:
        """Update user profile"""
        logger.info(f"✏️ Updating profile for: {user.email}")
        
        # Update full name if provided
        if profile_data.full_name is not None:
            logger.info(f"📝 Updating full name: {profile_data.full_name}")
            user.full_name = profile_data.full_name
        
        # Update email if provided
        if profile_data.email is not None:
            logger.info(f"📧 Checking if new email is available: {profile_data.email}")
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == profile_data.email,
                User.id != user.id
            ).first()
            
            if existing_user:
                logger.warning(f"⚠️  Email already taken: {profile_data.email}")
                raise UserAlreadyExistsException()
            
            logger.info(f"📧 Updating email from {user.email} to {profile_data.email}")
            user.email = profile_data.email
            # Mark email as unverified when changed
            user.is_verified = False
        
        logger.info(f"💾 Saving profile changes to database")
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Profile updated successfully for: {user.email}")
        
        return user
    
    @staticmethod
    def change_password(user: User, password_data: ChangePassword, db: Session) -> dict:
        """Change user password"""
        logger.info(f"🔐 Password change request for: {user.email}")
        
        # Check if user is a Google user
        if user.is_google_user:
            logger.warning(f"⚠️  Cannot change password for Google user: {user.email}")
            raise InvalidCredentialsException()
        
        # Verify current password
        logger.info(f"🔍 Verifying current password")
        if not verify_password(password_data.current_password, user.hashed_password):
            logger.warning(f"⚠️  Invalid current password for: {user.email}")
            raise InvalidCredentialsException()
        
        logger.info(f"✅ Current password verified")
        
        # Hash and update new password
        logger.info(f"🔐 Hashing new password")
        user.hashed_password = get_password_hash(password_data.new_password)
        
        logger.info(f"💾 Saving new password to database")
        db.commit()
        logger.info(f"✅ Password changed successfully for: {user.email}")
        
        return {"message": "Password changed successfully"}
    
    @staticmethod
    def delete_account(user: User, db: Session) -> dict:
        """Delete user account (Permanent delete)"""
        logger.info(f"🗑️ Permanent account deletion request for: {user.email}")
        
        # Import models to delete dependencies
        from app.models.project import Project
        from app.models.chat import Conversation, Message
        from app.models.credit import CreditTransaction
        
        # 1. Delete Credit Transactions
        db.query(CreditTransaction).filter(CreditTransaction.user_id == user.id).delete()
        
        # 2. Get user conversations to delete messages
        user_conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
        conversation_ids = [c.id for c in user_conversations]
        
        if conversation_ids:
            # Delete messages in those conversations
            db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
            # Delete conversations
            db.query(Conversation).filter(Conversation.id.in_(conversation_ids)).delete(synchronize_session=False)
            
        # 3. Delete Projects
        db.query(Project).filter(Project.user_id == user.id).delete()
        
        # 4. Delete Avatar file if exists
        if user.avatar_url:
            from app.utils.file_upload import delete_avatar_file
            try:
                delete_avatar_file(user.avatar_url)
            except Exception as e:
                logger.error(f"Failed to delete avatar file: {e}")

        # 5. Delete User
        db.delete(user)
        
        logger.info(f"💾 Committing deletion to database")
        db.commit()
        logger.info(f"✅ Account permanently deleted: {user.email}")
        
        return {"message": "Account permanently deleted"}
    
    @staticmethod
    async def upload_avatar(user: User, avatar_url: str, db: Session) -> User:
        """Update user avatar URL"""
        logger.info(f"🖼️ Updating avatar for: {user.email}")
        
        # Delete old avatar file if exists
        if user.avatar_url:
            from app.utils.file_upload import delete_avatar_file
            delete_avatar_file(user.avatar_url)
        
        # Update avatar URL
        user.avatar_url = avatar_url
        
        logger.info(f"💾 Saving avatar URL to database")
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Avatar updated successfully for: {user.email}")
        
        return user
    
    @staticmethod
    def delete_avatar(user: User, db: Session) -> dict:
        """Delete user avatar"""
        logger.info(f"🗑️ Deleting avatar for: {user.email}")
        
        if not user.avatar_url:
            logger.warning(f"⚠️  No avatar to delete for: {user.email}")
            return {"message": "No avatar to delete"}
        
        # Delete avatar file
        from app.utils.file_upload import delete_avatar_file
        delete_avatar_file(user.avatar_url)
        
        # Remove avatar URL from database
        user.avatar_url = None
        
        logger.info(f"💾 Removing avatar URL from database")
        db.commit()
        logger.info(f"✅ Avatar deleted successfully for: {user.email}")
        
        return {"message": "Avatar deleted successfully"}
    
    @staticmethod
    def get_account_details(user: User) -> dict:
        """Get account details including member since and status"""
        from datetime import datetime
        
        logger.info(f"📊 Fetching account details for: {user.email}")
        
        # Calculate days since account creation
        days_since_creation = (datetime.utcnow() - user.created_at).days
        
        # Format member since date
        member_since = user.created_at.strftime("%B %Y")  # e.g., "January 2024"
        
        # Determine account status
        account_status = "Active" if user.is_active else "Inactive"
        
        logger.info(f"✅ Account details retrieved for: {user.email}")
        
        return {
            "member_since": user.created_at,
            "member_since_formatted": member_since,
            "account_status": account_status,
            "total_days": days_since_creation,
            "is_verified": user.is_verified,
            "is_google_user": user.is_google_user
        }
