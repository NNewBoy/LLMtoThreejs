"""ResizeSkill — adjusts cabinet dimensions and triggers body board recalculation."""

from skills.base import BaseSkill, SkillResult


class ResizeSkill(BaseSkill):
    skill_id = "adjust_cabinet_size"
    skill_name = "调整柜体尺寸"
    description = "调整柜子整体尺寸（宽度、高度、深度），并自动重新计算所有必选板件（顶/底/左/右/背板）的位置和尺寸。"
    examples = [
        "把柜子加高20厘米",
        "柜子宽度改成1000",
        "把深度减少10厘米",
    ]

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["尺寸", "宽度", "高度", "深度", "加高", "加宽", "resize", "变大", "变小"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        update_cabinet_size = self.tools["update_cabinet_size"]
        update_component = self.tools["update_component"]

        cabinet = await get_structure(cabinet_id)

        new_width = params.get("width", cabinet["width"])
        new_height = params.get("height", cabinet["height"])
        new_depth = params.get("depth", cabinet["depth"])

        # Support delta values
        if "width_delta" in params:
            new_width = cabinet["width"] + params["width_delta"]
        if "height_delta" in params:
            new_height = cabinet["height"] + params["height_delta"]
        if "depth_delta" in params:
            new_depth = cabinet["depth"] + params["depth_delta"]

        # Clamp to minimum dimensions
        new_width = max(200, new_width)
        new_height = max(200, new_height)
        new_depth = max(100, new_depth)

        operations: list[dict] = []

        # Update cabinet size
        cab_op = await update_cabinet_size(
            cabinet_id=cabinet_id,
            width=new_width,
            height=new_height,
            depth=new_depth,
        )
        operations.append(cab_op)

        # Recalculate body board positions
        w, h, d = new_width, new_height, new_depth
        t = cabinet.get("board_thickness", 18)
        internal_width = w - 2 * t
        internal_height = h - 2 * t
        internal_depth = d - t

        board_updates = {
            "top_board": {
                "width": w, "height": t, "depth": d,
                "position_x": 0.0, "position_y": h / 2.0 - t / 2.0, "position_z": 0.0,
            },
            "bottom_board": {
                "width": w, "height": t, "depth": d,
                "position_x": 0.0, "position_y": -h / 2.0 + t / 2.0, "position_z": 0.0,
            },
            "left_board": {
                "width": t, "height": internal_height, "depth": d,
                "position_x": -w / 2.0 + t / 2.0, "position_y": 0.0, "position_z": 0.0,
            },
            "right_board": {
                "width": t, "height": internal_height, "depth": d,
                "position_x": w / 2.0 - t / 2.0, "position_y": 0.0, "position_z": 0.0,
            },
            "back_board": {
                "width": internal_width, "height": internal_height, "depth": t,
                "position_x": 0.0, "position_y": 0.0, "position_z": -d / 2.0 + t / 2.0,
            },
        }

        for comp in cabinet["components"]:
            if comp["component_type"] in board_updates:
                updates = board_updates[comp["component_type"]]
                op = await update_component(
                    cabinet_id=cabinet_id,
                    component_id=comp["id"],
                    **updates,
                )
                operations.append(op)

        # Also resize shelves to fit new internal width
        for comp in cabinet["components"]:
            if comp["component_type"] == "shelf":
                op = await update_component(
                    cabinet_id=cabinet_id,
                    component_id=comp["id"],
                    width=internal_width,
                    depth=internal_depth,
                )
                operations.append(op)

        return SkillResult(
            success=True,
            message=f"柜体尺寸已调整为 {new_width}mm × {new_height}mm × {new_depth}mm",
            operations=operations,
        )
