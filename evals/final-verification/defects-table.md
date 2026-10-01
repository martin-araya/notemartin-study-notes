# Defects table — veredicto por cada defecto del diagnóstico inicial

> Documento normativo de F125. Mapea cada garantía de `docs/product-manifesto.md` §3 (Fidelidad / Cobertura / Trazabilidad / Portabilidad) a un veredicto concreto basado en los artefactos de la verificación final.

**Fecha:** 2026-10-01T01:54:48.155914+00:00

## Defectos del diagnóstico inicial (product-manifesto.md §3)

| # | Defecto | Métrica | Mecanismo | Veredicto |
|---|---|---|---|---|
| **D-FID** | Fidelidad: ninguna unidad fáctica inventada/redondeada/perdida | 100% must-keep terminal + 100% source_refs resolubles | F114 (fidelity-audit) + F15 (ledger) + F43 (completeness-audit) | **PASS** |
| **D-COB** | Cobertura: ninguna sección sin nota o descarte no documentado | respuesta única a "¿dónde quedó X?" + loss_rate = 0 | F43 + F38 + F15 | **PARTIAL** |
| **D-TRZ** | Trazabilidad: ida y vuelta bloque↔nota | todo nodo fáctico con source_ref + todo bloque usado con notas | F52 + F13 + F46 | **PASS** |
| **D-PRT** | Portabilidad: mismo Note IR, 7 destinos sin pérdida fáctica | F63 cross-target reporta 0 unidades ausentes | F63 + F53 + F54-F60 | **PASS** |

## Veredicto global

**PARTIAL**

## Resumen de los criterios del ROADMAP F125

| # | Criterio | Resultado |
|---|---|---|
| C1 | Oracle en 3 destinos ricos (quality gate) | **PASS** |
| C2 | PDF escaneado con código fiel | **PASS** |
| C3 | Tasa de pérdida = 0 en must-keep | **PASS** |
| C4 | SKILL.md < 500 líneas | **PASS** |

## Detalles por criterio

### C1: Oracle surrogate (`case-01-postgresql-select`)

- Validators: 3 ejecutados.
- Destinations: ['obsidian', 'notion_api', 'appflowy'].
- Caveats: [].

### C2: PDF escaneado (`case-13-internet-archive-scan-hostil`)

- Bloques OCR: 0.
- Bloques `low_confidence`: 0.
- Caveats: [].
- Muestra real del corpus 13: pendiente por F6.

### C3: Loss rate per source

- Avg loss rate: 0.0.
- Sources medidas: 12/14.
- Sources pending: 2/14.

### C4: SKILL.md stats

- Líneas: 311 (límite 500).
- Secciones: 9.
- Caveats: [].

## Cambios que reabren F125

- Cambiar los criterios del ROADMAP F125 (no son modificables sin reabrir la fase).
- Cambiar la métrica de cualquier defecto del diagnóstico inicial.
- Cambiar el límite de SKILL.md (INV-02).
