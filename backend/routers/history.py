from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.history import HistoryCreate, HistoryResponse, HistoryListResponse
from schemas.common import UnifiedResponse
from services.history_service import HistoryService

router = APIRouter(
    prefix="/api/cabinets/{cabinet_id}/history", tags=["history"]
)


def _svc(db: Session = Depends(get_db)) -> HistoryService:
    return HistoryService(db)


@router.get("", response_model=UnifiedResponse)
def list_history(cabinet_id: int, svc: HistoryService = Depends(_svc)):
    records = svc.list_by_cabinet(cabinet_id)
    return UnifiedResponse(
        success=True,
        data=HistoryListResponse(
            items=[HistoryResponse.model_validate(r) for r in records],
            total=len(records),
        ).model_dump(),
    )


@router.get("/{history_id}", response_model=UnifiedResponse)
def get_history(
    cabinet_id: int, history_id: int, svc: HistoryService = Depends(_svc)
):
    record = svc.get(history_id)
    return UnifiedResponse(
        success=True, data=HistoryResponse.model_validate(record).model_dump()
    )


@router.post("", response_model=UnifiedResponse, status_code=201)
def create_history(
    cabinet_id: int, body: HistoryCreate, svc: HistoryService = Depends(_svc)
):
    record = svc.create(cabinet_id, body)
    return UnifiedResponse(
        success=True, data=HistoryResponse.model_validate(record).model_dump()
    )
