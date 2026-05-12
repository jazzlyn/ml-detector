"""Tests for model logic."""

from typing import Any

import cv2
import pytest
import torch

if not hasattr(cv2, "imshow"):
    cv2.imshow = lambda *args, **kwargs: None  # type: ignore[assignment] # noqa: ARG005

from src.config import InferenceConfig, ModelConfig
from src.model import PersonDetector


class MockBoxes:
    """Mock for YOLO results boxes."""

    def __init__(self, cls: torch.Tensor, conf: torch.Tensor, xyxy: torch.Tensor) -> None:
        """Init mock boxes."""
        self.cls = cls
        self.conf = conf
        self.xyxy = xyxy

    def __len__(self) -> int:
        """Get length."""
        return len(self.cls)


class MockResult:
    """Mock for YOLO result."""

    def __init__(self, boxes: MockBoxes | None) -> None:
        """Init mock result."""
        self.boxes = boxes


@pytest.fixture
def detector() -> PersonDetector:
    """Fixture for detector."""
    model_config = ModelConfig(device="cpu", download_on_startup=False)
    inf_config = InferenceConfig(conf_threshold=0.25)
    return PersonDetector(model_config, inf_config, classes_to_detect=[0])


def test_process_results_with_detections(detector: PersonDetector) -> None:
    """Test process_results with detections."""
    # Mock detection: 2 persons (class 0), 1 bicycle (class 1)
    cls_tensor = torch.tensor([0, 0, 1])
    conf_tensor = torch.tensor([0.9, 0.8, 0.7])
    xyxy_tensor = torch.tensor([[10.0, 10.0, 50.0, 50.0], [60.0, 60.0, 100.0, 100.0], [200.0, 200.0, 300.0, 300.0]])

    boxes = MockBoxes(cls=cls_tensor, conf=conf_tensor, xyxy=xyxy_tensor)
    result = MockResult(boxes=boxes)

    processed: dict[str, Any] = detector._process_results([result], "test.jpg")  # type: ignore[misc] # noqa: SLF001

    assert processed["filename"] == "test.jpg"  # noqa: S101
    assert processed["person_detected"] is True  # noqa: S101
    assert processed["num_persons"] == 2  # noqa: S101, PLR2004
    assert processed["confidence"] == pytest.approx(0.9)  # type: ignore[misc] # noqa: S101
    assert len(processed["person_boxes"]) == 2  # noqa: S101, PLR2004
    assert processed["person_boxes"][0]["confidence"] == pytest.approx(0.9)  # type: ignore[misc] # noqa: S101


def test_process_results_no_target_class(detector: PersonDetector) -> None:
    """Test process_results with no target class."""
    # Mock detection: 1 bicycle (class 1)
    cls_tensor = torch.tensor([1])
    conf_tensor = torch.tensor([0.9])
    xyxy_tensor = torch.tensor([[10.0, 10.0, 50.0, 50.0]])

    boxes = MockBoxes(cls=cls_tensor, conf=conf_tensor, xyxy=xyxy_tensor)
    result = MockResult(boxes=boxes)

    processed: dict[str, Any] = detector._process_results([result], "test.jpg")  # type: ignore[misc] # noqa: SLF001

    assert processed["person_detected"] is False  # noqa: S101
    assert processed["num_persons"] == 0  # noqa: S101
    assert processed["confidence"] == 0.0  # noqa: S101


def test_process_results_empty(detector: PersonDetector) -> None:
    """Test process_results with empty detections."""
    result = MockResult(boxes=None)
    processed: dict[str, Any] = detector._process_results([result], "test.jpg")  # type: ignore[misc] # noqa: SLF001

    assert processed["person_detected"] is False  # noqa: S101
    assert processed["num_persons"] == 0  # noqa: S101
