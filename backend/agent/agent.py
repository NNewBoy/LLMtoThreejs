"""CabinetAgent — LLM-powered agent that selects and executes Skills.

Uses the openai library (async) for LLM calls. Falls back gracefully
if no API key is configured.
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

from openai import AsyncOpenAI

from config import settings
from agent.prompts import build_system_prompt
from agent.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)


class CabinetAgent:
    """Agent that uses an LLM to select skills and execute them."""

    def __init__(self, skill_registry: SkillRegistry, db_session_factory=None):
        self.registry = skill_registry
        self.db_session_factory = db_session_factory
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY or "no-key",
                base_url=settings.LLM_BASE_URL,
            )
        return self._client

    @property
    def has_api_key(self) -> bool:
        return bool(settings.LLM_API_KEY)

    async def chat_stream(
        self,
        cabinet_id: int,
        message: str,
        history: list[dict],
        cabinet_context: str,
    ) -> AsyncGenerator[dict, None]:
        """Process a user message and yield SSE event dicts.

        Yields dicts with 'event' and 'data' keys suitable for SSE streaming.
        """
        if not self.has_api_key:
            yield await self._fallback_response(cabinet_id, message)
            return

        # Build messages for LLM
        system_prompt = build_system_prompt(
            self.registry.get_skill_descriptions_for_prompt()
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Add cabinet context
        messages.append({
            "role": "system",
            "content": f"当前柜子状态:\n{cabinet_context}",
        })

        # Add conversation history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": message})

        # Get available tools
        tools = self.registry.get_all_skill_tools()

        yield {"event": "thinking", "data": {"content": "正在分析你的需求..."}}

        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
            )

            choice = response.choices[0]
            assistant_msg = choice.message

            # If the LLM chose to call tools
            if assistant_msg.tool_calls:
                yield {
                    "event": "skill_selected",
                    "data": {
                        "skill_id": assistant_msg.tool_calls[0].function.name,
                        "skill_name": assistant_msg.tool_calls[0].function.name,
                        "reasoning": assistant_msg.content or "",
                    },
                }

                all_operations = []
                skills_used = []

                for tool_call in assistant_msg.tool_calls:
                    skill_id = tool_call.function.name
                    skill = self.registry.get(skill_id)

                    if skill is None:
                        yield {
                            "event": "error",
                            "data": {"content": f"未知的 Skill: {skill_id}"},
                        }
                        continue

                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    skill_params = args.get("params", {})
                    skills_used.append(skill_id)

                    yield {
                        "event": "tool_calls",
                        "data": {
                            "calls": [
                                {"tool": skill_id, "args": skill_params}
                            ]
                        },
                    }

                    # Execute the skill
                    db = self.db_session_factory() if self.db_session_factory else None
                    try:
                        # Build tools dict with db session bound
                        bound_tools = self._bind_tools(db)
                        skill.tools = bound_tools
                        result = await skill.execute(cabinet_id, skill_params, {})

                        yield {
                            "event": "skill_completed",
                            "data": {
                                "skill_id": skill_id,
                                "result": result.message,
                                "success": result.success,
                            },
                        }

                        if result.success:
                            all_operations.extend(result.operations)
                    except Exception as e:
                        logger.exception(f"Skill {skill_id} execution failed")
                        yield {
                            "event": "skill_completed",
                            "data": {
                                "skill_id": skill_id,
                                "result": f"执行失败: {str(e)}",
                                "success": False,
                            },
                        }
                    finally:
                        if db:
                            db.close()

                # Generate summary message
                summary = self._build_summary(skills_used, all_operations)
                yield {"event": "message", "data": {"content": summary}}
                yield {
                    "event": "done",
                    "data": {
                        "cabinet_id": cabinet_id,
                        "operations": all_operations,
                        "skills_used": skills_used,
                    },
                }

            else:
                # LLM responded with text only (e.g., a question or explanation)
                content = assistant_msg.content or "我理解了你的需求，但没有找到合适的操作。"
                yield {"event": "message", "data": {"content": content}}
                yield {
                    "event": "done",
                    "data": {
                        "cabinet_id": cabinet_id,
                        "operations": [],
                        "skills_used": [],
                    },
                }

        except Exception as e:
            logger.exception("LLM call failed")
            yield {
                "event": "error",
                "data": {"content": f"AI 服务调用失败: {str(e)}"},
            }
            yield {
                "event": "done",
                "data": {
                    "cabinet_id": cabinet_id,
                    "operations": [],
                    "skills_used": [],
                },
            }

    async def _fallback_response(self, cabinet_id: int, message: str) -> dict:
        """Handle requests when no LLM API key is configured.

        Uses keyword matching as a last resort.
        """
        skill = self.registry.match_skill(message, {})
        if skill:
            db = self.db_session_factory() if self.db_session_factory else None
            try:
                bound_tools = self._bind_tools(db)
                skill.tools = bound_tools
                result = await skill.execute(cabinet_id, {}, {})
                return {
                    "event": "done",
                    "data": {
                        "cabinet_id": cabinet_id,
                        "message": result.message,
                        "operations": result.operations if result.success else [],
                        "skills_used": [skill.skill_id],
                        "fallback": True,
                    },
                }
            except Exception as e:
                return {
                    "event": "done",
                    "data": {
                        "cabinet_id": cabinet_id,
                        "message": f"执行失败: {str(e)}",
                        "operations": [],
                        "skills_used": [],
                        "fallback": True,
                    },
                }
            finally:
                if db:
                    db.close()
        else:
            return {
                "event": "done",
                "data": {
                    "cabinet_id": cabinet_id,
                    "message": (
                        "未配置 LLM API Key，无法处理复杂指令。"
                        "请在 .env 文件中设置 LLM_API_KEY 后重试。"
                        "支持的简单指令: 加隔板、加门板、加抽屉、换材质、查询结构、调整尺寸"
                    ),
                    "operations": [],
                    "skills_used": [],
                    "fallback": True,
                },
            }

    def _bind_tools(self, db) -> dict[str, Any]:
        """Create a tools dict with the db session bound to each tool function."""
        from agent import tools as tool_module

        return {
            "add_component": lambda **kw: tool_module.add_component(db, **kw),
            "remove_component": lambda **kw: tool_module.remove_component(db, **kw),
            "update_component": lambda **kw: tool_module.update_component(db, **kw),
            "get_cabinet_structure": lambda cid: tool_module.get_cabinet_structure(db, cid),
            "get_component": lambda cid, comp_id: tool_module.get_component(db, cid, comp_id),
            "list_components": lambda cid, ct=None: tool_module.list_components(db, cid, ct),
            "update_cabinet_size": lambda **kw: tool_module.update_cabinet_size(db, **kw),
            "get_snapshot_description": lambda cid: tool_module.get_snapshot_description(db, cid),
        }

    def _build_summary(self, skills_used: list[str], operations: list[dict]) -> str:
        """Build a human-readable summary of what was done."""
        if not skills_used:
            return "已完成操作。"

        parts = []
        op_types: dict[str, int] = {}
        for op in operations:
            action = op.get("action", op.get("component_type", "component"))
            op_types[action] = op_types.get(action, 0) + 1

        for skill_id in skills_used:
            skill = self.registry.get(skill_id)
            name = skill.skill_name if skill else skill_id
            parts.append(name)

        summary = f"已执行: {', '.join(parts)}。"
        if operations:
            summary += f" 共 {len(operations)} 个操作。"

        return summary
