from pydantic import BaseModel
from typing import Optional


class PlayerInput(BaseModel):
    name: str
    hours: Optional[float] = None


class CreateBillRequest(BaseModel):
    total_cost: float
    court_name: Optional[str] = None
    note: Optional[str] = None
    split_mode: str  # "equal" | "hours"
    players: list[PlayerInput]
    host_name: Optional[str] = None


class PlayerResult(BaseModel):
    name: str
    hours: Optional[float]
    amount: float


class BillResponse(BaseModel):
    id: str
    total_cost: float
    court_name: Optional[str]
    note: Optional[str]
    split_mode: str
    host_name: Optional[str]
    created_at: str
    players: list[PlayerResult]
