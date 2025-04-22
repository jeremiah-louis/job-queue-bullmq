import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from app.main import app
import os
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Create test client fixture
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_pdf_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test.pdf"
    file.content_type = "application/pdf"
    file.file = MagicMock()
    async def mock_read():
        return b"Test PDF content"
    file.file.read = mock_read
    return file

@pytest.fixture
def mock_youtube_url():
    return "https://www.youtube.com/watch?v=test123"

@pytest.fixture
def mock_website_url():
    return "https://example.com"

@pytest.mark.asyncio
async def test_generate_podcast_pdf_success(mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript, \
         patch('podcastfy.client.generate_podcast') as mock_generate:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.return_value = "Test transcript content"
        mock_generate.return_value = "test_audio.mp3"
        
        # Make request
        response = await client.post(
            "/generate-podcast",
            files={"file": ("test.pdf", mock_pdf_file.file, "application/pdf")},
            data={
                "resource_type": "pdf",
                "collection_id": "test-collection"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Test transcript content" in data["data"]["transcript"]
        assert "audio_url" in data["data"]
        
        # Verify cleanup
        assert not os.path.exists("test_audio.mp3")
        assert not os.path.exists(os.path.join(".storage", "temp_transcript.txt"))

@pytest.mark.asyncio
async def test_generate_podcast_youtube_success(mock_youtube_url):
    with patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript, \
         patch('podcastfy.client.generate_podcast') as mock_generate:
        
        # Setup mocks
        mock_transcript.return_value = "Test transcript content"
        mock_generate.return_value = "test_audio.mp3"
        
        # Make request
        response = await client.post(
            "/generate-podcast",
            data={
                "resource_type": "youtube",
                "resource_data": mock_youtube_url,
                "collection_id": "test-collection"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Test transcript content" in data["data"]["transcript"]
        assert "audio_url" in data["data"]
        
        # Verify cleanup
        assert not os.path.exists("test_audio.mp3")
        assert not os.path.exists(os.path.join(".storage", "temp_transcript.txt"))

@pytest.mark.asyncio
async def test_generate_podcast_invalid_resource_type():
    response = await client.post(
        "/generate-podcast",
        data={
            "resource_type": "invalid",
            "collection_id": "test-collection"
        }
    )
    assert response.status_code == 400
    assert "Invalid resource type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_missing_file():
    response = await client.post(
        "/generate-podcast",
        data={
            "resource_type": "pdf",
            "collection_id": "test-collection"
        }
    )
    assert response.status_code == 400
    assert "File is required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_invalid_pdf(mock_pdf_file):
    # Change content type to invalid type
    mock_pdf_file.content_type = "text/plain"
    
    response = await client.post(
        "/generate-podcast",
        files={"file": ("test.pdf", mock_pdf_file.file, "text/plain")},
        data={
            "resource_type": "pdf",
            "collection_id": "test-collection"
        }
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_transcript_error(mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.side_effect = Exception("Transcript generation failed")
        
        response = await client.post(
            "/generate-podcast",
            files={"file": ("test.pdf", mock_pdf_file.file, "application/pdf")},
            data={
                "resource_type": "pdf",
                "collection_id": "test-collection"
            }
        )
        assert response.status_code == 500
        assert "Transcript generation failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_audio_error(mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript, \
         patch('podcastfy.client.generate_podcast') as mock_generate:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.return_value = "Test transcript content"
        mock_generate.side_effect = Exception("Audio generation failed")
        
        response = await client.post(
            "/generate-podcast",
            files={"file": ("test.pdf", mock_pdf_file.file, "application/pdf")},
            data={
                "resource_type": "pdf",
                "collection_id": "test-collection"
            }
        )
        assert response.status_code == 500
        assert "Audio generation failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_endpoint(client, mock_pdf_file):
    # Mock the transcript generation
    mock_transcript = "This is a test transcript"
    mock_audio_url = "https://example.com/audio.mp3"
    
    with patch("app.main.generate_transcript", new_callable=AsyncMock) as mock_gen_transcript, \
         patch("app.main.generate_audio", new_callable=AsyncMock) as mock_gen_audio:
        
        # Setup mocks
        mock_gen_transcript.return_value = mock_transcript
        mock_gen_audio.return_value = mock_audio_url
        
        # Make request
        response = client.post(
            "/generate-podcast",
            files={"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == mock_transcript
        assert data["audio_url"] == mock_audio_url
        
        # Verify mocks were called
        mock_gen_transcript.assert_called_once()
        mock_gen_audio.assert_called_once_with(mock_transcript) 