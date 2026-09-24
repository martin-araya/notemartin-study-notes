# OCR de código y consolas — `references/01-ingest/code-ocr.md`

> Documento normativo de la Fase 25 del roadmap. Define cómo el script `scripts/ingest/code_ocr.py` consume las regiones `semantic_class = "code"` o `"console"` de F22, reconstruye el texto byte-exact (preservando indentación), aplica solo correcciones sintácticas forzadas (cada una registrada), separa prompt y salida en consolas, y marca como `low_confidence: true` cualquier bloque dudoso.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, provee anclas `code` y `console`), `references/01-ingest/formulas.md` (F24), `references/01-ingest/pdf-native.md` (F18), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Reconstrucción byte-exact](#3-reconstrucción-byte-exact) · 4. [Detección de lenguaje](#4-detección-de-lenguaje) · 5. [Tabla de confusiones (regla dura)](#5-tabla-de-confusiones-regla-dura) · 6. [Validación sintáctica y corrección forzosa](#6-validación-sintáctica-y-corrección-forzosa) · 7. [Separación prompt / salida](#7-separación-prompt--salida) · 8. [Bloques de baja confianza](#8-bloques-de-baja-confianza) · 9. [Forma de `code_blocks.json` y `code_summary.json`](#9-forma-de-code_blocksjson-y-code_summaryjson) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Producir texto de código fuente y consolas con preservación estricta de indentación, separación prompt/salida, y registro de toda corrección sintáctica. La salida es la entrada contractual para F31 (`build_sdm.py`).

`scripts/ingest/code_ocr.py` produce, en `<out-dir>/ingest/code/`:

- `page-NNNN.code.json` — array de `CodeBlock` con `text`, `language`, `confidence`, `low_confidence`, `corrections[]`, `commands`, `output`, `bbox`.
- `code_summary.json` — global con `block_count`, `language_distribution`, `corrections_total`, `low_confidence_count`.

## 2. Cuándo se aplica

Tras F22 (`regions.py`). Las regiones con `semantic_class = "code"` o `"console"` son anclas para F25. Si F22 no marcó ninguna, F25 autodetecta clusters de palabras con `font_name` monoespaciado.

```
python3 scripts/ingest/code_ocr.py \
    --source <regions_dir> --out-dir <dir> \
    [--fragments <fragments.json>] [--json-only]
```

## 3. Reconstrucción byte-exact

Reglas:

1. Ordenar palabras por `y_center` descendente (PDF coords), luego `x` ascendente dentro de cada línea.
2. Detectar saltos de línea: `|y_center − prev_y_center| > LINE_HEIGHT_TOL_PX = 4.0` → nueva línea.
3. Concatenar palabras dentro de una línea: si `next.x − (prev.x + prev.w) > SMALL_GAP = 2.0`, insertar `" "` (espacio); en otros casos, no insertar.
4. **Nunca** colapsar whitespace, **nunca** modificar indentación, **nunca** aplicar pretty-printing.
5. Preservar tabs (`\t`) y saltos de línea (`\n`) literalmente.

Salida: cadena `text` que coincide carácter por carácter con el texto fuente extraído (excepto por las correcciones registradas).

## 4. Detección de lenguaje

Heurística por keywords (case-sensitive):

| Lenguaje | Señales |
|---|---|
| `python` | `def `, `class `, `import `, `from `, `if __name__`, `print(`, `lambda`, `:`, `self.` |
| `javascript` | `function`, `const `, `let `, `var `, `=>`, `console.log`, `import`, `export` |
| `sql` | `SELECT`, `FROM`, `WHERE`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, `VALUES` |
| `bash` | Líneas con prompt `$ ` o comandos `cd`, `ls`, `cat`, `grep` |
| `json` | Comienza con `{` o `[`; todo entre comillas |
| `console` | Líneas con prompt de REPL (`>>> `, `In[N]:`) o shell |
| `unknown` | Sin keywords identificados |

Si dos lenguajes empatan en señales, se prefiere `python > javascript > sql > bash > json`.

## 5. Tabla de confusiones (regla dura)

Cuando F25 detecta una ambigüedad tipográfica en monoespaciado, consulta la `CONFUSION_TABLE`:

| Confusión | Estrategia de resolución | ¿Forzada? |
|---|---|---|
| `l`/`1`/`I` | Sin regla de resolución por contexto (todas válidas como identificador). | NO |
| `0`/`O` | Sin regla de resolución. | NO |
| `-` (hyphen) / `—` (em-dash) | Si rodeado de espacios (`word — word`) → em-dash; si pegado a letras (`word-word`) → hyphen. | SÍ (resolución por contexto) |
| `"` straight vs `"` `”` curly | En código monoespaciado, straight es esperable. Si F18 extrajo curly → straight. | SÍ |
| `'` straight vs `'` `'` curly | Misma regla que `"`. | SÍ |
| `;` / `:` | Depende del lenguaje: Python `:` es dominante en `def:` / `if:` / `for:`. SQL `;` cierra statements. | NO (lenguaje-dependiente) |
| `{` / `(` | Ambos válidos según contexto (dict literal vs function call). | NO |

**Regla dura (criterio 3):** una corrección SOLO se aplica si es **forzada**, es decir, si la validación sintáctica falla sin ella. Cada corrección se registra individualmente en `corrections[]` con `{char_pos, original, corrected, reason}`.

## 6. Validación sintáctica y corrección forzosa

Algoritmo:

1. **Python**: intentar `ast.parse(text)`. Si falla con `SyntaxError`, capturar `(lineno, offset, text, msg)`. Buscar correcciones que harían el parse succeed:
   - Comilla de cierre faltante: añadir `"` o `'` al final.
   - Paréntesis de cierre faltante: contar `(` vs `)` en cada línea; si imbalance, añadir `)` al final de la línea que abre.
   - **NO** corregir `:` por `;` (decisión de lenguaje, no forzada).
   - **NO** corregir `0` por `O` (no forzada).
   - **NO** corregir `l`/`1`/`I` (no forzada).
   Cada corrección aplicada se registra en `corrections[]` con `char_pos`, `original`, `corrected`, `reason`.

2. **JSON**: intentar `json.loads(text)`. Si falla, capturar error. Buscar correcciones forzadas (comilla doble faltante al final).

3. **JavaScript/SQL/Bash**: validación de brackets balanceados `()[]{}` y comillas. Si no balancean, intentar pares específicos (p.ej., añadir `)` faltante al final del bloque). Cada corrección registrada.

4. Si después de aplicar todas las correcciones forzadas posibles, el parser sigue fallando → marcar `low_confidence: true` con `reason: "parser_failure_after_corrections"`.

## 7. Separación prompt / salida

Para bloques `console` (no para `code`), F25 separa las líneas en `commands[]` y `output[]` usando los `PROMPT_PATTERNS`:

```
^[$>]              # bash, fish, root
^\s*#              # root bash
^>>>               # Python REPL
^In\[\d+\]:        # IPython
^mysql>|^postgres>|^sqlite>   # DB shells
```

Algoritmo:
1. Recorrer líneas del bloque.
2. Si una línea comienza con un patrón de prompt → es comando. Guardar en `commands[]`.
3. Si una línea NO comienza con un patrón de prompt → es salida. Guardar en `output[]`.
4. Líneas vacías se mantienen (no son comando ni salida).

## 8. Bloques de baja confianza

Se marca `low_confidence: true` si:

- Algún carácter tiene `CONFUSION_TABLE` con estrategia no resuelta (e.g., `l/1/I` en identificador).
- El parser falla después de las correcciones aplicadas.
- La indentación detectada es inconsistente (mezcla de tabs y espacios en la misma línea).
- Confianza heurística < `LOW_CONFIDENCE_THRESHOLD = 0.7`.

Regla dura: **ningún bloque pasa en silencio**. Si hay duda, se marca `low_confidence: true` con `reason` documentado.

## 9. Forma de `code_blocks.json` y `code_summary.json`

`code_blocks.json` por página:

```jsonc
{
  "page": 3,
  "blocks": [
    {
      "id": "c001",
      "language": "python",
      "text": "def hello(name):\n    print(f'Hello, {name}!')\n\nhello('world')\n",
      "confidence": 0.95,
      "low_confidence": false,
      "corrections": [],
      "commands": [],
      "output": [],
      "bbox": [54, 100, 300, 200],
      "page": 3,
      "dwell_ms": 8
    }
  ]
}
```

`code_summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": { "regions_dir": "...", "hash": "..." },
  "block_count": 8,
  "language_distribution": {"python": 3, "javascript": 2, "console": 3},
  "corrections_total": 4,
  "low_confidence_count": 2,
  "corrections": [
    {"page": 3, "block_id": "c001", "char_pos": 15, "original": "\"", "corrected": "\"", "reason": "curly quote in code → straight quote (JSON parse)"}
  ],
  "low_confidence_blocks": [
    {"page": 3, "block_id": "c002", "reason": "mixed_indentation"}
  ],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 10. Anti-patrones

- **No** corregir `l`/`1`/`I` por plausibilidad (criterio 3).
- **No** corregir `0`/`O` por plausibilidad.
- **No** corregir `;` por `:` (o viceversa) sin validación de parser.
- **No** colapsar whitespace ni re-formatear indentación.
- **No** aplicar pretty-printing al código extraído.
- **No** omitir `corrections[]` en el JSON. Cada corrección debe tener los 4 campos.
- **No** marcar `low_confidence: true` sin `reason` documentado.
- **No** emitir bloque sin `language`. Si no se detecta, `language: "unknown"`.
- **No** mezclar lógica de corrección en el reconstructor (separación de responsabilidades).

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El input son regiones de F22 o fragments de F18?
2. ¿Cada bloque tiene `text` byte-exact (excepto por correcciones registradas)?
3. ¿Las correcciones forzadas están todas en `corrections[]` con 4 campos?
4. ¿Los bloques con confusiones no resueltas tienen `low_confidence: true`?
5. ¿Los bloques consola tienen `commands[]` y `output[]` separados?

```bash
python3 evals/code-ocr-sample/run_eval.py
# Esperado: "PASS los 4 criterios"
```

**Cambios permitidos sin reabrir Fase 25:**

- Añadir un nuevo lenguaje a la detección.
- Añadir una nueva regla de resolución a `CONFUSION_TABLE` con ADR.
- Ajustar las constantes numéricas con ADR.
- Añadir un nuevo patrón de prompt.

**Reabren Fase 25:**

- Cambiar la política de corrección forzosa.
- Cambiar el algoritmo de reconstrucción byte-exact.
- Cambiar la regla de baja confianza.
- Eliminar el registro obligatorio de correcciones.

## 12. Siguiente fase — `review_report.py` (F26)

Tras F25 (code-ocr), F26 agrega la capa de confianza y revisión humana:

1. F26 lee `ingest/{regions,tables,formulas,code}.json` (F22/F23/F24/F25) + opcionalmente `images-dir/*.processed.png` (F19).
2. **Umbrales por tipo** (15 clases, justificados en §2 de `confidence.md`): code/console ≥ 0.90 (typo = syntax error), table ≥ 0.85 (números importan), formula/syntax_diagram ≥ 0.75, heading/caption ≥ 0.70, editorial_note ≥ 0.65, text ≥ 0.60, figure/capture/diagram ≥ 0.50.
3. **Bloqueo** si `critical_low_confidence_count ≥ MAX_LOW_CONF_CRITICAL = 3` (regiones críticas = code, console, table, formula, syntax_diagram). Exit code 1, `summary.blocked = true`.
4. **Reporte HTML** con filter bar JS inline; layout `<img>` (recorte Pillow, padding 5 px) + `<pre class="region-text">` lado a lado en cada `<tr class="region-row">`.
5. **Correcciones humanas** (`corrections.json`): aplica a la región especificada + propaga a todas las regiones con `original_text` idéntico (mínimo 5 chars para evitar propagación de chars sueltos).

Detalles y umbrales: [`confidence.md`](confidence.md).
