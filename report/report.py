"""Boss-friendly reports: CSV, JSON, and a summary chart."""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt


def to_csv(rows: List[Dict], path: str) -> None:
    fieldnames = ["region", "date", "blooms", "buds", "total", "images"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_json(rows: List[Dict], path: str, meta: Dict | None = None) -> None:
    payload = {"meta": meta or {}, "rows": rows}
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def summary_chart(rows: List[Dict], path: str, title: str = "Bloom / Bud counts") -> None:
    labels = [f"{r['region']}\n{r['date']}" for r in rows]
    blooms = [r["blooms"] for r in rows]
    buds = [r["buds"] for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(max(6, len(rows) * 1.4), 4.5))
    ax.bar(x, blooms, label="blooms (open)")
    ax.bar(x, buds, bottom=blooms, label="buds")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("count")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_all(rows: List[Dict], out_dir: str, meta: Dict | None = None) -> Dict[str, str]:
    """Write CSV + JSON + chart. Returns the created file paths."""
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "csv": os.path.join(out_dir, "bloom_report.csv"),
        "json": os.path.join(out_dir, "bloom_report.json"),
        "chart": os.path.join(out_dir, "bloom_chart.png"),
    }
    to_csv(rows, paths["csv"])
    to_json(rows, paths["json"], meta=meta)
    summary_chart(rows, paths["chart"])
    return paths
