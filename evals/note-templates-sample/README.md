# `evals/note-templates-sample/` — Fase 75

Verificador de la Fase 75 (plantillas visuales por tipo). Cubre los 3 criterios del ROADMAP §1467-1470 con 5 sub-criterios:

| Criterio | Qué verifica | Método |
|---|---|---|
| **C1** | `note-templates.md` §6 contiene 15 subsecciones numeradas (§6.1 a §6.15) y los 15 nombres canónicos de tipo | regex sobre el doc |
| **C2** | Apertura común (§3) y cierre común (§4) documentados: frontmatter → `## Cabecera` → `## TL;DR`; `## Backlinks` → `## Queries` → `## Ver también` | in-process: `## Cabecera`, `## TL;DR`, `## Backlinks`, `## Queries`, `## Ver también` presentes en el doc |
| **C3** | INV-P5 con 5 universales; `FRONTMATTER_ORDER` 20 entries; `_emitter.py` con posiciones 4-5 correctas; `validate_frontmatter` funcional | in-process: imports de `_emitter` + `validate_ir`; assert len(FRONTMATTER_ORDER) == 20; assert order[3] == "summary"; assert order[4] == "reading-time-minutes"; assert validate_frontmatter detecta missing universals en published |
| **C4** | Los 7 renderers (obsidian, notion_api, notion_md, appflowy, markdown, html_pdf, flashcards) importan `emit_cabecera`; cada destino produce output no-vacío | in-process: regex sobre los 7 archivos + invocación directa de `emit_cabecera` con frontmatter de prueba |
| **C5** | `note-templates.md` ≤ 500 líneas | `wc -l` |

## Uso

```bash
# Generar fixtures y ejecutar
python3 evals/note-templates-sample/run_eval.py

# Forzar regeneración de fixtures
python3 evals/note-templates-sample/run_eval.py --regen
```

## Salida esperada

```
============================================================
Fase 75 — Plantillas visuales por tipo
============================================================
  PASS  C1-doc-15-types (15 subsecciones §6.1-§6.15; 15 tipos canónicos)
  PASS  C2-common-pattern (apertura y cierre comunes §3+§4)
  PASS  C3-5-universals (FRONTMATTER_ORDER=20, posiciones 4-5 correctas, UNIVERSAL_PROPERTIES=5, validate_frontmatter funciona)
  PASS  C4-renderers (7/7 importan emit_cabecera; 7/7 producen output no-vacío)
  PASS  C5-doc-size (433 líneas ≤ 500)
============================================================
PASS 5/5
```

Exit code `0` si todos pasan; `1` si alguno falla.

## Archivos

- `build_fixtures.py` — genera `fixtures/sample-ir.json` (IR sintético con frontmatter completo de las 5 universales) y `fixtures/cabecera-snapshot.json` (dump de los 7 outputs de `emit_cabecera`).
- `run_eval.py` — los 5 sub-criterios documentados arriba.

## Wirings

- Cierra los 3 criterios de `ROADMAP.md` §1467-1470 para Fase 75.
- El criterio C3 (5 universales) es el más estricto: garantiza que las 2 propiedades nuevas (`summary`, `reading-time-minutes`) están añadidas al frontmatter canónico (FRONTMATTER_ORDER tiene 20 entries en lugar de 18) y que el validador las exige en `status: published`.
- El criterio C4 (7 renderers) garantiza que el helper `_header.py` está integrado en todos los destinos (sin él, las 5 propiedades nuevas no se renderizarían).
