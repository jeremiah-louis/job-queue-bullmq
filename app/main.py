from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.schemas.input import ResourceType
from app.services.file_upload import FileUploadService
from app.services.wetrocloud import WetrocloudService
from app.services.podcastfy import PodcastfyService
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobStatus, Job
from app.tasks.podcast_tasks import PodcastTaskHandler
from pydantic import HttpUrl
from typing import Dict, Optional
import os
import io
import logging
from datetime import datetime, timedelta
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Podcast Generation API",
    description="API for generating podcasts from various resources",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


file_upload_service = FileUploadService()
wetrocloud_service = WetrocloudService()
podcastfy_service = PodcastfyService()
job_repository = JobRepository()
podcast_task_handler = PodcastTaskHandler()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def health_check():
    return {"status": "healthy"}

@app.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    response: Response
) -> Dict:
    """
    Get the status of a podcast generation job.
    
    Args:
        job_id: The ID of the job to check
        
    Returns:
        Dict containing job status and details
    """
    logger.info(f"Checking status for job {job_id}")
    
    try:
        job = await job_repository.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        # Set cache headers
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # If job is complete, redirect to audio URL
        if job.status == JobStatus.COMPLETE and job.result_audio_url:
            logger.info(f"Job {job_id} complete, returning audio URL")
            return {
                "job_id": job.job_id,
                "status": job.status,
                "audio_url": str(job.result_audio_url)
            }
        
        # For failed jobs, return error details
        if job.status == JobStatus.FAILED:
            logger.info(f"Job {job_id} failed: {job.error_message}")
            return {
                "job_id": job.job_id,
                "status": job.status,
                "error": job.error_message
            }
        
        # For cancelled jobs, return cancellation status
        if job.status == JobStatus.CANCELLED:
            logger.info(f"Job {job_id} was cancelled")
            return {
                "job_id": job.job_id,
                "status": job.status
            }
        
        # For all other states, return basic status
        logger.info(f"Job {job_id} status: {job.status}")
        return {
            "job_id": job.job_id,
            "status": job.status
        }
    
    except HTTPException as e:
        logger.error(f"HTTP Exception for job {job_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking status for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/generate-podcast")
async def generate_podcast(
    background_tasks: BackgroundTasks,
    resource_type: str = Form(...),
    resource_data: Optional[str] = Form(None),
    collection_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    response: Response = None
) -> Dict:
    """
    Generate a podcast from the given resource.
    
    Args:
        resource_type: Type of resource (file, youtube, web)
        resource_data: URL for YouTube/Web resources
        collection_id: Collection ID for file upload
        file: PDF file for file resources
        
    Returns:
        Dict containing job ID for status tracking
    """
    logger.info(f"Received request with parameters:")
    logger.info(f"Resource Type: {resource_type}")
    logger.info(f"Resource Data: {resource_data}")
    logger.info(f"Collection ID: {collection_id}")
    logger.info(f"File present: {'Yes' if file else 'No'}")

    try:
        # Convert string to ResourceType enum
        try:
            resource_type_enum = ResourceType(resource_type.lower())
            logger.info(f"Successfully parsed resource type: {resource_type_enum}")
        except ValueError as e:
            logger.error(f"Invalid resource type: {resource_type}. Error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid resource type. Must be one of: file, youtube, web"
            )

        # Initialize variables
        file_name = None
        file_content_type = None
        file_content = None

        # Validate input based on resource type
        if resource_type_enum == ResourceType.FILE:
            if not file:
                logger.error("No file provided for file resource")
                raise HTTPException(
                    status_code=400,
                    detail="File is required for file resources"
                )
            
            # Read file content immediately
            file_content = await file.read()
            file_name = file.filename
            file_content_type = file.content_type

            if file.content_type != "application/pdf":
                logger.error(f"Invalid file type: {file.content_type}")
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF files are supported"
                )
        
        elif resource_type_enum in [ResourceType.YOUTUBE, ResourceType.WEB]:
            if not resource_data:
                logger.error("No URL provided for YouTube/Web resource")
                raise HTTPException(
                    status_code=400,
                    detail="URL is required for YouTube/Web resources"
                )
            
            # Validate URL format
            try:
                HttpUrl(resource_data)
                logger.info(f"URL validated successfully: {resource_data}")
            except ValueError as e:
                logger.error(f"Invalid URL format: {resource_data}. Error: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL format"
                )
        
        else:
            logger.error(f"Unsupported resource type: {resource_type_enum}")
            raise HTTPException(
                status_code=400,
                detail="Unsupported resource type"
            )
        
        # Create job record
        job = await job_repository.create_job(
            JobCreate(
                input_resource_type=resource_type_enum.value,
                input_collection_id=collection_id,
                input_resource_url=resource_data if resource_type_enum in [ResourceType.YOUTUBE, ResourceType.WEB] else None,
                status=JobStatus.PENDING
            )
        )
        
        # Add task to background tasks
        background_tasks.add_task(
            podcast_task_handler.process_podcast,
            job_id=job.job_id,
            resource_type=resource_type_enum.value,
            collection_id=collection_id,
            resource_data=resource_data,
            file_name=file_name,
            file_content_type=file_content_type,
            file_content=file_content
        )
        
        # Set response headers
        response.status_code = 202
        response.headers["Location"] = f"/status/{job.job_id}"
        
        return {
            "job_id": job.job_id,
            "status": "accepted",
            "status_url": f"/status/{job.job_id}"
        }
    
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
