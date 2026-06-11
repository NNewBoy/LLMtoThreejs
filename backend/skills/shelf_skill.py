"""ShelfSkill — adds shelves at specified positions within a cabinet."""

import logging
from skills.base import BaseSkill, SkillResult

logger = logging.getLogger(__name__)


class ShelfSkill(BaseSkill):
    skill_id = "add_shelf"
    skill_name = "添加隔板"
    description = "在柜体内部指定位置添加活动隔板，支持单块或多块均匀分布。可指定 position_ratios（0~1 相对高度列表）或让系统均匀分布。"
    examples = [
        "加一块隔板",
        "在柜子中间加一块隔板",
        "加三块均匀分布的隔板",
        "在高度60厘米处加一块隔板",
    ]

    MIN_SHELF_SPACING = 150  # mm
    DEFAULT_THICKNESS = 18  # mm

    def can_handle(self, intent: str, context: dict) -> bool:
        keywords = ["隔板", "层板", "shelf", "隔层"]
        return any(kw in intent for kw in keywords)

    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        get_structure = self.tools["get_cabinet_structure"]
        add_component = self.tools["add_component"]

        cabinet = await get_structure(cabinet_id)
        if not cabinet or "height" not in cabinet:
            return SkillResult(
                success=False,
                message=f"找不到柜子 (ID: {cabinet_id})",
                operations=[],
                error="cabinet_not_found",
            )

        internal = self._calc_internal_space(cabinet)

        position_ratios = params.get("position_ratios")
        count = params.get("count", 1)
        material = params.get("material")
        color = params.get("color")

        if position_ratios is None:
            position_ratios = [i / (count + 1) for i in range(1, count + 1)]

        existing_shelves = [
            c for c in cabinet["components"] if c["component_type"] == "shelf"
        ]

        operations: list[dict] = []

        for ratio in position_ratios:
            y_pos = internal["y_min"] + ratio * internal["y_range"]
            logger.info(f"[ShelfSkill] ratio={ratio}, y_pos={y_pos:.1f}, y_range={internal['y_range']:.1f}")

            if self._would_overlap(y_pos, existing_shelves, self.MIN_SHELF_SPACING):
                logger.info(f"[ShelfSkill] skip overlap at y={y_pos:.1f}")
                continue

            logger.info(f"[ShelfSkill] adding shelf at y={y_pos:.1f}, w={internal['width']:.1f}, d={internal['depth']:.1f}")
            op = await add_component(
                cabinet_id=cabinet_id,
                component_type="shelf",
                position_x=0.0,
                position_y=y_pos,
                position_z=0.0,
                width=internal["width"],
                height=self.DEFAULT_THICKNESS,
                depth=internal["depth"],
                material=material,
                color=color,
            )
            operations.append(op)
            existing_shelves.append({"position_y": y_pos})

        logger.info(f"[ShelfSkill] total added: {len(operations)} shelves")

        if not operations:
            return SkillResult(
                success=False,
                message="无法添加隔板（位置与已有板件重叠或空间不足）",
                operations=[],
            )

        return SkillResult(
            success=True,
            message=f"已添加 {len(operations)} 块隔板",
            operations=operations,
        )

    def _calc_internal_space(self, cabinet: dict) -> dict:
        """Calculate internal space between body boards."""
        w = cabinet["width"]
        h = cabinet["height"]
        d = cabinet["depth"]
        t = cabinet.get("board_thickness", 18)

        internal_width = w - 2 * t
        internal_depth = d - t  # back board on one side

        # Y range: from top of bottom_board to bottom of top_board
        y_min = -h / 2.0 + t
        y_max = h / 2.0 - t

        return {
            "width": internal_width,
            "depth": internal_depth,
            "y_min": y_min,
            "y_max": y_max,
            "y_range": y_max - y_min,
        }

    def _would_overlap(
        self, y_pos: float, existing: list[dict], min_spacing: float
    ) -> bool:
        """Check if a shelf at y_pos would be too close to any existing shelf."""
        for shelf in existing:
            existing_y = shelf.get("position_y", 0)
            if abs(y_pos - existing_y) < min_spacing:
                return True
        return False
