# Bloom-Counter

[English](README.md) | **[简体中文](README.zh-CN.md)** | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Português](README.pt.md) | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**基于视觉的花朵开花／花蕾计数，用于智慧农业与产量预估。**

把相机对准大棚苗床或果园的一行，得到*每个区域、每一天各有多少花已开、多少蕾未放*——种植者预估产量、安排人工、向老板汇报所需的原始数字。

> **项目状态：可运行的演示版（诚实版）。**
> 整条流水线今天跑在**模拟**的田间照片上（每张生成的图都有水印）。真实的部分：图像接入、花／蕾检测、按区域／按天汇总、CSV／JSON／图表报告。
> 仍是 TODO（代码中明确标注）：针对真实照片训练好的检测器，以及 EXIF／GPS 元数据解析。这里没有任何东西假装自己已是生产级农艺工具。
>
> *背景说明：本演示脱敏自一个真实客户项目——商业种植中的花／蕾计数用于产量汇报。不包含任何客户数据、图像或可识别信息。*

---

## 要解决的问题

在商业花卉／果树种植中，已开花数 vs 未开蕾数是未来产量最早的硬信号。今天靠人工数：慢、不一致、无法在多个大棚间扩展。一台相机＋计数流水线，把一次巡棚变成一张表格。

## 工作原理

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **接入**（`pipeline/counter.py`）——读取按 `<region>_<YYYY-MM-DD>.jpg` 命名的照片文件夹。
2. **检测**（`detector/`）——演示后端在 HSV 空间分割花瓣颜色（粉／白／黄 vs 绿色叶片），再按连通域大小分为 `bloom`（已开）与 `bud`（未开）。检测器藏在 `BloomDetector` 接口后面，换上训练好的模型无需改动流水线。
3. **汇总**——按区域、按日期求和。
4. **报告**（`report/report.py`）——输出 `bloom_report.csv`、`bloom_report.json` 和堆叠柱状图（`bloom_chart.png`），给老板的一页纸。

## 快速上手

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 完整演示：生成模拟照片 -> 检测 -> 评分 -> 报告
python examples/demo.py
# 输出：demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# 在你自己的照片上运行（文件名须遵循 <region>_<YYYY-MM-DD>.jpg 规则）
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# 测试
python -m pytest tests/ -q
```

## 演示结果（模拟数据）

6 张照片，2 区域 × 3 天，共 357 朵花：

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*（示例输出在演示运行时生成；入库的是生成器，不是图片。）*

## 项目结构

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

## 路线图

- [ ] `YoloDetector`：在已标注的真实花／蕾照片上微调 YOLOv8/v11，实现 `BloomDetector`，替换后端（无需改动流水线）
- [ ] 真实相机／无人机照片的 EXIF／GPS 解析（替代文件名规则）
- [ ] 视频／无人机扫拍模式：跨帧去重，一次数完一整行
- [ ] 花蕾分期分类（紧蕾 → 显色 → 绽口），做更细的产量预测
- [ ] 多作物颜色配置（玫瑰、牡丹、樱桃、苹果花）

## 技术栈

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## 许可证

MIT —— 见 [LICENSE](LICENSE)。
