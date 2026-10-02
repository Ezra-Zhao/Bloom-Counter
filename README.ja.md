# Bloom-Counter

[English](README.md) | [简体中文](README.zh-CN.md) | **[日本語](README.ja.md)** | [한국어](README.ko.md) | [Español](README.es.md) | [Português](README.pt.md) | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**スマート農業と収量予測のための、画像ベースの開花／つぼみ計数。**

温室の苗床や果樹園の列にカメラを向けるだけ。*地域別・日別に「開花数／つぼみ数」*が返ってきます——収量予測・人員配置・報告に必要な生の数字です。

> **プロジェクト状態：動作するデモ版（正直エディション）。**
> エンドツーエンドのパイプラインは現在、**シミュレーション**の圃場写真で動作します（生成画像には全て透かし入り）。実際に動く部分：画像取り込み、開花／つぼみ検出、地域別・日別集計、CSV／JSON／チャート出力。
> 未実装（コード内で明示）：実写真用の学習済み検出器と EXIF／GPS メタデータ解析。ここにあるものは、本番の農業ツールであるふりをしていません。
>
> *背景注記：このデモは実際のクライアント案件を匿名化したものです——収量報告のための商業栽培における開花／つぼみ計数。クライアントのデータ・画像・特定情報は一切含まれていません。*

---

## 課題

商業用の花卉・果樹栽培では、開花数 vs 未開つぼみ数が、将来の収量を示す最も早い確かなシグナルです。現在は手作業で数えています：遅い、ばらつく、温室をまたいで拡張できない。カメラ＋計数パイプラインがあれば、見回りがそのまま表計算になります。

## 仕組み

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **取り込み**（`pipeline/counter.py`）——`<region>_<YYYY-MM-DD>.jpg` という命名規則の写真フォルダを読み込みます。
2. **検出**（`detector/`）——デモ用バックエンドは HSV 空間で花弁の色を分割し（緑の葉に対するピンク／白／黄）、連結成分のサイズで `bloom`（開花）と `bud`（つぼみ）に分類します。検出器は `BloomDetector` インターフェースの背後にあるため、学習済みモデルへの差し替えはパイプラインに触れずに可能です。
3. **集計**——地域別・日別に合計します。
4. **レポート**（`report/report.py`）——`bloom_report.csv`、`bloom_report.json`、積み上げ棒グラフ（`bloom_chart.png`）を出力。上司への一枚資料です。

## クイックスタート

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# フルデモ：シミュレーション写真の生成 → 検出 → スコア → レポート
python examples/demo.py
# 出力：demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# 自分の写真で実行（<region>_<YYYY-MM-DD>.jpg の命名規則が必須）
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# テスト
python -m pytest tests/ -q
```

## デモ結果（シミュレーションデータ）

6 枚の写真、2 地域 × 3 日間、合計 357 輪：

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*（サンプル出力はデモ実行時に生成されます。リポジトリに含まれるのは生成器であり、画像ではありません。）*

## プロジェクト構成

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

## ロードマップ

- [ ] `YoloDetector`：アノテーション済みの実花／つぼみ写真で YOLOv8/v11 をファインチューニングし、`BloomDetector` を実装してバックエンドを差し替え（パイプライン変更不要）
- [ ] 実カメラ／ドローン写真の EXIF／GPS 解析（命名規則の置き換え）
- [ ] 動画／ドローン走査モード：フレーム間の重複排除で一列全体を計数
- [ ] つぼみステージ分類（堅いつぼみ → 着色 → 開裂）でより精密な収量予測
- [ ] マルチ作物カラープロファイル（バラ、ボタン、サクラ、リンゴの花）

## 技術スタック

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## ライセンス

MIT —— [LICENSE](LICENSE) を参照。
