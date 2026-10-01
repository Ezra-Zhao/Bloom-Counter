"""Synthetic flower-field image generator (SIMULATED data).

Generates greenhouse-style photos with randomly placed blooms and buds on a
foliage background, plus a ground-truth JSON sidecar so the demo can score the
detector. Every generated image is watermarked "SIMULATED".

TODO(ezra): point the pipeline at real photos (phone / greenhouse camera /
drone). The detector interface and reporting stay the same; real photos just
need the filename convention ``<region>_<YYYY-MM-DD>.jpg`` or EXIF parsing
(see pipeline/counter.py).
"""

from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Tuple

import cv2
import numpy as np

# BGR colors tuned to sit inside the detector's HSV petal ranges.
PINK = (147, 20, 255)
PINK_BUD = (160, 70, 230)
WHITE = (245, 245, 245)
YELLOW = (0, 215, 255)
LEAF_DARK = (28, 78, 38)
LEAF_BASE = (45, 110, 55)
LEAF_LIGHT = (62, 140, 70)


def _foliage_background(rng: np.random.Generator, w: int, h: int) -> np.ndarray:
    img = np.full((h, w, 3), LEAF_BASE, dtype=np.uint8)
    # Soft light/dark patches for texture.
    for _ in range(60):
        cx, cy = int(rng.integers(0, w)), int(rng.integers(0, h))
        r = int(rng.integers(40, 160))
        color = LEAF_DARK if rng.random() < 0.5 else LEAF_LIGHT
        cv2.circle(img, (cx, cy), r, color, -1)
    img = cv2.GaussianBlur(img, (31, 31), 0)
    # Fine grain noise.
    noise = rng.integers(-14, 15, size=(h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # A few leaf streaks.
    for _ in range(40):
        x1, y1 = int(rng.integers(0, w)), int(rng.integers(0, h))
        x2, y2 = x1 + int(rng.integers(-120, 120)), y1 + int(rng.integers(-40, 40))
        cv2.line(img, (x1, y1), (x2, y2), LEAF_DARK, int(rng.integers(2, 5)))
    return img


def _draw_bloom(img: np.ndarray, rng: np.random.Generator, cx: int, cy: int, r: int) -> None:
    petal = PINK if rng.random() < 0.6 else WHITE
    n_petals = int(rng.integers(6, 9))
    for i in range(n_petals):
        ang = 2 * math.pi * i / n_petals + rng.uniform(-0.15, 0.15)
        px = int(cx + math.cos(ang) * r * 0.62)
        py = int(cy + math.sin(ang) * r * 0.62)
        axes = (int(r * 0.42), int(r * 0.30))
        cv2.ellipse(img, (px, py), axes, math.degrees(ang), 0, 360, petal, -1)
    cv2.circle(img, (cx, cy), int(r * 0.34), YELLOW, -1)
    cv2.circle(img, (cx, cy), int(r * 0.34), (0, 150, 200), 2)


def _draw_bud(img: np.ndarray, rng: np.random.Generator, cx: int, cy: int, r: int) -> None:
    angle = float(rng.uniform(0, 180))
    cv2.ellipse(img, (cx, cy), (int(r * 0.55), r), angle, 0, 360, PINK_BUD, -1)
    cv2.ellipse(img, (cx, cy), (int(r * 0.55), r), angle, 0, 360, (120, 40, 180), 2)


def _place(rng: np.random.Generator, w: int, h: int, radii: List[int],
           margin: int = 30) -> List[Tuple[int, int]]:
    """Rejection-sample non-overlapping centers."""
    centers: List[Tuple[int, int]] = []
    for r in radii:
        for _ in range(200):  # attempts
            cx = int(rng.integers(margin + r, w - margin - r))
            cy = int(rng.integers(margin + r, h - margin - r))
            if all(math.hypot(cx - x, cy - y) >= r + rr + 8 for x, y, rr in
                   [(x, y, rr) for (x, y), rr in zip(centers, radii[:len(centers)])]):
                centers.append((cx, cy))
                break
    return centers


def generate_image(path: str, n_blooms: int, n_buds: int, seed: int,
                   width: int = 1280, height: int = 960) -> Dict:
    """Generate one simulated field photo. Returns the ground truth dict."""
    rng = np.random.default_rng(seed)
    img = _foliage_background(rng, width, height)

    bloom_radii = [int(v) for v in rng.integers(30, 50, size=n_blooms)]
    bud_radii = [int(v) for v in rng.integers(11, 17, size=n_buds)]
    centers = _place(rng, width, height, bloom_radii + bud_radii)

    truth: Dict = {"blooms": 0, "buds": 0, "objects": [], "simulated": True}
    idx = 0
    for r in bloom_radii:
        if idx >= len(centers):
            break
        cx, cy = centers[idx]; idx += 1
        _draw_bloom(img, rng, cx, cy, r)
        truth["blooms"] += 1
        truth["objects"].append({"label": "bloom", "cx": cx, "cy": cy, "r": r})
    for r in bud_radii:
        if idx >= len(centers):
            break
        cx, cy = centers[idx]; idx += 1
        _draw_bud(img, rng, cx, cy, r)
        truth["buds"] += 1
        truth["objects"].append({"label": "bud", "cx": cx, "cy": cy, "r": r})

    cv2.putText(img, "SIMULATED", (width - 260, height - 24),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (110, 110, 110), 2)
    cv2.imwrite(path, img)
    gt_path = os.path.splitext(path)[0] + "_groundtruth.json"
    with open(gt_path, "w") as f:
        json.dump(truth, f, indent=2)
    return truth


def generate_demo_set(out_dir: str, seed: int = 7) -> List[str]:
    """Generate a small multi-region / multi-date demo set.

    Filenames follow the pipeline convention: <region>_<YYYY-MM-DD>.jpg
    """
    os.makedirs(out_dir, exist_ok=True)
    plan = [
        ("greenhouse-A", "2026-09-26", 34, 22),
        ("greenhouse-A", "2026-09-27", 41, 18),
        ("greenhouse-A", "2026-09-28", 52, 15),
        ("greenhouse-B", "2026-09-26", 28, 26),
        ("greenhouse-B", "2026-09-27", 33, 24),
        ("greenhouse-B", "2026-09-28", 45, 19),
    ]
    paths = []
    for i, (region, date, nb, nd) in enumerate(plan):
        path = os.path.join(out_dir, f"{region}_{date}.jpg")
        generate_image(path, nb, nd, seed=seed + i)
        paths.append(path)
    return paths
