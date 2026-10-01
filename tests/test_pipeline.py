"""Pipeline + aggregation tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detector.base import Detection
from pipeline.counter import aggregate, parse_filename, ImageResult


def test_parse_filename_convention(tmp_path):
    p = tmp_path / "greenhouse-A_2026-09-28.jpg"
    p.write_bytes(b"x")
    region, date = parse_filename(str(p))
    assert region == "greenhouse-A"
    assert date == "2026-09-28"


def test_parse_filename_fallback(tmp_path):
    p = tmp_path / "IMG_001.jpg"
    p.write_bytes(b"x")
    region, date = parse_filename(str(p))
    assert region == "unknown"
    assert len(date) == 10  # YYYY-MM-DD from mtime


def _res(region, date, blooms, buds):
    return ImageResult(path="x", region=region, date=date,
                       blooms=blooms, buds=buds, detections=[])


def test_aggregate_sums_by_region_date():
    rows = aggregate([
        _res("A", "2026-09-28", 10, 5),
        _res("A", "2026-09-28", 7, 3),
        _res("B", "2026-09-28", 4, 4),
    ])
    assert len(rows) == 2
    a = next(r for r in rows if r["region"] == "A")
    assert (a["blooms"], a["buds"], a["total"], a["images"]) == (17, 8, 25, 2)
    b = next(r for r in rows if r["region"] == "B")
    assert b["total"] == 8


def test_detection_dataclass_centroid():
    d = Detection(x=10, y=20, w=30, h=40, label="bloom", confidence=0.9)
    assert (d.cx, d.cy) == (25.0, 40.0)
