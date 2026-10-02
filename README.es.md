# Bloom-Counter

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | **[Español](README.es.md)** | [Português](README.pt.md) | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**Conteo de flores abiertas y capullos basado en visión artificial, para agricultura inteligente y estimación de rendimiento.**

Apunta una cámara a un bancal de invernadero o a una hilera de huerto y obtén *cuántas flores se han abierto y cuántos capullos siguen cerrados, por región y por día*: los números crudos que un productor necesita para estimar el rendimiento, organizar la mano de obra e informar.

> **Estado del proyecto: demo funcional (edición honesta).**
> El pipeline completo funciona hoy con fotos de campo **SIMULADAS** (toda imagen generada lleva marca de agua). Lo que es real: ingesta de imágenes, detección de flores/capullos, agregación por región y día, e informes CSV/JSON/gráficos.
> Lo que sigue siendo TODO (marcado claramente en el código): un detector entrenado para fotos reales y el análisis de metadatos EXIF/GPS. Nada aquí pretende ser todavía una herramienta agronómica de producción.
>
> *Nota de contexto: esta demo está anonimizada a partir de un proyecto real de un cliente — conteo de flores/capullos en un cultivo comercial para informes de rendimiento. No incluye datos, imágenes ni detalles identificables del cliente.*

---

## El problema

En el cultivo comercial de flores/frutas, el número de flores abiertas frente a capullos cerrados es la primera señal sólida del rendimiento futuro. Hoy se cuenta a mano: lento, inconsistente e imposible de escalar entre invernaderos. Una cámara + un pipeline de conteo convierte un recorrido en una hoja de cálculo.

## Cómo funciona

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **Ingesta** (`pipeline/counter.py`): lee una carpeta de fotos nombradas `<region>_<YYYY-MM-DD>.jpg`.
2. **Detección** (`detector/`): el backend de la demo segmenta los colores de los pétalos en el espacio HSV (rosa/blanco/amarillo contra follaje verde) y luego clasifica los componentes por tamaño en `bloom` (abierta) vs `bud` (cerrado). El detector vive tras la interfaz `BloomDetector`, así que un modelo entrenado se integra sin tocar el pipeline.
3. **Agregación**: los conteos se suman por región y por fecha.
4. **Informe** (`report/report.py`): escribe `bloom_report.csv`, `bloom_report.json` y un gráfico de barras apiladas (`bloom_chart.png`): la hoja resumen para el jefe.

## Inicio rápido

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Demo completa: generar fotos SIMULADAS -> detectar -> puntuar -> informar
python examples/demo.py
# salidas: demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# Ejecutar con tus propias fotos (deben seguir el nombre <region>_<YYYY-MM-DD>.jpg)
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# Pruebas
python -m pytest tests/ -q
```

## Resultados de la demo (datos simulados)

6 fotos, 2 regiones × 3 días, 357 flores en total:

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*(La muestra se genera al ejecutar la demo; el repo incluye el generador, no las imágenes.)*

## Estructura del proyecto

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

## Hoja de ruta

- [ ] `YoloDetector`: afinar YOLOv8/v11 con fotos reales anotadas de flores/capullos, implementar `BloomDetector` y cambiar el backend (sin tocar el pipeline)
- [ ] Análisis EXIF/GPS para fotos reales de cámara/dron (reemplaza la convención de nombres)
- [ ] Modo vídeo/barrido con dron: deduplicar flores entre fotogramas, contar una hilera entera
- [ ] Clasificación de la etapa del capullo (cerrado → con color → abriéndose) para un pronóstico de rendimiento más fino
- [ ] Perfiles de color multicultivo (rosas, peonías, cerezos, manzanos en flor)

## Tecnologías

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## Licencia

MIT — ver [LICENSE](LICENSE).
