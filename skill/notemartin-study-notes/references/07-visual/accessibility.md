# `references/07-visual/accessibility.md` — Accesibilidad visual

> **Propósito:** definir las reglas de accesibilidad visual para figuras y diagramas de la skill. Cumple WCAG 2.1 nivel AA como mínimo, AAA donde sea factible. Cubre contraste, tamaño mínimo, "nunca color como único portador", alt text obligatorio, roles ARIA y semántica SVG, y navegación por teclado.
>
> **Cuándo cargar:** el agente o revisor visual crea o audita una figura/diagrama, o necesita validar que cumple WCAG AA antes de publicar una nota.

---

## §1 · Propósito y alcance

**Cumple los 3 niveles WCAG 2.1:**

- **A** (mínimo, obligatorio): perceptible, operable, comprensible, robusto.
- **AA** (estándar legal): contraste 4.5:1 texto normal, 3:1 texto grande, 3:1 UI.
- **AAA** (deseable): contraste 7:1 texto normal, 4.5:1 texto grande.

**Niveles aplicados en este archivo:**

- Mínimo obligatorio: **AA**.
- Deseable donde factible: **AAA** para texto principal.
- Compromise: la paleta Okabe-Ito (F70) es **colorblind-safe** (ΔE≥20) pero no siempre cumple AA para texto pequeño. Ver §8.

**Fuera de alcance:**

- Reconstrucción de diagramas → `reconstruction.md` (F71).
- Sintaxis de directivas visuales → `notemark.md` (F12 §10).
- Tokens de color → `tokens.md` (F72).

---

## §2 · Contraste

### §2.1 · Ratios WCAG 2.1

| Tipo de contenido | AA (mínimo) | AAA (deseable) |
|---|---|---|
| Texto normal (<18px o <14px bold) | 4.5:1 | 7:1 |
| Texto grande (≥18px o ≥14px bold) | 3:1 | 4.5:1 |
| Iconos UI (≥24px) | 3:1 | 4.5:1 |
| Componentes UI (botones, inputs) | 3:1 | 4.5:1 |
| Texto decorativo (sin significado) | exento | exento |
| Logo o nombre de marca | exento | exento |

### §2.2 · Verificación de contraste

Fórmula simplificada (sRGB → luminancia relativa):

```
L = 0.2126 * R + 0.7152 * G + 0.0722 * B  (con cada canal linealizado)
ratio = (L1 + 0.05) / (L2 + 0.05)  (donde L1 > L2)
```

Para calcular programáticamente, ver §8 (ejemplo con Okabe-Ito).

### §2.3 · Reglas operativas

