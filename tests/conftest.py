"""Common test fixtures."""

from typing import Any

import pytest


@pytest.fixture
def mock_image_bytes() -> bytes:
    """Return a tiny valid image payload or just random bytes."""
    return b"fake_image_data"


@pytest.fixture
def base_config_dict() -> dict[str, Any]:
    """Return a base valid configuration dictionary."""
    return {
        "server": {"host": "127.0.0.1", "port": 8000, "reload": False},
        "model": {"size": "nano", "device": "cpu", "download_on_startup": False},
        "inference": {"conf_threshold": 0.25, "iou_threshold": 0.45},
        "classes_to_detect": [0],
    }
