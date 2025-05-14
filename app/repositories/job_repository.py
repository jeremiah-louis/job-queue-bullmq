from pymongo import ReturnDocument
from app.core.mongodb import MongoDB
from app.schemas.job import Job, JobCreate, JobUpdate, JobStatus
from datetime import datetime, UTC
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class JobRepository:
    def __init__(self):
        self.mongodb = MongoDB()
        self.collection = self.mongodb.collection

    async def create_job(self, job: JobCreate) -> Job:
        """Create a new job in the database"""
        try:
            job_dict = job.model_dump()
            job_dict["created_at"] = datetime.now(UTC)
            job_dict["updated_at"] = datetime.now(UTC)
            
            result = self.collection.insert_one(job_dict)
            job_dict["_id"] = result.inserted_id
            
            return Job(**job_dict)
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its ID"""
        try:
            job_dict = self.collection.find_one({"job_id": job_id})
            if job_dict:
                return Job(**job_dict)
            return None
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {str(e)}")
            raise

    async def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[Job]:
        """Update a job's status and other fields"""
        try:
            update_data = job_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.now(UTC)
            logger.info(f"Updating job {job_id} with data: {update_data}")
            
            result = self.collection.find_one_and_update(
                {"job_id": job_id},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
            
            if result:
                return Job(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job by its ID"""
        try:
            result = self.collection.delete_one({"job_id": job_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise

    def validate_status_transition(self, current_status: JobStatus, new_status: JobStatus) -> bool:
        """Validate if a status transition is allowed"""
        valid_transitions = {
            JobStatus.PENDING: [JobStatus.UPLOADING],
            JobStatus.UPLOADING: [JobStatus.PROCESSING_TRANSCRIPT, JobStatus.FAILED],
            JobStatus.PROCESSING_TRANSCRIPT: [JobStatus.PROCESSING_AUDIO, JobStatus.FAILED],
            JobStatus.PROCESSING_AUDIO: [JobStatus.COMPLETE, JobStatus.FAILED],
            JobStatus.COMPLETE: [],
            JobStatus.FAILED: []
        }
        
        return new_status in valid_transitions.get(current_status, []) 