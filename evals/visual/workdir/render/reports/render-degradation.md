# Reporte de degradación — HTML/PDF

- **schema_version:** 1.0.0
- **target:** html_pdf
- **source_hash:** `0000000000000000000000000000000000000000000000000000000000000000`
- **generated_at:** 2026-09-27T19:32:25Z
- **pdf_status:** skipped: weasyprint not installed

## Resumen

| Métrica | Valor |
|---|---|
| Nodos IR totales | 0 |
| Degradaciones | 1 |
| Pérdida de contenido | 0 |
| Notas publicadas | 1 |
| PDF status | skipped: weasyprint not installed |

## Diferencias vs otros destinos

- **vs markdown (F58):** HTML permite callouts nativos (<aside>), table con rowspan/colspan nativos, backlinks via <aside>; pierde portabilidad de texto plano
- **vs obsidian (F54):** HTML self-contained; Obsidian usa wikilinks [[id]] y callout syntax [!type]
- **vs appflowy (F57):** HTML <aside class='callout-*'>; AppFlowy usa > [!type] en Markdown

## Degradaciones

### html_pdf / pdf-export

- **node_path:** `renderer/pdf`
- **node_type:** `pdf`
- **alternative:** PDF no generado (weasyprint no instalado). HTML producido como alternativa; usuario puede `pip install weasyprint` y re-renderizar, o usar browser print-to-PDF con la CSS @media print
- **evidence:** `python3 -c 'import weasyprint' → ImportError`
- **content_intact:** `True`

## Cobertura

- Nodos contabilizados: 1
- Nodos IR totales: 0
- content_loss: 0 (debe ser 0; RC-01)