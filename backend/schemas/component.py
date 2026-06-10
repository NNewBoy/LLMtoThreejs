from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ComponentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_type: str
    parent_id: Optional[int] = None
    label: str = ""
    sort_order: int = 0
    width: float
    height: float
    depth: float
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    material: Optional[str] = None
    color: Optional[str] = None
    door_style: Optional[str] = None
    handle_style: Optional[str] = None
    is_enabled: bool = True


class ComponentUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_type: Optional[str] = None
    parent_id: Optional[int] = None
    label: Optional[str] = None
    sort_order: Optional[int] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    rotation_x: Optional[float] = None
    rotation_y: Optional[float] = None
    rotation_z: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    door_style: Optional[str] = None
    handle_style: Optional[str] = None
    is_enabled: Optional[bool] = None


class ComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cabinet_id: int
    component_type: str
    parent_id: Optional[int]
    label: str
    sort_order: int
    width: float
    height: float
    depth: float
    position_x: float
    position_y: float
    position_z: float
    rotation_x: float
    rotation_y: float
    rotation_z: float
    material: Optional[str]
    color: Optional[str]
    door_style: Optional[str]
    handle_style: Optional[str]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class ComponentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[ComponentResponse]
    total: int
