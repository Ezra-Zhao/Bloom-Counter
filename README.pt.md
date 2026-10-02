# Bloom-Counter

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | **[Português](README.pt.md)** | [Русский](README.ru.md)

![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: demo](https://img.shields.io/badge/status-working_demo-orange)


**Contagem de flores abertas e botões baseada em visão computacional, para agricultura inteligente e estimativa de produtividade.**

Aponte uma câmera para um canteiro de estufa ou fileira de pomar e receba *quantas flores abriram e quantos botões continuam fechados, por região e por dia* — os números brutos de que um produtor precisa para estimar a produtividade, organizar a mão de obra e reportar.

> **Estado do projeto: demo funcional (edição honesta).**
> O pipeline de ponta a ponta hoje roda com fotos de campo **SIMULADAS** (toda imagem gerada tem marca d'água). O que é real: ingestão de imagens, detecção de flores/botões, agregação por região e dia, e relatórios CSV/JSON/gráficos.
> O que ainda é TODO (marcado claramente no código): um detector treinado para fotos reais e a análise de metadados EXIF/GPS. Nada aqui finge ser ainda uma ferramenta agronômica de produção.
>
> *Nota de contexto: esta demo foi anonimizada a partir de um projeto real de um cliente — contagem de flores/botões em um cultivo comercial para relatórios de produtividade. Não inclui dados, imagens ou detalhes identificáveis do cliente.*

---

## O problema

No cultivo comercial de flores/frutas, o número de flores abertas vs. botões fechados é o primeiro sinal sólido da produtividade futura. Hoje conta-se à mão: lento, inconsistente e impossível de escalar entre estufas. Uma câmera + um pipeline de contagem transforma uma ronda em uma planilha.

## Como funciona

```
  field photos                detection                  reporting
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ greenhouse-A │      │  BloomDetector       │      │  per region/date │
│ _2026-09-28  │─────▶│  interface           │─────▶│  blooms | buds   │──▶ CSV / JSON
│ .jpg         │      │  ├─ color-seg (demo) │      │  totals          │    + bar chart
└──────────────┘      │  └─ YOLO (TODO)      │      └──────────────────┘
                      └─────────────────────┘
```

1. **Ingestão** (`pipeline/counter.py`): lê uma pasta de fotos nomeadas `<region>_<YYYY-MM-DD>.jpg`.
2. **Detecção** (`detector/`): o backend da demo segmenta as cores das pétalas no espaço HSV (rosa/branco/amarelo contra folhagem verde) e depois classifica os componentes por tamanho em `bloom` (aberta) vs `bud` (fechado). O detector fica atrás da interface `BloomDetector`, então um modelo treinado entra sem tocar no pipeline.
3. **Agregação**: as contagens são somadas por região e por data.
4. **Relatório** (`report/report.py`): gera `bloom_report.csv`, `bloom_report.json` e um gráfico de barras empilhadas (`bloom_chart.png`) — o resumo de uma página para o chefe.

## Início rápido

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Demo completa: gerar fotos SIMULADAS -> detectar -> pontuar -> relatar
python examples/demo.py
# saídas: demo/images/  demo/output/{bloom_report.csv,bloom_report.json,
#           bloom_chart.png,annotated_sample.jpg}

# Executar com suas próprias fotos (devem seguir o nome <region>_<YYYY-MM-DD>.jpg)
python - <<'EOF'
from detector.color_segmentation import ColorSegmentationDetector
from pipeline.counter import process_directory, aggregate
from report.report import write_all

detector = ColorSegmentationDetector()
rows = aggregate(process_directory(detector, "my_photos"))
write_all(rows, "my_report")
EOF

# Testes
python -m pytest tests/ -q
```

## Resultados da demo (dados simulados)

6 fotos, 2 regiões × 3 dias, 357 flores no total:

| image | truth blooms/buds | detected | recall |
|---|---|---|---|
| greenhouse-A_2026-09-26 | 34 / 22 | 34 / 22 | 100% |
| greenhouse-A_2026-09-28 | 52 / 15 | 52 / 15 | 100% |
| greenhouse-B_2026-09-28 | 45 / 19 | 44 / 19 | 98% |
| **TOTAL** | **233 / 124** | **232 / 124** | **99.7%** |

![annotated sample](demo/output/annotated_sample.jpg)

*(A amostra é gerada ao executar a demo; o repo inclui o gerador, não as imagens.)*

## Estrutura do projeto

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

## Roteiro

- [ ] `YoloDetector`: ajustar YOLOv8/v11 com fotos reais anotadas de flores/botões, implementar `BloomDetector` e trocar o backend (sem mexer no pipeline)
- [ ] Análise EXIF/GPS para fotos reais de câmera/drone (substitui a convenção de nomes)
- [ ] Modo vídeo/varredura com drone: deduplicar flores entre quadros, contar uma fileira inteira
- [ ] Classificação do estágio do botão (fechado → com cor → abrindo) para uma previsão de produtividade mais fina
- [ ] Perfis de cor multicultura (rosas, peônias, cerejeiras, macieiras em flor)

## Tecnologias

Python · OpenCV (HSV segmentation, contour analysis) · NumPy · Matplotlib

## Licença

MIT — ver [LICENSE](LICENSE).
