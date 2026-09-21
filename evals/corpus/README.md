# Corpus dorado — `evals/corpus/`

Conjunto de 14 fuentes (12 friendly + 2 hostile) que ejercitan la cadena completa del pipeline. Cada fuente tiene una ficha (`card.md`) con metadatos verificables y, cuando es posible, una muestra pequeña del documento original. La matriz de cobertura está en [`coverage.md`](coverage.md).

## Fuentes

| # | Identificador | Título | Categoría | Friendly/Hostil | Idioma | Páginas | Muestra |
|---|---|---|---|---|---|---|---|
| 01 | `01-postgresql-chapter` | PostgreSQL 16, "The SQL Language" | Documentación de producto | Friendly | en | ~80 | `sample.html` ✓ |
| 02 | `02-database-internals-chapter` | "Database Internals" sample chapter | Libro técnico de editorial | Friendly | en | ~30 | pendiente |
| 03 | `03-rfc-7231` | RFC 7231 — HTTP/1.1 Semantics | RFC | Friendly | en | ~100 | `sample.txt` ✓ |
| 04 | `04-arxiv-two-column` | arXiv preprint (dos columnas) | PDF dos columnas | Friendly | en | ~15 | `sample.pdf` ✓ |
| 05 | `05-iso-sql-tables` | PostgreSQL Reference (denso en tablas) | 20+ tablas / doc ≥ 200 pp | Friendly | en | ≥ 200 | `sample.html` ✓ |
| 06 | `06-kubernetes-api-ref` | Kubernetes API Reference — Pod v1 | API reference extensa | Friendly | en | ~30 (de ~500 totales) | `sample.html` ✓ |
| 07 | `07-docker-cli-ref` | Docker Engine CLI Reference | Referencia CLI | Friendly | en | ~15 | `sample.html` ✓ |
| 08 | `08-conference-transcript` | PostgreSQL conference transcript | Transcripción | Friendly | en | ~20 | pendiente |
| 09 | `09-conference-slides` | Conference slides (PPTX/PDF) | Diapositivas | Friendly | en | ~30 | pendiente |
| 10 | `10-postgres-readme-repo` | PostgreSQL GitHub repo (README) | README + repositorio | Friendly | en | ~5 | `sample.md` ✓ |
| 11 | `11-iso-cpp-syntax` | ISO C++ draft (EBNF railroad) | Diagramas de sintaxis | Friendly | en | ~50 | `sample.html` ✓ |
| 12 | `12-arxiv-formulas` | arXiv preprint (fórmulas densas) | Documento con fórmulas | Friendly | en | ~15 | `sample.pdf` ✓ |
| 13 | `13-internet-archive-scan-hostil` | Internet Archive scan torcido | **Hostil** (escaneo torcido + OCR sucio) | **Hostil** | en | muestra | pendiente |
| 14 | `14-book-bad-numbering-hostil` | Book with inconsistent numbering | **Hostil** (numeración inconsistente) | **Hostil** | en | muestra | pendiente |

**Resumen:** 14 fuentes · 9 con muestra descargada · 5 con muestra pendiente (decisión editorial o registro requerido, documentadas en cada `card.md`).

## Cómo se usa

- **Verificación de cobertura:** leer [`coverage.md`](coverage.md).
- **Ejecutar un eval:** el agente carga la skill, lee la `card.md` de la fuente elegida, ingiere la muestra con la cadena L0–L4, y mide con la rúbrica (F7) o la suite de evals (F118).
- **Descargar muestra faltante:** seguir el comando documentado en `card.md` y verificar el hash sha256.

## Convenciones

- Cada `card.md` declara: identificador, título, URL, licencia, formato, páginas, densidad, idioma, versión, presencia de tipos de contenido, hostilidad, OCR requerido, destinos esperados, tipos de nota esperados, plan de ingesta, categoría cubierta, riesgo si falta, y datos de la muestra (archivo, comando, hash sha256).
- Cada `sample.*` es una muestra de 3–10 páginas representativas. No es el documento completo.
- Las muestras con hash sha256 declarado son reproducibles: si la fuente original cambia, el sha256 detecta el cambio y se reabre la ficha.

## Lo que **no** está aquí

- El corpus **completo** de cada fuente (no versionado; se descarga bajo demanda cuando un eval real lo necesite).
- La rúbrica de evaluación — vive en `evals/rubric.md` (F7).
- Las suites de evaluación automatizadas — viven en `evals/` (F118).
- Las comparativas entre iteraciones de la skill — viven en `evals/runs/` (F118-F119).
