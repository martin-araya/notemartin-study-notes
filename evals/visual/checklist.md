# `evals/visual/checklist.md` — Checklist para destinos externos (F77)

> Los 3 destinos externos (Obsidian nativo, Notion API, AppFlowy nativo) **no
> se pueden capturar localmente** — requieren un panel nativo o una API key.
> F77 documenta aquí exactamente qué inspeccionar visualmente cuando un operador
> humano abre la nota en cada destino.
>
> **Cómo usar:** para cada fila, abrir la nota en el destino × tema y verificar
> los items de la columna "Inspeccionar". Marcar el checkbox cuando se confirme
> que el item se ve correctamente. Si se detecta un defecto nuevo, registrarlo
> en `defects.md` con severidad y fase de arreglo.

## Tabla 6 entradas (2 notas × 3 destinos externos)

| # | Nota | Destino | Tema | Items a inspeccionar visualmente | Status |
|---|---|---|---|---|---|
| 1 | `probe.nm` | Obsidian | light | - Panel Properties muestra 5 universales (title, note-type, status, summary, reading-time-minutes) <br> - Callouts nativos con colores correctos (info, tip, warning, danger, example) <br> - Tabla con sticky thead + scroll horizontal <br> - Code fence con syntax highlight <br> - Diagrama Mermaid pre-renderizado en SVG/PNG | [ ] |
| 2 | `probe.nm` | Obsidian | dark | - Variables CSS resuelven correctamente (contraste WCAG AA) <br> - Bordes de callouts visibles sin saturación <br> - Tabla con thead sticky en dark theme <br> - Code con fondo oscuro legible | [ ] |
| 3 | `probe.nm` | Notion API | light | - `page.properties` con las 5 universales + properties-bearing <br> - `callout` block con `icon` + `color` correctos (F73 mapping) <br> - `rich_text` formateado (bold/italic/code) <br> - Tabla con `has_column_header` y `children` correctos | [ ] |
| 4 | `probe.nm` | Notion API | dark | - Icono del callout visible en dark mode (no se vuelve invisible) <br> - Color del callout coincide con F73 (yellow_background para warning) <br> - Texto del callout legible sobre fondo dark | [ ] |
| 5 | `probe.nm` | AppFlowy | light | - Properties panel con 5 universales <br> - Callout nativo con colores canónicos <br> - Tabla interactiva (sortable) <br> - Code con monospace font | [ ] |
| 6 | `probe.nm` | AppFlowy | dark | - Bordes de callout visibles <br> - Fondo de callout no demasiado oscuro (legible) <br> - Code con contraste suficiente | [ ] |
| 7 | `real-postgresql-arrays.md` | Obsidian | light | - **Tabla 10+ columnas** (la "Criterio" + "Array" + "Junction" table): scroll horizontal funciona, sticky thead se queda arriba <br> - 5 callouts de severidades distintas: info, warning, danger, example, tip <br> - Mermaid ERD se renderiza correctamente <br> - 6 anclas `{src:blk_xxxx}` visibles como footers <br> - `## Cabecera` con 5 campos (F75) <br> - Densidad visual: ≥ 1 anclaje cada 200 palabras (F76 R3) | [ ] |
| 8 | `real-postgresql-arrays.md` | Obsidian | dark | - Tabla 10+ cols en dark: contraste suficiente en celdas <br> - 5 callouts: borde visible en dark mode <br> - Mermaid: fondo del SVG visible (no transparente) | [ ] |
| 9 | `real-postgresql-arrays.md` | Notion API | light | - Tabla 10+ cols: ¿Notion API trunca a 100 cols? (límite duro) <br> - 5 callouts: icon y color únicos <br> - Mermaid: ¿se pre-renderiza o se inserta como imagen? (limitación API) <br> - Cabecera: ¿page.properties.summary aparece? | [ ] |
| 10 | `real-postgresql-arrays.md` | Notion API | dark | - Tabla 10+ cols: contraste dark <br> - 5 callouts: iconos dark mode <br> - Cabecera: page.properties dark mode | [ ] |
| 11 | `real-postgresql-arrays.md` | AppFlowy | light | - Tabla 10+ cols: scroll horizontal <br> - 5 callouts: colores <br> - Mermaid: renderiza o embed? <br> - Cabecera: properties panel | [ ] |
| 12 | `real-postgresql-arrays.md` | AppFlowy | dark | - Tabla 10+ cols: contraste <br> - 5 callouts: bordes <br> - Mermaid: contraste del SVG | [ ] |

## Cierre

Cuando los 12 checkboxes estén marcados (o marcados con `not-applicable` con
justificación), el operador actualiza `defects.md` con cualquier defecto nuevo
encontrado y archiva este checklist con la fecha y el nombre del operador.
