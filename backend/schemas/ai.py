from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChatMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str


class AIChatRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cabinet_id: int
    message: str
    history: list[ChatMessage] = []


class AIChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    skill_used: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


class SkillInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: str
    skill_name: str
    description: str
    examples: list[str]


class SkillsListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skills: list[SkillInfo]
