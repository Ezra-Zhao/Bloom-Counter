# Bloom-Counter

**[English](README.md)** | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Português](README.pt.md) | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**Vision-based flower bloom / bud counting for smart agriculture and yield estimation.**

Point a camera at a greenhouse bed or an orchard row; get back *how many flowers
have opened, how many buds are still closed, per region and per day* — the raw
numbers a grower needs to estimate yield, schedule labor, and report to the boss.

> **Project status: working demo (honest edition).**
> The end-to-end pipeline runs today on **SIMULATED** field photos (every
> generated image is watermarked). What is real: image ingest, bloom/bud
> detection, per-region/per-day aggregation, and CSV/JSON/chart reporting.
> What is still TODO (clearly marked in code): a trained detector for real
> photos and EXIF/GPS metadata parsing. Nothing here pretends to be a
> production agronomy tool yet.
>
> *Background note: this demo is anonymized from a real client project —
> counting blooms/buds in a commercial planting operation for yield reporting.
> No client data, imagery, or identifying details are included.*

---

## The problem

In commercial flower/fruit planting, the number of open blooms vs. unopened buds
is the earliest hard signal of coming yield. Today it is counted by hand:
slow, inconsistent, and impossible to scale across greenhouses. A camera +
counting pipeline turns a walk-through into a spreadsheet.

## How it works

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **Ingest** (`pipeline/counter.py`) — reads a folder of photos named
   `<region>_<YYYY-MM-DD>.jpg`.
2. **Detect** (`detector/`) — the demo backend segments petal colors in HSV
   space (pink/white/yellow against green foliage), then classifies components
   by size into `bloom` (open) vs `bud` (unopened). The detector sits behind the
   `BloomDetector` interface, so a trained model drops in without touching the
   pipeline.
3. **Aggregate** — counts are summed per region and per date.
4. **Report** (`report/report.py`) — writes `bloom_report.csv`,
   `bloom_report.json`, and a stacked bar chart (`bloom_chart.png`) — the
   one-pager for the boss.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Full demo: generate SIMULATED photos -> detect -> score -> report
python examples/demo.py
# outputs: demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# Run on your own photos (must follow <region>_<YYYY-MM-DD>.jpg naming)
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# Tests
python -m pytest tests/ -q
```

## Demo results (simulated data)

6 photos, 2 regions × 3 days, 357 flowers total:

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*(Sample output is generated at demo time; the checked-in repo ships the
generator, not the images.)*

## Project structure

```
Bloom-Counter/
├── detector/
│   ├── base.py                 # BloomDetector interface + Detection dataclass
│   └── color_segmentation.py   # demo backend: HSV segmentation + contour analysis
├── pipeline/counter.py         # batch ingest, filename convention, aggregation
├── report/report.py            # CSV / JSON / chart
├── simulator/generate.py       # SIMULATED photo generator + ground-truth JSON
├── examples/demo.py            # end-to-end demo
└── tests/                      # unit tests (detector + pipeline)
```

## Roadmap

- [ ] `YoloDetector`: fine-tune YOLOv8/v11 on annotated real bloom/bud photos,
      implement `BloomDetector`, swap the backend (no pipeline changes needed)
- [ ] EXIF/GPS parsing for real camera/drone photos (replace filename convention)
- [ ] Video / drone-sweep mode: de-duplicate flowers across frames, count a whole row
- [ ] Bud-stage classification (tight bud → showing color → cracking) for finer
      yield forecasting
- [ ] Multi-crop color profiles (roses, peonies, cherry, apple blossom)

## Tech

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## License

MIT — see [LICENSE](LICENSE).
