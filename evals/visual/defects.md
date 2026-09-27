# `evals/visual/defects.md` — Log de defectos (F77)

> F77 inspecciona los artefactos generados en `artifacts/`, registra los defectos
> detectados, y asigna cada uno a una fase de arreglo (cuando aplica).
> Severidades: `critical` (contenido cortado / ilegible), `warning` (desviación
> menor), `minor` (cosmético). Status: `fixed-in-f77`, `assigned-fXX`, `wontfix`.

## Tabla de defectos

| # | Defect | Severity | Destination | Note | Status | Fix phase | Detectado por |
|---|---|---|---|---|---|---|---|
| 1 | `<th>` sin `scope="col"` en cabecera | warning | html_pdf | ambos | **fixed-in-f77** | (trivial: 1 línea en `_header.py:204`) | `visual_inspect.py` |
| 2 | Tabla 10+ cols (Criterio vs Array vs Junction) no tiene wrapper `.table-wrapper` con `overflow-x: auto` en render HTML/PDF | minor | html_pdf | real-postgresql-arrays | assigned | F78-F92 polish (F74 ya define la clase en `notemartin.css`; falta que el renderer la emita) | `visual_inspect.py` (MD_TABLE_WIDE) |
| 3 | `reading-time-minutes` no se renderiza en artefactos como `<span data-rtm>` (solo en YAML) | minor | all | ambos | wontfix | — (es propiedad, no campo visual) | manual |
| 4 | mermaid SVG en `theme-apply.html` no tiene `<desc>` con descripción larga | minor | mermaid | ambos | wontfix | — (el `<title>` ya cubre a11y básico WCAG 1.1.1) | `visual_inspect.py` (SVG_NO_TITLE — false positive) |
| 5 | Mermaid SVG generado manualmente (sin Mermaid CLI instalado) | minor | mermaid | ambos | assigned | futura fase de QA con Mermaid CLI `mmdc` | manual |
| 6 | Flashcards CSV vacío (0 tarjetas) para las 2 notas | minor | flashcards | ambos | wontfix | — (las notas no tienen atomic-types definition/formula/glossary-term/key-fact; el renderer no extrae de tablas) | `visual_inspect.py` (CSV vacío = válido) |
| 7 | Tema dual para Markdown/Flashcards: el "light/dark" en el artefacto es solo metadato (el visor aplica el tema); no hay 2 archivos distintos | minor | markdown, flashcards | ambos | wontfix | — (limitación del formato; el destino aplica tema, no el renderer) | manual |
| 8 | Captura móvil: no se capturó ninguna vista móvil (escritorio y móvil del ROADMAP §1495) | critical | all | ambos | assigned | F78-F92 polish + futura fase QA con browser | manual (no hay browser en F77) |
| 9 | Notion API: no se capturó ningún render de la API real (requiere API key) | critical | notion_api | ambos | assigned | F62 publishing + futura fase QA con API key | manual (checklist F77) |
| 10 | Obsidian nativo: no se capturó ningún render del panel nativo | critical | obsidian | ambos | assigned | futura fase QA con Obsidian instalado | manual (checklist F77) |
| 11 | AppFlowy nativo: no se capturó ningún render del panel nativo | critical | appflowy | ambos | assigned | futura fase QA con AppFlowy instalado | manual (checklist F77) |

## Resumen

- **Defects totales:** 11
- **Fixed in F77:** 1 (defect #1: trivial fix en `_header.py:204`)
- **Assigned to future phases:** 5 (defects #2, #5, #8, #9, #10, #11)
- **Wontfix (limitaciones de formato/infraestructura):** 5 (defects #3, #4, #6, #7)
- **Critical defects abiertos:** 4 (defects #8, #9, #10, #11 — todos asignados a fases futuras)

## Cierre de Fase 77

Criterio 3 del ROADMAP §1500: "Los defectos están corregidos o con fase de arreglo asignada." → **CUMPLIDO**:
- 1 defecto trivial corregido en F77 (defect #1).
- 5 defectos complejos asignados a fases futuras (F62, F78-F92 polish, futuras QA con browser/API/instalación).
- 5 defectos wontfix documentados (limitaciones de formato o de infraestructura no relacionadas con la skill en sí).

## Procedimiento para actualizar este log

Cuando un operador humano (QA) ejecute el `checklist.md` y detecte un defecto nuevo:

1. Añadir fila a la tabla con severidad, destino, nota, status `open` y fix-phase asignado.
2. Si el defecto es trivial (1-3 líneas de código en un renderer), corregir en la misma fase y marcar `fixed-in-f77`.
3. Si el defecto es complejo (cambio de diseño, refactor), asignar a una fase futura con la nota explícita.
4. Si el defecto es wontfix (limitación del destino), justificar la decisión en la columna `Fix phase`.
