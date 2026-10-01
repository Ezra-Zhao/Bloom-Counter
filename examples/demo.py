"""End-to-end demo: generate SIMULATED field photos -> detect -> report.

Usage:
    python examples/demo.py [--out demo] [--seed 7]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import aggregate, process_directory
from report.report import write_all
from simulator.generate import generate_demo_set


def annotate(image_path: str, out_path: str, detector) -> None:
    image = cv2.imread(image_path)
    for d in detector.detect(image):
        color = (0, 255, 0) if d.label == "bloom" else (255, 200, 0)
        cv2.rectangle(image, (d.x, d.y), (d.x + d.w, d.y + d.h), color, 2)
        cv2.putText(image, f"{d.label} {d.confidence:.2f}", (d.x, d.y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    cv2.imwrite(out_path, image)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="demo", help="demo working directory")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    img_dir = os.path.join(args.out, "images")
    out_dir = os.path.join(args.out, "output")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[1/4] generating SIMULATED field photos -> {img_dir}")
    paths = generate_demo_set(img_dir, seed=args.seed)

    detector = ColorSegmentationDetector()
    print(f"[2/4] detecting with '{detector.name}'")
    results = process_directory(detector, img_dir)

    print("[3/4] scoring against ground truth (simulated data only)")
    print(f"{'image':42s} {'truth B/b':>10s} {'got B/b':>10s} {'recall':>7s}")
    tot_tb = tot_tu = tot_db = tot_du = 0
    for r in results:
        gt = r.ground_truth or {}
        tb, tu = gt.get("blooms", 0), gt.get("buds", 0)
        tot_tb += tb; tot_tu += tu; tot_db += r.blooms; tot_du += r.buds
        recall = (r.blooms + r.buds) / max(1, tb + tu)
        print(f"{os.path.basename(r.path):42s} {tb:4d}/{tu:<4d} {r.blooms:4d}/{r.buds:<4d} {recall:6.1%}")
    overall = (tot_db + tot_du) / max(1, tot_tb + tot_tu)
    print(f"{'TOTAL':42s} {tot_tb:4d}/{tot_tu:<4d} {tot_db:4d}/{tot_du:<4d} {overall:6.1%}")

    rows = aggregate(results)
    print("[4/4] writing boss report")
    meta = {"detector": detector.name, "simulated": True,
            "note": "demo on SIMULATED data; anonymized from a real client project"}
    paths_out = write_all(rows, out_dir, meta=meta)
    annotate(paths[0], os.path.join(out_dir, "annotated_sample.jpg"), detector)
    for k, v in paths_out.items():
        print(f"  {k}: {v}")
    print("  annotated sample:", os.path.join(out_dir, "annotated_sample.jpg"))
    print(f"\nOverall detection recall on simulated data: {overall:.1%}")


if __name__ == "__main__":
    main()
