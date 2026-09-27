# `references/07-visual/tokens.md` — Design tokens

> **Propósito:** documentar el catálogo de design tokens canónicos de la skill, la regla `INV-14` operativa, el procedimiento de verificación de contraste WCAG 2.1 y el mapeo intención → severidad admonition. La fuente única de valores es `assets/tokens.json`; este doc **no** lista los hex (evita duplicación desincronizada). Apunta a `tokens.json` como source of truth.
>
> **Cuándo cargar:** antes de cualquier CSS, antes de escribir una figura (`make_figure.py`), antes de mapear severidades de admonition a estilo por destino, y en cualquier revisión que toque color.

---

## §1 · Propósito y alcance

`assets/tokens.json` es la **fuente única** de color, tipografía, espaciado, radios y pesos para toda la skill. Aplica `INV-14`: ningún archivo del proyecto contiene un color literal fuera de `tokens.json`. Esto cubre:
- Notas producidas en NoteMark.
- Plantillas visuales (F75).
- Snippet CSS para Obsidian (`assets/notemartin.css` + `assets/css-tokens.generated.css` auto-generado; F74 ✅).
- Renderers (`obsidian.py`, `notion_api.py`, `notion_md.py`, `appflowy.py`, `markdown.py`, `html_pdf.py`, `flashcards.py`).
- Figuras de datos (`scripts/render/make_figure.py`, F70).
- CSS de la plantilla HTML/PDF (F59, migración pendiente para una fase futura; ver §10).

**Cumple WCAG 2.1 AA** (ratio mínimo 4.5:1 entre `fgOnBg` y `bg`) en ambos temas (light y dark) para los 9 tokens semánticos; AAA (7:1) donde es factible.

**Fuera de alcance:**

- Accesibilidad visual general → `accessibility.md` (F71).
- Reconstrucción de diagramas → `reconstruction.md` (F71).
- Mapeo intención → estilo por destino → `style-mapping.md` (F73).
- Snippet CSS para Obsidian → `assets/notemartin.css` (F74).

**Estructura de `tokens.json`** (5 categorías top-level + `_neutral`):

| Categoría | Contenido | Tokens |
|---|---|---|
| `typography` | Familias, escala, pesos, lineHeights | `families.{serif,sans,mono}`, `scale.{xs,sm,base,md,lg,xl,2xl,3xl}`, `weights.{regular,medium,semibold,bold}`, `lineHeights.{tight,snug,normal,loose}` |
| `spacing` | Escala modular (rem) + mapeo por `density` | `scale.0..8`, `density.{compact,normal,spacious}` |
| `radii` | Radios predefinidos (px) | `none, sm, md, lg, xl, pill` |
| `_neutral` | Grises base (text, surface, code, quote) | 9 tokens × {light, dark} |
| `semantic` | Paleta semántica con 9 intenciones | 9 tokens × {light, dark} × {fg, bg, border, fgOnBg, borderContrast} |
| `series` | Paleta Okabe-Ito (F70) + ejes neutros | 8 colores Okabe-Ito + `axisLight` + `axisDark` |

Cada token semántico expone **5 valores por modo** para evitar que el renderer calcule contraste en runtime:

| Clave | Rol | Ratio WCAG garantizado |
|---|---|---|
| `fg` | Color del icono / título del callout (sobre `bg`) | AA (4.5:1) |
| `bg` | Fondo del bloque | — |
| `border` | Borde lateral estándar | UI AA (3:1) |
| `fgOnBg` | Color del cuerpo del texto (sobre `bg`) | AA (4.5:1) |
| `borderContrast` | Borde alternativo AAA cuando el cuerpo lleva texto encima | AAA (7:1) |

## §2 · Catálogo de tokens

> Los valores hex NO aparecen aquí; se consultan en `assets/tokens.json` vía `scripts/util/tokens.py`. La tabla de la izquierda es la **interfaz pública**.

### §2.1 · Semánticos (9)

