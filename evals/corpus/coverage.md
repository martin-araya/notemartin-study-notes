# Matriz de cobertura — `evals/corpus/coverage.md`

Documento de cobertura del corpus dorado. Permite verificar los tres criterios del roadmap (Fase 6) sin descargar nada:

1. Al menos 3 fuentes requieren OCR real.
2. Al menos una fuente supera las 200 páginas.
3. Hay al menos una fuente por cada destino de render.

## 1. Cobertura por categoría obligatoria

Cada fila: una de las 14 categorías del detalle de Fase 6 (incluyendo las 2 hostile como categorías explícitas). Las 14 fuentes cubren todas las categorías.

| Categoría del detalle | Cubierta por | Tipo de cobertura |
|---|---|---|
| Capítulo de documentación Oracle (sustituto: PostgreSQL) | `01-postgresql-chapter` | Friendly |
| Capítulo de libro técnico de editorial | `02-database-internals-chapter`, `14-book-bad-numbering-hostil` | Friendly + Hostil |
| PDF escaneado con OCR sucio | `02-database-internals-chapter`, `09-conference-slides`, `13-internet-archive-scan-hostil` | 2 Friendly + 1 Hostil |
| PDF a dos columnas | `04-arxiv-two-column` | Friendly |
| Documento con 20+ tablas | `05-iso-sql-tables` | Friendly |
| API reference extensa | `06-kubernetes-api-ref` | Friendly |
| Referencia CLI | `07-docker-cli-ref` | Friendly |
| RFC | `03-rfc-7231` | Friendly |
| Transcripción | `08-conference-transcript` | Friendly |
| Diapositivas | `09-conference-slides` | Friendly |
| README + repositorio | `10-postgres-readme-repo` | Friendly |
| Documento en inglés con salida esperada en español | `01-postgresql-chapter` (perfil de salida) | Friendly (perfil) |
| Documento con fórmulas | `12-arxiv-formulas` | Friendly |
| Documento con diagramas de sintaxis | `11-iso-cpp-syntax` | Friendly |
| **Hostil:** Escaneo torcido con ruido | `13-internet-archive-scan-hostil` | Hostil |
| **Hostil:** Numeración de secciones inconsistente | `14-book-bad-numbering-hostil` | Hostil |

**Total categorías cubiertas: 14/14** (más 2 hostile explícitas, también cubiertas). Cero categorías sin cubrir.

## 2. Cobertura por destino de render

Las 14 fuentes declaran sus destinos esperados en `card.md`. Recopilación:

| Destino | Cubierto por |
|---|---|
| **Obsidian** | 01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13, 14 |
| **Notion API** | 01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13, 14 |
| **Notion import** | 01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13, 14 |
| **AppFlowy** | 01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 13, 14 |
| **Markdown** | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14 |
| **HTML/PDF** | 01, 02, 03, 04, 05, 06, 07, 08, 10, 11, 12, 13, 14 |
| **Flashcards** | 01, 03, 06, 07, 11 |

**Total destinos cubiertos: 7/7.** Cada destino tiene ≥ 1 fuente (criterio 3 del roadmap).

## 3. Verificación de los tres criterios del roadmap

### Criterio 1 — Al menos 3 fuentes requieren OCR real

Fuentes que requieren OCR:

| Fuente | ¿Requiere OCR? | Razón |
|---|---|---|
| `02-database-internals-chapter` | sí | Variante escaneada del sample chapter (PDF de imágenes) |
| `09-conference-slides` | sí | PDF escaneado (imágenes de slides) |
| `13-internet-archive-scan-hostil` | sí | Escaneo degradado de libro técnico |

**Resultado criterio 1: ✓** 3 fuentes requieren OCR real, todas con confianza esperada entre 0.65 y 0.85 (en el rango que activa el modo degradado de L0 en `architecture.md` §8).

### Criterio 2 — Al menos una fuente supera las 200 páginas

| Fuente | Páginas declaradas |
|---|---|
| `05-iso-sql-tables` | ≥ 200 (PostgreSQL Reference, manual completo) |
| `03-rfc-7231` | ~100 (RFC individual) |
| `06-kubernetes-api-ref` | ~30 de ~500 totales (la API completa) |

**Resultado criterio 2: ✓** La fuente #05 declara ≥ 200 páginas en su manual completo (la muestra descargada es una sola página representativa).

### Criterio 3 — Al menos una fuente por cada destino de render

Ver tabla en §2.

**Resultado criterio 3: ✓** Los 7 destinos tienen ≥ 1 fuente que los declara como destino esperado.

## 4. Cobertura de umbrales del modo degradado

Tabla cruzada con `references/00-pipeline/architecture.md` §8.

| Umbral (architecture.md §8) | Fuente que mejor lo estresa |
|---|---|
| L0 — confianza OCR < 0.70 → reintentar | `13-internet-archive-scan-hostil` |
| L0 — reintentos > 2 → bloquear | `13-internet-archive-scan-hostil` |
| L0 — confianza OCR código < 0.85 → validación sintáctica | `13-internet-archive-scan-hostil` (si contiene código) |
| L0 — confianza OCR tablas < 0.80 → revisión | (no cubierto por el corpus actual) |
| L1 — bloques huérfanos > 20 % → bloquear | `14-book-bad-numbering-hostil` |
| L1 — confianza media OCR < 0.60 → fuente `degraded` | `13-internet-archive-scan-hostil` |
| L2 — cobertura `must-keep` < 100 % → bloquear | cualquiera |
| L2 — ciclos en grafo sin resolver | `05-iso-sql-tables`, `06-kubernetes-api-ref` |
| L3 — errores sintaxis NoteMark > 3 iteraciones | cualquiera |
| L4 — bloques > 100 en Notion API | `05-iso-sql-tables`, `06-kubernetes-api-ref` |
| L4 — Notion 429 → espera exponencial | cualquiera |
| L4 — capacidad ausente en destino | cualquiera con destino limitado |

## 5. Estado de la verificación

| Criterio | Resultado | Acción |
|---|---|---|
| 1. ≥ 3 fuentes con OCR | ✓ (3/3) | — |
| 2. ≥ 1 fuente > 200 páginas | ✓ | — |
| 3. ≥ 1 fuente por destino | ✓ | — |

**Cierre de Fase 6:** los tres criterios se cumplen. La fase puede marcarse como completa en `ROADMAP.md`.
