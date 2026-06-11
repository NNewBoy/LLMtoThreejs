"""Atomic tool functions used by Skills to interact with the database.

Each tool is an async function that takes a db Session and keyword parameters.
They wrap the existing CabinetService / ComponentService / HistoryService logic
but operate directly on the DB session for use within the agent/skill layer.
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from models.cabinet import Cabinet
from models.component import Component

logger = logging.getLogger(__name__)


async def add_component(
    db: Session,
    cabinet_id: int,
    component_type: str,
    width: float = 0.0,
    height: float = 0.0,
    depth: float = 0.0,
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
    rotation_x: float = 0.0,
    rotation_y: float = 0.0,
    rotation_z: float = 0.0,
    material: str | None = None,
    color: str | None = None,
    door_style: str | None = None,
    handle_style: str | None = None,
    label: str = "",
    sort_order: int = 0,
    parent_id: int | None = None,
    **kwargs: Any,
) -> dict:
    """Add a new component to a cabinet and return it as a dict."""
    comp = Component(
        cabinet_id=cabinet_id,
        component_type=component_type,
        width=width,
        height=height,
        depth=depth,
        position_x=position_x,
        position_y=position_y,
        position_z=position_z,
        rotation_x=rotation_x,
        rotation_y=rotation_y,
        rotation_z=rotation_z,
        material=material,
        color=color,
        door_style=door_style,
        handle_style=handle_style,
        label=label,
        sort_order=sort_order,
        parent_id=parent_id,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    comp_dict = _component_to_dict(comp)
    logger.info(f"[tools.add_component] created component id={comp.id}, type={component_type}, cabinet_id={cabinet_id}")
    return {"action": "add", "componentType": component_type, "data": comp_dict}


async def remove_component(
    db: Session,
    cabinet_id: int,
    component_id: int,
) -> dict:
    """Remove a component by ID. Returns a deletion operation dict."""
    comp = db.query(Component).filter(
        Component.id == component_id,
        Component.cabinet_id == cabinet_id,
    ).first()
    if comp is None:
        return {"action": "remove", "componentId": component_id, "error": "not_found"}

    result = {"action": "remove", "componentId": component_id, "componentType": comp.component_type}
    db.delete(comp)
    db.commit()
    return result


async def update_component(
    db: Session,
    cabinet_id: int,
    component_id: int,
    **fields: Any,
) -> dict:
    """Update fields on an existing component. Returns update operation dict."""
    comp = db.query(Component).filter(
        Component.id == component_id,
        Component.cabinet_id == cabinet_id,
    ).first()
    if comp is None:
        return {"action": "update", "componentId": component_id, "error": "not_found"}

    for key, value in fields.items():
        if hasattr(comp, key) and value is not None:
            setattr(comp, key, value)

    db.commit()
    db.refresh(comp)
    comp_dict = _component_to_dict(comp)
    return {"action": "update", "componentId": component_id, "data": comp_dict}


async def get_cabinet_structure(
    db: Session,
    cabinet_id: int,
) -> dict:
    """Return the full cabinet structure as a dict including all components."""
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if cabinet is None:
        logger.warning(f"[tools.get_cabinet_structure] cabinet {cabinet_id} NOT FOUND")
        return {}

    components = (
        db.query(Component)
        .filter(Component.cabinet_id == cabinet_id)
        .order_by(Component.sort_order, Component.id)
        .all()
    )
    logger.info(f"[tools.get_cabinet_structure] cabinet {cabinet_id}: {len(components)} components")

    return {
        "id": cabinet.id,
        "name": cabinet.name,
        "width": cabinet.width,
        "height": cabinet.height,
        "depth": cabinet.depth,
        "board_thickness": cabinet.board_thickness,
        "global_material": cabinet.global_material,
        "global_color": cabinet.global_color,
        "components": [_component_to_dict(c) for c in components],
    }


async def get_component(
    db: Session,
    cabinet_id: int,
    component_id: int,
) -> dict | None:
    """Get a single component as a dict."""
    comp = db.query(Component).filter(
        Component.id == component_id,
        Component.cabinet_id == cabinet_id,
    ).first()
    if comp is None:
        return None
    return _component_to_dict(comp)


async def list_components(
    db: Session,
    cabinet_id: int,
    component_type: str | None = None,
) -> list[dict]:
    """List components, optionally filtered by type."""
    query = db.query(Component).filter(Component.cabinet_id == cabinet_id)
    if component_type:
        query = query.filter(Component.component_type == component_type)
    components = query.order_by(Component.sort_order, Component.id).all()
    return [_component_to_dict(c) for c in components]


async def update_cabinet_size(
    db: Session,
    cabinet_id: int,
    width: float,
    height: float,
    depth: float,
) -> dict:
    """Update cabinet dimensions and return the updated cabinet dict."""
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if cabinet is None:
        return {}

    cabinet.width = width
    cabinet.height = height
    cabinet.depth = depth
    db.commit()
    db.refresh(cabinet)

    return {
        "action": "update_cabinet_size",
        "cabinet_id": cabinet.id,
        "width": cabinet.width,
        "height": cabinet.height,
        "depth": cabinet.depth,
    }


async def get_snapshot_description(
    db: Session,
    cabinet_id: int,
) -> str:
    """Generate a human-readable description of the cabinet for the LLM."""
    structure = await get_cabinet_structure(db, cabinet_id)
    if not structure:
        return "Cabinet not found."

    from collections import Counter

    components = structure["components"]
    type_counts = Counter(c["component_type"] for c in components)

    TYPE_ZH = {
        "top_board": "顶板", "bottom_board": "底板",
        "left_board": "左侧板", "right_board": "右侧板",
        "back_board": "背板", "shelf": "隔板",
        "door": "门板", "drawer": "抽屉",
        "handle": "拉手", "leg": "柜脚", "baseboard": "踢脚线",
    }

    lines = [
        f"柜子「{structure['name']}」: "
        f"{structure['width']}×{structure['height']}×{structure['depth']}mm, "
        f"板厚{structure['board_thickness']}mm",
        f"组件({len(components)}个): "
        + ", ".join(
            f"{TYPE_ZH.get(t, t)}×{c}" for t, c in sorted(type_counts.items())
        ),
    ]

    return " | ".join(lines)


def _component_to_dict(comp: Component) -> dict:
    """Convert a Component ORM instance to a plain dict."""
    return {
        "id": comp.id,
        "cabinet_id": comp.cabinet_id,
        "component_type": comp.component_type,
        "parent_id": comp.parent_id,
        "label": comp.label or "",
        "sort_order": comp.sort_order,
        "width": comp.width,
        "height": comp.height,
        "depth": comp.depth,
        "position_x": comp.position_x,
        "position_y": comp.position_y,
        "position_z": comp.position_z,
        "rotation_x": comp.rotation_x,
        "rotation_y": comp.rotation_y,
        "rotation_z": comp.rotation_z,
        "material": comp.material,
        "color": comp.color,
        "door_style": comp.door_style,
        "handle_style": comp.handle_style,
        "is_enabled": comp.is_enabled,
    }
