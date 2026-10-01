# `notemartin-study-notes`

Skill instalable que convierte documentación técnica, libros técnicos y **PDFs escaneados (OCR)** en notas de estudio completas, trazables y publicables en **Obsidian**, **Notion** y **AppFlowy** (más Markdown estándar, HTML/PDF y sistemas de repaso espaciado).

> Lo que promete: fidelidad al original, cobertura verificable por ledger, formato intermedio NoteMark para que las notas viajen entre destinos sin reescritura.

---

## §1 · Qué es

`notemartin-study-notes` es una **skill** (no una aplicación). El razonamiento lo hace un agente que carga las instrucciones; los scripts solo hacen tareas deterministas (OCR, layout, hashes, validación de esquemas, render). Las notas se redactan en un formato intermedio (NoteMark) que se traduce a cada destino sin reescritura.

- Producto y garantías: [`docs/product-manifesto.md`](docs/product-manifesto.md) (F1).
- Manifiesto y decisiones: [`docs/adr/`](docs/adr/) y [`ROADMAP.md`](ROADMAP.md).
- Patrón de uso: la skill se dispara cuando un usuario entrega una fuente técnica y pide —o implica— producir notas de estudio publicables.

## §2 · Galería multi-dominio

La skill procesa **14 fuentes** del corpus dorado ([`docs/galaxy.md`](docs/galaxy.md)) que cubren 14 categorías del ROADMAP, incluyendo manuales de producto, libros técnicos, RFCs, PDFs escaneados, referencias API y diapositivas. Cuatro de ellas se entregan como ejemplos end-to-end en [`examples/`](examples/) (F120):

| Fuente | Categoría | Perfil | Salida |
|---|---|---|---|
| [PostgreSQL SELECT](examples/01-postgresql-chapter/) | Documentación de producto | reference | `api-reference` |
| [Database Internals](examples/02-database-internals-chapter/) | Libro técnico | study | `concept` |
| [Kubernetes Pod v1](examples/06-kubernetes-api-ref/) | API reference extensa | reference | `api-reference` |
| [Internet Archive scan](examples/13-internet-archive-scan-hostil/) | PDF escaneado hostil | hybrid | `concept` con `low_confidence` |

Las capturas SVG sintéticas por destino se ven en `examples/<id>/render/<destino>/captures/`.

## §3 · Flujo de 5 capas

```
L0 Ingesta   scripts   PDF / EPUB / DOCX / PPTX / HTML → regiones, texto, OCR
L1 SDM       script construye, agente inspecciona   árbol con anclas estables
L2 Conocimiento  agente decide, script contabiliza  unidades, ledger, grafo, plan
L3 Autoría   agente redacta NoteMark; script parsea a IR y valida
L4 Render    scripts   Obsidian · Notion · AppFlowy · Markdown · HTML/PDF · flashcards
```

Tres puertas bloqueantes: **fidelidad** (¿está todo?), **calidad** (¿enseña bien?), **render** (¿se ve bien en el destino?). Detalle operativo en [`docs/skill-anatomy.md`](docs/skill-anatomy.md) y [`skill/notemartin-study-notes/SKILL.md`](skill/notemartin-study-notes/SKILL.md).

## §4 · Garantías

Per [`docs/product-manifesto.md`](docs/product-manifesto.md) §3 (4 garantías, en orden de prioridad cuando chocan: fidelidad > cobertura > pedagogía):

1. **Fidelidad al original.** Métrica: el validador de fidelidad (F114) reporta cero invenciones detectadas; los literales (mensajes de error, defaults, sintaxis, comandos) se preservan textualmente (INV-09).
2. **Cobertura verificable.** Métrica: el 100 % de unidades `must-keep` del ledger alcanza estado terminal antes de cerrar (INV-08). El reporte del ledger responde "¿dónde quedó la sección 4.3.2?" en una consulta.
3. **Trazabilidad bidireccional.** Métrica: cada nodo fáctico del IR tiene `source_ref` resoluble al SDM; cada bloque del SDM tiene unidad asociada en al menos una nota.
4. **Portabilidad entre destinos.** Métrica: el validador cross-target (F63) reporta cero unidades ausentes en cualquier destino; las diferencias entre destinos son degradaciones declaradas (F53), nunca contenido eliminado (INV-07).

