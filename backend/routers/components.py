from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.component import (
    ComponentCreate,
    ComponentUpdate,
    ComponentResponse,
    ComponentListResponse,
)
from schemas.common import UnifiedResponse
from services.component_service import ComponentService

router = APIRouter(
    prefix="/api/cabinets/{cabinet_id}/components", tags=["components"]
)


def _svc(db: Session = Depends(get_db)) -> ComponentService:
    return ComponentService(db)


@router.get("", response_model=UnifiedResponse)
def list_components(cabinet_id: int, svc: ComponentService = Depends(_svc)):
    components = svc.list_by_cabinet(cabinet_id)
    return UnifiedResponse(
        success=True,
        data=ComponentListResponse(
            items=[ComponentResponse.model_validate(c) for c in components],
            total=len(components),
        ).model_dump(),
    )


@router.get("/{comp_id}", response_model=UnifiedResponse)
def get_component(cabinet_id: int, comp_id: int, svc: ComponentService = Depends(_svc)):
    comp = svc.get(comp_id)
    return UnifiedResponse(
        success=True, data=ComponentResponse.model_validate(comp).model_dump()
    )


@router.post("", response_model=UnifiedResponse, status_code=201)
def create_component(
    cabinet_id: int, body: ComponentCreate, svc: ComponentService = Depends(_svc)
):
    comp = svc.create(cabinet_id, body)
    return UnifiedResponse(
        success=True, data=ComponentResponse.model_validate(comp).model_dump()
    )


@router.put("/{comp_id}", response_model=UnifiedResponse)
def update_component(
    cabinet_id: int,
    comp_id: int,
    body: ComponentUpdate,
    svc: ComponentService = Depends(_svc),
):
    comp = svc.update(comp_id, body)
    return UnifiedResponse(
        success=True, data=ComponentResponse.model_validate(comp).model_dump()
    )


@router.delete("/{comp_id}", response_model=UnifiedResponse)
def delete_component(
    cabinet_id: int, comp_id: int, svc: ComponentService = Depends(_svc)
):
    svc.delete(comp_id)
    return UnifiedResponse(success=True, data=None)
