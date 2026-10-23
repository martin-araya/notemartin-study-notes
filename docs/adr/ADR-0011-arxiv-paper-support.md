# ADR-0011 — Soporte de artículos científicos arXiv y compuerta de completitud ≥ 98 %

**Fecha:** 2026-10-23
**Estado:** aceptada

**Atada a:** P0–P7, F18 (pdf_native), F22 (regions), F24 (formulas), F31 (build_sdm), F34 (provenance), F37 (information-units), F43 (completeness), F56 (notion_md), F115 (quality_gate), INV-05, INV-08.

## Contexto

La skill `notemartin-study-notes` fue concebida inicialmente para capítulos de libros técnicos y documentación web estructurada. Al evaluar su comportamiento sobre artículos científicos procedentes de arXiv (`evals/corpus/04-arxiv-two-column/sample.pdf`), se identificaron deficiencias estructurales que impedían garantizar una meta de completitud del contenido $\ge 98\%$:
1. **Pérdida matemática**: el OCR de fórmulas trataba cada glifo de fuentes Computer Modern como texto suelto, fragmentando ecuaciones y clasificando erróneamente 446 sub/superíndices como notas al pie.
2. **Entornos académicos no modelados**: teoremas, demostraciones, algoritmos y tablas eran tratados como texto de cuerpo genérico sin semántica formal.
3. **Ausencia de metadatos bibliográficos y de red**: no existía resolución de IDs ni descarga automatizada de la API de arXiv ni extracción del código fuente LaTeX.
4. **Falta de métrica de completitud para papers**: el ledger verificaba únicamente el 100 % de unidades `must-keep`, pero no existía una medición objetiva ponderada por palabras del cuerpo del documento.

## Decisión

Se adoptan cinco decisiones de diseño:

- **D1. Adquisición desacoplada (`arxiv_fetch.py`)**:
  Se implementa la resolución de identificadores arXiv (modernos `YYMM.NNNNN` y legacy `arch-ive/YYMMNNN`), la consulta a la API Atom (`export.arxiv.org/api/query`), y la descarga del PDF y del e-print (`.tar.gz`) mediante Python stdlib (`urllib.request`). Emite un `source-meta.yaml` contractual con procedencia `arxiv_api`, permitiendo ejecución reproducible y testing offline mediante flags `--pdf` y `--tex-archive`.

- **D2. Oráculo de código fuente TeX (`arxiv_tex.py`) y cascada de fórmulas**:
  Cuando el e-print LaTeX está disponible, se utiliza como oráculo autoritativo de verdad:
  1. Aplana inclusiones recursivas (`\input` e `\include`) ignorando comentarios `%`.
  2. Expande macros de autor del preámbulo (`\newcommand`, `\def`, `\DeclareMathOperator`) para que el renderizado en KaTeX/Notion no falle.
  3. Extrae ecuaciones display, teoremas, algoritmos, tablas y referencias (`.bbl`).
  4. En `formulas.py` se establece una cascada de 4 niveles: TeX Oracle (`latex_source: "tex"`) $\to$ motor OCR externo opcional $\to$ reconstrucción geométrica por glifos $\to$ `pending: true` con recorte de imagen para revisión asistida.

- **D3. Reutilización de `chapter-digest` mediante `paper-overlay.md`**:
  En lugar de crear un 16º tipo de nota principal en el enum cerrado (lo que causaría fragmentación masiva en `note-plan`, `selector.md` y checklists), se reutiliza el tipo `chapter-digest` con un *overlay* de secciones académicas (`references/05-note-types/paper-overlay.md`). El flujo de compilación y salida permanece inalterado: `NoteMark → IR → notion_md.py → .md → Notion`.

- **D4. Extensiones aditivas a los esquemas (`sdm.schema.json` y `ledger.schema.json`)**:
  Se realizan adiciones compatibles hacia atrás:
  - En `sdm.schema.json`: campos opcionales en `source` (`arxiv_id`, `arxiv_version`, `categories`, `doi`, `license`, `journal_ref`, `abstract`, `tex_available`), método `"arxiv_api"` en `source_provenance`, tipos de bloque `abstract`, `theorem`, `proof`, `algorithm`, `reference-list`, `reference-entry`, y origen `"source_tex"`.
  - En `ledger.schema.json`: nuevos tipos de unidad `theorem`, `proof`, `algorithm`, `claim-result`, `experimental-setup`, `bibliography-entry`.

- **D5. Validador bloqueante de completitud (`paper_coverage.py`)**:
  Se introduce `scripts/validate/paper_coverage.py` integrado condicionalmente en `quality_gate.py`:
  - Exige una cobertura ponderada de palabras $\ge 98\%$ del cuerpo del paper.
  - Exige el 100 % obligatorio de conservación para ecuaciones numeradas, teoremas, algoritmos y tablas.
  - Exige integridad bibliográfica y resolución de citas en el cuerpo.

## Consecuencias

**Ganamos:**
- Procesamiento de papers de arXiv con preservación demostrable $\ge 98\%$ del contenido hacia Markdown para Notion.
- Fórmulas matemáticas display de alta fidelidad compilables en KaTeX sin dependencias externas obligatorias.
- Preservación completa de teoremas (callouts), pruebas (toggles plegables `<details>`), algoritmos y tablas con valores numéricos íntegros.
- Capacidad de auditoría y puerta de calidad objetiva (`paper_coverage.py`).

**Perdemos:**
- Papers sin fuente TeX ni motor OCR instalado dependen de heurísticas de glifos o recortes pendientes (`pending: true`), requiriendo transcripción asistida por el agente para ecuaciones complejas.
- El preámbulo LaTeX de autores con macros no estándar requiere expansión previa.
