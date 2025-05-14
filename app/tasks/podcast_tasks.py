from app.services.file_upload import FileUploadService
from app.services.wetrocloud import WetrocloudService
from app.services.podcastfy import PodcastfyService
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobUpdate, JobStatus
from fastapi import UploadFile
from pydantic import HttpUrl
import io
import logging
import os
import tempfile
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class PodcastTaskHandler:
    def __init__(self):
        self.file_upload_service = FileUploadService()
        self.wetrocloud_service = WetrocloudService()
        self.podcastfy_service = PodcastfyService()
        self.job_repository = JobRepository()
        self._is_cancelled = False
        self._temp_files = []

    async def cancel(self):
        """Cancel the current task gracefully"""
        self._is_cancelled = True
        logger.info("Task cancellation requested")

    async def process_podcast(
        self,
        job_id: str,
        resource_type: str,
        collection_id: str,
        resource_data: str = None,
        file_name: Optional[str] = None,
        file_content_type: Optional[str] = None,
        file_content: Optional[bytes] = None
    ):
        """Process podcast generation in background"""
        try:
            logger.info(f"Starting podcast processing for job {job_id}")
            
            # Upload file if PDF
            if resource_type == "file":
                await self._handle_pdf_upload(job_id, file_name, file_content_type, file_content, collection_id)
 
            else:
                # For YouTube/Website, use resource_data directly
                await self._update_job_status(job_id, JobStatus.PROCESSING_TRANSCRIPT)

            if self._is_cancelled:
                logger.info(f"Task cancelled during initial setup for job {job_id}")
                await self._update_job_status(job_id, JobStatus.CANCELLED)
                return

            # Get current job state
            job = await self.job_repository.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Generate transcript
            try:
                logger.info(f"Generating transcript for job {job_id} and resource url {job.input_resource_url}")
                transcript = await self.wetrocloud_service.generate_transcript(
                    collection_id=collection_id,
                    resource_url=job.input_resource_url,
                    resource_type=resource_type
                )
                
                if self._is_cancelled:
                    logger.info(f"Task cancelled during transcript generation for job {job_id}")
                    await self._update_job_status(job_id, JobStatus.CANCELLED)
                    return
                
                await self._update_job_status(job_id, JobStatus.PROCESSING_AUDIO)
            except Exception as e:
                logger.error(f"Transcript generation failed for job {job_id}: {str(e)}")
                await self._update_job_status(job_id, JobStatus.FAILED, error=str(e))
                return

            # Generate audio
            try:
                logger.info(f"Generating audio for job {job_id}")
                logger.info(f"Transcript type: {type(transcript)}")
                logger.info(f"Transcript content: {transcript}")
                if isinstance(transcript, dict) and "error" in transcript:
                    raise Exception(transcript["error"])
                transcript_bytes = transcript.encode('utf-8')
                transcript_file = UploadFile(
                    file=io.BytesIO(transcript_bytes),
                    filename="transcript.txt"
                )
                self._temp_files.append(transcript_file)
                
                audio_result = await self.podcastfy_service.generate_audio(
                    transcript_file=transcript_file,
                    collection_id=collection_id
                )
                
                if self._is_cancelled:
                    logger.info(f"Task cancelled during audio generation for job {job_id}")
                    await self._update_job_status(job_id, JobStatus.CANCELLED)
                    return
                
                await self._update_job_status(
                    job_id,
                    JobStatus.COMPLETE,
                    audio_url=audio_result["url"]
                )
                logger.info(f"Successfully completed podcast processing for job {job_id}")
            except Exception as e:
                logger.error(f"Audio generation failed for job {job_id}: {str(e)}")
                await self._update_job_status(job_id, JobStatus.FAILED, error=str(e))

        except Exception as e:
            logger.error(f"Podcast processing failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, JobStatus.FAILED, error=str(e))
        finally:
            await self._cleanup()

    async def _handle_pdf_upload(self, job_id: str, file_name: str, file_content_type: str, file_content: bytes, collection_id: str):
        """Handle PDF file upload"""
        try:
            logger.info(f"Starting PDF upload for job {job_id}")
            await self._update_job_status(job_id, JobStatus.UPLOADING)
            upload_response = await self.file_upload_service.upload_file(file_name, file_content_type, file_content, collection_id)
            
            logger.info(f"Upload response for job {job_id}")
            
            if not upload_response.get("success"):
                raise Exception("Failed to upload file")
            # Assuming the response contains the URL of the uploaded file
            uploaded_file_url = upload_response.get("url")
            logger.info(f"Extracted URL for job {job_id}: {uploaded_file_url}")

            # Update job with the file URL
            await self.job_repository.update_job(job_id, JobUpdate(
                status=JobStatus.PROCESSING_TRANSCRIPT,
                input_resource_url=uploaded_file_url,
                error_message=None,
                result_audio_url=None
            ))
            logger.info(f"PDF upload completed for job {job_id}")
        except Exception as e:
            logger.error(f"PDF upload failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, JobStatus.FAILED, error=str(e))
            raise

    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: str = None,
        audio_url: str = None
    ):
        """Update job status with optional error message"""
        update_data = JobUpdate(
            status=status,
            error_message=error,
            result_audio_url=audio_url
        )
        
        await self.job_repository.update_job(job_id, update_data)
        logger.info(f"Updated job {job_id} status to {status}")

    async def _cleanup(self):
        """Clean up temporary files"""
        for temp_file in self._temp_files:
            try:
                if hasattr(temp_file, 'file') and hasattr(temp_file.file, 'close'):
                    temp_file.file.close()
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")
        self._temp_files = [] 