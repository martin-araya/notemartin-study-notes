# OCR de fórmulas — `references/01-ingest/formulas.md`

> Documento normativo de la Fase 24 del roadmap. Define cómo el script `scripts/ingest/formulas.py` consume las regiones `semantic_class = "formula"` de F22 (con fallback geométrico), emite LaTeX, lo valida con un verificador regex, marca como pendiente cualquier fórmula inválida y preserva la numeración de la fuente.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, provee anclas `formula`), `references/01-ingest/tables.md` (F23), `references/01-ingest/pdf-native.md` (F18), `references/01-ingest/ocr-engines.md` (F20), `references/01-ingest/preprocess.md` (F19, provee imágenes `.processed.png` para recortes), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Triple entrada y detección de fórmulas](#3-triple-entrada-y-detección-de-fórmulas) · 4. [Reconocimiento a LaTeX (v1)](#4-reconocimiento-a-latex-v1) · 5. [Validador LaTeX (reglas regex)](#5-validador-latex-reglas-regex) · 6. [Detección bloque vs en línea](#6-detección-bloque-vs-en-línea) · 7. [Numeración preservada](#7-numeración-preservada) · 8. [Fallback: imagen pendiente](#8-fallback-imagen-pendiente) · 9. [Forma de `formulas.json` y `formulas_summary.json`](#9-forma-de-formulasjson-y-formulas_summaryjson) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Extraer fórmulas matemáticas de la fuente como LaTeX válido, preservando numeración y marcando como pendiente cualquier fórmula que no se pueda reconocer limpiamente. La salida es la entrada contractual para F31 (`build_sdm.py`).

`scripts/ingest/formulas.py` produce, en `<out-dir>/ingest/formulas/`:

- `page-NNNN.formulas.json` — array de fórmulas con `latex`, `latex_compiled`, `number`, `pending`, `image_path`, `bbox`.
- `formulas_summary.json` — global con `formula_count`, `compiled_count`, `pending_count`, `equation_index[]`.
- `images/page-NNNN/f001.formula.png` — recortes de fórmulas pendientes (cuando input es PNG/JPEG).

## 2. Cuándo se aplica

Tras F22 (`regions.py`). Las regiones con `semantic_class = "formula"` son anclas para F24. Si F22 no marcó ninguna, F24 detecta fórmulas geométricamente desde fragments.

```
python3 scripts/ingest/formulas.py \
    --source <regions_dir> --out-dir <dir> \
    [--fragments <fragments.json>] [--ocr <ocr_summary.json>] \
    [--images-dir <images_dir>] [--json-only]
```

Si `--source` no se pasa, busca `<out-dir>/ingest/regions/`. Si `--images-dir` se pasa (típicamente `<out-dir>/ingest/pages/`), F24 puede recortar la región de la imagen original cuando la fórmula es inválida.

## 3. Triple entrada y detección de fórmulas

**Modo 1 (con F22)**: lee `page-NNNN.regions.json` y selecciona regiones con `semantic_class = "formula"`. Cada una es una fórmula candidato.

**Modo 2 (sin F22)**: lee fragments/words y aplica detección geométrica:
- Construye histograma de alineaciones X (palabras con mismo `x` ± 6 px, conteo ≥ 3).
- Construye histograma de alineaciones Y.
- Una región "formula" candidata tiene ≥ 3 X × ≥ 1 Y con `S_SYMBOL_DENSITY ≥ 0.3` (proxy: ratio de símbolos no-alfanuméricos).

**Modo 3 (input PNG/JPEG con `--images-dir`)**: F24 puede recortar la región de la imagen original. Útil cuando el input es rasterizado (escaneos).

**Salidas**: lista de `FormulaRegion {page, bbox, words, image_path?}`.

## 4. Reconocimiento a LaTeX (v1)

El texto extraído de la región (concatenación de palabras en orden de lectura) se trata como LaTeX-like:

- Si el texto contiene `\(` / `\)` o `\[` / `\]` o `\frac`, `\sum`, etc., se conserva tal cual.
- Si el texto no tiene marcadores LaTeX pero tiene alta densidad de símbolos (S_SYMBOL_DENSITY ≥ 0.5), se asume LaTeX-like y se emite como tal.
- Normalización: eliminar whitespace redundante, unificar `\\` a `\`, etc.

En v1 NO se invoca `pdflatex`, `pix2tex`, ni `Nougat`. El script NO aproxima la expresión: si no compila, marca `pending: true`.

## 5. Validador LaTeX (reglas regex)

`LaTeXValidator.validate(text) → (bool, list[error])` verifica cinco reglas:

1. **Llaves balanceadas**: cada `{` tiene su `}` correspondiente.
2. **Anidamiento**: profundidad de llaves ≤ `LATEX_MAX_NESTED_BRACES = 5`.
3. **Comandos conocidos**: regex whitelist con macros comunes:
   ```
   \frac \sum \int \sqrt \prod \coprod
   \alpha \beta \gamma \delta \epsilon \zeta \eta \theta \iota \kappa \lambda \mu \nu \xi \pi \rho \sigma \tau \phi \chi \psi \omega
   \infty \partial \nabla \forall \exists
   \cdot \times \div \pm \mp \cup \cap \setminus \subset \supset \subseteq \supseteq \in \ni \notin
   \leq \geq \neq \approx \equiv \sim \simeq \cong \propto \to \rightarrow \leftarrow \Leftarrow \Rightarrow \leftrightarrow \mapsto
   \bar \hat \tilde \vec \dot \ddot \sum \prod
   \text \mathrm \mathbf \mathit \mathcal \mathbb \mathfrak
   \begin \end \left \right \big \Big \bigg \Bigg
   ```
   Comandos desconocidos (no en la whitelist) no invalidan la fórmula; se reportan en `compile_errors[]` pero la compilación puede pasar.
4. **Entornos balanceados**: `\begin{name}...\end{name}` con `name` válido:
   ```
   equation, align, aligned, matrix, pmatrix, bmatrix, vmatrix, Vmatrix,
   cases, gathered, alignat, split, eqnarray, multline
   ```
   Cada `\begin` debe tener su `\end` con el mismo `name`.
5. **Sin especiales huérfanos**: `_`, `^` no deben estar al principio o sin operando a la izquierda.

Si alguna regla falla, `latex_compiled = false` y `compile_errors[]` lista los problemas. Si pasa, `latex_compiled = true`.

## 6. Detección bloque vs en línea

Una fórmula es `inline` si:
- `height ≤ INLINE_MAX_HEIGHT_PX = 30` (en píxeles).
- `width < INLINE_MAX_WIDTH_RATIO × page_width = 0.5 × 612 = 306`.

En otros casos, `block`.

El script emite `inline: true/false` en el JSON. Esto permite a F31 aplicar la notación correcta en NoteMark (texto inline `$...$` vs bloque `$$...$$` o `\[...\]`).

## 7. Numeración preservada

Patrones de numeración detectados al final de la región formula o adyacentes:

- `(N.M)` o `(N)` en margen derecho, dentro de la región.
- `[N.M]` en margen.
- `\tag{N.M}` en LaTeX (preservado como parte de `latex`).
- `\label{eq:N.M}` (preservado como parte de `latex`).

El script extrae el primer match `(N.M)` o `(N)` y lo emite como `number`. Mantiene una tabla global `equation_index[]` en `formulas_summary.json`:

```jsonc
{
  "equation_index": [
    {"number": "(1.1)", "region_id": "f001", "page": 4},
    {"number": "(1.2)", "region_id": "f002", "page": 5}
  ]
}
```

Las referencias en el texto (`see eq. (1.1)` o `\ref{eq:1.1}`) NO se resuelven en F24 — esa resolución semántica queda para F31 (`build_sdm.py`).

## 8. Fallback: imagen pendiente

Si `latex_compiled = false`:

1. Si `--images-dir` se pasa y la región tiene imagen correspondiente, recortar y guardar como `ingest/formulas/images/page-NNNN/<id>.formula.png`. Marcar `pending: true` con `image_path: <ruta>`.
2. Si no hay imagen, marcar `pending: true` con `bbox` referencial (para F26 rasterizar después).
3. `compile_errors[]` se preserva en el JSON.

El script NUNCA aproxima una expresión inválida a una "cercana". Una fórmula no reconocida se preserva como imagen marcada.

## 9. Forma de `formulas.json` y `formulas_summary.json`

`formulas.json` por página:

```jsonc
{
  "page": 4,
  "formulas": [
    {
      "id": "f001",
      "latex": "\\frac{\\partial L}{\\partial \\theta} = \\sum_{i=1}^{n} x_i - \\mu",
      "latex_compiled": true,
      "compile_errors": [],
      "number": "(1.1)",
      "inline": false,
      "pending": false,
      "image_path": null,
      "bbox": [180, 320, 250, 80],
      "page": 4,
      "dwell_ms": 12
    }
  ]
}
```

`formulas_summary.json` global:

```jsonc
{
  "schema_version": "1.0.0",
  "source": { "regions_dir": "...", "hash": "..." },
  "formula_count": 5,
  "compiled_count": 4,
  "pending_count": 1,
  "equation_index": [
    {"number": "(1.1)", "region_id": "f001", "page": 4}
  ],
  "pending_formulas": [{"page": 1, "region_id": "f002", "image_path": "..."}],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 10. Anti-patrones

- **No** aproximar expresiones inválidas a válidas (criterio 2).
- **No** invocar `pdflatex` ni compiladores TeX externos.
- **No** usar OCR-ML (pix2tex, Nougat, etc.). La validación regex es suficiente para los criterios.
- **No** descartar numeración: si existe `(N.M)`, se preserva en `number`.
- **No** emitir `latex_compiled: true` cuando hay errores estructurales. La regla es dura.
- **No** rechazar el comando por desconocido: solo errores estructurales (llaves, anidamiento, entornos) invalidan `latex_compiled`.
- **No** aceptar PDF como input de imagen. Si `--images-dir` apunta a PNG/JPEG, recortar; si no, bbox referencial.

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El input es regions de F22 o fragments/ocr?
2. ¿Cada fórmula tiene `latex` no vacío?
3. ¿Las válidas tienen `latex_compiled: true` y `compile_errors: []`?
4. ¿Las inválidas tienen `pending: true` y `image_path` o `bbox`?
5. ¿Las numeradas tienen `number` preservado y `equation_index[]` actualizado?

```bash
python3 evals/formulas-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 24:**

- Añadir más comandos LaTeX al whitelist con ADR.
- Ajustar las constantes numéricas (`LATEX_MAX_NESTED_BRACES`, etc.) con ADR.
- Añadir más patrones de numeración.
- Añadir un campo opcional a `formulas.json` con default sensato.

**Reabren Fase 24:**

- Cambiar el algoritmo del validador (de regex a `pdflatex`).
- Cambiar la convención de numeración.
- Cambiar el formato de fallback (de imagen a otra cosa).
- Eliminar LaTeX como representación canónica.

## 12. Siguiente extractor — `code_ocr.py` (F25)

Tras F24 (formulas), las regiones con `semantic_class = "code"` o `"console"` (incluyendo AMB) se consumen para extracción de código:

1. F25 lee `ingest/regions/page-NNNN.regions.json` + `fragments.json` (F18).
2. **Reconstrucción byte-exact**: ordena palabras por `y_center` descendente, dentro de cada línea por `x` ascendente; inserta `\n` si `|Δy| > 4 px` (LINE_HEIGHT_TOL_PX) y `" "` si `gap > 2 px` (SMALL_GAP). NUNCA colapsa whitespace, NUNCA modifica indentación.
3. **Detección de lenguaje** por keywords (python/javascript/sql/bash/json) — no afecta las correcciones, solo el campo `language`.
4. **Tabla de confusiones** (regla dura): `l/1/I`, `0/O`, `-/—`, `"`/`"`, etc. SOLO se resuelven cuando la validación del parser falla sin la corrección.
5. **Validación sintáctica**: `ast.parse` para Python, `json.loads` para JSON, bracket matching para JS/SQL/Bash. Cada corrección registrada en `corrections[]` con `{char_pos, original, corrected, reason}`.
6. **Separación prompt/salida** para consolas con regex `^[$>]|>>>|In\[N\]:|mysql>|postgres>`.
7. **Bloques low_confidence** con `reason` documentado (mixed_indentation, applied_forced_correction, ambiguous_monospace_chars).

Detalles y umbrales: [`code-ocr.md`](code-ocr.md).
