"""DrawerSkill — adds drawers within a specified zone of the cabinet."""

from skills.base import BaseSkill, SkillResult


class DrawerSkill(BaseSkill):
    skill_id = "add_drawers"
    skill_name = "添加抽屉"
    description = "在柜体指定区域添加抽屉组。可指定数量 count、起止比例 start_ratio/end_ratio（0~1 相对高度），自动计算每个抽屉的位置和尺寸并添加配套拉手。"
    examples = [
        "加两个抽屉",
        "下面加三个抽屉",
        "在下半部分加两个大抽屉",
    ]

    DEFAULT_HANDLE = "long"
    DRAWER_GAP = 3  # mm between drawers
    MIN_DRAWER_HEIGHT = 80  # mm

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["抽屉", "drawer"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        add_component = self.tools["add_component"]

        cabinet = await get_structure(cabinet_id)
        internal = self._calc_internal_space(cabinet)

        count = params.get("count", 1)
        start_ratio = params.get("start_ratio", 0.0)
        end_ratio = params.get("end_ratio", 1.0)
        handle_style = params.get("handle_style", self.DEFAULT_HANDLE)
        material = params.get("material")
        color = params.get("color")

        zone_y_min = internal["y_min"] + start_ratio * internal["y_range"]
        zone_y_max = internal["y_min"] + end_ratio * internal["y_range"]
        zone_height = zone_y_max - zone_y_min

        available_height = zone_height - (count - 1) * self.DRAWER_GAP
        drawer_height = available_height / count

        if drawer_height < self.MIN_DRAWER_HEIGHT:
            return SkillResult(
                success=False,
                message=f"抽屉区域空间不足，每个抽屉最小需要 {self.MIN_DRAWER_HEIGHT}mm 高度",
                operations=[],
                error="insufficient_space",
            )

        operations: list[dict] = []

        for i in range(count):
            # Bottom-up stacking
            y_pos = zone_y_min + drawer_height / 2 + i * (drawer_height + self.DRAWER_GAP)

            drawer_op = await add_component(
                cabinet_id=cabinet_id,
                component_type="drawer",
                position_x=0.0,
                position_y=y_pos,
                position_z=0.0,
                width=internal["width"],
                height=drawer_height,
                depth=internal["depth"],
                material=material,
                color=color,
                label=f"抽屉{i + 1}",
            )
            operations.append(drawer_op)

            # Add handle on the drawer front
            handle_op = await add_component(
                cabinet_id=cabinet_id,
                component_type="handle",
                position_x=0.0,
                position_y=y_pos,
                position_z=cabinet["depth"] / 2 + 5,
                width=internal["width"] * 0.3,
                height=10,
                depth=5,
                handle_style=handle_style,
                label=f"抽屉拉手{i + 1}",
            )
            operations.append(handle_op)

        return SkillResult(
            success=True,
            message=f"已添加 {count} 个抽屉",
            operations=operations,
        )

    def _calc_internal_space(self, cabinet: dict) -> dict:
        w = cabinet["width"]
        h = cabinet["height"]
        d = cabinet["depth"]
        t = cabinet.get("board_thickness", 18)

        internal_width = w - 2 * t
        internal_depth = d - t

        y_min = -h / 2.0 + t
        y_max = h / 2.0 - t

        return {
            "width": internal_width,
            "depth": internal_depth,
            "y_min": y_min,
            "y_max": y_max,
            "y_range": y_max - y_min,
        }
