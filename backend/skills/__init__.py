"""Skills module — imports all skill classes for easy registration."""

from skills.base import BaseSkill, SkillResult
from skills.shelf_skill import ShelfSkill
from skills.door_skill import DoorSkill
from skills.drawer_skill import DrawerSkill
from skills.material_skill import MaterialSkill
from skills.query_skill import QuerySkill
from skills.resize_skill import ResizeSkill
from skills.layout_skill import ReorganizeLayoutSkill

ALL_SKILLS = [
    ShelfSkill,
    DoorSkill,
    DrawerSkill,
    MaterialSkill,
    QuerySkill,
    ResizeSkill,
    ReorganizeLayoutSkill,
]

__all__ = [
    "BaseSkill",
    "SkillResult",
    "ALL_SKILLS",
    "ShelfSkill",
    "DoorSkill",
    "DrawerSkill",
    "MaterialSkill",
    "QuerySkill",
    "ResizeSkill",
    "ReorganizeLayoutSkill",
]
