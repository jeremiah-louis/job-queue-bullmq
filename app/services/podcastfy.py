import os
from typing import Dict, Optional
from podcastfy.client import generate_podcast
from decouple import config
from fastapi import UploadFile
from .file_upload import FileUploadService

class PodcastfyService:
    def __init__(self):
        self.file_upload_service = FileUploadService()
        # Set environment variables
        os.environ["GEMINI_API_KEY"] = config("GEMINI_API_KEY")
        os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")
        self.storage_dir = ".storage"
        os.makedirs(self.storage_dir, exist_ok=True)

    async def generate_audio(self, transcript_file: UploadFile, collection_id: str) -> Dict:
        """
        Generate audio from transcript and return the S3 URL.
        """
        temp_transcript_path = None
        audio_file = None
        
        try:
            if not transcript_file:
                raise Exception("Transcript file is required")

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
                upload_result = await self.file_upload_service.upload_file(
                    audio_upload,
                    collection_id
                )

            # Cleanup
            if temp_transcript_path and os.path.exists(temp_transcript_path):
                os.remove(temp_transcript_path)
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)

            return upload_result

        except Exception as e:
            # Cleanup in case of error
            if temp_transcript_path and os.path.exists(temp_transcript_path):
                os.remove(temp_transcript_path)
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            raise Exception(f"Failed to generate audio: {str(e)}") 