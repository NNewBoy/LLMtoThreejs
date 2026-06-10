from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CabinetCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = "未命名柜子"
    width: float = 800.0
    height: float = 2000.0
    depth: float = 500.0
    board_thickness: float = 18.0
    global_material: str = "wood_oak"
    global_color: str = "#C49A6C"


class CabinetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    board_thickness: Optional[float] = None
    global_material: Optional[str] = None
    global_color: Optional[str] = None


class CabinetSizeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    width: float
    height: float
    depth: float


class CabinetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    width: float
    height: float
    depth: float
    board_thickness: float
    global_material: str
    global_color: str
    created_at: datetime
    updated_at: datetime


class CabinetDetailResponse(CabinetResponse):
    model_config = ConfigDict(from_attributes=True)

    components: list = []


class CabinetListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[CabinetResponse]
    total: int
