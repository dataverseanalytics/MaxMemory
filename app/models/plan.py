from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.database import Base

class Plan(Base):
    """
    Subscription Plan model.
    """
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    credits = Column(Float, nullable=False, default=0.0) # Monthly credits
    features = Column(JSON, nullable=True) # List of features
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Plan {self.name}>"
