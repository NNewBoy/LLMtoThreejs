from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class UnifiedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    data: Any = None
    error: Optional[str] = None
