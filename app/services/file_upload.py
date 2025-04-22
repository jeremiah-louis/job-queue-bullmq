import httpx
from fastapi import UploadFile
from typing import Dict, Optional

class FileUploadService:
    def __init__(self, upload_service_url: str = "https://file-upload-service-python.vercel.app/upload/"):
        self.upload_service_url = upload_service_url

    async def upload_file(self, file: UploadFile, collection_id: str) -> Dict:
        """
        Upload a file to the external file upload service and return the S3 URL.
        """
        try:
            files = {"file": (file.filename, file.file, file.content_type)}
            data = {"collection_id": collection_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.upload_service_url,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to upload file: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during file upload: {str(e)}") 