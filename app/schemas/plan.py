from pydantic import BaseModel
from typing import List, Optional

class PlanBase(BaseModel):
    name: str
    price: float
    credits: float
    features: Optional[List[str]] = []
    is_active: bool = True

class PlanCreate(PlanBase):
    pass

class PlanUpdate(PlanBase):
    name: Optional[str] = None
    price: Optional[float] = None
    credits: Optional[float] = None

class PlanResponse(PlanBase):
    id: int

    class Config:
        from_attributes = True

class PlanAssign(BaseModel):
    plan_id: int
