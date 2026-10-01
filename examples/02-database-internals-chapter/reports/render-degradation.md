# Reporte de degradación — HTML/PDF

- **schema_version:** 1.0.0
- **target:** html_pdf
- **source_hash:** `0000000000000000000000000000000000000000000000000000000000000000`
- **generated_at:** 2026-09-30T23:21:28Z
- **pdf_status:** skipped: --no-pdf flag

## Resumen

| Métrica | Valor |
|---|---|
| Nodos IR totales | 0 |
| Degradaciones | 0 |
| Pérdida de contenido | 0 |
| Notas publicadas | 1 |
| PDF status | skipped: --no-pdf flag |

## Diferencias vs otros destinos

- **vs markdown (F58):** HTML permite callouts nativos (<aside>), table con rowspan/colspan nativos, backlinks via <aside>; pierde portabilidad de texto plano
- **vs obsidian (F54):** HTML self-contained; Obsidian usa wikilinks [[id]] y callout syntax [!type]
- **vs appflowy (F57):** HTML <aside class='callout-*'>; AppFlowy usa > [!type] en Markdown

> Cero degradaciones en este destino. Esta sección se mantiene siempre para confirmar cobertura.

## Cobertura

- Nodos contabilizados: 0
- Nodos IR totales: 0
- content_loss: 0 (debe ser 0; RC-01)