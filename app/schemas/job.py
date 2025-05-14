from fastapi import Form
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum
from datetime import datetime, UTC
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING_TRANSCRIPT = "processing_transcript"
    PROCESSING_AUDIO = "processing_audio"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobBase(BaseModel):
    input_resource_type: str
    input_resource_url: Optional[str] = Form(None)
    input_collection_id: str
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    result_audio_url: Optional[str] = None

class JobCreate(JobBase):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    result_audio_url: Optional[str] = None
    input_resource_url: Optional[str] = None

class Job(JobBase):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        from_attributes = True 