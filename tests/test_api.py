# tests/test_api.py
"""API endpoint tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.inference import AppState, app


@pytest.fixture
def mock_detector() -> MagicMock:
    """Fixture for mocking the PersonDetector."""
    mock = MagicMock()
    mock.detect_persons.return_value = {
        "filename": "test.jpg",
        "person_detected": True,
        "confidence": 0.99,
        "num_persons": 1,
        "person_boxes": [{"confidence": 0.99, "bbox": [0, 0, 100, 100]}],
    }
    return mock


@pytest.fixture
def client(mock_detector: MagicMock) -> Generator[TestClient]:
    """Fixture for TestClient with mocked detector and ready state."""
    # Patch the global state and model in inference.py
    with (
        patch("src.inference.state", AppState.READY),
        patch("src.inference.model", mock_detector),
    ):
        yield TestClient(app)


def test_health_check_info(client: TestClient) -> None:
    """Test the root info endpoint."""
    response = client.get("/")
    assert response.status_code == 200  # noqa: S101, PLR2004
    assert "version" in response.json()  # noqa: S101


def test_liveness_probe(client: TestClient) -> None:
    """Test the liveness probe endpoint."""
    response = client.get("/livez")
    assert response.status_code == 200  # noqa: S101, PLR2004


def test_readiness_probe(client: TestClient) -> None:
    """Test the readiness probe endpoint."""
    response = client.get("/readyz")
    assert response.status_code == 200  # noqa: S101, PLR2004


def test_readiness_probe_not_ready() -> None:
    """Test readiness probe when service is not ready."""
    with patch("src.inference.state", AppState.INITIALIZING):
        client_not_ready = TestClient(app)
        response = client_not_ready.get("/readyz")
        assert response.status_code == 503  # noqa: S101, PLR2004


def test_detect_person_success(client: TestClient, mock_image_bytes: bytes, mock_detector: MagicMock) -> None:
    """Test successful person detection."""
    files: dict[str, tuple[str, bytes, str]] = {"file": ("test.jpg", mock_image_bytes, "image/jpeg")}
    response = client.post("/detect", files=files)

    assert response.status_code == 200  # noqa: S101, PLR2004
    data: dict[str, Any] = response.json()
    assert data["person_detected"] is True  # noqa: S101
    assert data["confidence"] == 0.99  # noqa: S101, PLR2004

    # Verify mock was called
    mock_detector.detect_persons.assert_called_once()


def test_detect_person_empty_file(client: TestClient) -> None:
    """Test person detection with an empty file."""
    files: dict[str, tuple[str, bytes, str]] = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/detect", files=files)
    assert response.status_code == 400  # noqa: S101, PLR2004
    assert "Empty file" in response.json()["detail"]  # noqa: S101
