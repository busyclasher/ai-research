from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentIngestPayload(BaseModel):
    """Metadata accompanying an ingestion request."""

    source_type: str = Field(..., description="Type of the upstream source (ugc, api, partner, etc.)")
    language: Optional[str] = Field(None, description="ISO language code if known")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional free-form metadata")


class DocumentResponse(BaseModel):
    """Representation of a stored document."""

    id: str
    source_type: str
    status: str
    raw_uri: str
    original_filename: Optional[str]
    language: Optional[str]
    metadata: dict[str, Any]
    ingested_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    modality: str
    ordinal: int
    text: str
    metadata: dict[str, Any]

    model_config = {"from_attributes": True}
