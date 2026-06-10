from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class HistoryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operation_type: str
    target_type: str
    target_id: Optional[int] = None
    snapshot_json: str
    description: str = ""


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cabinet_id: int
    operation_type: str
    target_type: str
    target_id: Optional[int]
    snapshot_json: str
    description: str
    created_at: datetime


class HistoryListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[HistoryResponse]
    total: int
