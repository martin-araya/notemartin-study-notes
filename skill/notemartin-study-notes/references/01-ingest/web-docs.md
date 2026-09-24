# Documentación web multipágina — `references/01-ingest/web-docs.md`

> Documento normativo de la Fase 29 del roadmap. Define cómo el script `scripts/ingest/web_docs.py` consume un mirror de documentación HTML multipágina (descargado con wget o presente en un directorio local) y produce `sections.json` con el orden del índice, texto limpio (sin boilerplate: nav/menus/banners/footers), URL canónica por sección y versión del producto detectada.
>
> Documentos complementarios: `references/01-ingest/regions.md` (F22, contrato de `regions.json`), `references/01-ingest/other-formats.md` (F28, precedente de script de formatos), `references/00-pipeline/architecture.md` §3.1 (L0 Ingesta), §5 (frontera de capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Descubrimiento del índice y del orden](#2-descubrimiento-del-índice-y-del-orden) · 3. [Eliminación de boilerplate](#3-eliminación-de-boilerplate) · 4. [Límites de dominio y política del sitio](#4-límites-de-dominio-y-política-del-sitio) · 5. [URL canónica por sección](#5-url-canónica-por-sección) · 6. [Detección de versión del producto](#6-detección-de-versión-del-producto) · 7. [Forma de `sections.json` y `metadata.json`](#7-forma-de-sectionsjson-y-metadatajson) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Cómo conectar con F31](#9-cómo-conectar-con-f31) · 10. [Diferencias con F28](#10-diferencias-con-f28-other_formats) · 11. [Cómo verificar + cambios permitidos](#11-cómo-verificar--cambios-permitidos)

## 1. Propósito

Producir `sections.json` estandarizado a partir de un mirror de documentación HTML multipágina, con el orden del índice preservado, el boilerplate eliminado y las URLs canónicas preservadas para F31.

`scripts/ingest/web_docs.py` produce, en `<out-dir>/ingest/web_docs/`:

- `sections.json` — array de secciones en orden del índice.
- `metadata.json` — global con `total_pages`, `index_url`, `product_version`, `domain`, `warnings[]`.

## 2. Descubrimiento del índice y del orden

Algoritmo:

1. Parsear `--index <path>` (default `index.html`) para extraer:
   - `<link rel="canonical">` → URL canónica raíz.
   - `<nav>` → menú principal; cada `<a href>` es un nodo hijo del índice.
   - `<meta name="product">`, `<meta name="version">`, `<meta name="docfx:product">` → producto + versión.
2. BFS desde el índice: para cada `<a href>` en el `<nav>`, leer la página local correspondiente y extraer:
   - `<link rel="canonical">` → URL canónica de esa sección.
   - `<h1>`, `<h2>`, `<h3>` → jerarquía de headings.
   - `<main>` o `<article>` o `<div class="content">` → contenido principal (después de eliminar boilerplate).
3. Mantener el orden de aparición en el `<nav>` (orden del índice).

## 3. Eliminación de boilerplate

Lista de selectores CSS a eliminar:

```
nav
header.navbar, header.topbar
div.navbar, div.topbar
footer
aside, div.sidebar, div.sidebar-left, div.sidebar-right
div.banner, div.cookie-banner, div.alert-banner
[role="banner"], [role="navigation"], [role="complementary"]
script, style, noscript
```

Adicionalmente:

- Eliminar comentarios HTML (`<!-- ... -->`).
- Eliminar elementos ocultos (`display: none` o `visibility: hidden` inferidos del HTML inline).
- Preservar el contenido principal: `<main>`, `<article>`, `<div class="content">`, `<section>`.

## 4. Límites de dominio y política del sitio

- `--base-url <url>`: URL canónica base que se usa como raíz del índice.
- `--allow-domain <domain>`: dominio(s) permitido(s) (default: extraído del `base-url`).
- `--respect-robots-txt`: lee `<source>/robots.txt` si existe; respeta `Disallow:` (F29 omite URLs que coincidan).
- `--max-depth N`: profundidad máxima del crawl (default: 5).
- `--max-pages N`: número máximo de páginas (default: 500).

Si una URL externa aparece en el nav pero está fuera del dominio, se omite con warning.

## 5. URL canónica por sección

Cada sección emite su URL canónica:
- Extraída de `<link rel="canonical">` si existe.
- Si falta, se construye como `base-url + path + #fragment` donde fragment es el id del primer heading (`<h1 id="...">`).
- Se incluye como `canonical_url` en `sections.json` para que F31 pueda crear anchors profundos.

## 6. Detección de versión del producto

Algoritmo (en orden):
1. `<meta name="product">` o `<meta name="docfx:product">` con valor separado por comas o espacios → `product`.
2. `<meta name="version">` con valor → `version`.
3. Regex en la URL base: `/v(\d+\.\d+\.\d+)/` → extrae versión.
4. Regex en la URL base: `/(\d+\.\d+)/` (versión mayor.menor) → fallback.
5. Si no se detecta → `product_version: null` con warning.

## 7. Forma de `sections.json` y `metadata.json`

`sections.json`:

```jsonc
{
  "source_url": "https://example.com/docs/",
  "total_pages": 4,
  "sections": [
    {
      "url_path": "intro.html",
      "canonical_url": "https://example.com/docs/intro.html",
      "level": 1,
      "title": "Introduction",
      "text": "Lorem ipsum dolor sit amet...",
      "headings": [
        {"level": 2, "text": "What is this?", "anchor": "what-is-this"}
      ],
      "links_internal": [
        {"text": "Next", "href": "install.html"}
      ],
      "page_metadata": {
        "product": "PostgreSQL",
        "version": "16.0",
        "domain": "example.com",
        "fetched_at": "2026-09-24T..."
      }
    }
  ]
}
```

`metadata.json`:

```jsonc
{
  "schema_version": "1.0.0",
  "source": {
    "dir": "...",
    "base_url": "https://example.com/docs/",
    "index": "index.html",
    "hash": "..."
  },
  "total_pages": 4,
  "index_url": "https://example.com/docs/index.html",
  "product_version": "16.0",
  "domain": "example.com",
  "allowed_prefixes": ["/docs/"],
  "disallowed_patterns": [],
  "boilerplate_selectors_removed": ["nav", "header.navbar", "footer", "..."],
  "warnings": [],
  "generated_at": "2026-09-24T..."
}
```

## 8. Anti-patrones

- **No** descargar URLs remotas (wget se hace fuera de F29).
- **No** usar ML para entender la estructura del sitio.
- **No** inventar URLs canónicas; usar la del `<link rel="canonical">` o derivar del `<h1 id="...">`.
- **No** omitir el `headings[]` array; cada `<h2>`, `<h3>` debe estar presente con su anchor.
- **No** eliminar `<main>` o `<article>`; son el contenido principal.
- **No** aceptar robots.txt que prohíba TODO sin warning explícito.
- **No** visitar URLs externas fuera de `--allow-domain` sin warning.

## 9. Cómo conectar con F31

F31 consume `sections.json` y construye bloques del SDM con `canonical_url` como ancla profunda. Cada `<h2>`, `<h3>` se usa como heading interno del bloque.

## 10. Diferencias con F28 (other_formats)

| Aspecto | F28 (other_formats) | F29 (web_docs) |
|---|---|---|
| Input | Archivos individuales (EPUB, DOCX, PPTX, etc.) | Mirror de HTML |
| Formato de URL | Sin URLs (formato cerrado) | URL canónica como ancla |
| Boilerplate | N/A | Eliminado (nav, footer, banner) |
| Orden | Cada archivo individual | Orden del índice del sitio |

## 11. Cómo verificar + cambios permitidos

Cinco pasos:

1. ¿El input es un directorio con archivos HTML?
2. ¿El índice (`--index`) se parsea correctamente y produce el orden esperado?
3. ¿Cada página tiene `canonical_url`?
4. ¿El boilerplate (nav, footer, banner) está ausente en `text`?
5. ¿La versión del producto está detectada (o `null` con warning)?

```bash
python3 evals/web-docs-sample/run_eval.py
# Esperado: "PASS los 3 criterios"
```

**Cambios permitidos sin reabrir Fase 29:**

- Añadir un selector a `BOILERPLATE_SELECTORS` con ADR.
- Añadir un patrón regex para detectar versión con ADR.
- Cambiar `--max-pages` o `--max-depth` con ADR.

**Reabren Fase 29:**

- Cambiar el algoritmo de crawl (no BFS).
- Eliminar la canonical URL preservation.
- Eliminar la detección de versión.
- Eliminar el respeto a robots.txt.

## 12. Siguiente fase — `ingest_check.py` (F30)

Tras F29 (web_docs), F30 actúa como **puerta de verificación** entre L0 (ingesta) y L1/L2 (procesamiento posterior):

1. F30 lee `--sdm <path>` (file o directorio con `page-*.regions.json`) + opcional `--declared-index <path>`.
2. **5 validaciones**:
   - Cobertura de páginas: cada página del input tiene ≥ 1 bloque; missing → anomalía crítica.
   - Secciones del índice: cada sección declarada aparece como heading; missing → anomalía crítica.
   - Saltos de numeración: consecutivos permitidos ≤ `MAX_NUMBERING_JUMP_FOR_WARNING = 1`; > `MAX_NUMBERING_JUMP_FOR_CRITICAL = 100` → anomalía crítica.
   - Bloques vacíos: heading sin contenido → crítica; otro bloque vacío → warning.
   - Densidad anómala: `MIN_WORDS_PER_BLOCK = 3` / `MAX_WORDS_PER_BLOCK = 5000` → warning.
3. **Comparación** índice declarado (TOC) vs jerarquía extraída del SDM → `missing_sections` (crítico) + `extra_sections` (info).
4. **Gate de anomalías críticas**:
   - Exit 0: sin anomalías o override humano aplicado.
   - Exit 1: críticas sin override → F31 NO debe consumir el SDM.
   - Exit 2: solo warnings → gate abierto, decisión recomendada.
5. **Override humano explícito** con `--allow-critical` + `--human-decision "reason"`; registra en `decision_log.json`.
6. **Sin ML**, sin OCR; solo heurísticas deterministas sobre `len(text)`, `word_count`, regex de números y comparación contra `declared-index`.

Detalles y constantes: [`ingest-check.md`](ingest-check.md).
