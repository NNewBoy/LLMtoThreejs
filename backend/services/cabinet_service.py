from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.cabinet import Cabinet
from models.component import Component
from schemas.cabinet import CabinetCreate, CabinetUpdate, CabinetSizeUpdate


class CabinetService:
    """Cabinet data service — handles CRUD and default initialization."""

    def __init__(self, db: Session):
        self.db = db

    def create_default(self, name: str = "未命名柜子", **kwargs) -> Cabinet:
        """Create a new cabinet with default body boards (top, bottom, left, right, back).

        Uses constraint rules from SPEC2 section 4.1.3:
        - Coordinate system: center at (0,0,0), X=width, Y=height, Z=depth
        - Default: 800mm wide, 2000mm tall, 500mm deep, 18mm board thickness
        """
        width = kwargs.get("width", 800.0)
        height = kwargs.get("height", 2000.0)
        depth = kwargs.get("depth", 500.0)
        board_thickness = kwargs.get("board_thickness", 18.0)
        global_material = kwargs.get("global_material", "wood_oak")
        global_color = kwargs.get("global_color", "#C49A6C")

        cabinet = Cabinet(
            name=name,
            width=width,
            height=height,
            depth=depth,
            board_thickness=board_thickness,
            global_material=global_material,
            global_color=global_color,
        )
        self.db.add(cabinet)
        self.db.flush()

        # Compute body board positions using constraint rules
        w, h, d, t = width, height, depth, board_thickness

        # Internal dimensions (space between boards)
        internal_width = w - 2 * t
        internal_height = h - 2 * t
        internal_depth = d - t  # back board only on one side

        body_boards = [
            # Top board: full width & depth, at Y = height/2 - thickness/2
            Component(
                cabinet_id=cabinet.id,
                component_type="top_board",
                label="顶板",
                sort_order=0,
                width=w,
                height=t,
                depth=d,
                position_x=0.0,
                position_y=h / 2.0 - t / 2.0,
                position_z=0.0,
            ),
            # Bottom board: full width & depth, at Y = -height/2 + thickness/2
            Component(
                cabinet_id=cabinet.id,
                component_type="bottom_board",
                label="底板",
                sort_order=1,
                width=w,
                height=t,
                depth=d,
                position_x=0.0,
                position_y=-h / 2.0 + t / 2.0,
                position_z=0.0,
            ),
            # Left board: internal height & full depth, at X = -width/2 + thickness/2
            Component(
                cabinet_id=cabinet.id,
                component_type="left_board",
                label="左侧板",
                sort_order=2,
                width=t,
                height=internal_height,
                depth=d,
                position_x=-w / 2.0 + t / 2.0,
                position_y=0.0,
                position_z=0.0,
            ),
            # Right board: internal height & full depth, at X = width/2 - thickness/2
            Component(
                cabinet_id=cabinet.id,
                component_type="right_board",
                label="右侧板",
                sort_order=3,
                width=t,
                height=internal_height,
                depth=d,
                position_x=w / 2.0 - t / 2.0,
                position_y=0.0,
                position_z=0.0,
            ),
            # Back board: internal width & internal height, at Z = -depth/2 + thickness/2
            Component(
                cabinet_id=cabinet.id,
                component_type="back_board",
                label="背板",
                sort_order=4,
                width=internal_width,
                height=internal_height,
                depth=t,
                position_x=0.0,
                position_y=0.0,
                position_z=-d / 2.0 + t / 2.0,
            ),
        ]

        self.db.add_all(body_boards)
        self.db.commit()
        self.db.refresh(cabinet)
        return cabinet

    def get(self, cabinet_id: int) -> Cabinet:
        cabinet = self.db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
        if not cabinet:
            raise HTTPException(status_code=404, detail="Cabinet not found")
        return cabinet

    def get_with_components(self, cabinet_id: int) -> Cabinet:
        cabinet = self.get(cabinet_id)
        return cabinet

    def list_all(self) -> list[Cabinet]:
        return self.db.query(Cabinet).order_by(Cabinet.updated_at.desc()).all()

    def update(self, cabinet_id: int, data: CabinetUpdate) -> Cabinet:
        cabinet = self.get(cabinet_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cabinet, field, value)
        self.db.commit()
        self.db.refresh(cabinet)
        return cabinet

    def update_size(self, cabinet_id: int, data: CabinetSizeUpdate) -> Cabinet:
        cabinet = self.get(cabinet_id)
        cabinet.width = data.width
        cabinet.height = data.height
        cabinet.depth = data.depth
        self.db.commit()
        self.db.refresh(cabinet)
        return cabinet

    def delete(self, cabinet_id: int) -> None:
        cabinet = self.get(cabinet_id)
        self.db.delete(cabinet)
        self.db.commit()

    def build_snapshot(self, cabinet_id: int) -> str:
        """Build a JSON snapshot of the cabinet and all its components."""
        import json

        cabinet = self.get(cabinet_id)
        components = (
            self.db.query(Component)
            .filter(Component.cabinet_id == cabinet_id)
            .order_by(Component.sort_order)
            .all()
        )
        snapshot = {
            "cabinet": {
                "id": cabinet.id,
                "name": cabinet.name,
                "width": cabinet.width,
                "height": cabinet.height,
                "depth": cabinet.depth,
                "board_thickness": cabinet.board_thickness,
                "global_material": cabinet.global_material,
                "global_color": cabinet.global_color,
            },
            "components": [
                {
                    "id": c.id,
                    "component_type": c.component_type,
                    "parent_id": c.parent_id,
                    "label": c.label,
                    "sort_order": c.sort_order,
                    "width": c.width,
                    "height": c.height,
                    "depth": c.depth,
                    "position_x": c.position_x,
                    "position_y": c.position_y,
                    "position_z": c.position_z,
                    "rotation_x": c.rotation_x,
                    "rotation_y": c.rotation_y,
                    "rotation_z": c.rotation_z,
                    "material": c.material,
                    "color": c.color,
                    "door_style": c.door_style,
                    "handle_style": c.handle_style,
                    "is_enabled": c.is_enabled,
                }
                for c in components
            ],
        }
        return json.dumps(snapshot, ensure_ascii=False)
