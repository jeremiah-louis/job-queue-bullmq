from fastapi.testclient import TestClient
from app.main import app
from app.schemas.input import ResourceType
import os
import pytest
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_services():
    with patch('app.main.file_upload_service.upload_file', new_callable=AsyncMock) as mock_upload, \
         patch('app.main.wetrocloud_service.generate_transcript', new_callable=AsyncMock) as mock_generate:
        # Mock successful file upload
        mock_upload.return_value = {
            "success": True,
            "url": "https://wetro.s3.amazonaws.com/test.pdf"
        }
        # Mock successful transcript generation
        mock_generate.return_value = "Test transcript content"
        yield mock_upload, mock_generate

def test_generate_pdf():
    # Create a test PDF file
    test_file_path = "test.pdf"
    with open(test_file_path, "wb") as f:
        f.write(b"test content")
    
    try:
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/generate",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={
                    "resource_type": ResourceType.FILE,
                    "collection_id": "test"
                }
            )
        assert response.status_code == 200
        assert "message" in response.json()
        assert "url" in response.json()
        assert "transcript" in response.json()
        assert response.json()["url"].startswith("https://wetro.s3.amazonaws.com")
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_generate_youtube():
    response = client.post(
        "/generate",
        data={
            "resource_type": ResourceType.YOUTUBE,
            "resource_data": "https://www.youtube.com/watch?v=test",
            "collection_id": "test"
        }
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "url" in response.json()
    assert "transcript" in response.json()

def test_generate_website():
    response = client.post(
        "/generate",
        data={
            "resource_type": ResourceType.WEB,
            "resource_data": "https://example.com",
            "collection_id": "test"
        }
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "url" in response.json()
    assert "transcript" in response.json()

def test_invalid_file_type():
    # Create a test file with invalid type
    test_file_path = "test.txt"
    with open(test_file_path, "wb") as f:
        f.write(b"test content")
    
    try:
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/generate",
                files={"file": ("test.txt", f, "text/plain")},
                data={
                    "resource_type": ResourceType.FILE,
                    "collection_id": "test"
                }
            )
        assert response.status_code == 400
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_invalid_url():
    response = client.post(
        "/generate",
        data={
            "resource_type": ResourceType.WEB,
            "resource_data": "not-a-url",
            "collection_id": "test"
        }
    )
    assert response.status_code == 400 