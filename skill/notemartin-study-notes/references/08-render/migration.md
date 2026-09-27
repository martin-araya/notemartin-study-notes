# Migration — Re-render entre destinos y reverse import

> Spec normativa para F64. Define el workflow de re-render desde IRs persistidos sin volver a la fuente, el reverse-import cuando el IR se perdió, y el reporte de ganancias/pérdidas.

## Índice

1. [Propósito](#1-propósito) · 2. [Re-render workflow](#2-re-render-workflow) · 3. [Capability comparison](#3-capability-comparison) · 4. [Migration report](#4-migration-report) · 5. [Reverse import](#5-reverse-import) · 6. [CLI workflows](#6-cli-workflows) · 7. [Verificación](#7-verificación) · 8. [Cambios permitidos](#8-cambios-permitidos)

## 1. Propósito

F54-F60 producen artifacts locales (`render/<dest>/<note>.{md,html}`) y F62 los publica a destinos remotos. F64 cubre dos necesidades:

- **Migración entre destinos** sin re-ingestar la fuente: el usuario ya tiene IRs persistidos (de una corrida previa); quiere renderizarlos a un destino nuevo sin volver al PDF original.
- **Reverse import** cuando el IR se perdió: solo se tiene el artifact renderizado (e.g., un `.md`); se necesita reconstruir un IR estructural.

Criterios cubiertos:

- **C1**: un conjunto de Obsidian se re-renderiza a Notion sin tocar el PDF.
- **C2**: el reporte lista ganancias y pérdidas por capacidad.
- **C3**: la importación inversa reconstruye la estructura.

## 2. Re-render workflow

```
$ python3 scripts/render/migrate.py re-render \
    --ir-source <path> --out-dir <dir> \
    --from <source> --to <target>

# Ejemplo: migrar de obsidian a notion_api.
$ python3 scripts/render/migrate.py re-render \
    --ir-source /workdir/ir/ \
    --out-dir /workdir-new/ \
    --from obsidian --to notion_api
```

Pasos:

1. El script carga los IRs desde `--ir-source` (directorio de `*.json`).
2. Invoca el renderer del destino (`scripts/render/<to>.py`) pasándole los IRs como `--ir` y el `--out-dir` destino.
3. Captura el `report-degradation.json` del renderer target.
4. Genera el `migration-report.{json,md}` comparando capacidades source vs target.

El script NO invoca el renderer source; los IRs ya están renderizados y persisten. No toca los artifacts de source (`render/<source>/`).

## 3. Capability comparison

La matriz F8 (`references/08-render/capability-matrix.md`) es la fuente de verdad para qué capacidades soporta cada destino. Para cada par `(source, target)`:

- **Ganancias** (`gains[]`): capacidades que `target` soporta ✅ y `source` no soportaba ❌.
- **Pérdidas** (`losses[]`): capacidades que `source` soportaba ✅ y `target` no soporta ❌.

Ejemplo: `obsidian` → `notion_api`:
- Ganancia: `backlinks` (Notion los tiene nativos, Obsidian no).
- Pérdida: `backlinks` custom section ("Referenciado por") que el renderer Obsidian inyectaba y Notion no necesita.

## 4. Migration report

`reports/migration-report.json`:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "...",
  "source": "obsidian",
  "target": "notion_api",
  "summary": {
    "notes_total": 12,
    "notes_created": 12,
    "notes_updated": 0,
    "notes_skipped": 0,
    "notes_errors": 0,
    "capabilities_gained": 1,
    "capabilities_lost": 0
  },
  "capability_diff": {
    "gains": [
      {"capability": "backlinks", "alternative": "Notion panel nativo"}
    ],
    "losses": []
  },
  "notes": [
    {
      "note_id": "nt-001",
      "status": "migrated",
      "degradations": [],
      "lost_units": []
    }
  ]
}
```

`reports/migration-report.md`: tabla legible con summary + per-note breakdown.

## 5. Reverse import

Cuando solo se tiene el artifact renderizado y no el IR, el sub-comando `reverse-import` parsea el archivo markdown/HTML y reconstruye un IR estructuralmente equivalente.

Heurística por tipo de block:

| Markdown | IR node |
|---|---|
| `# H1` ... `## H2` ... | `section` con level 1/2/... |
| Texto suelto | `paragraph` |
| ` ```lang ` ... ` ``` ` | `code` |
| `> texto` | `quote` (con `> [cite]` → `attrs.cite`) |
| `> [!note]`, `> [!warning]`, `> [!danger]`, etc. | `admonition` con `attrs.severity` |
| `- [ ] item`, `- [x] item` | `checklist` con `attrs.done` |
| `- item`, `* item`, `1. item` | `list` |
| `| h1 | h2 |` ... `| --- | --- |` | `table` con `headers` + `rows` |
| ` ```mermaid ` | `diagram` con `attrs.kind="mermaid"` |
| `$$ ... $$` (display) o `$ ... $` (inline) | `equation` |
| `<details markdown="1">` ... `<summary>` ... `</details>` | `collapsible` |
| `[[target|alias]]` | `link-note` con `attrs.target`, `attrs.text` |
| `![alt](src)` | `figure` con `attrs.src`, `attrs.alt` |

El reverse-import **NO recupera**:
- Contenido semántico perdido (texto eliminado manualmente).
- Atributos no serializados en el artifact (ej. `attrs.prompt` solo si el artifact lo preserva).
- Comentarios del usuario dentro de `<!-- user-content -->` (preservados verbatim).

Confidence level reportado en `migration-report.confidence`:
- `high`: ≥80% de los bloques identificados correctamente.
- `medium`: ≥50%.
- `low`: <50%.

## 6. CLI workflows

```
# Re-render desde obsidian a notion_api.
python3 scripts/render/migrate.py re-render \
    --ir-source <path> --out-dir <dir> \
    --from obsidian --to notion_api

