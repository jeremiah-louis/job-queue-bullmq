import io
import httpx
from fastapi import UploadFile
from typing import Dict, Optional
from app.schemas.error import ServiceError
import logging

logger = logging.getLogger(__name__)

class FileUploadService:
    def __init__(self, upload_service_url: str = "https://file-upload-service-python.vercel.app/upload/"):
        self.upload_service_url = upload_service_url

    async def upload_file(self, file_name: str, file_content_type: str, file_content: bytes, collection_id: str, job_id: Optional[str] = None) -> Dict:
        """
        Upload a file to the external file upload service and return the S3 URL.
        
        Args:
            file: The file to upload
            collection_id: ID for the collection
            job_id: Optional job ID for error tracking
            
        Returns:
            Dict containing upload result or error details
        """
        try:
            file_bytes = io.BytesIO(file_content)
            files = {"file": (file_name, file_bytes, file_content_type)}
            data = {"collection_id": collection_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.upload_service_url,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Upload service response: {response_data}")
                
                # Extract the file URL from the response
                if not response_data.get("url"):
                    logger.error(f"No URL found in upload response: {response_data}")
                    raise ValueError("No URL returned in upload response")
                    
                return {
                    "success": True,
                    "url": response_data["url"]
                }
                
        except httpx.HTTPError as e:
            error = ServiceError(
                error=f"Failed to upload file: {str(e)}",
                details={
                    "status_code": e.response.status_code if hasattr(e, 'response') else None,
                    "message": str(e)
                },
                job_id=job_id,
                stage="uploading"
            )
            logger.error(f"File upload failed: {error.model_dump_json()}")
            return error.model_dump()
            
        except Exception as e:
            error = ServiceError(
                error=f"Unexpected error during file upload: {str(e)}",
                details={"message": str(e)},
                job_id=job_id,
                stage="uploading"
            )
            logger.error(f"Unexpected error during file upload: {error.model_dump_json()}")
            return error.model_dump() 