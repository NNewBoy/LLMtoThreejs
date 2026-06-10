from datetime import datetime
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Component(Base):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cabinet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cabinets.id", ondelete="CASCADE"), nullable=False
    )
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("components.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str] = mapped_column(String(64), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    depth: Mapped[float] = mapped_column(Float, nullable=False)
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    material: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True, default=None)
    door_style: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    handle_style: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    cabinet: Mapped["Cabinet"] = relationship(back_populates="components")
    parent: Mapped["Component | None"] = relationship(
        "Component", remote_side="Component.id", back_populates="children"
    )
    children: Mapped[list["Component"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan", lazy="selectin"
    )
