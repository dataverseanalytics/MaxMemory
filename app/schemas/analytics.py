from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ChartPoint(BaseModel):
    date: str  # YYYY-MM-DD
    value: float

class UsageSummary(BaseModel):
    credits_used_this_month: float
    total_credit_limit: float = 10000.0 # Standard limit
    month_query_count: int
    query_growth_percent: float # vs last month

class AnalyticsResponse(BaseModel):
    summary: UsageSummary
    credits_daily: List[ChartPoint]
    queries_daily: List[ChartPoint]
