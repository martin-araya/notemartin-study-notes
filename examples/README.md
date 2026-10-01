# Ejemplos end-to-end — `examples/`

> Documento normativo de la **Fase 120** del roadmap. Carpeta con 4 ejemplos end-to-end completos que demuestran la cadena L0–L4 sobre el corpus (F6): SDM, ledger, NoteMark, IR, renders en Obsidian / Notion API / AppFlowy, capturas SVG, reportes de calidad.
>
> Documentos complementarios: `evals/suite/cases/*.yaml` (F118), `evals/regression/cases/*.yaml` (F119), `evals/corpus/` (F6), `evals/rubric.md` (F7), `evals/sdm-sample/` + `evals/ledger-sample/` + `evals/ir-sample/` (patrones sintéticos), `references/08-render/contract.md` (F53).

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Los 4 ejemplos](#2-los-4-ejemplos) · 3. [Estructura por ejemplo](#3-estructura-por-ejemplo) · 4. [Cómo regenerar](#4-cómo-regenerar) · 5. [Cómo validar](#5-cómo-validar) · 6. [Capturas SVG](#6-capturas-svg) · 7. [Cambios permitidos](#7-cambios-permitidos)

## 1. Propósito y alcance

Esta carpeta contiene **4 ejemplos end-to-end completos** que demuestran la cadena completa de la skill sobre el corpus, uno por cada categoría del ROADMAP que la fase pide. Cada ejemplo:

- Cubre las 5 capas del pipeline (L0 ingesta → L1 SDM → L2 conocimiento → L3 autoría → L4 render).
- Pasa la puerta de calidad (F115) y los validadores (F113, F114).
- Muestra todos los artefactos intermedios commiteados al repo (no es necesario ejecutar nada para inspeccionarlos).
- Incluye capturas en los 3 destinos ricos (Obsidian, Notion API, AppFlowy) más Notion-md y HTML/PDF como bonus.

**Qué cierra (criterios del ROADMAP):**
- **C1.** Los cuatro pasan la puerta de calidad y los validadores.
- **C2.** Cada ejemplo muestra los artefactos intermedios.
- **C3.** Cada ejemplo incluye capturas de los tres destinos.

**Qué NO es:**
- No es la suite de evals de la skill (eso es `evals/suite/`, F118).
- No es la galería pública con capturas reales (eso es F121).
- No es una ejecución con un agente en producción: los artefactos se producen directamente desde el corpus + scripts. La ejecución con agente real se hace en F118/F119 sobre estos mismos casos.

## 2. Los 4 ejemplos

| Case ID | Categoría ROADMAP | Corpus source | Tipo de nota |
|---|---|---|---|
| `01-postgresql-chapter` | documentación de producto | `evals/corpus/01-postgresql-chapter/` (HTML nativo) | `api-reference` (perfil reference) |
| `02-database-internals-chapter` | libro técnico | `evals/corpus/02-database-internals-chapter/` | `concept` (perfil study) |
| `13-internet-archive-scan-hostil` | PDF escaneado | reuse `evals/preprocess-sample/fixtures/hostile-scan.png` | `concept` con `low_confidence` markers |
| `06-kubernetes-api-ref` | API reference extensa | `evals/corpus/06-kubernetes-api-ref/` (HTML nativo) | `api-reference` con tabla exhaustiva |

**Particularidad del caso 13:** la muestra del corpus `13-internet-archive-scan-hostil/` está pendiente de descarga por F6. F120 reutiliza el fixture sintético `hostile-scan.png` generado por F19 (ver `evals/preprocess-sample/`). Cuando F6 descargue la muestra real, regenerar con `build_examples.py --example 13-internet-archive-scan-hostil --source evals/corpus/13-internet-archive-scan-hostil/sample.pdf`.

## 3. Estructura por ejemplo

```
examples/<case-id>/
├── README.md                       # qué demuestra, cómo regenerarlo
├── source/                         # copia del corpus sample usado
│   └── sample.{html,pdf,png}
├── artifacts/                      # generado por build_examples.py
│   ├── triage.json                 # L0
│   ├── sdm.json                    # L1
│   ├── knowledge/
│   │   ├── ledger.json             # L2
│   │   ├── note-plan.json
│   │   └── glossary.json
│   ├── notemark/
│   │   └── <note-id>.nm            # L3 (1-2 notas por ejemplo)
│   └── ir/
│       └── <note-id>.json          # L3→IR
├── render/                         # L4
│   ├── obsidian/
│   │   ├── <note-id>.md
│   │   └── captures/<note-id>.svg
│   ├── notion_api/
│   │   ├── payloads/<note-id>-NNN.json
│   │   └── captures/<note-id>.svg
│   ├── notion_md/
│   │   ├── <note-id>.md
│   │   └── captures/<note-id>.svg
│   ├── appflowy/
│   │   ├── <note-id>.md
│   │   └── captures/<note-id>.svg
│   └── html_pdf/
│       ├── <note-id>.html
│       └── captures/<note-id>.svg
└── reports/                        # validadores
    ├── quality-gate.json           # F115
    ├── validator-suite.json        # F113 (subset)
    ├── fidelity-audit.json         # F114
    └── rubric-application.json     # F7 (evaluación humana con anclas)
```

## 4. Cómo regenerar

```bash
# Regenerar un ejemplo concreto.
python examples/build_examples.py --example 01-postgresql-chapter

# Regenerar todos.
python examples/build_examples.py --all

# Con capturas reales (requiere Playwright instalado).
python examples/build_examples.py --all --real-captures
```

Códigos de salida:
- 0 PASS — todos los ejemplos regenerados y validados.
- 1 FAIL — algún validador falló.
- 2 USAGE — argumentos inválidos.

## 5. Cómo validar

Cada `examples/<id>/reports/` contiene los JSON con el resultado de los validadores. Inspección rápida:

```bash
for ex in examples/*/; do
  echo "=== $ex ==="
  test -f "$ex/reports/quality-gate.json" && jq '.summary.errors // "n/a"' "$ex/reports/quality-gate.json"
  test -f "$ex/reports/fidelity-audit.json" && jq '.fidelity_score // .issues | length // "n/a"' "$ex/reports/fidelity-audit.json"
done
```

Para validar los renders, abrir `examples/<id>/render/<destino>/captures/<note-id>.svg` en un navegador.

## 6. Capturas SVG

Las capturas son **aproximaciones estructurales**: cada SVG muestra el layout del destino (callouts nativos, plegables, wikilinks, Mermaid como placeholder, propiedades). NO son screenshots reales de las plataformas.

**Para capturas reales**, instalar Playwright + Chromium:

```bash
pip install playwright
playwright install chromium
python examples/build_examples.py --all --real-captures
```

`--real-captures` añade PNG junto al SVG. Los SVG siguen siendo el entregable principal porque son reproducibles y no requieren browser.

## 7. Cambios permitidos

**No reabren F120:**
- Regenerar un ejemplo (artefactos se actualizan; mismo commit explica por qué).
- Añadir un 5º ejemplo (extensión; no toca los 4 ya cerrados).
- Cambiar `--source` de un ejemplo (swap a muestra real de corpus).
- Mejorar las plantillas SVG (mejor aproximación visual).
- Cambiar `--real-captures` de Playwright a otro headless browser (con ADR).

**Reabren F120:**
- Cambiar el conjunto de los 4 casos.
- Cambiar la lista de 3 destinos obligatorios.
- Cambiar el contrato de `artifacts/` o `render/`.
- Cambiar las plantillas SVG sin preservar la forma canónica (callouts, plegables, wikilinks).
- Cambiar el contrato de `reports/`.
