"""Batch counting pipeline.

Walks a directory of field photos, runs the detector on each, and aggregates
counts per region and per date.

Filename convention: ``<region>_<YYYY-MM-DD>.jpg``, e.g.
``greenhouse-A_2026-09-28.jpg``. Files not matching fall back to
region="unknown" and the file's modification date.

TODO(ezra): for real deployments, parse EXIF (capture time, GPS) instead of
relying on filenames -- greenhouse cameras and drones usually embed both.
"""

from __future__ import annotations

import datetime
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2

from detector.base import BloomDetector, Detection

FILENAME_RE = re.compile(r"^(?P<region>.+)_(?P<date>\d{4}-\d{2}-\d{2})\.(jpg|jpeg|png)$",
                         re.IGNORECASE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


@dataclass
class ImageResult:
    path: str
    region: str
    date: str  # YYYY-MM-DD
    blooms: int
    buds: int
    detections: List[Detection] = field(default_factory=list)
    ground_truth: Optional[Dict] = None  # populated for simulated images

    @property
    def total(self) -> int:
        return self.blooms + self.buds


def parse_filename(path: str) -> tuple[str, str]:
    name = os.path.basename(path)
    m = FILENAME_RE.match(name)
    if m:
        return m.group("region"), m.group("date")
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return "unknown", mtime.strftime("%Y-%m-%d")


def _load_ground_truth(image_path: str) -> Optional[Dict]:
    import json

    gt_path = os.path.splitext(image_path)[0] + "_groundtruth.json"
    if os.path.exists(gt_path):
        with open(gt_path) as f:
            return json.load(f)
    return None


def process_image(detector: BloomDetector, path: str) -> ImageResult:
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"cannot read image: {path}")
    detections = detector.detect(image)
    region, date = parse_filename(path)
    blooms = sum(1 for d in detections if d.label == "bloom")
    buds = sum(1 for d in detections if d.label == "bud")
    return ImageResult(
        path=path,
        region=region,
        date=date,
        blooms=blooms,
        buds=buds,
        detections=detections,
        ground_truth=_load_ground_truth(path),
    )


def process_directory(detector: BloomDetector, directory: str) -> List[ImageResult]:
    results: List[ImageResult] = []
    for name in sorted(os.listdir(directory)):
        if os.path.splitext(name)[1].lower() in IMAGE_EXTS:
            results.append(process_image(detector, os.path.join(directory, name)))
    return results


def aggregate(results: List[ImageResult]) -> List[Dict]:
    """Aggregate per (region, date): blooms, buds, total, image count."""
    buckets: Dict[tuple[str, str], Dict] = {}
    for r in results:
        key = (r.region, r.date)
        b = buckets.setdefault(key, {"region": r.region, "date": r.date,
                                     "blooms": 0, "buds": 0, "images": 0})
        b["blooms"] += r.blooms
        b["buds"] += r.buds
        b["images"] += 1
    rows = list(buckets.values())
    for b in rows:
        b["total"] = b["blooms"] + b["buds"]
    return sorted(rows, key=lambda b: (b["region"], b["date"]))