| Token | Categoría | Rol | Modo |
|---|---|---|---|
| `semantic.info` | semantic | Consejo neutro, etiqueta de versión | light + dark |
| `semantic.success` | semantic | Logro, consejo positivo | light + dark |
| `semantic.warning` | semantic | Atención no destructiva, contradicción | light + dark |
| `semantic.danger` | semantic | Atención destructiva, error irrecuperable | light + dark |
| `semantic.note` | semantic | Nota informativa neutra | light + dark |
| `semantic.example` | semantic | Ejemplo demostrativo | light + dark |
| `semantic.deprecated` | semantic | Obsolescencia, versión eliminada | light + dark |
| `semantic.security` | semantic | Aviso de seguridad, CVE, secreto | light + dark |
| `semantic.performance` | semantic | Aviso de rendimiento, hot-path, latencia | light + dark |

### §2.2 · Neutros (9) — prefijo `_` indica no-semántico

| Token | Categoría | Rol | Modo |
|---|---|---|---|
| `_neutral.text` | _neutral | Texto principal del documento | light + dark |
| `_neutral.textMuted` | _neutral | Texto secundario (subtítulo, caption) | light + dark |
| `_neutral.background` | _neutral | Fondo del documento | light + dark |
| `_neutral.surface` | _neutral | Fondo elevado (header nota, tabla thead) | light + dark |
| `_neutral.border` | _neutral | Borde estándar (separadores, hr) | light + dark |
| `_neutral.code` | _neutral | Fondo de bloque código (inline + fence) | light + dark |
| `_neutral.codeText` | _neutral | Color de texto en bloque código | light + dark |
| `_neutral.quote` | _neutral | Fondo para admonition sin token (external, derived) | light + dark |
| `_neutral.quoteBorder` | _neutral | Borde de quote/external/derived | light + dark |

### §2.3 · Series (paleta de datos, F70 Okabe-Ito)

| Token | Categoría | Rol | Inversión light↔dark |
|---|---|---|---|
| `series.okabe-ito-orange` | series | Serie de datos 1 | No |
| `series.okabe-ito-sky-blue` | series | Serie de datos 2 | No |
| `series.okabe-ito-bluish-green` | series | Serie de datos 3 (único con AA en texto, ver F71 §8) | No |
| `series.okabe-ito-yellow` | series | Serie de datos 4 | No |
| `series.okabe-ito-blue` | series | Serie de datos 5 (default) | No |
| `series.okabe-ito-vermillion` | series | Serie de datos 6 | No |
| `series.okabe-ito-reddish-purple` | series | Serie de datos 7 | No |
| `series.okabe-ito-black` | series | Serie 8 (ejes / línea de referencia) | **Sí** (`#000000` ↔ `#FFFFFF`) |
| `series.axisLight` | series | Ejes neutros tema claro (axisLine, gridline, textAxis, title, subtitle, background) | — |
| `series.axisDark` | series | Ejes neutros tema oscuro (mismos campos) | — |

La paleta Okabe-Ito es **colorblind-safe** (verificada con ΔE CIEL76 ≥ 20 entre pares adyacentes en `make_figure.py`). La inversión de `okabe-ito-black` se modela en `tokens.json` como `{light: "#000000", dark: "#FFFFFF"}` y `resolve_series()` la aplica automáticamente.

### §2.4 · Tipografía

- Familias: `serif` (Lora / IBM Plex Serif / Georgia), `sans` (Inter / Helvetica Neue), `mono` (JetBrains Mono / Fira Code).
- Escala: `xs` 0.75rem (12px), `sm` 0.875rem (14px), `base`/`md` 1rem (16px), `lg` 1.25rem (20px), `xl` 1.6rem (25.6px), `2xl` 2.2rem (35.2px), `3xl` 2.8rem (44.8px). Base asumida `html { font-size: 16px; }`.
- Pesos: `regular` 400, `medium` 500, `semibold` 600, `bold` 700.
- LineHeights: `tight` 1.25 (headings), `snug` 1.4 (subtítulos), `normal` 1.7 (cuerpo), `loose` 2.0 (listas densas).

### §2.5 · Espaciado y radios

