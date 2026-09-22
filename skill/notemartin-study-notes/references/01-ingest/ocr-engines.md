# Motores OCR — `references/01-ingest/ocr-engines.md`

> Documento normativo de la Fase 20 del roadmap. Define cómo el script `scripts/ingest/ocr.py` ejecuta OCR sobre las imágenes preprocesadas por F19, con Tesseract como motor principal, EasyOCR como alternativo, idiomas combinados español+inglés, listas de palabras del dominio, reintentos automáticos ante baja confianza, y documentación de instalación por sistema operativo.
>
> Documentos complementarios: `references/01-ingest/preprocess.md` (F19, provee las imágenes `.processed.png`), `references/01-ingest/triage.md` (F17, marca `pure_scan`), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §8 (modo degradado: confianza OCR < 0.70).

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-aplica) · 3. [Motores soportados](#3-motores-soportados) · 4. [Idiomas combinados](#4-idiomas-combinados) · 5. [Listas de palabras y patrones](#5-listas-de-palabras-y-patrones) · 6. [Instalación por sistema operativo](#6-instalación-por-sistema-operativo) · 7. [Reintentos y modo degradado](#7-reintentos-y-modo-degradado) · 8. [Forma de `ocr_summary.json`](#8-forma-de-ocr_summaryjson) · 9. [Advertencias y códigos de salida](#9-advertencias-y-códigos-de-salida) · 10. [Anti-patrones](#10-anti-patrones) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Extraer texto de las imágenes preprocesadas por F19 con posición y confianza por palabra. El script es la última etapa de L0 Ingesta que produce bloques con contenido textual; F22 los clasifica y F31 los monta en el SDM.

`scripts/ingest/ocr.py` produce, en `<out-dir>/ingest/ocr/`:

- `ocr_summary.json` — resumen global con reintentos y configuración.
- `ocr_pages/<basename>-NNNN.json` — palabras con bbox + confianza por página.

## 2. Cuándo se aplica

Tras F19 (preprocesado). Para cada imagen `<basename>-NNNN.processed.png` que NO esté marcada como `is_blank: true`, F20 ejecuta OCR con reintentos si la confianza media es baja.

```
python3 scripts/ingest/ocr.py --source <dir|img> --out-dir <workdir/ingest/ocr/> \
    [--languages "spa+eng"] [--engine tesseract|easyocr|auto] \
    [--user-words <path>] [--user-patterns <path>] [--json-only]
```

Si la imagen es un PDF, F19 ya la rasterizó: el input debe ser PNG/JPEG. Si el usuario entrega un PDF directo, F20 falla con error claro (refiera a F19).

## 3. Motores soportados

### 3.1 Tesseract (motor principal)

| Aspecto | Valor |
|---|---|
| Versión recomendada | Tesseract 5.x |
| Multi-idioma nativo | Sí (ISO 639-3 codes; e.g. `spa`, `eng`) |
| Salida estructurada | `image_to_data` (TSV) con `level/page/block/par/line/word/left/top/width/height/conf/text` |
| Vía Python | `pytesseract` ≥ 0.3.10 |
| Binario | `tesseract` (externo a Python) |
| PSM por defecto | `6` (uniform block of text) |
| PSM en reintento sparse | `11` (sparse text — sin orden particular) |
| Determinismo | Determinista para el mismo input + parámetros |

Tesseract cubre el 95 % de los casos. Se invoca con:

```
tesseract <input.png> stdout --psm 6 -l spa+eng tsv
```

El script parsea el TSV y emite `words[]` con `bbox` y `conf`.

### 3.2 EasyOCR (motor alternativo)

| Aspecto | Valor |
|---|---|
| Versión recomendada | EasyOCR ≥ 1.7 |
| Multi-idioma nativo | Sí (códigos propios; e.g. `es`, `en`) |
| Salida estructurada | Lista de `(bbox, text, confidence)` |
| Vía Python | `import easyocr` |
| Inferencia | PyTorch; determinista con `seed` env var (`EASYOCR_SEED`) |
| Peso | ~100 MB (descarga bajo demanda) |
| Latencia | ~10x mayor que Tesseract para páginas pequeñas |

**Cuándo usar EasyOCR** (criterio de selección):

1. Tesseract no reconoce el idioma (p.ej. coreano, árabe, chino).
2. Tesseract falla con `mean_conf < 0.70` tras los 3 reintentos (`invert`, `sparse_psm`, `invert+sparse_psm`).
3. El usuario lo especifica explícitamente vía `--engine easyocr`.

EasyOCR se importa **bajo demanda** (lazy import) para no penalizar el caso por defecto.

## 4. Idiomas combinados

### 4.1 Convención de código

Tesseract usa ISO 639-3 (`spa`, `eng`, `deu`, `fra`, ...). EasyOCR usa ISO 639-1 o códigos propios (`es`, `en`, `de`, `fr`). El script acepta CSV en Tesseract-style y traduce a EasyOCR-style si es necesario.

### 4.2 Combinación español + inglés

Idioma por defecto: `spa+eng` (Tesseract) o `es,en` (EasyOCR). El script acepta:

```
--languages "spa+eng"     # Tesseract style
--languages "es,en"       # EasyOCR style (auto-detectado)
```

Para combinar correctamente, Tesseract instala los language data:

| macOS | `brew install tesseract-lang` |
| Ubuntu | `apt install tesseract-ocr-spa tesseract-ocr-eng` |
| Windows | vía installer o `tesseract-ocr-spa` + `tesseract-ocr-eng` packages |

## 5. Listas de palabras y patrones

Tesseract acepta dos archivos opcionales para mejorar la precisión sobre vocabulario específico:

- `--user-words <path>` — una palabra por línea. Tesseract las trata como válidas aunque no estén en su diccionario base.
- `--user-patterns <path>` — un patrón regex por línea. Útil para tokens técnicos (UUIDs, comandos CLI, etc.).

Ejemplo `user-words.txt`:

```
PostgreSQL
pg_dump
psql
pg_basebackup
WAL
MVCC
```

Ejemplo `user-patterns.txt`:

```
\d+
\d+\.\d+\.\d+
[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}
```

### 5.3 Sourcing desde `profile.yaml`

Si el `profile.yaml` de la fuente declara `ocr.user_words` y/o `ocr.user_patterns`, el script los carga automáticamente si no se pasan `--user-words`/`--user-patterns` explícitamente. Precedencia:

1. CLI (`--user-words <path>`) gana.
2. Si no, `profile.yaml.ocr.user_words` (path a archivo).
3. Si no, defaults vacíos (no wordlist).

## 6. Instalación por sistema operativo

### 6.1 macOS (Homebrew)

```bash
brew install tesseract tesseract-lang
# Verificación
tesseract --version
tesseract --list-langs
```

`tesseract-lang` instala los datos de idioma para los 100+ idiomas soportados (incluyendo `spa.traineddata` y `eng.traineddata`).

Para EasyOCR:

```bash
pip install easyocr
# En el primer uso, descarga ~100MB de modelos. Configurable vía EASYOCR_MODULE_PATH.
```

### 6.2 Ubuntu / Debian (apt)

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
# Verificación
tesseract --version
tesseract --list-langs
```

Para EasyOCR:

```bash
pip install easyocr
```

### 6.3 Fedora / RHEL (dnf)

```bash
sudo dnf install -y tesseract tesseract-spanish tesseract-english
# Verificación
tesseract --version
tesseract --list-langs
```

Para EasyOCR:

```bash
pip install easyocr
```

### 6.4 Arch Linux (pacman)

```bash
sudo pacman -S tesseract tesseract-data-spa tesseract-data-eng
# Verificación
tesseract --version
tesseract --list-langs
```

Para EasyOCR:

```bash
pip install easyocr
```

### 6.5 Windows

**Opción A — Instalador oficial:**

1. Descargar el instalador de Tesseract en [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki).
2. Durante la instalación, seleccionar idiomas adicionales (Spanish, English).
3. Agregar `C:\Program Files\Tesseract-OCR` al PATH.
4. Verificación en PowerShell:
   ```powershell
   tesseract --version
   tesseract --list-langs
   ```

**Opción B — Chocolatey:**

```powershell
choco install tesseract
# Idioma adicional (ejecutar después):
choco install tesseract-languages
```

**Opción C — Scoop:**

```powershell
scoop install tesseract
# Idioma adicional:
scoop install tesseract-languages
```

Para EasyOCR (Python):

```powershell
pip install easyocr
```

### 6.6 Verificación post-instalación

Tres comandos deben funcionar sin error:

```bash
tesseract --version                 # muestra versión (4.x o 5.x)
tesseract --list-langs              # lista idiomas instalados (debe incluir spa y eng)
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

Si `--list-langs` no incluye `spa` y `eng`, instalar los paquetes de idioma adicionales (§6.1–§6.5).

## 7. Reintentos y modo degradado

Política de reintentos en cascada (máximo `OCR_MAX_RETRIES = 3`):

1. **Intento inicial**: motor primario (Tesseract) con la imagen preprocesada por F19 y `--psm 6`.
2. **Reintento 1** (`action: "invert"`): mismo motor, pero invierte la imagen (`cv2.bitwise_not`). Útil para texto claro sobre fondo oscuro (negativos de escaneo).
3. **Reintento 2** (`action: "alternative_engine"`): motor alternativo (EasyOCR si Tesseract).
4. **Reintento 3** (`action: "sparse_psm"`): motor primario con `--psm 11` (sparse text).

Cada reintento se registra en `ocr_summary.json.retries[]` con `{page, attempt, reason, action, resulting_mean_conf, succeeded}`. El script escoge el resultado con mayor `mean_conf` entre los intentos.

**Trigger del reintento:**

```
if mean_conf < OCR_RETRY_THRESHOLD (= 0.70) AND len(words) > OCR_MIN_WORDS (= 5):
    retry
```

`OCR_RETRY_THRESHOLD = 0.70` coincide con `architecture.md` §8 (modo degradado L0). `OCR_MIN_WORDS = 5` evita reintentar en páginas casi vacías (probablemente blank — F19 ya marca `is_blank`).

**Páginas blank:** si F19 marca `is_blank: true`, F20 emite `pages[].words = []` sin invocar OCR. Warning en `ocr_summary.json.warnings[]`.

## 8. Forma de `ocr_summary.json`

`schema_version: "1.0.0"` (const). Campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `schema_version` | string const | sí | `"1.0.0"` |
| `source.path` | string | sí | ruta absoluta del input |
| `source.hash` | string hex 64 | sí | sha256 del input |
| `source.size_bytes` | int | sí | bytes del input |
| `source.format` | enum | sí | `image / images-dir` |
| `engine` | string | sí | motor final usado (`tesseract` o `easyocr`) |
| `languages` | array<string> | sí | idiomas combinados |
| `user_words_applied` | bool | sí | si se aplicaron listas de palabras |
| `user_patterns_applied` | bool | sí | si se aplicaron patrones |
| `retries[]` | array | sí | eventos de reintento (puede ser vacío) |
| `page_count` | int | sí | total de páginas procesadas |
| `pages[]` | array | sí | una entrada por página |
| `pages[].page` | int | sí | 1-indexed |
| `pages[].is_blank` | bool | sí | si la página es blank (heredado de F19) |
| `pages[].words[]` | array | sí | lista de `OCRWord` (puede ser vacío) |
| `pages[].words[].text` | string | sí | contenido de la palabra |
| `pages[].words[].bbox` | array[4 ints] | sí | `[x, y, w, h]` en píxeles |
| `pages[].words[].conf` | float | sí | confianza [0, 100] |
| `pages[].words[].page` | int | sí | 1-indexed |
| `pages[].words[].block/par/line/word` | int | sí | posición Tesseract-style |
| `pages[].mean_conf` | float | sí | confianza media de la página [0, 100] |
| `pages[].engine_used` | string | sí | motor del intento ganador |
| `pages[].retries_for_page` | int | sí | número de reintentos disparados |
| `pages[].dwell_ms` | int | sí | tiempo de procesamiento |
| `warnings[]` | array<string> | sí | advertencias detectadas |
| `generated_at` | string ISO 8601 | sí | timestamp UTC |

## 9. Advertencias y códigos de salida

Códigos: 0 OK · 1 error fatal · 2 OK con advertencias.

Warnings posibles:

- `engine 'tesseract' not available; falling back to 'easyocr'`
- `page N: language 'XXX' not installed; OCR may degrade`
- `page N: mean_conf=0.62 < 0.70; 3 retries did not reach threshold; using best=0.68`
- `page N: is_blank (per F19); skipping OCR`
- `retry 1 (invert) succeeded: 0.74 ≥ 0.70`

`architecture.md` §8 aplica aguas abajo: si la confianza OCR es < 0.60, F26 (`review_report.py`) marca la página para revisión humana.

## 10. Anti-patrones

- **No** filtrar palabras con `conf < 0` antes de calcular `mean_conf`. Tesseract marca palabras no detectadas con `conf = -1`; omitirlas infla la media artificialmente. Filtrar para `words[]`, NO para `mean_conf`.
- **No** invocar OCR sobre imágenes originales (`<basename>-NNNN.png`). Siempre sobre `.processed.png` de F19.
- **No** ejecutar OCR sobre páginas marcadas `is_blank: true` por F19. Consumir directamente `pages[].words = []`.
- **No** introducir dependencias nuevas en `scripts/ingest/ocr.py` más allá de `pytesseract` y la lazy import de `easyocr`. Tesseract es binario externo.
- **No** aceptar PDF como `--source`. F19 lo rasteriza; F20 falla con error claro si llega PDF.
- **No** emitir bbox con `w = 0` o `h = 0`. Filtrar palabras mal segmentadas (outlier típico de Tesseract en glifos raros).
- **No** desordenar las palabras. Tesseract emite en orden de lectura; el script respeta ese orden.

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El motor principal (Tesseract) está disponible? (`tesseract --version`).
2. ¿Los idiomas `spa` y `eng` están instalados? (`tesseract --list-langs`).
3. ¿La salida tiene `words[].conf >= 0` y `bbox` válido para ≥ 90% de las palabras?
4. ¿Los reintentos se registran cuando `mean_conf < 0.70`?
5. ¿La documentación de instalación cubre macOS, Ubuntu/Debian y Windows?

```bash
python3 evals/ocr-sample/run_eval.py
# Esperado: "PASS los 4 criterios"
```

**Cambios permitidos sin reabrir Fase 20:**

- Añadir un nuevo motor OCR tras la interfaz `OCREngine` (con ADR).
- Ajustar umbrales numéricos con evidencia experimental (con ADR).
- Añadir un campo opcional a `ocr_summary.json` con default sensato.

**Reabren Fase 20:**

- Cambiar la interfaz `OCREngine`.
- Cambiar la política de reintentos (afecta a F26).
- Cambiar la convención de bbox (afecta a F22 layout, F31 SDM).
- Eliminar Tesseract como motor principal.
