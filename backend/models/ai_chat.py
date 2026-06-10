from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class AIChatHistory(Base):
    __tablename__ = "ai_chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cabinet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cabinets.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    skill_used: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    tool_calls_json: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cabinet: Mapped["Cabinet"] = relationship(back_populates="ai_chat_history")
