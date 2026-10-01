"""Detector tests on SIMULATED images with known ground truth."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector.color_segmentation import ColorSegmentationDetector
from simulator.generate import generate_image
import cv2


def _sim_image(tmp_path, n_blooms=12, n_buds=10, seed=123):
    path = str(tmp_path / "test.jpg")
    truth = generate_image(path, n_blooms, n_buds, seed=seed, width=800, height=600)
    image = cv2.imread(path)
    return image, truth


def test_detector_finds_most_objects(tmp_path):
    image, truth = _sim_image(tmp_path)
    dets = ColorSegmentationDetector().detect(image)
    blooms = sum(1 for d in dets if d.label == "bloom")
    buds = sum(1 for d in dets if d.label == "bud")
    # Heuristic detector: allow generous tolerance, but it must find most.
    assert blooms >= truth["blooms"] * 0.7, f"blooms {blooms} < 70% of {truth['blooms']}"
    assert buds >= truth["buds"] * 0.6, f"buds {buds} < 60% of {truth['buds']}"
    # ...and not hallucinate wildly.
    assert blooms + buds <= (truth["blooms"] + truth["buds"]) * 1.4


def test_detection_labels_and_confidence(tmp_path):
    image, _ = _sim_image(tmp_path)
    dets = ColorSegmentationDetector().detect(image)
    assert dets, "expected at least one detection"
    for d in dets:
        assert d.label in ("bloom", "bud")
        assert 0.0 <= d.confidence <= 1.0
        assert d.w > 0 and d.h > 0


def test_detector_handles_empty_image():
    import numpy as np

    dets = ColorSegmentationDetector().detect(np.zeros((100, 100, 3), dtype=np.uint8))
    assert dets == []
