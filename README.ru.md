# Bloom-Counter

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Português](README.pt.md) | **[Русский](README.ru.md)**

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**Подсчёт распустившихся цветов и бутонов на основе компьютерного зрения — для умного сельского хозяйства и прогноза урожайности.**

Наведите камеру на тепличную гряду или ряд в саду — и получите *сколько цветов распустилось, а сколько бутонов ещё закрыто, по регионам и по дням*. Это исходные цифры, нужные производителю для прогноза урожая, планирования работ и отчётности.

> **Статус проекта: рабочее демо (честная редакция).**
> Сквозной конвейер сегодня работает на **СИМУЛИРОВАННЫХ** полевых фото (все сгенерированные изображения с водяным знаком). Что реально: приём изображений, детекция цветов/бутонов, агрегация по регионам и дням, отчёты CSV/JSON/графики.
> Что пока TODO (явно помечено в коде): обученный детектор для реальных фото и разбор метаданных EXIF/GPS. Ничто здесь не притворяется промышленным агрономическим инструментом.
>
> *Примечание: это демо анонимизировано на основе реального клиентского проекта — подсчёт цветов/бутонов в коммерческом хозяйстве для отчётности об урожае. Данные, изображения и идентифицирующие детали клиента не включены.*

---

## Задача

В коммерческом цветоводстве/садоводстве число распустившихся цветов против закрытых бутонов — самый ранний надёжный сигнал будущего урожая. Сегодня считают вручную: медленно, нестабильно, немасштабируемо между теплицами. Камера + конвейер подсчёта превращает обход в таблицу.

## Как это работает

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **Приём** (`pipeline/counter.py`) — читает папку фотографий с именами `<region>_<YYYY-MM-DD>.jpg`.
2. **Детекция** (`detector/`) — демо-бэкенд сегментирует цвета лепестков в пространстве HSV (розовый/белый/жёлтый на фоне зелёной листвы), затем классифицирует компоненты по размеру на `bloom` (распустившийся) и `bud` (закрытый). Детектор скрыт за интерфейсом `BloomDetector`, поэтому обученная модель подключается без изменения конвейера.
3. **Агрегация** — подсчёты суммируются по регионам и датам.
4. **Отчёт** (`report/report.py`) — пишет `bloom_report.csv`, `bloom_report.json` и столбчатую диаграмму с накоплением (`bloom_chart.png`) — одностраничная сводка для руководителя.

## Быстрый старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Полное демо: генерация СИМУЛИРОВАННЫХ фото -> детекция -> оценка -> отчёт
python examples/demo.py
# выходные данные: demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# Запуск на своих фото (имена обязаны следовать шаблону <region>_<YYYY-MM-DD>.jpg)
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# Тесты
python -m pytest tests/ -q
```

## Результаты демо (симулированные данные)

6 фото, 2 региона × 3 дня, всего 357 цветков:

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*(Пример вывода генерируется при запуске демо; в репозитории лежит генератор, а не изображения.)*

## Структура проекта

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

## Планы развития

- [ ] `YoloDetector`: дообучить YOLOv8/v11 на размеченных реальных фото цветов/бутонов, реализовать `BloomDetector`, заменить бэкенд (без изменений конвейера)
- [ ] Разбор EXIF/GPS для реальных фото с камеры/дрона (вместо именования файлов)
- [ ] Видео / режим облёта дроном: удаление дублей между кадрами, подсчёт целого ряда
- [ ] Классификация стадий бутона (плотный → окрашенный → раскрывающийся) для более точного прогноза урожая
- [ ] Цветовые профили для нескольких культур (розы, пионы, вишня, яблоневый цвет)

## Технологии

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## Лицензия

MIT — см. [LICENSE](LICENSE).
