import io
import os
from typing import Dict, Optional, Union
from podcastfy.client import generate_podcast
from fastapi import UploadFile
from .file_upload import FileUploadService
import logging
from app.schemas.error import ServiceError

logger = logging.getLogger(__name__)

class PodcastfyService:
    def __init__(self):
        self.file_upload_service = FileUploadService()
        # Set environment variables
        os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        self.storage_dir = ".storage"
        os.makedirs(self.storage_dir, exist_ok=True)

    async def generate_audio(self, transcript_file: UploadFile, collection_id: str, job_id: Optional[str] = None) -> Dict:
        """
        Generate audio from transcript and return the S3 URL.
        
        Args:
            transcript_file: The transcript file to process
            collection_id: ID for the collection
            job_id: Optional job ID for error tracking
            
        Returns:
            Dict containing audio URL or error details
        """
        temp_transcript_path = None
        audio_file = None
        
        try:
            if not transcript_file:
                error = ServiceError(
                    error="Transcript file is required",
                    job_id=job_id,
                    stage="processing_audio"
                )
                logger.error(f"Audio generation failed: {error.model_dump_json()}")
                return error.model_dump()

            # Save transcript to temporary file
            temp_transcript_path = os.path.join(self.storage_dir, "temp_transcript.txt")
            with open(temp_transcript_path, "wb") as f:
                content = await transcript_file.read()
                f.write(content)

            # Generate podcast
            audio_file = generate_podcast(transcript_file=temp_transcript_path)
            
            # Upload audio file
            with open(audio_file, "rb") as f:
                # Create a proper UploadFile object
                audio_upload = UploadFile(
                    file=f,
                    filename=os.path.basename(audio_file)
                )
                # Read the file content
                file_content = await audio_upload.read()
                upload_result = await self.file_upload_service.upload_file(
                    file_name=audio_upload.filename,
                    file_content_type=audio_upload.content_type,
                    file_content=file_content,
                    collection_id=collection_id,
                    job_id=job_id
                )

            # Check if upload was successful
            if not upload_result.get("success", False):
                error = ServiceError(
                    error="Failed to upload generated audio",
                    details=upload_result,
                    job_id=job_id,
                    stage="processing_audio"
                )
                logger.error(f"Audio upload failed: {error.model_dump_json()}")
                return error.model_dump()

            # Cleanup
            if temp_transcript_path and os.path.exists(temp_transcript_path):
                os.remove(temp_transcript_path)
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)

            return {"success": True, **upload_result}

        except Exception as e:
            error = ServiceError(
                error=f"Failed to generate audio: {str(e)}",
                details={"message": str(e)},
                job_id=job_id,
                stage="processing_audio"
            )
            logger.error(f"Audio generation failed: {error.model_dump_json()}")
            return error.model_dump()
            
        finally:
            # Cleanup in case of error
            if temp_transcript_path and os.path.exists(temp_transcript_path):
                os.remove(temp_transcript_path)
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file) 