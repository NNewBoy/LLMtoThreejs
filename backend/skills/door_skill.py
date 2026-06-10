"""DoorSkill — adds doors with specified count, style, and cover range."""

from skills.base import BaseSkill, SkillResult

STYLE_ZH = {
    "flat": "平板",
    "panel": "造型",
    "glass": "玻璃",
    "louver": "百叶",
}


class DoorSkill(BaseSkill):
    skill_id = "add_doors"
    skill_name = "添加门板"
    description = "添加柜门。支持指定数量、样式（flat/panel/glass/louver）、覆盖范围（full/upper/lower），自动删除旧门板并添加配套拉手。"
    examples = [
        "加两扇门",
        "加一扇玻璃门",
        "上面加两扇对开门",
        "换成平板门",
    ]

    VALID_STYLES = ["flat", "panel", "glass", "louver"]
    DOOR_GAP = 3  # mm
    DEFAULT_HANDLE = "long"
    DOOR_THICKNESS = 18  # mm — match board_thickness for visual consistency

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["门", "门板", "door", "柜门"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        add_component = self.tools["add_component"]
        remove_component = self.tools["remove_component"]

        cabinet = await get_structure(cabinet_id)
        count = params.get("count", 1)
        style = params.get("style", "flat")
        cover_range = params.get("cover_range", "full")
        handle_style = params.get("handle_style", self.DEFAULT_HANDLE)
        material = params.get("material")
        color = params.get("color")

        if style not in self.VALID_STYLES:
            return SkillResult(
                success=False,
                message=f"不支持的门板样式: {style}，可选: {', '.join(self.VALID_STYLES)}",
                operations=[],
                error="invalid_style",
            )

        door_zone = self._calc_door_zone(cabinet, cover_range)
        door_width = (cabinet["width"] - (count - 1) * self.DOOR_GAP) / count

        operations: list[dict] = []

        # Remove existing doors and their handles
        existing_doors = [
            c for c in cabinet["components"] if c["component_type"] == "door"
        ]
        existing_handles = [
            c for c in cabinet["components"] if c["component_type"] == "handle"
        ]

        for door in existing_doors:
            op = await remove_component(cabinet_id=cabinet_id, component_id=door["id"])
            operations.append(op)

        # Also remove handles that were children of removed doors
        for handle in existing_handles:
            if handle.get("parent_id") and any(
                d["id"] == handle["parent_id"] for d in existing_doors
            ):
                op = await remove_component(
                    cabinet_id=cabinet_id, component_id=handle["id"]
                )
                operations.append(op)

        # Create new doors
        for i in range(count):
            x_pos = (
                -cabinet["width"] / 2
                + door_width / 2
                + i * (door_width + self.DOOR_GAP)
            )

            door_op = await add_component(
                cabinet_id=cabinet_id,
                component_type="door",
                position_x=x_pos,
                position_y=door_zone["y_center"],
                position_z=cabinet["depth"] / 2 + self.DOOR_THICKNESS / 2,
                width=door_width,
                height=door_zone["height"],
                depth=self.DOOR_THICKNESS,
                door_style=style,
                material=material,
                color=color,
                label=f"门板{i + 1}",
            )
            operations.append(door_op)

            # Add handle for this door
            handle_op = await add_component(
                cabinet_id=cabinet_id,
                component_type="handle",
                position_x=x_pos + door_width / 2 - 20,
                position_y=door_zone["y_center"],
                position_z=cabinet["depth"] / 2 + self.DOOR_THICKNESS + 5,
                width=10,
                height=door_zone["height"] * 0.3,
                depth=5,
                handle_style=handle_style,
                label=f"拉手{i + 1}",
            )
            operations.append(handle_op)

        style_zh = STYLE_ZH.get(style, style)
        return SkillResult(
            success=True,
            message=f"已添加 {count} 扇{style_zh}门板",
            operations=operations,
        )

    def _calc_door_zone(self, cabinet: dict, cover_range: str) -> dict:
        """Calculate the Y position and height for doors based on cover_range."""
        h = cabinet["height"]
        t = cabinet.get("board_thickness", 18)

        # Full internal height
        internal_height = h - 2 * t
        y_center_full = 0.0

        if cover_range == "upper":
            zone_height = internal_height / 2
            y_center = internal_height / 4
        elif cover_range == "lower":
            zone_height = internal_height / 2
            y_center = -internal_height / 4
        else:  # full
            zone_height = internal_height
            y_center = 0.0

        return {"y_center": y_center, "height": zone_height}