- Escala spacing (rem): `0=0`, `1=0.25`, `2=0.5`, `3=0.75`, `4=1`, `5=1.5`, `6=2`, `7=2.5`, `8=3`.
- `density.{compact,normal,spacious}` mapea a tripletas `{paragraph, list-item, section}` para que el renderer consulte el `profile.visual.density` (F11) y resuelva el espaciado. La skill ship con `normal` por defecto (ver `assets/profile.template.yaml` línea 110).
- Radios (px): `none=0`, `sm=2`, `md=4`, `lg=6`, `xl=12`, `pill=9999px`. `lg` (6px) es el default para callouts (heredado de F59 `html_pdf.template.css`).

## §3 · Regla INV-14 operativa

**Ningún archivo del proyecto contiene un color literal fuera de `tokens.json`.** La verificación:

```
rg -nP '(?<![A-Za-z_])#[0-9A-Fa-f]{3,8}\b|(?<![A-Za-z_])rgba?\(' \
   skill/notemartin-study-notes \
   --glob '!**/tokens.json' \
   --glob '!**/html_pdf.template.css'
```

Devuelve **0 ocurrencias** en cualquier archivo creado o modificado a partir de F72. El lookbehind negativo `(?

**Excepción vigente (parcial):** `references/08-render/html_pdf.template.css` (F59) aún contiene literales hex. El snippet `notemartin.css` (F74) sí consume `var(--token)` desde `assets/css-tokens.generated.css` (auto-generado por `scripts/render/css_from_tokens.py`); la migración retroactiva de `html_pdf.template.css` queda para una **fase futura** (decisión del usuario en F74, alcance "Solo snippet + generador"). La verificación de INV-14 sigue **excluyendo** `html_pdf.template.css` vía `--glob` hasta esa fase.

**Cómo consumir tokens en código Python:**

```python
from scripts.util.tokens import load_tokens, resolve_token, resolve_series

