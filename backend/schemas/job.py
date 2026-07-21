from typing import Dict, Optional

from pydantic import BaseModel, Field


class ModelResult(BaseModel):
    status: str
    url: Optional[str] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    success: bool
    job_id: str
    status: str
    progress: int
    input_image: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: Dict[str, ModelResult] = Field(default_factory=dict)
    error: Optional[str] = None
