from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.input import ResourceType
from app.services.file_upload import FileUploadService
from app.services.wetrocloud import WetrocloudService
from app.services.podcastfy import PodcastfyService
from pydantic import HttpUrl
from typing import Dict, Optional
import os
import io

app = FastAPI(
    title="Podcast Generation API",
    description="API for generating podcasts from various resources",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

file_upload_service = FileUploadService()
wetrocloud_service = WetrocloudService()
podcastfy_service = PodcastfyService()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/generate-podcast")
async def generate_podcast(
    resource_type: str = Form(...),
    resource_data: Optional[str] = Form(None),
    collection_id: str = Form(...),
    file: Optional[UploadFile] = File(None)
) -> Dict:
    """
    Generate a podcast from the given resource.
    
    Args:
        resource_type: Type of resource (pdf, youtube, website)
        resource_data: URL for YouTube/Website resources
        collection_id: Collection ID for file upload
        file: PDF file for PDF resources
        
    Returns:
        Dict containing status message, transcript, and audio URL
    """
    temp_transcript_path = None
    try:
        # Convert string to ResourceType enum
        try:
            resource_type_enum = ResourceType(resource_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid resource type. Must be one of: pdf, youtube, website"
            )

        if resource_type_enum == ResourceType.PDF:
            if not file:
                raise HTTPException(
                    status_code=400,
                    detail="File is required for PDF resources"
                )
            
            if file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF files are supported"
                )
            
            # Upload file to get S3 URL
            upload_response = await file_upload_service.upload_file(file, collection_id)
            if not upload_response.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to upload file"
                )
            
            resource_url = upload_response["url"]
        
        elif resource_type_enum in [ResourceType.YOUTUBE, ResourceType.WEBSITE]:
            if not resource_data:
                raise HTTPException(
                    status_code=400,
                    detail="URL is required for YouTube/Website resources"
                )
            
            # Validate URL format
            try:
                HttpUrl(resource_data)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL format"
                )
            
            resource_url = resource_data
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported resource type"
            )
        
        # Generate transcript
        transcript = await wetrocloud_service.generate_transcript(
            collection_id=collection_id,
            resource_url=resource_url,
            resource_type=resource_type_enum.value
        )

        transcript_bytes = transcript.encode('utf-8')
        transcript_file = UploadFile(
            file=io.BytesIO(transcript_bytes),
            filename="transcript.txt"
        )
        # Generate audio using PodcastfyService
        audio_result = await podcastfy_service.generate_audio(
            transcript_file=transcript_file,
            collection_id=collection_id
        )

        return {
            "success": True,
            "message": f"{resource_type_enum.value.capitalize()} processing completed",
            "data": {
                "transcript": transcript,
                "audio_url": audio_result["url"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Cleanup temporary file if it exists
        if temp_transcript_path and os.path.exists(temp_transcript_path):
            os.remove(temp_transcript_path)
