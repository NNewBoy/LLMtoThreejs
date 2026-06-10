"""Base Skill ABC and SkillResult dataclass per SPEC2 section 10.1."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SkillResult:
    """Skill execution result returned to the agent and frontend."""

    success: bool
    message: str
    operations: list[dict] = field(default_factory=list)
    error: Optional[str] = None


class BaseSkill(ABC):
    """Abstract base class for all cabinet design skills."""

    skill_id: str
    skill_name: str
    description: str
    examples: list[str]

    def __init__(self, tools: dict[str, Any]):
        """
        Args:
            tools: dict of atomic tool functions, e.g.
                   {'add_component': async_func, 'get_cabinet_structure': async_func, ...}
        """
        self.tools = tools

    @abstractmethod
    def can_handle(self, intent: str, context: dict) -> bool:
        """Return True if this skill can handle the given user intent."""
        ...

    @abstractmethod
    async def execute(self, cabinet_id: int, params: dict, context: dict) -> SkillResult:
        """Execute the skill and return a SkillResult with operations for the frontend."""
        ...

    async def pre_check(self, cabinet_id: int, params: dict) -> bool:
        """Optional pre-execution validation."""
        return True

    async def post_check(self, cabinet_id: int, result: SkillResult) -> bool:
        """Optional post-execution validation."""
        return True

    async def rollback(self, cabinet_id: int, params: dict) -> None:
        """Optional rollback on failure."""
        pass
