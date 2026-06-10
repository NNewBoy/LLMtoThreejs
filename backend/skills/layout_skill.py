"""ReorganizeLayoutSkill — orchestrates sub-skills for complex layout changes."""

from skills.base import BaseSkill, SkillResult
from skills.door_skill import DoorSkill
from skills.drawer_skill import DrawerSkill
from skills.shelf_skill import ShelfSkill


class ReorganizeLayoutSkill(BaseSkill):
    skill_id = "reorganize_layout"
    skill_name = "重新布局"
    description = "对柜子进行复杂结构调整，如'上面两门下面三抽屉'。接受 layout_spec 参数，包含 zones 列表，每个 zone 指定类型（door/drawer/shelf）和参数。自动编排子 Skills 完成整体布局。"
    examples = [
        "上面加两扇对开门，下面加三个抽屉",
        "重新布局：上半部玻璃门，下半部两个大抽屉",
    ]

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["布局", "重新", "上面", "下面", "layout"]
        # Needs at least two different component types mentioned
        has_door = any(kw in intent for kw in ["门", "door"])
        has_drawer = any(kw in intent for kw in ["抽屉", "drawer"])
        has_shelf = any(kw in intent for kw in ["隔板", "shelf"])
        combo_count = sum([has_door, has_drawer, has_shelf])
        return combo_count >= 2 or "布局" in intent or "layout" in intent

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        layout_spec = params.get("layout_spec")
        if not layout_spec or "zones" not in layout_spec:
            return SkillResult(
                success=False,
                message="缺少 layout_spec 参数，需要包含 zones 列表",
                operations=[],
                error="missing_layout_spec",
            )

        all_operations: list[dict] = []
        messages: list[str] = []

        for zone in layout_spec["zones"]:
            zone_type = zone.get("type")
            sub_skill = self._resolve_sub_skill(zone_type)
            if sub_skill is None:
                messages.append(f"跳过未知区域类型: {zone_type}")
                continue

            sub_params = {k: v for k, v in zone.items() if k != "type"}
            result = await sub_skill.execute(cabinet_id, sub_params, context)
            all_operations.extend(result.operations)
            messages.append(result.message)

        return SkillResult(
            success=True,
            message="；".join(messages) if messages else "布局调整完成",
            operations=all_operations,
        )

    def _resolve_sub_skill(self, zone_type: str) -> BaseSkill | None:
        mapping = {
            "door": DoorSkill,
            "drawer": DrawerSkill,
            "shelf": ShelfSkill,
        }
        skill_cls = mapping.get(zone_type)
        return skill_cls(self.tools) if skill_cls else None