1. **Texto sobre fondo claro** (white #FFFFFF): usar colores con ratio ≥ 4.5:1.
2. **Texto sobre fondo oscuro** (black #000000 o dark theme #1E1E1E): usar colores con ratio ≥ 4.5:1.
3. **Líneas de ejes y gridlines**: ratio ≥ 3:1 (cumple UI-AA).
4. **Series de datos** (rellenos grandes, ≥18px efectivo): ratio ≥ 3:1 contra fondo; **pero nunca como único portador** (ver §4).

---

## §3 · Tamaño mínimo de texto

### §3.1 · Tamaños mínimos

| Elemento | Tamaño mínimo | Recomendado |
|---|---|---|
| Texto normal (cuerpo, etiquetas) | 14px | 16px |
| Título de figura | 16px | 20px |
| Subtítulo | 12px | 14px |
| Etiquetas de ejes | 10px | 12px |
| Texto en tabla Markdown | 14px | 16px |
| Texto en admonitions (`:::note` etc.) | 14px | 16px |
| Texto en `:::collapsible` plegado | 14px | 14px |

### §3.2 · En SVG

El atributo `font-size` del SVG debe respetar los tamaños anteriores. El script `make_figure.py` (F70) usa defaults:

- Título: 16px (cumple §3.1).
- Etiquetas de ejes: 10px (mínimo §3.1; **no usar < 10px**).
- Etiquetas de datos: 9-10px (solo OK para datos puntuales, no para texto corrido).

### §3.3 · Escalado por destino

| Destino | Comportamiento |
|---|---|
| Obsidian | Respeta `font-size` del SVG. |
| Notion import | Respeta `font-size`. **No escala** el SVG. |
| HTML/PDF | Respeta `font-size`. Escala el SVG con CSS del theme. |
| Markdown | SVG embebido como `<img>`; escala según CSS del theme. |

Si un destino escala el SVG, el tamaño efectivo puede reducirse. Asegurar que `font-size` mínimo sea **16px** (no 14px) si el destino puede reducir 25%.

---

## §4 · Nunca color como único portador

Cumple el **criterio 3 de F71** y **WCAG 2.1 SC 1.4.1** (Use of Color).

### §4.1 · Regla

**Nunca transmitir significado solo por color.** Si un color codifica información (e.g., "rojo = error"), añadir un **segundo canal**: forma, etiqueta, patrón, estilo de línea, o icono.

### §4.2 · Tabla cerrada de 12 patrones

| # | Patrón | Cómo añadir segundo canal |
|---|---|---|
| 1 | `flowchart` con decisiones | Forma del nodo (`{}` rombo) + texto "sí/no" en aristas (`-->|sí|` / `-->|no|`) |
| 2 | `line` con múltiples series | Estilo de línea (sólida / punteada / discontinua) + marcador (círculo / triángulo / cuadrado) |
| 3 | `heatmap` | Etiqueta numérica en cada celda (no solo color) |
| 4 | `confusion_matrix` | Texto en cada celda con valor numérico |
| 5 | `distribution` (histograma) | Etiqueta de bin en X (`0-10`, `10-20`, etc.) |
| 6 | `before/after` (dumbbell) | Forma del punto + texto "antes/después" en la leyenda |
| 7 | `gantt` | Estilo de barra (sólida vs discontinua) + texto de fase |
| 8 | `stateDiagram` | Etiqueta de estado explícita + estilo de flecha (`-->` vs `-->|event|`) |
| 9 | `bar` con series | Texto de valor sobre la barra (no solo color) |
| 10 | `classDiagram` | Visibilidad (`+`/`-`/`#`) + tipo de relación (línea continua/discontinua según herencia) |
| 11 | `pie` | Etiqueta de categoría (no solo color de sector) |
| 12 | `gitGraph` | Etiqueta de commit + rama visible |

### §4.3 · Casos donde color es el único portador (prohibidos)

- **Heatmap sin etiquetas numéricas**: las celdas claras vs oscuras no se distinguen sin color.
- **Línea roja para indicar error** sin etiqueta textual "ERROR".
- **Estados coloreados** sin texto del nombre del estado.

Para heatmap: añadir `<text>` con el valor numérico en cada celda (ver F70 §3.3 `build_heatmap`).

---

## §5 · Alt text obligatorio

### §5.1 · Regla

Toda figura/diagrama debe tener un atributo `alt` no vacío. Cumple `R-D-04` de F65 y el criterio de accesibilidad WCAG 2.1 SC 1.1.1 (Non-text Content).

### §5.2 · Sintaxis

```notemark
:::diagram src="blk_xxx" alt="Descripción textual concisa del diagrama"
```mermaid
...
```
:::
```

```notemark
:::figure src="blk_xxx" alt="Descripción de la imagen (incluye lo esencial)"
:::
```

### §5.3 · Longitud y formato

- **Longitud:** 1-280 caracteres (límite de tweet; ajustarse a ~150 para legibilidad).
- **Primera frase:** completa (no cortar a media frase).
- **Contenido:** qué muestra la figura, no "imagen de..." o "figura con..." (ya implícito).
- **Evitar:** redundancia con el título de la figura.
- **Incluir:** el tipo de diagrama (bar/line/heatmap), el dominio (PostgreSQL/MySQL), el eje Y (latencia ms), el dato clave si aplica.

### §5.4 · Ejemplos

| Tipo | Alt text correcto | Alt text incorrecto |
|---|---|---|
| Bar | "Gráfico de barras: PostgreSQL 12ms vs MySQL 45ms en SELECT 1k." | "Gráfico de barras comparativo" |
| Heatmap | "Heatmap de correlación: variables A-B = 0.5, B-C = 0.7." | "Mapa de calor" |
| Line | "Línea temporal: latencia API baja de 100ms (Ene) a 60ms (Mar)." | "Gráfico de líneas" |
| Conf. matrix | "Matriz de confusión 2x2: TP=80, FP=5, FN=10, TN=90." | "Matriz de confusión" |

### §5.5 · Para diagramas derivados (F71)

El `alt` debe indicar explícitamente que es una reconstrucción:

> `"Reconstrucción en Mermaid de la arquitectura PostgreSQL del SDM p. 42 (derivado)"`

---

## §6 · Roles ARIA y semántica SVG

### §6.1 · SVG accesible

El SVG debe tener `role="img"` y `aria-label` o `aria-labelledby`:

```xml
<svg xmlns="..." role="img" aria-labelledby="title desc" ...>
  <title id="title">Diagrama de arquitectura PostgreSQL</title>
  <desc id="desc">5 capas con flujo bidireccional: Cliente, Frontend, Backend, Acceso, Disco.</desc>
  ...
</svg>
```

### §6.2 · Plantillas ARIA listas para copiar

#### §6.2.1 · Mermaid SVG export (recomendado para HTML/PDF)

```xml
<svg xmlns="http://www.w3.org/2000/svg" role="img"
     aria-labelledby="diag-title diag-desc"
     width="800" height="500" viewBox="0 0 800 500">
  <title id="diag-title">{title}</title>
  <desc id="diag-desc">{alt_text}</desc>
  <!-- contenido del diagrama -->
</svg>
```

#### §6.2.2 · HTML inline

```html
<figure role="figure" aria-labelledby="fig-caption">
  <img src="diagram.svg" alt="{alt_text}" />
  <figcaption id="fig-caption">{title}</figcaption>
</figure>
```

#### §6.2.3 · Obsidian embed

```markdown
![{alt_text}](diagram.svg){#fig}
```

Obsidian genera automáticamente `<img alt="{alt_text}">` con el texto alt.

---

## §7 · Navegación por teclado

### §7.1 · Regla

Toda figura interactiva (con zoom, click, hover) debe ser navegable por teclado. Las figuras estáticas (SVG simple, Mermaid render) **no requieren** navegación por teclado — son imágenes.

### §7.2 · Figuras interactivas

Si una figura tiene:

- **Zoom**: tabindex="0", keyboard handler para `+`/`-`/`0`.
- **Click en nodo**: cada nodo enfocable tiene `tabindex="0"` y `role="button"`, con handler de teclado (Enter/Space).
- **Hover con tooltip**: tooltip debe aparecer también en `focus`, no solo en `hover`.

### §7.3 · Diagramas Mermaid (estáticos)

Los diagramas Mermaid renderizan como SVG sin interactividad nativa. **No requieren** navegación por teclado. Sin embargo:

- En Mermaid `flowchart`, los nodos pueden tener `click` definido (F65 lo desaconseja por F66 §R-MP-06).
- Si se necesita interactividad, considerar una versión HTML custom con ARIA (ver §6.2.2).

---

## §8 · Contraste de la paleta Okabe-Ito (F70)

### §8.1 · Ratios de contraste

| Color Okabe-Ito | Hex | Ratio vs `#FFFFFF` | Ratio vs `#000000` | AA texto | AA UI |
|---|---|---|---|---|---|
| Orange | `#E69F00` | 2.30 | 9.13 | ❌ | ❌ |
| Sky Blue | `#56B4E9` | 2.01 | 10.41 | ❌ | ❌ |
| Bluish Green | `#009E73` | 4.78 | 4.39 | ✅ | ✅ |
| Yellow | `#F0E442` | 1.84 | 11.40 | ❌ | ❌ |
| Blue | `#0072B2` | 5.66 | 3.71 | ✅ | ✅ |
| Vermillion | `#D55E00` | 3.83 | 5.49 | ❌ (texto) | ✅ |
| Reddish Purple | `#CC79A7` | 3.41 | 6.16 | ❌ | ✅ |
| Black | `#000000` | 21.00 | 1.00 | ✅ | ✅ |

### §8.2 · Reglas operativas

1. **Para texto**: usar solo `Bluish Green` o `Blue` (los únicos con ratio ≥ 4.5:1 contra ambos fondos).
2. **Para rellenos grandes** (≥18px efectivo, iconos ≥3px): cualquier color Okabe-Ito cumple ratio 3:1 UI-AA.
3. **Combinaciones seguras** (series vs fondo):
   - Cualquier Okabe-Ito sobre `#FFFFFF` o `#1E1E1E` cumple 3:1 para rellenos.
   - Para texto pequeño, usar solo Bluish Green o Blue.
4. **Nunca como único portador** (§4): incluso si el ratio cumple, el color por sí solo no basta; añadir forma/etiqueta/estilo.

### §8.3 · Verificación programática

El script `make_figure.py` (F70) puede verificar ratios con la función `verify_palette_colorblind_safe()` (que verifica ΔE) extendida con `verify_contrast_against_backgrounds()`.

---

## §9 · Tabla de auto-verificación por figura

10 puntos de verificación antes de publicar una figura:

| # | Verificación | Criterio | ✓/✗ |
|---|---|---|---|
| 1 | `alt` no vacío, ≤ 280 chars | §5.3 | ☐ |
| 2 | `alt` describe el contenido, no "imagen de..." | §5.4 | ☐ |
| 3 | SVG tiene `role="img"` + `<title>` + `<desc>` | §6 | ☐ |
| 4 | Contraste texto ≥ 4.5:1 (texto normal) | §2 | ☐ |
| 5 | Contraste series (rellenos) ≥ 3:1 contra fondo | §8 | ☐ |
| 6 | Tamaño de fuente mínimo 10px (etiquetas), 14px (texto) | §3 | ☐ |
| 7 | Color no es único portador (forma/etiqueta/estilo añadido) | §4 | ☐ |
| 8 | Toda serie tiene `source_refs` (F70 INV-04) | F70 §6 | ☐ |
| 9 | Si es reconstrucción, marcada `derived="true"` + imagen original enlazada | F71 §5 | ☐ |
| 10 | Si tiene interactividad, navegable por teclado | §7 | ☐ |

Si alguna falla, corregir antes de publicar.

---

## §10 · Wirings

- **F65** `diagram-catalog.md`: provee los tipos de diagrama (Mermaid) y la regla R-D-04 (alt text obligatorio).
- **F66** `mermaid-portable.md`: provee las reglas de portabilidad que afectan accesibilidad (acentos, contraste implícito).
- **F67** `scripts/validate/mermaid.py`: regla L-06 (alt ausente) implementada; ampliar para detectar "derivado" en alt sin `derived="true"`.
- **F69** `monospace-diagrams.md`: monoespaciado no requiere color (cumple §4 trivialmente); pero tamaño mínimo aplica (§3).
- **F70** `scripts/render/make_figure.py`: paleta Okabe-Ito + `verify_palette_colorblind_safe()` (ver §8); alt text auto-generado.
- **F72** `tokens.md` (F72): provee la paleta canónica con ratios WCAG pre-validados (18/18 AA en ambos temas, 14/18 AAA; `assets/tokens.json` + `scripts/util/tokens.py` + `scripts/validate/contrast_check.py`).

---

**Verificación al cierre de la fase:**

- `wc -l accessibility.md` ≤ 700 líneas.
- §2 tabla WCAG con ratios AA y AAA.
- §3 tamaños mínimos (14/16/20px) para cada elemento.
- §4 tabla cerrada de 12 patrones "nunca color".
- §5 reglas de alt text con ejemplos correcto/incorrecto.
- §6 plantillas ARIA (SVG, HTML, Obsidian).
- §8 ratios Okabe-Ito documentados.
- §9 checklist de 10 puntos.
