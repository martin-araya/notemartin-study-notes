# Ingesta de artículos arXiv — `references/01-ingest/arxiv.md`

> Documento normativo para la ingesta de artículos de investigación procedentes de arXiv (P1/P3). Define la resolución de identificadores, adquisición de metadatos mediante la API de arXiv, el oráculo de código fuente LaTeX (`arxiv_tex.py`), la cascada de reconocimiento de fórmulas y el modelo de completitud garantizada (≥ 98 %).
>
> Documentos complementarios: `references/01-ingest/formulas.md` (F24, cascada de ecuaciones), `references/01-ingest/pdf-native.md` (F18, extracción y normalizaciones), `references/02-source-model/provenance.md` (F34, procedencia `arxiv_api`), `references/05-note-types/paper-overlay.md` (plantilla académica sobre `chapter-digest`), `docs/arxiv-adaptation-plan.md`.

## Índice

1. [Propósito](#1-propósito) · 2. [Cuándo se aplica](#2-cuándo-se-aplica) · 3. [Resolución de identificadores](#3-resolución-de-identificadores) · 4. [Adquisición y metadatos (`arxiv_fetch.py`)](#4-adquisición-y-metadatos-arxiv_fetchpy) · 5. [Oráculo de código fuente TeX (`arxiv_tex.py`)](#5-oráculo-de-código-fuente-tex-arxiv_texpy) · 6. [Cascada de reconocimiento matemático](#6-cascada-de-reconocimiento-matemático) · 7. [Garantía de completitud ≥ 98 % (`paper_coverage.py`)](#7-garantía-de-completitud--98--paper_coveragepy) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Cómo verificar](#9-cómo-verificar)

---

## 1. Propósito

Permitir que la skill procese artículos científicos de arXiv manteniendo una **completitud del contenido ≥ 98 %** hacia Markdown para Notion, capturando con 100 % de fidelidad:
- Ecuaciones matemáticas numeradas en KaTeX (`$$ ... $$`).
- Enunciados de teoremas, lemas, proposiciones y corolarios.
- Pruebas y demostraciones completas (colapsables vía `<details>`).
- Algoritmos y pseudocódigo con numeración de pasos.
- Tablas y resultados numéricos sin truncamiento.
- Bibliografía completa con resolución de citas `[n]` o `[cite:n]`.

## 2. Cuándo se aplica

Se activa en cualquiera de los siguientes casos:
1. El usuario suministra un arXiv ID (`2201.00001`, `hep-th/9901001`, `2201.00001v3`).
2. El usuario suministra una URL de arXiv (`https://arxiv.org/abs/...`, `https://arxiv.org/pdf/...`).
3. El documento PDF procesado contiene la estampa lateral oficial de arXiv (`detect_arxiv_stamp` de `paper_text.py`).

---

## 3. Resolución de identificadores

`arxiv_fetch.py` parsea y normaliza identificadores modernos y legacy:
- **Modernos (post-2007)**: `YYMM.NNNNN[vN]` (e.g. `2201.00001v3`).
- **Legacy (pre-2007)**: `arch-ive/YYMMNNN[vN]` (e.g. `hep-th/9901001v2`).
- **URIs y URLs**: extrae el canonical ID descartando parámetros o prefijos (`arxiv:`, `https://arxiv.org/abs/`).

---

## 4. Adquisición y metadatos (`arxiv_fetch.py`)

```bash
python3 scripts/ingest/arxiv_fetch.py --id 2201.00001 --out-dir .notes-work/<hash>/ --with-tex
```

1. **Consulta API Atom**: `https://export.arxiv.org/api/query?id_list=<base_id>`.
2. **Extracción**:
   - `title`: título del artículo con espacios y saltos de línea normalizados.
   - `authors`: lista de autores individuales.
   - `published` / `updated`: fechas canónicas en ISO 8601 (`YYYY-MM-DD`).
   - `categories`: categorías temáticas primarias y secundarias (e.g. `math.NA`, `cs.LG`).
   - `doi` y `journal_ref`: identificadores persistentes de publicación formal.
   - `abstract`: resumen completo del autor.
3. **Descarga de PDF**: `https://arxiv.org/pdf/<canonical_id>` guardado en `<out-dir>/source.pdf`.
4. **Descarga de e-print TeX** (opcional con `--with-tex`): `https://arxiv.org/e-print/<canonical_id>`.
   - Se desempaqueta en `<out-dir>/tex/`.
5. **Emisión de `source-meta.yaml`**: genera el manifiesto contractual con `vendor: "arXiv"`, `hash: <sha256>`, `format: "pdf"`, campos opcionales y `source_provenance.method = "arxiv_api"`.

---

## 5. Oráculo de código fuente TeX (`arxiv_tex.py`)

Cuando existe código fuente LaTeX en `<out-dir>/tex/`, `arxiv_tex.py` actúa como oráculo de verdad para fórmulas y bloques formales:

```bash
python3 scripts/ingest/arxiv_tex.py --tex-dir <dir>/tex --out-dir <dir>
```

- **Aplanado recursivo**: reemplaza directivas `\input{...}` e `\include{...}` eliminando comentarios `%`.
- **Expansión de macros de autor**: extrae `\newcommand`, `\def` y `\DeclareMathOperator` del preámbulo y las sustituye en las ecuaciones para garantizar compatibilidad con KaTeX y Notion.
- **Extracción de entornos**:
  - `equation`, `align`, `gather`, `multline` (numerados y no numerados).
  - `theorem`, `lemma`, `proposition`, `corollary`, `definition`, `claim`, `proof`.
  - `algorithm`, `algorithmic`.
  - `table`, `tabular`.
  - `thebibliography` y archivos `.bbl`.
- **Alineación**: vincula las ecuaciones extraídas del TeX con las regiones `formula` detectadas en el PDF mediante número de ecuación y orden de lectura.

---

## 6. Cascada de reconocimiento matemático

Cada fórmula en `formulas.py` atraviesa una cascada priorizada:

1. **Nivel 1 — TeX Oracle**: si existe fuente TeX y la ecuación fue alineada, se adopta el LaTeX directo del autor con macros expandidas (`latex_source: "tex"`). Fidelidad: 100 %.
2. **Nivel 2 — Motor externo** (opcional): si el entorno cuenta con `marker`, `nougat` o `pix2tex`, se ejecuta sobre el recorte de la fórmula (`latex_source: "engine"`).
3. **Nivel 3 — Reconstrucción por glifos**: ensamblado de caracteres de fuentes Computer Modern (`CMMI`, `CMSY`, `CMR`) con inferencia geométrica de sub/superíndices (`latex_source: "glyphs"`).
4. **Nivel 4 — Pending con recorte**: si no compila o la confianza es baja, se marca `pending: true` y se rasteriza el recorte de imagen para transcripción asistida por el agente (`latex_source: "pending"`).

---

## 7. Garantía de completitud ≥ 98 % (`paper_coverage.py`)

El validador especializado `paper_coverage.py` actúa como compuerta de calidad bloqueante para fuentes académicas:

```bash
python3 scripts/validate/paper_coverage.py --sdm <sdm.json> --ledger <ledger.json> --min 0.98
```

- **Cobertura ponderada de palabras**:
  $$\text{Cobertura} = \frac{\sum \text{palabras de bloques con unidad } (written \lor merged)}{\sum \text{palabras del cuerpo (sin boilerplate)}} \ge 0.98$$
- **Compuerta de entidades críticas (100 % obligatorio)**:
  - 100 % de ecuaciones numeradas presentes en la nota.
  - 100 % de teoremas, lemas y proposiciones enunciados fielmente.
  - 100 % de algoritmos preservados.
  - 100 % de tablas y resultados numéricos sin omisión.
- **Integridad de referencias**: toda cita `[n]` o `[cite:n]` en el texto debe resolver a una entrada en la bibliografía final.

---

## 8. Anti-patrones

- ❌ **Omitir demostraciones o apéndices**: descartar apéndices técnicos rompe el umbral del 98 %. Las demostraciones largas deben plegarse en `<details>`, no eliminarse.
- ❌ **Sustituir ecuaciones clave por prosa vaga**: decir "el autor aplica una ecuación diferencial" en lugar de emitir la fórmula `$$ ... $$` viola la compuerta de ecuaciones críticas.
- ❌ **Usar macros de LaTeX sin expandir**: incluir `\R` o `\diag` sin expandir causa errores de renderizado en Notion/KaTeX.
- ❌ **Asumir dos columnas fijas sin verificar**: papers con bloques de autores en 3 columnas o figuras full-width deben tratarse mediante bandas horizontales y columnas dinámicas.

---

## 9. Cómo verificar

```bash
# 1. Ingesta completa con TeX
python3 scripts/ingest/arxiv_fetch.py --id 2201.00001 --out-dir .notes-work/test/ --with-tex

# 2. Oráculo TeX
python3 scripts/ingest/arxiv_tex.py --tex-dir .notes-work/test/tex --out-dir .notes-work/test/

# 3. Validación del gate de cobertura
python3 scripts/validate/paper_coverage.py --workdir .notes-work/test/ --min 0.98

# 4. Evals automáticos
python3 evals/paper-text-sample/run_eval.py
python3 evals/paper-coverage-sample/run_eval.py
```
