"""Detector interface.

The detection backend is swappable: implement this protocol and drop it into
the pipeline. The default backend is color-segmentation based (good enough for
the demo); the production path is a trained model (see TODO in
color_segmentation.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

import numpy as np


@dataclass
class Detection:
    """One detected flower object."""

    x: int  # bounding-box top-left
    y: int
    w: int
    h: int
    label: str  # "bloom" (open flower) or "bud" (unopened)
    confidence: float  # 0.0 - 1.0

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0


class BloomDetector(Protocol):
    """Anything that can count blooms/buds in a BGR image."""

    @property
    def name(self) -> str: ...

    def detect(self, image: np.ndarray) -> List[Detection]:
        """Return detections for a BGR uint8 image."""
        ...
