# F34 — `provenance-sample/`

Battery de evaluación de la Fase 34 (procedencia y versión). Verifica los 3 criterios de la fase:

1. Procedencia presente en cada SDM (`source_provenance` cubre los campos requeridos).
2. Distinguibilidad read/inferred (reglas duras: `read ⇒ confidence==1.0`; `inferred* ⇒ confidence<1.0`).
3. Version gating: `--require-version` exit 1 cuando la documentación no trae versión.

## Estructura

```
evals/provenance-sample/
├── README.md                         # este archivo
├── build_fixtures.py                 # genera 3 sdms sintéticos
├── fixtures/
│   ├── source-full/sdm.json                   # todos los campos via --source-meta (read)
│   ├── source-web-docs-fallback/sdm.json      # vendor/product/version inferidos
│   └── source-version-absent/sdm.json         # vendor+product presentes, version ausente
├── expected/
│   ├── full-expectations.json
│   ├── fallback-expectations.json
│   └── absent-expectations.json
└── run_eval.py                       # ejecuta los 3 criterios + --require-version
```

## Cómo correr

```bash
python3 evals/provenance-sample/run_eval.py
```

Exit 0 = PASS los 3 criterios; 1 = FAIL alguno; 2 = setup error.

## Lo que mide cada criterio

### Criterio 1 (`_criterion_1_propagation`)
Cada SDM lleva `source_provenance` con `id`, `hash`, `vendor`, `product`, `version` populados (los campos requeridos por spec §5). Verifica también que la proporción `read:method` vs `inferred:method` respeta `expected/*.json`.

### Criterio 2 (`_criterion_2_distinguishability`)
Recorre `source_provenance[*]` y aplica las reglas duras de spec §4:
- `method:"read"` ⇒ `confidence` debe ser exactamente 1.0.
- `method ∈ {inferred, url_regex, cover_or_header, web_docs_metadata}` ⇒ `confidence` debe ser < 1.0.
- `triage_metadata` queda excluido (spec §4 permite `confidence == 1.0` cuando el hash es computado determinísticamente).

### Criterio 3 (`_criterion_3_version_gate`)
Tres sub-casos:
- `source-version-absent` SIN `--require-version` → exit 2 (warning; version null + method=absent).
- `source-version-absent` CON `--require-version` → exit 1 (hard fail; documentación sin versión).
- `source-full` CON `--require-version` → exit 0/2 (version presente, gate pasa).

## Regresión a F13/F31/F32/F33

```bash
python3 scripts/util/validate_sdm.py --validate evals/sdm-sample/*.json       # PASS los 15 F13
python3 evals/build-sdm-sample/run_eval.py                                     # PASS los 3 F31
python3 evals/anchors-sample/run_eval.py                                       # PASS los 3 F32
python3 evals/assets-sample/run_eval.py                                        # PASS los 3 F33
```

F34 introduce `source_provenance` como bloque opcional en `sdm.schema.json` (no reabre F13 — solo añade una `properties` opcional). F31 fue editado para emitir el bloque cuando se ejecuta `build_sdm.py`.

## Wiring del F34 (commit único de F34)

Los entregables de la fase se commitean en este orden (cada uno su commit):

| Commit | Archivo | Tipo |
|---|---|---|
| 1 | `references/02-source-model/provenance.md` | spec |
| 2 | `evals/provenance-sample/` | eval battery |
| 3 | `scripts/validate/provenance.py` | validator |
| 4 | `schemas/sdm.schema.json` + `scripts/ingest/build_sdm.py` | integration (F13 additive + F31 edit menor) |
| 5 | `references/02-source-model/README.md` + `SKILL.md §5.2` + `scripts/README.md` | wiring |
| 6 | `ROADMAP.md` Fase 34 | cierre |
