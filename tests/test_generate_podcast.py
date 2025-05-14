import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from app.main import app
import os
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import io
from app.schemas.input import ResourceType

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
async def test_generate_podcast_pdf_success(client, mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript, \
         patch('podcastfy.client.generate_podcast') as mock_generate:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.return_value = "Test transcript content"
        mock_generate.return_value = "test_audio.mp3"
        
        # Make request
        files = {"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
        form_data = {"resource_type": ResourceType.FILE, "collection_id": "test-collection"}
        response = client.post("/generate-podcast", files=files, data=form_data)
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "status_url" in data
        assert response.headers["Location"].startswith("/status/")

@pytest.mark.asyncio
async def test_generate_podcast_youtube_success(client, mock_youtube_url):
    # Make request
    form_data = {
        "resource_type": ResourceType.YOUTUBE,
        "resource_data": mock_youtube_url,
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    
    # Verify response
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert "status_url" in data
    assert response.headers["Location"].startswith("/status/")

@pytest.mark.asyncio
async def test_generate_podcast_invalid_resource_type(client):
    form_data = {
        "resource_type": "invalid",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 400
    assert "Invalid resource type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_missing_file(client):
    form_data = {
        "resource_type": "file",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 400
    assert "File is required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_invalid_pdf(client, mock_pdf_file):
    # Change content type to invalid type
    mock_pdf_file.content_type = "text/plain"
    
    files = {"file": ("test.pdf", mock_pdf_file.file, "text/plain")}
    form_data = {
        "resource_type": "file",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", files=files, data=form_data)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_transcript_error(client, mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.side_effect = Exception("Transcript generation failed")
        
        files = {"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
        form_data = {
            "resource_type": "file",
            "collection_id": "test-collection"
        }
        response = client.post("/generate-podcast", files=files, data=form_data)
        assert response.status_code == 500
        assert "Transcript generation failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_audio_error(client, mock_pdf_file):
    with patch('app.services.file_upload.FileUploadService.upload_file') as mock_upload, \
         patch('app.services.wetrocloud.WetrocloudService.generate_transcript') as mock_transcript, \
         patch('podcastfy.client.generate_podcast') as mock_generate:
        
        # Setup mocks
        mock_upload.return_value = {"url": "https://example.com/file.pdf"}
        mock_transcript.return_value = "Test transcript content"
        mock_generate.side_effect = Exception("Audio generation failed")
        
        files = {"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
        form_data = {
            "resource_type": "file",
            "collection_id": "test-collection"
        }
        response = client.post("/generate-podcast", files=files, data=form_data)
        assert response.status_code == 500
        assert "Audio generation failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_endpoint(client, mock_pdf_file):
    # Mock the task handler
    with patch("app.tasks.podcast_tasks.PodcastTaskHandler.process_podcast") as mock_handler:
        mock_handler.return_value = {"job_id": "test-job", "status_url": "/status/test-job"}
        
        # Make request
        files = {"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
        form_data = {
            "resource_type": ResourceType.FILE,
            "collection_id": "test-collection"
        }
        response = client.post("/generate-podcast", files=files, data=form_data)
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "status_url" in data
        assert response.headers["Location"].startswith("/status/")
        
        # Verify mock was called
        mock_handler.assert_called_once()

@pytest.mark.asyncio
async def test_generate_podcast_pdf(client):
    """Test PDF podcast generation request"""
    # Create a mock PDF file
    pdf_content = b"%PDF-1.5 mock pdf content"
    files = {
        "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    form_data = {
        "resource_type": ResourceType.FILE,
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", files=files, data=form_data)
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert "status_url" in response.json()
    assert response.headers["Location"].startswith("/status/")

@pytest.mark.asyncio
async def test_generate_podcast_youtube(client):
    """Test YouTube podcast generation request"""
    form_data = {
        "resource_type": ResourceType.YOUTUBE,
        "resource_data": "https://www.youtube.com/watch?v=test",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert "status_url" in response.json()
    assert response.headers["Location"].startswith("/status/")

@pytest.mark.asyncio
async def test_generate_podcast_website(client):
    """Test website podcast generation request"""
    form_data = {
        "resource_type": "web",
        "resource_data": "https://example.com/article",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert "status_url" in response.json()
    assert response.headers["Location"].startswith("/status/")

@pytest.mark.asyncio
async def test_generate_podcast_invalid_file_type(client):
    """Test invalid file type"""
    files = {
        "file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")
    }
    form_data = {
        "resource_type": "file",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", files=files, data=form_data)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_missing_url(client):
    """Test missing URL for YouTube/website"""
    form_data = {
        "resource_type": "youtube",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 400
    assert "URL is required for YouTube/Web resources" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_podcast_invalid_url(client):
    """Test invalid URL format"""
    form_data = {
        "resource_type": "web",
        "resource_data": "not-a-url",
        "collection_id": "test-collection"
    }
    response = client.post("/generate-podcast", data=form_data)
    assert response.status_code == 400
    assert "Invalid URL format" in response.json()["detail"] 