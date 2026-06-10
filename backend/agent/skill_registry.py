"""SkillRegistry — manages registration, discovery, and invocation of Skills.

Per SPEC2 section 10.3: provides skill listing, prompt generation, and
OpenAI function-call schema generation for the agent.
"""

from typing import Any, Optional

from skills.base import BaseSkill


class SkillRegistry:
    """Central registry for all cabinet design skills."""

    def __init__(self, tools: dict[str, Any]):
        self.tools = tools
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """Register a skill instance."""
        self._skills[skill.skill_id] = skill

    def get(self, skill_id: str) -> Optional[BaseSkill]:
        """Get a skill by its ID."""
        return self._skills.get(skill_id)

    def list_all(self) -> list[dict]:
        """Return metadata for all registered skills."""
        return [
            {
                "skill_id": s.skill_id,
                "skill_name": s.skill_name,
                "description": s.description,
                "examples": s.examples,
            }
            for s in self._skills.values()
        ]

    def get_skill_descriptions_for_prompt(self) -> str:
        """Generate skill descriptions text for injection into the system prompt."""
        lines = []
        for s in self._skills.values():
            lines.append(f"- **{s.skill_id}** ({s.skill_name}): {s.description}")
            lines.append(f"  触发示例: {'; '.join(s.examples[:3])}")
        return "\n".join(lines)

    def get_all_skill_tools(self) -> list[dict]:
        """Convert all registered skills to OpenAI function-call schemas."""
        return [self._build_skill_tool_schema(s) for s in self._skills.values()]

    def match_skill(self, intent: str, context: dict) -> Optional[BaseSkill]:
        """Fallback keyword-based skill matching when LLM is unavailable."""
        for skill in self._skills.values():
            if skill.can_handle(intent, context):
                return skill
        return None

    def _build_skill_tool_schema(self, skill: BaseSkill) -> dict:
        """Build an OpenAI function-call schema for a skill."""
        return {
            "type": "function",
            "function": {
                "name": skill.skill_id,
                "description": skill.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cabinet_id": {
                            "type": "integer",
                            "description": "The ID of the cabinet to operate on",
                        },
                        "params": {
                            "type": "object",
                            "description": "Skill-specific parameters",
                        },
                    },
                    "required": ["cabinet_id", "params"],
                },
            },
        }
