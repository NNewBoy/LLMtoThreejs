"""MaterialSkill — batch changes material/color for components of specified types."""

from skills.base import BaseSkill, SkillResult


class MaterialSkill(BaseSkill):
    skill_id = "change_material"
    skill_name = "批量换材质"
    description = "将柜子中指定类型板件的材质和/或颜色统一替换。支持批量更换所有隔板、门板、抽屉等的材质。"
    examples = [
        "把所有隔板改成玻璃材质",
        "门板换成胡桃木",
        "把柜子改成白色烤漆",
    ]

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["材质", "颜色", "material", "color", "换成", "改成", "换", "烤漆"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        update_component = self.tools["update_component"]

        cabinet = await get_structure(cabinet_id)
        if not cabinet or "height" not in cabinet:
            return SkillResult(
                success=False,
                message=f"找不到柜子 (ID: {cabinet_id})",
                operations=[],
                error="cabinet_not_found",
            )

        target_types = params.get("component_types", [])
        material = params.get("material")
        color = params.get("color")

        if not material and not color:
            return SkillResult(
                success=False,
                message="请指定要更换的材质或颜色",
                operations=[],
                error="missing_params",
            )

        # If no specific types given, apply to all components
        all_components = cabinet["components"]
        if target_types:
            targets = [
                c for c in all_components if c["component_type"] in target_types
            ]
        else:
            targets = all_components

        # Skip mandatory body boards if explicitly targeted
        mandatory_types = {"top_board", "bottom_board", "left_board", "right_board"}
        targets = [c for c in targets if c["component_type"] not in mandatory_types]

        operations: list[dict] = []

        for comp in targets:
            updates = {}
            if material:
                updates["material"] = material
            if color:
                updates["color"] = color

            op = await update_component(
                cabinet_id=cabinet_id,
                component_id=comp["id"],
                **updates,
            )
            operations.append(op)

        type_names = ", ".join(target_types) if target_types else "所有组件"
        return SkillResult(
            success=True,
            message=f"已更新 {len(operations)} 个{type_names}的材质",
            operations=operations,
        )
