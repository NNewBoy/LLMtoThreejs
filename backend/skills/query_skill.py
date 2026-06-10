"""QuerySkill — returns cabinet structure description and component statistics."""

from collections import Counter
from skills.base import BaseSkill, SkillResult

COMPONENT_TYPE_ZH = {
    "top_board": "顶板",
    "bottom_board": "底板",
    "left_board": "左侧板",
    "right_board": "右侧板",
    "back_board": "背板",
    "shelf": "隔板",
    "door": "门板",
    "drawer": "抽屉",
    "handle": "拉手",
    "leg": "柜脚",
    "baseboard": "踢脚线",
}


class QuerySkill(BaseSkill):
    skill_id = "query_structure"
    skill_name = "查询柜子结构"
    description = "获取柜子的完整结构描述和各类型板件统计信息，返回人类可读的摘要。"
    examples = [
        "这个柜子有几块隔板？",
        "门板是什么材质的？",
        "柜子的结构是什么？",
    ]

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["几块", "多少", "什么材质", "结构", "查询", "统计", "有几"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        cabinet = await get_structure(cabinet_id)

        components = cabinet["components"]
        type_counts = Counter(c["component_type"] for c in components)

        # Build human-readable summary
        lines = [
            f"柜子「{cabinet.get('name', '未命名')}」尺寸: "
            f"{cabinet['width']}mm × {cabinet['height']}mm × {cabinet['depth']}mm",
            f"默认板件厚度: {cabinet.get('board_thickness', 18)}mm",
            f"全局材质: {cabinet.get('global_material', 'wood_oak')}",
            "",
            "板件统计:",
        ]

        for comp_type, count in sorted(type_counts.items()):
            zh_name = COMPONENT_TYPE_ZH.get(comp_type, comp_type)
            lines.append(f"  {zh_name} ({comp_type}): {count} 块")

        # Detail each component
        lines.append("")
        lines.append("板件详情:")
        for comp in sorted(components, key=lambda c: (c["component_type"], c.get("sort_order", 0))):
            zh_name = COMPONENT_TYPE_ZH.get(comp["component_type"], comp["component_type"])
            label = comp.get("label", "") or zh_name
            mat = comp.get("material") or cabinet.get("global_material", "wood_oak")
            clr = comp.get("color") or cabinet.get("global_color", "#C49A6C")
            lines.append(
                f"  [{comp['id']}] {label} | "
                f"位置({comp['position_x']:.0f}, {comp['position_y']:.0f}, {comp['position_z']:.0f}) | "
                f"尺寸({comp['width']:.0f}×{comp['height']:.0f}×{comp['depth']:.0f}) | "
                f"材质: {mat}, 颜色: {clr}"
            )

        summary = "\n".join(lines)

        return SkillResult(
            success=True,
            message=summary,
            operations=[],
        )
