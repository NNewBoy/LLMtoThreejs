from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.component import Component
from models.cabinet import Cabinet
from schemas.component import ComponentCreate, ComponentUpdate


class ComponentService:
    """Component data service — pure CRUD, no constraint logic."""

    def __init__(self, db: Session):
        self.db = db

    def list_by_cabinet(self, cabinet_id: int) -> list[Component]:
        self._verify_cabinet(cabinet_id)
        return (
            self.db.query(Component)
            .filter(Component.cabinet_id == cabinet_id)
            .order_by(Component.sort_order, Component.id)
            .all()
        )

    def get(self, component_id: int) -> Component:
        comp = self.db.query(Component).filter(Component.id == component_id).first()
        if not comp:
            raise HTTPException(status_code=404, detail="Component not found")
        return comp

    def create(self, cabinet_id: int, data: ComponentCreate) -> Component:
        self._verify_cabinet(cabinet_id)
        component = Component(cabinet_id=cabinet_id, **data.model_dump())
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        return component

    def update(self, component_id: int, data: ComponentUpdate) -> Component:
        component = self.get(component_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)
        self.db.commit()
        self.db.refresh(component)
        return component

    def delete(self, component_id: int) -> None:
        component = self.get(component_id)
        self.db.delete(component)
        self.db.commit()

    def batch_replace(self, cabinet_id: int, components_data: list[ComponentCreate]) -> list[Component]:
        """Replace all components for a cabinet. Used after AI operations."""
        self._verify_cabinet(cabinet_id)
        # Delete existing components
        self.db.query(Component).filter(Component.cabinet_id == cabinet_id).delete()
        self.db.flush()

        # Create new components
        new_components = []
        for data in components_data:
            comp = Component(cabinet_id=cabinet_id, **data.model_dump())
            self.db.add(comp)
            new_components.append(comp)

        self.db.commit()
        for comp in new_components:
            self.db.refresh(comp)
        return new_components

    def _verify_cabinet(self, cabinet_id: int) -> None:
        cabinet = self.db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
        if not cabinet:
            raise HTTPException(status_code=404, detail="Cabinet not found")
