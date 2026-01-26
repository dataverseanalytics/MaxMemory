from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base

class CreditTransaction(Base):
    """Represents a credit transaction (usage or purchase)"""
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False) # Negative for deduction, positive for addition
    transaction_type = Column(String, nullable=False) # 'USAGE', 'PURCHASE', 'BONUS'
    description = Column(String, nullable=True)
    
    # Metadata for usage stats (token counts etc)
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Transaction {self.id}: {self.amount} ({self.transaction_type})>"