## §5 · Quickstart

¿Tienes prisa? Estos 3 prompts disparan la skill y producen notas útiles. La lista completa está en [`PROMPTS.md`](PROMPTS.md).

**Documentación de producto:**
```
Tengo la página de la documentación de PostgreSQL 16 sobre el comando SELECT.
Quiero una nota api-reference con la firma completa, los parámetros
documentados y los ejemplos canónicos. Salida a Obsidian y Notion.
```

**Libro técnico (con pedagogía):**
```
Tengo el capítulo de muestra de "Database Internals" sobre árboles B.
Quiero una nota concept con intuición inicial, analogía, ejemplo,
comparación con LSM-trees y trampas explícitas. Salida a Obsidian.
```

**PDF escaneado (modo degradado):**
```
Tengo un escaneo hostil de un libro técnico antiguo (Internet Archive):
escaneo torcido, ruido de fondo, OCR degradado. Si la confianza media
queda bajo 0.70, marca las regiones dudosas como low_confidence y NO
inventes contenido. Salida a Obsidian.
```

## §6 · Documentación del proyecto

| Si quieres… | Lee |
|---|---|
| Instalar la skill | [`INSTALL.md`](INSTALL.md) (macOS, Ubuntu, Fedora, Windows) |
| Ver prompts de ejemplo | [`PROMPTS.md`](PROMPTS.md) (12 prompts copy-paste) |
| Añadir un tipo de nota | [`EXTEND.md`](EXTEND.md) (5 pasos) |
| Entender qué es la skill | [`docs/product-manifesto.md`](docs/product-manifesto.md) |
| Anatomía y divulgación progresiva | [`docs/skill-anatomy.md`](docs/skill-anatomy.md) |
| Estructura del repositorio | [`docs/repo-layout.md`](docs/repo-layout.md) |
| Estado del proyecto | [`ROADMAP.md`](ROADMAP.md) |
| Galería de fuentes | [`docs/galaxy.md`](docs/galaxy.md) |
| Spec de OCR | `skill/notemartin-study-notes/references/01-ingest/ocr-engines.md` |
| Catálogo de scripts | `skill/notemartin-study-notes/scripts/README.md` (F117) |
| Suite de evals | [`evals/suite/`](evals/suite/) (F118) |
| Regresión y varianza | [`evals/regression/`](evals/regression/) (F119) |
| Ejemplos end-to-end | [`examples/`](examples/) (F120) |
| Proceso de release | [`docs/release.md`](docs/release.md) (F119, paso de empaquetado en F122, paso de versionado en F123) |
| Empaquetar la skill | `scripts/build_skill.py`, `scripts/smoke_test.py` (F122) — produce `dist/<tag>.skill` |
| Versionado y CHANGELOG | [`VERSION`](VERSION) (1 línea) + [`CHANGELOG.md`](CHANGELOG.md) + [`VERSIONING.md`](VERSIONING.md) + [`COMPATIBILITY.md`](COMPATIBILITY.md) (F123) |
| Contribuir al proyecto | [`CONTRIBUTING.md`](CONTRIBUTING.md) + [`docs/external-ingest-contract.md`](docs/external-ingest-contract.md) + `scripts/check_pr.py` (F124) |
| ADRs | [`docs/adr/`](docs/adr/) |

## §7 · Estado del proyecto

> **v0.1.0** publicado el 2026-10-01 tras F125. 119/125 fases cerradas, 5 pendientes (F6 con 2 muestras del corpus + 3 opcionales), 1 con cierre parcial documentado (F6). Para el veredicto material, ver [`evals/final-verification/final-report.md`](evals/final-verification/final-report.md).Las fases cerradas más recientes (per [`ROADMAP.md`](ROADMAP.md)):

