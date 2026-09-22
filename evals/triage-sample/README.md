# Triage eval — `evals/triage-sample/`

Eval de F17. Clasifica las **14 fuentes del corpus dorado** + **1 fixture híbrido sintético** y compara contra los `expected.json` declarados.

## Cómo se corre

```bash
python3 evals/triage-sample/run_eval.py --check-ranges
```

Esperado: `15/15 PASS` + `3 clases distintas en plan ✓`.

Flags:

- `--check-ranges` (recomendado): además del PASS/FAIL, valida que `hybrid-synthetic` declare ≥ 3 clases distintas en su `plan_runs_expected[]` (criterio 2 del roadmap).
- `--only <source_id>`: corre solo una fuente (debug).

## Estructura

```
evals/triage-sample/
├── README.md                         este archivo
├── build_hybrid.py                   regenera el fixture PDF híbrido (requiere reportlab)
├── run_eval.py                       corre triage.py sobre cada fuente y compara
├── expected/                         15 expected.json (14 corpus + 1 fixture)
│   ├── 01-postgresql-chapter.json
│   ├── 02-database-internals-chapter.json
│   ├── ...
│   └── hybrid-synthetic.json
└── fixtures/
    └── hybrid-synthetic.pdf          PDF de 8 páginas: 3 reliable + 2 scan + 3 degraded
```

## Cobertura

| Tipo | Fuentes | Notas |
|---|---|---|
| **Real (`[real]`)** | 01, 03, 04, 05, 06, 07, 10 (markdown), 11, 12, 14, hybrid-synthetic | Triage corre sobre la muestra real del corpus (HTML, TXT, PDF, MD) o sobre `fixtures/hybrid-synthetic.pdf`. |
| **Stub (`[stub]`)** | 02, 08, 09, 13 | El corpus declara "no descargado" en `card.md`. `run_eval.py` genera un stub sintético (HTML/TXT/PDF-scan mínimo) para verificar la mecánica. La verificación material se difiere a F118. |

`hybrid-synthetic` aparece marcado como `[real]` porque usa un PDF real, no un stub.

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple en este eval |
|---|---|
| Clasifica correctamente las 14 fuentes del corpus | `run_eval.py` produce PASS para 01–14 (10 reales + 4 stubs). |
| Un PDF híbrido produce plan mixto por rangos | `hybrid-synthetic` produce `pdf_hybrid` con 3 rangos distintos; la fuente hostil 14 (sin muestra real, evaluada sobre el mismo fixture) también produce `pdf_hybrid`. |
| Todas las heurísticas tienen umbral numérico | `scripts/ingest/thresholds.yaml` declara 4 heurísticas PDF con umbrales numéricos (`chars_per_page`, `fonts`, `full_page_image`, `non_printable_ratio`). `references/01-ingest/triage.md` §4 los lista explícitamente. |

## Verificación rápida (sin run_eval.py)

```bash
# Criterio 1 — el script corre y clasifica el corpus
python3 skill/notemartin-study-notes/scripts/ingest/triage.py \
  --source evals/corpus/01-postgresql-chapter/sample.html \
  --out-dir /tmp/triage-demo
cat /tmp/triage-demo/triage.json | python3 -m json.tool | head -30

# Criterio 2 — el fixture híbrido produce plan mixto
python3 skill/notemartin-study-notes/scripts/ingest/triage.py \
  --source evals/triage-sample/fixtures/hybrid-synthetic.pdf \
  --out-dir /tmp/triage-hybrid
python3 -c "import json; d=json.load(open('/tmp/triage-hybrid/triage.json')); print('classes:', [r['class'] for r in d['plan']])"

# Criterio 3 — toda heurística con umbral numérico
python3 -c "
import yaml
t = yaml.safe_load(open('skill/notemartin-study-notes/scripts/ingest/thresholds.yaml'))
for key in ['chars_per_page', 'fonts', 'full_page_image', 'non_printable_ratio']:
    for subk, v in t['pdf'][key].items():
        assert isinstance(v, (int, float)), f'{key}.{subk} no es numérico'
print('OK: 4 heurísticas con umbrales numéricos')
"
```

## Regenerar el fixture híbrido

```bash
pip install reportlab pypdf pyyaml
python3 evals/triage-sample/build_hybrid.py
```

El script depende solo de `reportlab` (Pillow viene como dependencia transitiva). Si se omite, `run_eval.py` sigue funcionando porque opera sobre el PDF ya generado en `fixtures/`.

## Lo que **no** cubre

- Verificación material contra el corpus completo con muestras reales. Las 5 fuentes sin muestra (`02`, `08`, `09`, `13`, `14`) se difieren a F118.
- Pruebas de regresión automáticas en CI. La suite se materializa en F118.
- Tests de rendimiento con PDFs de > 200 páginas. F30 (`ingest_check.py`) cierra ese extremo.