tokens = load_tokens()  # busca en skill/notemartin-study-notes/assets/tokens.json
fg = resolve_token(tokens, "semantic", "info", "light", "fgOnBg")
blue = resolve_series(tokens, "okabe-ito-blue", "light")
```

**Cómo consumir tokens en CSS (F74 ✅):** el generador `scripts/render/css_from_tokens.py` produce `assets/css-tokens.generated.css`: un bloque `:root { --semantic-info-fg: #...; --semantic-info-bg: #...; ... }` (9 semánticos × 5 valores + 9 neutrals + tipografía + spacing + radii) seguido de `@media (prefers-color-scheme: dark) { :root { --semantic-info-fg: #...; ... } }` con los overrides dark. El snippet `assets/notemartin.css` empieza con `@import "css-tokens.generated.css";` y todas las propiedades consumen `var(--semantic-*)` o `var(--_neutral-*)`. Cero literales hex en `notemartin.css` (verificado por `evals/css-snippet-sample` C5).

**Cómo consumir tokens en Mermaid (`classDef`):** la cita a un token semántico se hace por nombre (`classDef warning fill:#semantic.warning.bg stroke:#semantic.warning.border`). Ver `mermaid-portable.md` §5 R-MP-01 y `diagram-catalog.md` §22.

## §4 · Procedimiento de verificación de contraste

**Fórmula WCAG 2.1 SC 1.4.3:**

```
L = 0.2126 R + 0.7152 G + 0.0722 B
  con cada canal linealizado:
    c <= 0.03928 → c / 12.92
    c >  0.03928 → ((c + 0.055) / 1.055) ** 2.4
ratio = (L_lighter + 0.05) / (L_darker + 0.05)
```

**Comando canónico:**

```
python3 skill/notemartin-study-notes/scripts/validate/contrast_check.py \
    --tokens skill/notemartin-study-notes/assets/tokens.json \
    --min-ratio 4.5 --mode both
```

**Exit codes:**

- `0` — todos los pares cumplen el mínimo.
- `1` — algún par cae por debajo (imprime cuáles en Markdown).
- `2` — archivo no encontrado / JSON inválido / uso incorrecto.

**Comportamiento por defecto:** tabla Markdown con 18 filas (9 tokens × 2 modos) y un veredicto final PASS/FAIL. Con `--json` emite el mismo contenido en JSON parseable por CI.

## §5 · Tablas WCAG pre-calculadas (referencia, no ejecutables)

Las ratios reales se generan ejecutando `contrast_check.py`; esta tabla documenta el resultado esperado a modo de contrato. **Si la tabla cambia respecto a la realidad, regenerar la documentación y bumpear `$version.patch` en `tokens.json`.**

| Token | Modo | Ratio `fgOnBg` vs `bg` | AA (≥4.5) | AAA (≥7.0) |
|---|---|---|---|---|
| `semantic.info` | light | 7.56:1 | ✅ | ✅ |
| `semantic.info` | dark | 13.15:1 | ✅ | ✅ |
| `semantic.success` | light | 7.00:1 | ✅ | ❌ |
| `semantic.success` | dark | 12.36:1 | ✅ | ✅ |
| `semantic.warning` | light | 10.65:1 | ✅ | ✅ |
| `semantic.warning` | dark | 13.04:1 | ✅ | ✅ |
| `semantic.danger` | light | 5.75:1 | ✅ | ❌ |
| `semantic.danger` | dark | 14.64:1 | ✅ | ✅ |
| `semantic.note` | light | 14.77:1 | ✅ | ✅ |
| `semantic.note` | dark | 10.87:1 | ✅ | ✅ |
| `semantic.example` | light | 12.61:1 | ✅ | ✅ |
| `semantic.example` | dark | 11.39:1 | ✅ | ✅ |
| `semantic.deprecated` | light | 9.79:1 | ✅ | ✅ |
| `semantic.deprecated` | dark | 14.17:1 | ✅ | ✅ |
| `semantic.security` | light | 5.75:1 | ✅ | ❌ |
| `semantic.security` | dark | 14.64:1 | ✅ | ✅ |
| `semantic.performance` | light | 6.83:1 | ✅ | ❌ |
| `semantic.performance` | dark | 13.37:1 | ✅ | ✅ |

**Resumen:** 18/18 cumplen AA, 14/18 cumplen AAA. Los 4 pares AAA-fail son: `success.light`, `danger.light`, `security.light`, `performance.light` — todos con `fg` saturado sobre fondo claro, lo cual es correcto semánticamente (color de marca intencional) y siguen siendo AA para texto normal.

## §6 · Tabla de mapeo intención → severidad admonition

La spec del ROADMAP (F72) lista 9 tokens semánticos; el parser NoteMark (`scripts/authoring/_ir_builder.py:ADMONITION_SEVERITIES` y `schemas/note-ir.schema.json`) admite 12 severidades. Esta tabla reconcilia ambos.

| Token semántico | Severidades que cubre | Justificación |
|---|---|---|
| `semantic.info` | `tip`, `version` | consejo neutro; etiqueta de versión (icono 🏷️ en html_pdf) |
| `semantic.success` | (reservado; no usado por defecto en F72) | logro positivo; se cubre con `tip` en F73 si se necesita |
| `semantic.warning` | `warning`, `conflict` | atención no destructiva; contradicción source-vs-source o version-mismatch |
| `semantic.danger` | `danger` | atención destructiva, error irrecuperable |
| `semantic.note` | `note` | nota informativa neutra (default) |
| `semantic.example` | `example` | ejemplo demostrativo |
| `semantic.deprecated` | `deprecated` | marcado de obsolescencia |
| `semantic.security` | `security` | aviso de seguridad, CVE, secreto |
| `semantic.performance` | `performance` | aviso de rendimiento, hot-path, latencia |
| `_neutral.quote` (no semántico) | `external`, `derived` | no llevan color saturado; usan el quote neutral con su `_neutral.quoteBorder` |
| `_neutral.note` (no semántico) | (no usado por admonition) | reservado para bloques neutros futuros |

F73 (`style-mapping.md`) cierra el contrato final `severidad → {emoji, icon, css class, color}` consumiendo esta tabla. Los 6 renderers actuales (`obsidian.py`, `notion_api.py`, `notion_md.py`, `appflowy.py`, `markdown.py`, `html_pdf.py`) ya consumían su propio mapeo severidad→emoji/icon; F73 los unifica en una sola tabla canónica de 20 severidades (esta tabla §6 lista 12; F73 §3 la amplía a 20 con `derived` + 7 nativas Obsidian no canónicas).

## §7 · Tipografía y espaciado

**Escala tipográfica modular (ratio ≈ 1.25 entre pasos):** 12 / 14 / 16 / 20 / 25.6 / 35.2 / 44.8 px. El `base` (16px) cumple el mínimo de `accessibility.md` §3.1 para texto en admonition y tabla. El renderer html_pdf asume `html { font-size: 16px; }` para que `1rem = 16px`; este contrato se reitera en F74.

**Pesos:** la jerarquía visual usa 400 (cuerpo), 500 (énfasis sutil), 600 (subtítulos H2-H4), 700 (H1, frontmatter título). Reservar `bold` (700) para destacar contenido fáctico, no decorativo.

**LineHeights:** `normal` (1.7) para cuerpo corrido; `tight` (1.25) para headings densos; `loose` (2.0) para listas con checkboxes y checklists de alta densidad.

**Espaciado por `density` (mapeado en `profile.template.yaml`):**

| Profile `visual.density` | `paragraph` | `list-item` | `section` |
|---|---|---|---|
| `compact` | spacing.1 (0.25rem) | spacing.2 (0.5rem) | spacing.5 (1.5rem) |
| `normal` | spacing.4 (1rem) | spacing.4 (1rem) | spacing.6 (2rem) |
| `spacious` | spacing.6 (2rem) | spacing.5 (1.5rem) | spacing.7 (2.5rem) |

Default del profile template: `normal`.

**Radios:** `sm` (2px) para chips/badges; `md` (4px) para botones/inputs; `lg` (6px) para callouts y cards; `xl` (12px) para modales; `pill` (9999px) para avatares y tags.

## §8 · Uso por destino

| Destino | Soporte color | Cómo consume tokens |
|---|---|---|
| Obsidian | ✅ | Snippet CSS `assets/notemartin.css` (F74) con `var(--token)` resuelto por `assets/css-tokens.generated.css` (auto-generado por `scripts/render/css_from_tokens.py`) |
| Notion API | parcial | Solo `bg` del color del callout (paleta Notion limitada); usa el `color` declarado en `notion_api.py` mapeado desde §6 |
| Notion import | ❌ | Emoji semántico + texto; color se pierde como estilo (limitación Notion import) |
| AppFlowy | ✅ | Color nativo; mapeo severidad→color en `appflowy.py` consume §6 |
| Markdown plano (GFM) | parcial | Emoji semántico + `class="callout-<severity>"` (F73) opcional; CSS externo si GitHub |
| HTML/PDF | ✅ | Plantilla `html_pdf.template.css` (F59) — pendiente migración a `var(--token)` para fase futura (F74 cerró el snippet Obsidian solamente) |
| Flashcards | ❌ | Sin color; solo emoji semántico en la cara (per `capability-matrix.md` §3 fila 13) |

## §9 · Cambios permitidos y política semver

`tokens.json` lleva `$version: "1.0.0"`. Reglas:

- **Major bump** (X.0.0): renombrar o eliminar un token existente. Obliga a actualizar todos los consumidores; el loader `scripts/util/tokens.py` advertirá si `$version.major > 1` (con `warn_if_unsupported_major`) y los renderers deben migrar antes de aceptar.
- **Minor bump** (1.X.0): añadir un token nuevo. Los consumidores existentes siguen funcionando; los nuevos lo adoptan cuando estén listos.
- **Patch bump** (1.0.X): ajustar un valor hex (p.ej. para mejorar contraste tras una auditoría WCAG). No requiere migración de consumidores; solo verificar con `contrast_check.py`.

**Auditoría periódica:** cada vez que se añada o modifique un token, ejecutar `contrast_check.py` y actualizar §5. Si la tabla pre-calculada cambia respecto al comando, regenerar este doc en el mismo commit.

**No se permite:**

- Añadir un color hex fuera de `tokens.json` (violación INV-14). Excepción única: `html_pdf.template.css` documentada en §3, hasta F74.
- Hardcodear el nombre de un token en una nota NoteMark (las notas no llevan color, solo intención semántica; el renderer consulta el perfil + tokens).
- Cambiar la paleta Okabe-Ito sin re-verificar `ΔE CIEL76 ≥ 20` (responsabilidad del script `make_figure.py`).

## §10 · Wirings

- **F11** `assets/profile.template.yaml` — `visual.density` mapea a `tokens.spacing.density`.
- **F46** `references/04-authoring/inline-marks.md` §7 — las marcas `{{nombre}}` (`highlight-token`), `{derived}`, `{external}` referencian tokens concretos (`_neutral.code`, `semantic.warning.bg` y `semantic.warning.border`, `_neutral.quote` y `_neutral.quoteBorder`).
- **F47** `references/04-authoring/properties.md` §3 — `INV-P3` (cero colores literales en propiedades) consume tokens.
- **F48** `references/04-authoring/notemark.md` §10 — la regla "no hex `#abc123` literales" en directivas consume tokens.
- **F65** `references/07-visual/diagram-catalog.md` §22 — la regla "color hex literal violada, usar `classDef` con nombres semánticos" consume tokens.
- **F66** `references/07-visual/mermaid-portable.md` §5/§10 — `INV-14` y la regla "`classDef` cita `tokens.md`" consumen tokens.
- **F69** `references/07-visual/monospace-diagrams.md` §1 — la cita a tokens.md se valida.
- **F70** `scripts/render/make_figure.py` — consumidor principal: carga `tokens.json` en import, resuelve Okabe-Ito y ejes neutros via `resolve_series` y `resolve_token`. Migrado en F72 (literales eliminados).
- **F71** `references/07-visual/accessibility.md` §1/§10 — la cita a tokens.md como fuente de ratios WCAG pre-validados queda ratificada.
- **F71** `references/07-visual/reconstruction.md` §12 — la cita a tokens.md para `classDef` y `style` queda ratificada.
- **F73** `references/07-visual/style-mapping.md` + `scripts/util/style_mapping.py` — **productor**: consume §6 y publica el contrato `severidad → {emoji, obsidian_callout, notion_icon, notion_color, appflowy_callout, html_css_class}` (20 severidades × 6 destinos). Tabla canónica única consumida por los 6 renderers L4.
- **F74** `assets/notemartin.css` (snippet) + `assets/css-tokens.generated.css` (auto-generado) + `scripts/render/css_from_tokens.py` (generador) — **productor**: genera `:root { --token: hex; }` con los 9 semánticos × 5 valores + 9 neutrals + tipografía + spacing + radii (light) + `@media (prefers-color-scheme: dark)` (dark). El snippet `notemartin.css` (363 líneas, 9 secciones: callouts, tablas, código, capas, procedencia, inline marks, mermaid, print, fallback) consume las variables vía `@import "css-tokens.generated.css";` — 0 literales hex. Cierra los 3 criterios del ROADMAP §1453-1455.
- **F77** `evals/visual/` — verificación visual multi-destino (cerrado). 2 notas (sonda F8 + real-postgresql-arrays), 12 artefactos reales en 4 destinos renderizables localmente + checklist para 3 destinos externos, 5/5 PASS en `evals/visual/run_eval.py`.

---

**Verificación al cierre de la fase:**

- `wc -l references/07-visual/tokens.md` ≤ 400 líneas.
- §1 tabla de estructura con 6 filas.
- §2 catálogo con 9 semánticos + 9 neutrals + 10 series + 4 sub-tablas.
- §3 comando `rg` documentado con lookbehind negativo y `--glob` de excepción.
- §4 comando `contrast_check.py` documentado con exit codes.
- §5 tabla 18 filas pre-calculadas.
- §6 tabla de mapeo intención → 12 severidades.
- §7 tipografía y densidad con tabla 3×3.
- §8 tabla 7 destinos con semántica de consumo.
- §9 política semver con major/minor/patch y lista de no-permitidos.
- §10 13 wirings documentados.
