from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class OperationHistory(Base):
    __tablename__ = "operation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cabinet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cabinets.id", ondelete="CASCADE"), nullable=False
    )
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cabinet: Mapped["Cabinet"] = relationship(back_populates="operation_history")
