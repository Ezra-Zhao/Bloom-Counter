"""Color-segmentation bloom detector (demo backend).

How it works: petal pixels are segmented in HSV space (pink / white / yellow
petals against green foliage), cleaned with morphology, then connected
components are measured. Components larger than ``bloom_area_min`` are counted
as open blooms, smaller ones as buds.

This is intentionally simple and transparent: it runs anywhere OpenCV runs,
needs no GPU and no training data. On real greenhouse photos with cluttered
backgrounds it will underperform -- that is exactly why the detector is behind
the :class:`BloomDetector` interface.

TODO(ezra): replace with a trained detector (YOLOv8/YOLOv11 fine-tuned on
annotated bloom/bud photos) implementing the same interface. The pipeline,
aggregation and reporting code does not need to change.
"""

from __future__ import annotations

from typing import List

import cv2
import numpy as np

from .base import BloomDetector, Detection


class ColorSegmentationDetector(BloomDetector):
    """HSV color-segmentation + contour analysis detector."""

    def __init__(
        self,
        min_area: int = 120,
        bloom_area_min: int = 900,
        morph_kernel: int = 7,
    ) -> None:
        """
        Args:
            min_area: ignore components smaller than this (noise), in px^2.
            bloom_area_min: components at/above this area count as open blooms,
                below it as buds. Tune per crop/camera distance.
            morph_kernel: closing kernel size to merge petal fragments.
        """
        self.min_area = min_area
        self.bloom_area_min = bloom_area_min
        self.morph_kernel = morph_kernel

    @property
    def name(self) -> str:
        return "color-segmentation-v0.1"

    @staticmethod
    def _petal_mask(hsv: np.ndarray) -> np.ndarray:
        # Pink / magenta petals (OpenCV H: 0-179).
        pink = cv2.inRange(hsv, (125, 50, 50), (170, 255, 255))
        # White petals: very low saturation, high value.
        white = cv2.inRange(hsv, (0, 0, 170), (179, 70, 255))
        # Yellow flower centers.
        yellow = cv2.inRange(hsv, (18, 80, 80), (40, 255, 255))
        return cv2.bitwise_or(cv2.bitwise_or(pink, white), yellow)

    def detect(self, image: np.ndarray) -> List[Detection]:
        if image is None or image.size == 0:
            return []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = self._petal_mask(hsv)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.morph_kernel, self.morph_kernel)
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: List[Detection] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            label = "bloom" if area >= self.bloom_area_min else "bud"
            # Heuristic confidence: larger, more circular components score higher.
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
            confidence = float(min(0.95, max(0.45, 0.45 + 0.5 * min(1.0, circularity))))
            detections.append(
                Detection(x=int(x), y=int(y), w=int(w), h=int(h),
                          label=label, confidence=round(confidence, 2))
            )
        return detections
