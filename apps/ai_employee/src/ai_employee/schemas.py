from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["low", "normal", "high"]
Status = Literal["pending", "in_progress", "done", "blocked"]


class NeedsActionFrontmatter(BaseModel):
    type: str
    created_at: datetime
    status: Status = "pending"
    priority: Priority = "normal"

    # Optional fields used by file drop watcher
    source: str | None = None
    source_path: str | None = None
    original_name: str | None = None
    size_bytes: int | None = None


class OrchestratorHeartbeat(BaseModel):
    name: str = "orchestrator"
    last_run_at: datetime = Field(default_factory=datetime.utcnow)
    note: str | None = None
