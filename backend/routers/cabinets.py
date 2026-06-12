from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.cabinet import (
    CabinetCreate,
    CabinetUpdate,
    CabinetSizeUpdate,
    CabinetFullUpdate,
    CabinetResponse,
    CabinetDetailResponse,
    CabinetListResponse,
)
from schemas.common import UnifiedResponse
from services.cabinet_service import CabinetService

router = APIRouter(prefix="/api/cabinets", tags=["cabinets"])


def _svc(db: Session = Depends(get_db)) -> CabinetService:
    return CabinetService(db)


@router.get("", response_model=UnifiedResponse)
def list_cabinets(svc: CabinetService = Depends(_svc)):
    cabinets = svc.list_all()
    return UnifiedResponse(
        success=True,
        data=CabinetListResponse(
            items=[CabinetResponse.model_validate(c) for c in cabinets],
            total=len(cabinets),
        ).model_dump(),
    )


@router.post("", response_model=UnifiedResponse, status_code=201)
def create_cabinet(body: CabinetCreate, svc: CabinetService = Depends(_svc)):
    cabinet = svc.create_default(
        name=body.name,
        width=body.width,
        height=body.height,
        depth=body.depth,
        board_thickness=body.board_thickness,
        global_material=body.global_material,
        global_color=body.global_color,
    )
    return UnifiedResponse(
        success=True, data=CabinetResponse.model_validate(cabinet).model_dump()
    )


@router.get("/{cabinet_id}", response_model=UnifiedResponse)
def get_cabinet(cabinet_id: int, svc: CabinetService = Depends(_svc)):
    cabinet = svc.get_with_components(cabinet_id)
    data = CabinetResponse.model_validate(cabinet).model_dump()
    from schemas.component import ComponentResponse

    data["components"] = [
        ComponentResponse.model_validate(c).model_dump() for c in cabinet.components
    ]
    return UnifiedResponse(success=True, data=data)


@router.put("/{cabinet_id}", response_model=UnifiedResponse)
def update_cabinet(
    cabinet_id: int, body: CabinetFullUpdate, svc: CabinetService = Depends(_svc)
):
    """Update cabinet and sync all components."""
    cabinet = svc.full_update(cabinet_id, body)
    return UnifiedResponse(
        success=True, data=CabinetResponse.model_validate(cabinet).model_dump()
    )


@router.delete("/{cabinet_id}", response_model=UnifiedResponse)
def delete_cabinet(cabinet_id: int, svc: CabinetService = Depends(_svc)):
    svc.delete(cabinet_id)
    return UnifiedResponse(success=True, data=None)


@router.put("/{cabinet_id}/size", response_model=UnifiedResponse)
def update_cabinet_size(
    cabinet_id: int, body: CabinetSizeUpdate, svc: CabinetService = Depends(_svc)
):
    cabinet = svc.update_size(cabinet_id, body)
    return UnifiedResponse(
        success=True, data=CabinetResponse.model_validate(cabinet).model_dump()
    )
