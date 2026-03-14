from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class IngestRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None


class IngestStatus(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["pending", "processing", "done", "error"] = "pending"
    progress_message: str = "Queued"
    recipe_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
