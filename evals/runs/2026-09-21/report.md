# Reporte del dry-run — Fase 10

Fecha: 2026-09-21
Source: `skill/notemartin-study-notes/SKILL.md`

## Description medida

> Convierte documentación técnica, manuales de producto, libros técnicos (incluidos PDFs escaneados), referencias de API y apuntes sueltos en notas de estudio completas, trazables y publicables en Obsidian, Notion, AppFlowy, Markdown estándar, HTML/PDF y sistemas de repaso espaciado. Mantiene fidelidad al original, cobertura verificable por ledger y formato intermedio NoteMark para que las notas viajen entre destinos sin reescritura.

Palabras: 58 / 100.

## Métricas

- TPR train     = 1.0000  (umbral ≥ 0.9)  → PASS
- TPR holdout   = 1.0000  (umbral ≥ 0.9)  → PASS
- FPR train     = 0.0000  (umbral ≤ 0.1)  → PASS
- FPR holdout   = 0.0000  (umbral ≤ 0.1)  → PASS

## Conteos

- positives_train: 18
- positives_holdout: 7
- negatives_train: 10
- negatives_holdout: 5

## Fallos por categoría

- (ninguno)

## Detalle por consulta

| ID | Categoría | Idioma | Split | Esperado | Predicho | Match |
|---|---|---|---|---|---|---|
| P-001 | documentacion-tecnica | es | train | dispara | dispara | ✓ |
| P-002 | documentacion-tecnica | es | train | dispara | dispara | ✓ |
| P-003 | documentacion-tecnica | en | train | dispara | dispara | ✓ |
| P-004 | documentacion-tecnica | en | holdout | dispara | dispara | ✓ |
| P-005 | capitulo-libro | es | train | dispara | dispara | ✓ |
| P-006 | capitulo-libro | es | train | dispara | dispara | ✓ |
| P-007 | capitulo-libro | en | train | dispara | dispara | ✓ |
| P-008 | capitulo-libro | en | holdout | dispara | dispara | ✓ |
| P-009 | pdf-escaneado | es | train | dispara | dispara | ✓ |
| P-010 | pdf-escaneado | es | train | dispara | dispara | ✓ |
| P-011 | pdf-escaneado | en | train | dispara | dispara | ✓ |
| P-012 | pdf-escaneado | en | holdout | dispara | dispara | ✓ |
| P-013 | api-reference | es | train | dispara | dispara | ✓ |
| P-014 | api-reference | es | train | dispara | dispara | ✓ |
| P-015 | api-reference | en | train | dispara | dispara | ✓ |
| P-016 | api-reference | en | holdout | dispara | dispara | ✓ |
| P-017 | destino-explicito | es | train | dispara | dispara | ✓ |
| P-018 | destino-explicito | es | train | dispara | dispara | ✓ |
| P-019 | destino-explicito | es | train | dispara | dispara | ✓ |
| P-020 | destino-explicito | en | holdout | dispara | dispara | ✓ |
| P-021 | destino-explicito | en | holdout | dispara | dispara | ✓ |
| P-022 | estudio-metas | es | train | dispara | dispara | ✓ |
| P-023 | estudio-metas | es | train | dispara | dispara | ✓ |
| P-024 | estudio-metas | en | train | dispara | dispara | ✓ |
| P-025 | estudio-metas | en | holdout | dispara | dispara | ✓ |
| N-001 | codigo-puro | es | train | no-dispara | no-dispara | ✓ |
| N-002 | codigo-puro | es | train | no-dispara | no-dispara | ✓ |
| N-003 | codigo-puro | es | train | no-dispara | no-dispara | ✓ |
| N-004 | codigo-puro | en | train | no-dispara | no-dispara | ✓ |
| N-005 | codigo-puro | en | holdout | no-dispara | no-dispara | ✓ |
| N-006 | codigo-puro | en | holdout | no-dispara | no-dispara | ✓ |
| N-007 | resumen-libre | es | train | no-dispara | no-dispara | ✓ |
| N-008 | resumen-libre | es | train | no-dispara | no-dispara | ✓ |
| N-009 | resumen-libre | en | train | no-dispara | no-dispara | ✓ |
| N-010 | resumen-libre | en | holdout | no-dispara | no-dispara | ✓ |
| N-011 | traduccion | es | train | no-dispara | no-dispara | ✓ |
| N-012 | traduccion | en | train | no-dispara | no-dispara | ✓ |
| N-013 | traduccion | en | holdout | no-dispara | no-dispara | ✓ |
| N-014 | ensayo-otro | es | train | no-dispara | no-dispara | ✓ |
| N-015 | ensayo-otro | en | holdout | no-dispara | no-dispara | ✓ |

## Decisión

**LOCK.** Los cuatro umbrales pasan. La `description` queda congelada como 'description final' sin más iteraciones.
