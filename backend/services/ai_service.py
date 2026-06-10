"""AIService — manages AI chat sessions, context, and delegates to CabinetAgent."""

import json
import logging
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from database import SessionLocal
from models.cabinet import Cabinet
from models.component import Component
from models.ai_chat import AIChatHistory
from agent.agent import CabinetAgent
from agent.skill_registry import SkillRegistry
from agent import tools as tool_module
from skills import ALL_SKILLS

logger = logging.getLogger(__name__)


class AIService:
    """Service that orchestrates AI chat interactions."""

    def __init__(self, db: Session):
        self.db = db
        self._registry: SkillRegistry | None = None
        self._agent: CabinetAgent | None = None

    @property
    def registry(self) -> SkillRegistry:
        if self._registry is None:
            self._registry = self._build_registry()
        return self._registry

    @property
    def agent(self) -> CabinetAgent:
        if self._agent is None:
            self._agent = CabinetAgent(
                skill_registry=self.registry,
                db_session_factory=SessionLocal,
            )
        return self._agent

    async def chat_stream(
        self,
        cabinet_id: int,
        message: str,
        history: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Process a chat message and yield SSE-formatted strings.

        Each yielded string is a complete SSE event block.
        """
        # Save user message to history
        self._save_message(cabinet_id, "user", message)

        # Build cabinet context for the agent
        cabinet_context = self._build_cabinet_context(cabinet_id)

        # Stream events from the agent
        async for event in self.agent.chat_stream(
            cabinet_id=cabinet_id,
            message=message,
            history=history,
            cabinet_context=cabinet_context,
        ):
            event_name = event.get("event", "message")
            event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
            yield f"event: {event_name}\ndata: {event_data}\n\n"

            # Save assistant messages to history
            if event_name == "message":
                content = event.get("data", {}).get("content", "")
                self._save_message(cabinet_id, "assistant", content)

    def get_skills_list(self) -> list[dict]:
        """Return metadata for all registered skills."""
        return self.registry.list_all()

    def _build_registry(self) -> SkillRegistry:
        """Build and populate a SkillRegistry with all skills and db-bound tools."""
        db_tools = {
            "add_component": lambda **kw: tool_module.add_component(self.db, **kw),
            "remove_component": lambda **kw: tool_module.remove_component(self.db, **kw),
            "update_component": lambda **kw: tool_module.update_component(self.db, **kw),
            "get_cabinet_structure": lambda cid: tool_module.get_cabinet_structure(self.db, cid),
            "get_component": lambda cid, comp_id: tool_module.get_component(self.db, cid, comp_id),
            "list_components": lambda cid, ct=None: tool_module.list_components(self.db, cid, ct),
            "update_cabinet_size": lambda **kw: tool_module.update_cabinet_size(self.db, **kw),
            "get_snapshot_description": lambda cid: tool_module.get_snapshot_description(self.db, cid),
        }
        registry = SkillRegistry(tools=db_tools)
        for skill_cls in ALL_SKILLS:
            registry.register(skill_cls(db_tools))
        return registry

    def _build_cabinet_context(self, cabinet_id: int) -> str:
        """Build a text description of the current cabinet state."""
        cabinet = self.db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
        if not cabinet:
            return "Cabinet not found."

        components = (
            self.db.query(Component)
            .filter(Component.cabinet_id == cabinet_id)
            .order_by(Component.sort_order, Component.id)
            .all()
        )

        from collections import Counter
        type_counts = Counter(c.component_type for c in components)

        TYPE_ZH = {
            "top_board": "顶板", "bottom_board": "底板",
            "left_board": "左侧板", "right_board": "右侧板",
            "back_board": "背板", "shelf": "隔板",
            "door": "门板", "drawer": "抽屉",
            "handle": "拉手", "leg": "柜脚", "baseboard": "踢脚线",
        }

        lines = [
            f"柜子「{cabinet.name}」: {cabinet.width}×{cabinet.height}×{cabinet.depth}mm, 板厚{cabinet.board_thickness}mm",
            f"全局材质: {cabinet.global_material}, 颜色: {cabinet.global_color}",
            f"组件({len(components)}个):",
        ]

        for comp in components:
            zh = TYPE_ZH.get(comp.component_type, comp.component_type)
            mat = comp.material or cabinet.global_material
            label = comp.label or zh
            lines.append(
                f"  [{comp.id}] {label} | "
                f"pos({comp.position_x:.0f},{comp.position_y:.0f},{comp.position_z:.0f}) | "
                f"size({comp.width:.0f}×{comp.height:.0f}×{comp.depth:.0f}) | "
                f"材质:{mat}"
            )

        return "\n".join(lines)

    def _save_message(self, cabinet_id: int, role: str, content: str) -> None:
        """Persist a chat message to the database."""
        try:
            record = AIChatHistory(
                cabinet_id=cabinet_id,
                role=role,
                content=content,
            )
            self.db.add(record)
            self.db.commit()
        except Exception:
            logger.exception("Failed to save chat message")
            self.db.rollback()
