from pydantic import BaseModel
from typing import Optional, Dict, Any

class ServiceError(BaseModel):
    """Standardized error response for service operations"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    stage: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Failed to upload file",
                "details": {
                    "status_code": 500,
                    "message": "Connection timeout"
                },
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "stage": "uploading"
            }
        } 