# Reverse import desde un markdown sin IR.
python3 scripts/render/migrate.py reverse-import \
    --input render/obsidian/note.md \
    --output-ir ir/note.json \
    --format md

# Diff de capacidades entre dos destinos (sin migrar).
python3 scripts/render/migrate.py diff-capabilities \
    --from markdown --to html_pdf
```

Flags comunes: `--report-out <path>` para personalizar la salida del reporte.

Códigos de salida: `0` OK · `1` fatal · `2` warnings (migration con degradaciones).

## 7. Verificación

```bash
# C1: re-render obsidian → notion sin tocar el PDF.
python3 scripts/render/migrate.py re-render \
    --ir-source /workdir/ir/ --out-dir /workdir-new/ \
    --from obsidian --to notion_api
ls /workdir-new/render/notion_api/   # debe tener artifacts
ls /workdir/render/pdf/             # debe estar intacto

# C2: el reporte lista ganancias y pérdidas.
cat reports/migration-report.json | jq '.capability_diff.gains, .capability_diff.losses'

# C3: la importación inversa reconstruye la estructura.
python3 scripts/render/migrate.py reverse-import \
    --input render/obsidian/lost-note.md --output-ir ir/reconstructed.json
# Verificar: la jerarquía de headings y orden de bloques coinciden.
```

## 8. Cambios permitidos sin reabrir

- Añadir nuevos sub-comandos (`rollback`, `validate-migration`).
- Cambiar el formato del `migration-report.json` siempre que los 3 criterios sean verificables.
- Añadir heurísticas al parser de reverse-import (sin romper las existentes).

## 9. Cambios que reabren

- Eliminar el re-render workflow (rompe C1).
- Eliminar el reporte de capability-diff (rompe C2).
- Eliminar el reverse-import (rompe C3).
- Cambiar el formato de la capability-matrix sin versionado (rompe compat).
