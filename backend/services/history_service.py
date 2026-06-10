from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.operation_history import OperationHistory
from models.cabinet import Cabinet
from schemas.history import HistoryCreate


class HistoryService:
    """Operation history service — stores and retrieves cabinet snapshots."""

    def __init__(self, db: Session):
        self.db = db

    def list_by_cabinet(self, cabinet_id: int) -> list[OperationHistory]:
        self._verify_cabinet(cabinet_id)
        return (
            self.db.query(OperationHistory)
            .filter(OperationHistory.cabinet_id == cabinet_id)
            .order_by(OperationHistory.created_at.desc())
            .all()
        )

    def get(self, history_id: int) -> OperationHistory:
        record = (
            self.db.query(OperationHistory)
            .filter(OperationHistory.id == history_id)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="History record not found")
        return record

    def create(self, cabinet_id: int, data: HistoryCreate) -> OperationHistory:
        self._verify_cabinet(cabinet_id)
        record = OperationHistory(cabinet_id=cabinet_id, **data.model_dump())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _verify_cabinet(self, cabinet_id: int) -> None:
        cabinet = self.db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
        if not cabinet:
            raise HTTPException(status_code=404, detail="Cabinet not found")
