from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def _camel(s: str) -> str:
    """snake_case → camelCase"""
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _alias_config() -> ConfigDict:
    """配置 alias_generator + populate_by_name，兼容 camelCase 和 snake_case"""
    return ConfigDict(
        from_attributes=True,
        alias_generator=_camel,
        populate_by_name=True,
    )


class CabinetCreate(BaseModel):
    model_config = _alias_config()

    name: str = "未命名柜子"
    width: float = 800.0
    height: float = 2000.0
    depth: float = 500.0
    board_thickness: float = 18.0
    global_material: str = "wood_oak"
    global_color: str = "#C49A6C"


class CabinetUpdate(BaseModel):
    model_config = _alias_config()

    name: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    board_thickness: Optional[float] = None
    global_material: Optional[str] = None
    global_color: Optional[str] = None


class CabinetSizeUpdate(BaseModel):
    model_config = _alias_config()

    width: float
    height: float
    depth: float


class ComponentSync(BaseModel):
    """用于同步 components 的 schema，支持新增、更新、删除"""
    model_config = _alias_config()

    id: Optional[int] = None  # 有 id 则更新，无 id 则新增
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


class CabinetFullUpdate(BaseModel):
    """完整的柜子更新请求，包含 cabinet 和 components"""
    model_config = _alias_config()

    cabinet: CabinetUpdate
    components: list[ComponentSync]


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