- **F118 — Suite de evals de la skill:** 6 casos YAML + runner + comparador.
- **F119 — Regresión y varianza:** set de 6 casos + medición de 5 métricas + gate de release con 4 condiciones.
- **F120 — Ejemplos end-to-end:** 4 ejemplos completos (PostgreSQL SELECT, Database Internals, Kubernetes Pod, Internet Archive scan) con SDM + ledger + IR + 5 renders + 5 capturas SVG + 4 reportes de calidad.
- **F121 — README, instalación y personalización:** este documento + `INSTALL.md` + `PROMPTS.md` + `EXTEND.md` + `docs/galaxy.md`.
- **F122 — Empaquetado e instalación:** `scripts/build_skill.py` (generador reproducible de `.skill` ZIP con manifest.json) + `scripts/smoke_test.py` (5 verificaciones: unpack + frontmatter + references resolubles + check_deps.py corre + tamaño ≤ 8 MB). Artefacto en `dist/notemartin-study-notes-0.1.0-dev.skill` (~1.2 MB comprimido).
- **F123 — Versionado y CHANGELOG:** `VERSION` (1 línea, source of truth) + `CHANGELOG.md` (formato Keep-a-Changelog 1.1 con `### Closed: F1, F2, ...`) + `VERSIONING.md` (SemVer 2.0.0 + criterios MAJOR/MINOR/PATCH) + `COMPATIBILITY.md` (matriz por artefacto) + `scripts/check_version.py` (5 verificaciones + `--propose-bump` + `--compat-check`).
- **F124 — Contribución y mantenimiento:** `CONTRIBUTING.md` (estilo de referencias + triada regla→motivación→prueba + checklist de PR) + `docs/external-ingest-contract.md` (contrato tool-independent para conversores externos) + `scripts/check_pr.py` (gate soft con 10 items verificables, 4 hard FAIL + 6 soft WARN) + `agent.md` (contrato del agente desarrollador) + `references/00-pipeline/contributing.md` (estilo de `references/`).
- **F125 — Verificación final:** `scripts/run_final_verification.py` (orquestador de 4 criterios + 6 modos CLI) + 7 artefactos en `evals/final-verification/`. Cierra el ciclo: `VERSION 0.1.0-dev → 0.1.0` con `## [0.1.0] — 2026-10-01` en CHANGELOG. Veredicto global PARTIAL (todos los criterios PASS; 2 fuentes pendientes por F6).

## §8 · Cómo contribuir

El proyecto sigue un roadmap de 125 fases (per [`ROADMAP.md`](ROADMAP.md)) con criterios verificables por fase. Para contribuir:

1. Lee [`docs/product-manifesto.md`](docs/product-manifesto.md) para entender qué **es** y qué **no es** la skill.
2. Lee [`ROADMAP.md`](ROADMAP.md) para ver qué fases están abiertas (marcadas `- [ ]`) y cuáles cerradas.
3. Para una fase concreta: lee el detalle y los criterios en `ROADMAP.md`, sigue el ciclo de `skills/AGENT.md` §9.
4. Para decisiones con consecuencias: abre un ADR en [`docs/adr/`](docs/adr/) antes de implementar.
5. Antes de un PR que toque la skill: ejecuta la suite de regresión (F119) y archiva evidencia de no-regresión.

Las fases restantes incluyen empaquetado (F122), versionado y CHANGELOG (F123), contribución y mantenimiento (F124), y casos de humo (F125). El roadmap completo está en [`ROADMAP.md`](ROADMAP.md).

---

**Versión:** el paquete `skill/notemartin-study-notes/` tiene su propio versionado (definido en F123). El repo del proyecto sigue el versionado de [`ROADMAP.md`](ROADMAP.md).

**Licencia:** ver `LICENSE` (a crear en F122 si no existe).
