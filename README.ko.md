# Bloom-Counter

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | **[한국어](README.ko.md)** | [Español](README.es.md) | [Português](README.pt.md) | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**스마트 농업과 수확량 예측을 위한 비전 기반 개화／봉오리 카운팅.**

온실 묘상이나 과수원 한 줄에 카메라를 향하게 하세요. *지역별·일자별로 핀 꽃과 아직 닫힌 봉오리 수*를 반환합니다 — 재배자가 수확량을 예측하고 인력을 배치하며 보고하는 데 필요한 원시 데이터입니다.

> **프로젝트 상태: 동작하는 데모 버전(정직 에디션).**
> 엔드투엔드 파이프라인은 현재 **시뮬레이션**된 현장 사진에서 동작합니다(생성된 모든 이미지에 워터마크 포함). 실제로 동작하는 부분: 이미지 수집, 개화/봉오리 검출, 지역별/일자별 집계, CSV/JSON/차트 리포트.
> 아직 TODO(코드에 명시): 실제 사진용 학습된 검출기와 EXIF/GPS 메타데이터 파싱. 여기 있는 어떤 것도 상용 농업ツール인 척하지 않습니다.
>
> *배경 안내: 이 데모는 실제 클라이언트 프로젝트를 익명화한 것입니다 — 수확량 보고를 위한 상업 재배에서의 개화/봉오리 카운팅. 클라이언트 데이터, 이미지, 식별 정보는 포함되어 있지 않습니다.*

---

## 문제

상업용 화훼/과수 재배에서 핀 꽃 수 vs 안 핀 봉오리 수는 향후 수확량을 보여주는 가장 이른 확실한 신호입니다. 현재는 손으로 셉니다: 느리고, 일관성이 없으며, 여러 온실로 확장할 수 없습니다. 카메라 + 카운팅 파이프라인은 순찰을 스프레드시트로 바꿔줍니다.

## 동작 원리

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **수집**(`pipeline/counter.py`) — `<region>_<YYYY-MM-DD>.jpg` 명명 규칙의 사진 폴더를 읽습니다.
2. **검출**(`detector/`) — 데모 백엔드는 HSV 공간에서 꽃잎 색상을 분할하고(녹색 잎에 대한 분홍/흰색/노랑), 연결 요소 크기로 `bloom`(개화)과 `bud`(봉오리)를 분류합니다. 검출기는 `BloomDetector` 인터페이스 뒤에 있어 학습된 모델로 교체해도 파이프라인은 그대로입니다.
3. **집계** — 지역별, 일자별로 합산합니다.
4. **리포트**(`report/report.py`) — `bloom_report.csv`, `bloom_report.json`, 누적 막대 차트(`bloom_chart.png`)를 출력합니다. 보고용 한 페이지 요약본입니다.

## 빠른 시작

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 전체 데모: 시뮬레이션 사진 생성 -> 검출 -> 스코어 -> 리포트
python examples/demo.py
# 출력: demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# 자신의 사진으로 실행(<region>_<YYYY-MM-DD>.jpg 명명 규칙 필수)
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# 테스트
python -m pytest tests/ -q
```

## 데모 결과(시뮬레이션 데이터)

사진 6장, 2개 지역 × 3일, 총 357송이:

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*(샘플 출력은 데모 실행 시 생성됩니다. 리포지토리에 포함된 것은 생성기이며 이미지가 아닙니다.)*

## 프로젝트 구조

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

## 로드맵

- [ ] `YoloDetector`: 어노테이션된 실제 꽃/봉오리 사진으로 YOLOv8/v11 파인튜닝, `BloomDetector` 구현, 백엔드 교체(파이프라인 변경 불필요)
- [ ] 실제 카메라/드론 사진의 EXIF/GPS 파싱(파일명 규칙 대체)
- [ ] 비디오/드론 스윕 모드: 프레임 간 중복 제거로 한 줄 전체 카운트
- [ ] 봉오리 단계 분류(단단한 봉오리 → 착색 → 벌어짐)로 더 정밀한 수확량 예측
- [ ] 다중 작물 색상 프로파일(장미, 모란, 벚꽃, 사과꽃)

## 기술 스택

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## 라이선스

MIT — [LICENSE](LICENSE) 참조.
