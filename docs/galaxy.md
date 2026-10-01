# Galería multi-dominio — `docs/galaxy.md`

> Catálogo de las 14 fuentes del corpus dorado (`evals/corpus/`, F6) que la skill procesa de extremo a extremo. Cada fila resume la fuente y enlaza a su ficha técnica, al caso F118 (cuando existe) y a la nota de ejemplo F120 (cuando existe).
>
> Documentos complementarios: `evals/corpus/README.md` (F6, índice + cobertura), `examples/` (F120, end-to-end), `evals/suite/cases/` (F118, suite de evals).

## Índice de fuentes

Las 14 fuentes del corpus se listan por categoría. Las marcadas como **hostil** ejercitan el modo degradado de L0 (`architecture.md` §8).

### Documentación de producto

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 01 | `01-postgresql-chapter` | PostgreSQL 16 — "The SQL Language" | Friendly | `case-01-postgresql-select` | [examples/01-postgresql-chapter/](../examples/01-postgresql-chapter/) |
| 06 | `06-kubernetes-api-ref` | Kubernetes API Reference — Pod v1 | Friendly | `case-06-kubernetes-api-ref` | [examples/06-kubernetes-api-ref/](../examples/06-kubernetes-api-ref/) |
| 10 | `10-postgres-readme-repo` | PostgreSQL GitHub repo (README) | Friendly | — | — |

### Libros técnicos de editorial

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 02 | `02-database-internals-chapter` | "Database Internals" sample chapter | Friendly | `case-02-database-internals-concept` | [examples/02-database-internals-chapter/](../examples/02-database-internals-chapter/) |
| 14 | `14-book-bad-numbering-hostil` | Book with inconsistent numbering | **Hostil** | — | — |

### RFC y referencias normativas

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 03 | `03-rfc-7231` | RFC 7231 — HTTP/1.1 Semantics | Friendly | `case-03-rfc-7231-concurrency` | — |
| 11 | `11-iso-cpp-syntax` | ISO C++ draft (EBNF railroad) | Friendly | — | — |

### Documentos con OCR

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 02 | `02-database-internals-chapter` | "Database Internals" (variante escaneada) | Friendly | (cubierto por el caso friendly) | — |
| 09 | `09-conference-slides` | Conference slides (PPTX/PDF) | Friendly | `case-09-conference-slides-diag` | — |
| 13 | `13-internet-archive-scan-hostil` | Internet Archive scanned book (torcido) | **Hostil** | `case-13-internet-archive-scan` | [examples/13-internet-archive-scan-hostil/](../examples/13-internet-archive-scan-hostil/) (sintético) |

### Documentos con fórmulas / tablas / diagramas

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 04 | `04-arxiv-two-column` | arXiv preprint (dos columnas) | Friendly | `case-04-arxiv-two-column-arch` | — |
| 05 | `05-iso-sql-tables` | PostgreSQL Reference (≥ 200 pp, denso en tablas) | Friendly | `case-05-iso-sql-tables-config` | — |
| 12 | `12-arxiv-formulas` | arXiv preprint (fórmulas densas) | Friendly | — | — |

### Otros

| # | Identificador | Título | Friendly/Hostil | Caso F118 | Ejemplo F120 |
|---|---|---|---|---|---|
| 07 | `07-docker-cli-ref` | Docker Engine CLI Reference | Friendly | — | — |
| 08 | `08-conference-transcript` | PostgreSQL conference transcript | Friendly | — | — |

## Cómo se usa esta tabla

- **Auditoría de cobertura**: el suite de F118 cubre 6/14 fuentes. Las 8 restantes se ejercitan en F120 + en corridas manuales con agente en producción.
- **Selección de fuentes para el set de regresión** (F119): la elección de las 4 fuentes del set se hace en `evals/regression/SET.md` con justificación por caso.
- **Selección de ejemplos end-to-end** (F120): los 4 ejemplos son las fuentes más representativas de cada categoría del ROADMAP.
- **Actualización**: cuando F6 descargue muestras faltantes o amplíe el corpus, regenerar esta tabla con `python scripts/build_galaxy.py` (a crear cuando F6 emita el primer cambio material).

## Categorías cubiertas (referencia F6)

14 categorías obligatorias del ROADMAP, todas cubiertas:

1. Capítulo de documentación Oracle (sustituto: PostgreSQL) → `01-postgresql-chapter`.
2. Capítulo de libro técnico de editorial → `02-database-internals-chapter`, `14-book-bad-numbering-hostil`.
3. PDF escaneado con OCR sucio → `02-database-internals-chapter` (variante), `09-conference-slides`, `13-internet-archive-scan-hostil`.
4. PDF a dos columnas → `04-arxiv-two-column`.
5. Documento con 20+ tablas → `05-iso-sql-tables`.
6. API reference extensa → `06-kubernetes-api-ref`.
7. Referencia CLI → `07-docker-cli-ref`.
8. RFC → `03-rfc-7231`.
9. Transcripción → `08-conference-transcript`.
10. Diapositivas → `09-conference-slides`.
11. README + repositorio → `10-postgres-readme-repo`.
12. Documento en inglés con salida esperada en español → `01-postgresql-chapter` (perfil de salida alternativo).
13. Documento con fórmulas → `12-arxiv-formulas`.
14. Documento con diagramas de sintaxis → `11-iso-cpp-syntax`.

**Hostiles explícitas:** escaneo torcido con ruido (`13-internet-archive-scan-hostil`), numeración inconsistente (`14-book-bad-numbering-hostil`).

## Cambios permitidos

**No reabren F121:**
- Añadir una columna nueva a la tabla (link a otra fase, cobertura de paleta, etc.).
- Añadir una fila nueva cuando F6 amplíe el corpus.
- Reordenar filas por categoría.

**Reabren F121:**
- Cambiar las categorías obligatorias (las 14 del ROADMAP F6).
- Cambiar la columna "Caso F118" (la decisión de qué casos están cubiertos).
