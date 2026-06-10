from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Cabinet(Base):
    __tablename__ = "cabinets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="未命名柜子")
    width: Mapped[float] = mapped_column(Float, nullable=False, default=800.0)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=2000.0)
    depth: Mapped[float] = mapped_column(Float, nullable=False, default=500.0)
    board_thickness: Mapped[float] = mapped_column(Float, nullable=False, default=18.0)
    global_material: Mapped[str] = mapped_column(String(32), default="wood_oak")
    global_color: Mapped[str] = mapped_column(String(16), default="#C49A6C")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    components: Mapped[list["Component"]] = relationship(
        back_populates="cabinet", cascade="all, delete-orphan", lazy="selectin"
    )
    operation_history: Mapped[list["OperationHistory"]] = relationship(
        back_populates="cabinet", cascade="all, delete-orphan", lazy="selectin"
    )
    ai_chat_history: Mapped[list["AIChatHistory"]] = relationship(
        back_populates="cabinet", cascade="all, delete-orphan", lazy="selectin"
    )
