from datetime import datetime

from pydantic import BaseModel


class RiskIndexSchema(BaseModel):
    rule_id: int
    from_date: datetime.date
    to_date: datetime.date
