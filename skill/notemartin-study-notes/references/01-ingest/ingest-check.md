# Verificación de ingesta — `references/01-ingest/ingest-check.md`

> Documento normativo de la Fase 30 del roadmap. Define cómo el script `scripts/validate/ingest_check.py` detecta anomalías en la ingesta (páginas omitidas, secciones del índice ausentes, saltos de numeración, bloques vacíos, densidad anómala) y bloquea el avance a L2 con anomalías críticas sin decisión explícita del humano.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, contrato de regions.json), `references/01-ingest/tables.md` (F23), `references/01-ingest/formulas.md` (F24), `references/01-ingest/code-ocr.md` (F25), `references/01-ingest/post-ocr.md` (F27), `references/01-ingest/confidence.md` (F26), `references/01-ingest/web-docs.md` (F29), `references/00-pipeline/architecture.md` §3.1 (L0), §4 (gate entre L0/L1).

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Cobertura de páginas](#2-cobertura-de-páginas) · 3. [Secciones del índice presentes](#3-secciones-del-índice-presentes) · 4. [Saltos de numeración](#4-saltos-de-numeración) · 5. [Bloques vacíos y densidad anómala](#5-bloques-vacíos-y-densidad-anómala) · 6. [Comparación índice declarado vs extraído](#6-comparación-índice-declarado-vs-extraído) · 7. [Gate de anomalías críticas](#7-gate-de-anomalías-críticas) · 8. [Forma de `validation_report.json`](#8-forma-de-validation_reportjson) · 9. [Cómo conectar con el pipeline](#9-cómo-conectar-con-el-pipeline) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito y alcance

Actuar como **puerta de verificación** entre L0 (ingesta) y L1/L2 (procesamiento posterior). F30 lee el SDM (o cualquier output L0 convertible a regions.json) + un índice declarado (TOC del documento original) y emite un reporte con las anomalías detectadas. Si hay anomalías críticas, F30 retorna exit code 1 y bloquea el avance. El humano puede usar `--allow-critical` con `--human-decision "..."` para override y registrar la decisión en `decision_log.json`.

`scripts/validate/ingest_check.py` produce, en `<out-dir>/`:

- `validation_report.json` — reporte con anomalies categorizadas (critical / warnings).
- `decision_log.json` (opcional) — registro de overrides humanos.

## 2. Cobertura de páginas

Algoritmo:
1. Extraer páginas presentes en el SDM: `pages_in_sdm = {r["page"] for r in regions}`.
2. Comparar contra `pages_declared` (de `--declared-index` o derivado de `regions` si no se provee índice).
3. `missing_pages = sorted(pages_declared - pages_in_sdm)`.
4. Si `missing_pages` no está vacío → anomalía crítica `{type: missing_page, page: p}` por cada página ausente.

## 3. Secciones del índice presentes

Algoritmo:
1. Extraer headings del SDM: `[(r["number"], r["text"], r["level"]) for r in regions if r["number"]]`.
2. Comparar contra `declared-sections = [s["number"] for s in declared_index["sections"]]`.
3. `missing_sections = sorted(set(declared-sections) - set(sdm-section-numbers))`.
4. `extra_sections = sorted(set(sdm-section-numbers) - set(declared-sections))`.
5. `missing_sections` no vacío → anomalía crítica `{type: missing_section, section: n}`.
6. `extra_sections` no vacío → info `{type: extra_section, section: n}` (no crítico).

## 4. Saltos de numeración

Algoritmo:
1. Ordenar `sdm_section_numbers` por orden natural.
2. Para cada par consecutivo `(a, b)`: si la diferencia entre `b` y `a` en el último nivel numérico es > `MAX_NUMBERING_JUMP_FOR_WARNING = 1` → warning `{type: numbering_jump, from: a, to: b, skipped: ...}`.
3. Si la diferencia es > `MAX_NUMBERING_JUMP_FOR_CRITICAL = 100` → anomalía crítica (probable omisión de una rama entera del documento).
4. Si una rama entera falta (e.g., 1.1 → 2.1 sin 1.2-1.99) → crítica `{type: missing_branch, from: "1.x", to: "2.1"}`.

## 5. Bloques vacíos y densidad anómala

Algoritmo:
1. Por cada bloque del SDM:
   - Si `block["text"].strip() == ""`:
     - Si `block["semantic_class"] in {"heading", "heading_1", ...}` → anomalía crítica `{type: empty_heading}`.
     - En otros casos → warning `{type: empty_block}`.
2. Si `word_count < MIN_WORDS_PER_BLOCK = 3` → warning `{type: too_short}`.
3. Si `word_count > MAX_WORDS_PER_BLOCK = 5000` → warning `{type: too_long}`.

## 6. Comparación índice declarado vs extraído

Compara la jerarquía del SDM contra el `--declared-index`:

```python
declared_index = json.loads(declared_index_path.read_text())
sections_declared = [(s["number"], s["title"], s.get("expected_pages", [])) for s in declared_index["sections"]]
sections_present = [(r.get("number"), r.get("text"), r["page"]) for r in regions if r.get("number")]

missing = [(n, t) for n, t, _ in sections_declared if n not in {p[0] for p in sections_present}]
extra = [(n, t) for n, t in sections_present if n not in {p[0] for p, *_ in sections_declared}]
```

`missing` → `missing_sections` (crítico). `extra` → `extra_sections` (info).

## 7. Gate de anomalías críticas

Política de exit codes:

- **exit 0**: sin anomalías (críticas ni warnings). El pipeline puede continuar.
- **exit 1**: anomalías críticas SIN override humano. F31 (`build_sdm.py`) NO debe consumir el SDM. Bloqueo.
- **exit 2**: solo warnings sin críticas. Gate abierto, decisión humana recomendada pero no bloqueante.
- **exit 0 con `human_decision: "override"`**: anomalías críticas presentes pero override humano explícito vía `--allow-critical` + `--human-decision "reason"`. Logged en `decision_log.json`.

```python
if allow_critical and critical_count > 0:
    if not human_decision:
        raise RuntimeError("--allow-critical requires --human-decision with reason")
    report["human_decision"] = "override"
    report["human_decision_reason"] = human_decision
    # Logged in decision_log.json
    exit_code = 0
```

## 8. Forma de `validation_report.json`

```jsonc
{
  "schema_version": "1.0.0",
  "sdm_path": "/path/to/sdm.json",
  "declared_index_path": "/path/to/index.json",
  "totals": {
    "pages_in_sdm": 10,
    "pages_declared": 10,
    "missing_pages": [],
    "sections_declared": 8,
    "sections_present": 7,
    "missing_sections": ["1.3"],
    "extra_sections": []
  },
  "anomalies": {
    "critical": [
      {"type": "missing_page", "page": 5, "reason": "page 5 not in SDM"},
      {"type": "missing_section", "section": "1.3", "reason": "section declared in index but not found"}
    ],
    "warnings": [
      {"type": "empty_block", "block_id": "b012", "reason": "text empty"},
      {"type": "numbering_jump", "from": "1.1", "to": "1.3", "skipped": "1.2", "reason": "consecutive number gap"}
    ]
  },
  "human_decision": null,
  "validated_at": "2026-09-24T..."
}
```

## 9. Cómo conectar con el pipeline

F30 se ejecuta entre L0 y L1/L2. Si exit 1, F31 (`build_sdm.py`) NO debe consumir el SDM. Si exit 0 (o 2, o override), F31 puede continuar.

Ejemplo:

```bash
python3 scripts/validate/ingest_check.py \
    --sdm ingest/output.json \
    --declared-index ingest/declared-index.json \
    --out-dir ingest/validation/

if [ $? -eq 1 ]; then
    echo "BLOCKED: critical anomalies detected"
    exit 1
fi

# Continuar con L1/L2
python3 scripts/build_sdm.py --source ingest/output.json ...
```

## 10. Anti-patrones

- **No** avanzar a L1/L2 sin verificar.
- **No** omitir anomalías críticas con `--allow-critical` sin `--human-decision`.
- **No** inventar números de página o sección faltantes.
- **No** marcar un bloque vacío como "no crítico" solo porque es corto (es crítico si es heading).
- **No** aplicar ML para detectar anomalías (heurísticas deterministas solamente).

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El SDM tiene `pages_in_sdm == pages_declared`?
2. ¿Cada sección del índice está presente en el SDM?
3. ¿Los saltos de numeración son ≤ 1 (warning) o > 100 (crítico)?
4. ¿Los headings tienen contenido (no están vacíos)?
5. ¿`--allow-critical` requiere `--human-decision`?

```bash
python3 evals/ingest-check-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 30:**

- Añadir un nuevo tipo de anomalía con ADR.
- Cambiar las constantes numéricas (`MIN_WORDS_PER_BLOCK`, etc.) con ADR.
- Cambiar el formato de `validation_report.json` con campos opcionales.

**Reabren Fase 30:**

- Eliminar el gate (dejar pasar críticas sin override).
- Cambiar la lógica de las 5 validaciones.
- Eliminar la comparación con `declared-index`.
