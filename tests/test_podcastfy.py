import pytest
from fastapi import UploadFile
from app.services.podcastfy import PodcastfyService
import os
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Fixture to create a PodcastfyService instance with mocked config
# This ensures we don't make real API calls during tests
@pytest.fixture
def podcastfy_service():
    with patch('decouple.config') as mock_config:
        mock_config.return_value = "test_api_key"
        service = PodcastfyService()
        return service

# Fixture to create a mock transcript file
# This simulates a file upload without actually creating a file
@pytest.fixture
def mock_transcript_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test_transcript.txt"
    file.content_type = "text/plain"
    file.file = MagicMock()
    file.file.read = AsyncMock(return_value=b"Test transcript content")
    return file

# Test successful audio generation and file upload
# Verifies the complete happy path of the service
@pytest.mark.asyncio
async def test_generate_audio_success(podcastfy_service, mock_transcript_file):
    # Mock both the podcast generation and file upload services
    with patch('podcastfy.client.generate_podcast') as mock_generate, \
         patch.object(podcastfy_service.file_upload_service, 'upload_file') as mock_upload:
        
        # Setup mocks to simulate successful operations
        mock_generate.return_value = "test_audio.mp3"
        mock_upload.return_value = {"url": "https://example.com/audio.mp3"}
        
        # Call the service with our mock transcript
        result = await podcastfy_service.generate_audio(
            transcript_file=mock_transcript_file,
            collection_id="test_collection"
        )
        
        # Verify the service returned the expected URL
        assert result["url"] == "https://example.com/audio.mp3"
        
        # Verify that both the podcast generation and file upload were called exactly once
        mock_generate.assert_called_once()
        mock_upload.assert_called_once()
        
        # Verify that temporary files were cleaned up
        assert not os.path.exists("test_audio.mp3")
        assert not os.path.exists(os.path.join(".storage", "temp_transcript.txt"))

# Test error handling when file upload fails
# Verifies that the service properly handles upload errors and cleans up
@pytest.mark.asyncio
async def test_generate_audio_file_upload_error(podcastfy_service, mock_transcript_file):
    with patch('podcastfy.client.generate_podcast') as mock_generate, \
         patch.object(podcastfy_service.file_upload_service, 'upload_file') as mock_upload:
        
        # Setup mocks to simulate successful podcast generation but failed upload
        mock_generate.return_value = "test_audio.mp3"
        mock_upload.side_effect = httpx.HTTPError("Upload failed")
        
        # Call the service and verify it raises an exception
        with pytest.raises(Exception) as exc_info:
            await podcastfy_service.generate_audio(
                transcript_file=mock_transcript_file,
                collection_id="test_collection"
            )
        
        # Verify the error message and cleanup
        assert "Failed to generate audio" in str(exc_info.value)
        assert not os.path.exists("test_audio.mp3")
        assert not os.path.exists(os.path.join(".storage", "temp_transcript.txt"))

# Test error handling when podcast generation fails
# Verifies that the service properly handles generation errors and cleans up
@pytest.mark.asyncio
async def test_generate_audio_podcast_generation_error(podcastfy_service, mock_transcript_file):
    with patch('podcastfy.client.generate_podcast') as mock_generate:
        # Setup mock to simulate podcast generation failure
        mock_generate.side_effect = Exception("Podcast generation failed")
        
        # Call the service and verify it raises an exception
        with pytest.raises(Exception) as exc_info:
            await podcastfy_service.generate_audio(
                transcript_file=mock_transcript_file,
                collection_id="test_collection"
            )
        
        # Verify the error message and cleanup
        assert "Failed to generate audio" in str(exc_info.value)
        assert not os.path.exists(os.path.join(".storage", "temp_transcript.txt"))

# Test handling of invalid file input
# Verifies that the service properly handles null file input
@pytest.mark.asyncio
async def test_generate_audio_invalid_file(podcastfy_service):
    with pytest.raises(Exception) as exc_info:
        await podcastfy_service.generate_audio(
            transcript_file=None,
            collection_id="test_collection"
        )
    assert "Failed to generate audio" in str(exc_info.value)

# Test storage directory creation
# Verifies that the service creates the storage directory if it doesn't exist
@pytest.mark.asyncio
async def test_generate_audio_storage_creation(podcastfy_service):
    # Remove storage directory if it exists to test creation
    if os.path.exists(".storage"):
        os.rmdir(".storage")
    
    # Create new service instance with mocked config
    with patch('decouple.config') as mock_config:
        mock_config.return_value = "test_api_key"
        service = PodcastfyService()
        
        # Verify storage directory was created
        assert os.path.exists(".storage")
        assert os.path.isdir(".storage") 