# `references/07-visual/style-mapping.md` — Mapeo de estilo por destino

> **Propósito:** declarar la tabla canónica `severidad → estilo por destino` (Obsidian callout nativo, Notion API icon + color, AppFlowy callout nativo, HTML/PDF CSS class), consumida por los 6 renderers L4 vía `scripts/util/style_mapping.py`. Cierra el criterio "ninguna intención queda sin mapeo" del ROADMAP §1437-1440 y elimina el drift entre los dicts `SEVERITY_TO_*` locales de cada renderer.
>
> **Cuándo cargar:** antes de modificar cualquier renderer L4, antes de añadir una nueva severidad al parser (F14/F45/F48), antes de definir un callout CSS en F74, y en cualquier revisión visual de notas (F77).

---

## §1 · Propósito y alcance

F73 publica el contrato canónico entre la **intención semántica** que el agente o el parser declaran en una nota (NoteMark → IR → admonition) y la **representación estilística** que cada destino renderiza. La tabla canónica vive en `scripts/util/style_mapping.py` como una tupla inmutable de `StyleMapping` (dataclass frozen); este doc la **reproduce en markdown** como interfaz legible.

**Cierra los 3 criterios del ROADMAP §1437-1440:**

1. _Cada intención tiene mapeo en los cuatro destinos con estilo_ — la tabla cubre 20 severidades × 5 campos de destino = 100 celdas; ninguna celda vacía.
2. _Un mismo tipo de advertencia usa el mismo icono en todos_ — `StyleMapping.icon` es canónico (1 emoji por intención, salvo los 3 casos documentados en §4).
3. _Ninguna intención queda sin mapeo_ — el módulo levanta `KeyError` con sugerencia Levenshtein si llega una severidad desconocida; cobertura exhaustiva de las 19 severidades legacy + `derived` (F72 §6).

**Fuera de alcance:**

- Tokens de color (hex concretos) → `tokens.md` (F72).
- Accesibilidad visual general → `accessibility.md` (F71).
- CSS de las clases `callout-*` → `assets/notemartin.css` (F74) + `references/08-render/html_pdf.template.css` (F59, migración pendiente).
- Verificación visual con capturas → `evals/visual/` (F77 cerrado; 12 artefactos reales + checklist 12 entradas para QA humana).

## §2 · Tabla canónica 20 × 5

Las 20 severidades se dividen en: **9 del IR schema enum** (`note, tip, warning, danger, security, performance, version, deprecated, conflict, external` — schema enum tiene 10; añadimos `tip` que está en schema), **7 nativas Obsidian no canónicas** (`caution, example, question, success, failure, bug, quote, abstract` — Obsidian 1.5+ las soporta nativamente pero el IR schema no las emite como admonition primary), y **`derived`** (existe en el parser `_block_parser.py:202` pero no en el schema enum — documentado en §7).

Cada fila da los 5 campos por destino:

| Severidad | Token (F72) | Icono | Obsidian callout | Notion color | AppFlowy | HTML class |
|---|---|---|---|---|---|---|
| `note` | `_neutral.quote` | 📝 | `note` | `default` | `note` | `callout-note` |
| `tip` | `semantic.info` | 💡 | `tip` | `green_background` | `info` | `callout-tip` |
| `info` | `semantic.info` | ℹ️ | `info` | `blue_background` | `info` | `callout-info` |
| `warning` | `semantic.warning` | ⚠️ | `warning` | `yellow_background` | `warning` | `callout-warning` |
| `caution` | `semantic.warning` | ⚠️ | `warning` | `orange_background` | `warning` | `callout-warning` |
| `danger` | `semantic.danger` | 🚫 | `danger` | `red_background` | `danger` | `callout-danger` |
| `example` | `semantic.example` | 📋 | `example` | `gray_background` | `info` | `callout-example` |
| `question` | `semantic.info` | ❓ | `question` | `purple_background` | `question` | `callout-question` |
| `success` | `semantic.success` | ✅ | `success` | `green_background` | `success` | `callout-success` |
| `failure` | `semantic.danger` | ❌ | `danger` | `red_background` | `danger` | `callout-danger` |
| `bug` | `semantic.danger` | 🐛 | `danger` | `red_background` | `danger` | `callout-danger` |
| `quote` | `_neutral.quote` | 💬 | `quote` | `gray_background` | `info` | `callout-note` |
| `abstract` | `_neutral.quote` | 📑 | `abstract` | `gray_background` | `info` | `callout-note` |
| `security` | `semantic.security` | 🔒 | `danger` | `red_background` | `danger` | `callout-danger` |
| `performance` | `semantic.performance` | ⚡ | `warning` | `orange_background` | `warning` | `callout-warning` |
| `version` | `semantic.info` | 🏷️ | `info` | `blue_background` | `info` | `callout-info` |
| `deprecated` | `semantic.deprecated` | ⛔ | `warning` | `gray_background` | `warning` | `callout-warning` |
| `conflict` | `semantic.warning` | ⚠️ | `warning` | `orange_background` | `warning` | `callout-warning` |
| `external` | `_neutral.quote` | 🔗 | `quote` | `gray_background` | `info` | `callout-info` |
| `derived` | `_neutral.quote` | ✨ | `quote` | `gray_background` | `info` | `callout-info` |

**Verificación:** las 100 celdas se validan al import del módulo (`validate_table()` en `scripts/util/style_mapping.py:128`). Si la tabla se rompe, el módulo lanza `RuntimeError` antes de servir cualquier helper.

## §3 · Mapeo severidad → token semántico

Esta tabla amplía `tokens.md` §6 (que listaba 12 severidades del parser) a las 20 severidades canónicas de F73. La columna _Token_ indica qué entrada de `assets/tokens.json` consume cada severidad para color de fondo, borde y texto.

| Severidad | Token en `tokens.json` | Justificación |
|---|---|---|
| `note`, `quote`, `abstract`, `external`, `derived` | `_neutral.quote` (bg + border) + `_neutral.quoteBorder` (border) | Bloques neutros; no llevan color saturado. F72 §6 ya mapea `external, derived` a este token. |
| `tip`, `info`, `version`, `question` | `semantic.info` | Consejo neutro / etiqueta / pregunta. El icono distingue el sub-tipo. |
| `warning`, `caution`, `conflict` | `semantic.warning` | Atención no destructiva; se distinguen por color (warning=yellow, caution/conflict=orange) e icono. |
| `danger`, `failure`, `bug`, `security` | `semantic.danger` o `semantic.security` | Atención destructiva o seguridad; mismo color rojo, icono distinto. `security` consume `semantic.security` (mismo anchor cromático per F72 §5, distinto icono 🔒). |
| `example` | `semantic.example` | Ejemplo demostrativo con su propio token. |
| `success` | `semantic.success` | Logro positivo. |
| `performance` | `semantic.performance` | Aviso de rendimiento con token ámbar. |
| `deprecated` | `semantic.deprecated` | Obsolescencia con token púrpura apagado. |

**Hex concretos:** consultar `assets/tokens.json` y `tokens.md` §5 (tabla WCAG pre-calculada). Este doc no duplica valores.

## §4 · Iconos canónicos

Cada severidad tiene **un único emoji** que se usa en los 4 destinos. Los 20 iconos:

| Severidad | Icono | Notas |
|---|---|---|
| `note` | 📝 | nota neutra |
| `tip` | 💡 | consejo positivo |
| `info` | ℹ️ | información |
| `warning` | ⚠️ | atención |
| `caution` | ⚠️ | ⚠️ compartido con `warning` (se distinguen por color Notion: yellow vs orange) |
| `danger` | 🚫 | atención destructiva |
| `example` | 📋 | ejemplo |
| `question` | ❓ | pregunta |
| `success` | ✅ | logro |
| `failure` | ❌ | fallo (vs `bug` 🐛) |
| `bug` | 🐛 | error de código (vs `failure` ❌) |
| `quote` | 💬 | cita |
| `abstract` | 📑 | resumen |
| `security` | 🔒 | seguridad (candado siempre; color rojo como `danger`) |
| `performance` | ⚡ | rendimiento (rayo; color ámbar como `warning`) |
| `version` | 🏷️ | etiqueta de versión |
| `deprecated` | ⛔ | obsolescencia (prohibido; no es un error) |
| `conflict` | ⚠️ | ⚠️ compartido con `warning` y `caution` (se distinguen por color Notion) |
| `external` | 🔗 | conocimiento externo (enlace) |
| `derived` | ✨ | contenido derivado del SDM (analogía, síntesis) |

**Casos donde 2-3 severidades comparten icono** (justificación obligatoria):

- **`warning`, `caution`, `conflict` → ⚠️:** los 3 comunican "atención no destructiva". El color Notion los diferencia (`yellow_background` vs `orange_background` vs `orange_background`); el texto del admonition distingue semánticamente. Mantener un icono único respeta la regla WCAG SC 1.4.1 ("nunca color como único portador"): un segundo canal (texto "WARNING:" / "CONFLICT:") acompaña al icono+color.
- Los 17 restantes tienen icono único.

## §5 · Paleta de Notion acotada

La Notion API (2022-06-28) acepta exactamente **10 valores** para el campo `color` de un callout block:

```
default, gray_background, brown_background, orange_background,
yellow_background, green_background, blue_background, purple_background,
pink_background, red_background
```

F73 declara la siguiente correspondencia canónica con los 9 colores que la skill usa efectivamente (F73 deja `pink_background` y `brown_background` **explícitamente fuera** del mapeo):

| Intención (F72) | Notion color | Severidades que lo usan |
|---|---|---|
| `semantic.info` | `blue_background` | `info`, `version` |
| `semantic.success` | `green_background` | `tip`, `success` |
| `semantic.warning` | `yellow_background` | `warning` |
| `semantic.warning` (variante orange) | `orange_background` | `caution`, `conflict`, `performance` |
| `semantic.danger` / `semantic.security` | `red_background` | `danger`, `failure`, `bug`, `security` |
| `semantic.example` | `gray_background` | `example` |
| `semantic.deprecated` | `gray_background` | `deprecated` |
| `semantic.info` (variante purple) | `purple_background` | `question` |
| `_neutral.quote` (nota neutra) | `gray_background` | `note`, `quote`, `abstract`, `external`, `derived` |
| (default = sin color) | `default` | `note` (variante; depende de la severidad) |

**Regla operativa:** si una nota pre-existente en Notion usa `pink_background` o `brown_background`, el renderer `notion_api.py` emite una **degradación explícita** (`evidence: "color fuera de paleta canónica"`) y aplica fallback al `default`. La nota no se rompe (F53 INV-07: la degradación cambia la forma, no omite contenido).

## §6 · Resolución de inconsistencias heredadas

Antes de F73, los 6 renderers L4 mantenían dicts `SEVERITY_TO_*` locales con divergencias en cómo ciertas severidades se mapeaban. F73 unifica todas en una sola tabla canónica (la de §2). Las 12 decisiones de cierre:

| Severidad | Antes (divergente) | F73 (canónico) | Justificación |
|---|---|---|---|
| `caution` | obsidian→`caution`; appflowy/html_pdf→`warning` | `warning` en todos | Obsidian tiene `caution` nativo, pero semánticamente es la misma intención que `warning` (atención no destructiva). Unificar evita doble mapeo. El color Notion (`orange_background`) los distingue. |
| `security` | obsidian→`warning`; appflowy/html_pdf→`danger` | `danger` en todos | Obsidian no tiene `security` nativo; mapeamos a `danger` (color rojo) + icono 🔒 prefijo. El bloque se distingue por el icono, no por el nombre del callout. |
| `performance` | obsidian→`note`; appflowy→`info`; html_pdf→`warning` | `warning` en todos | Mismo razonamiento: `performance` no es nativo. Color ámbar + icono ⚡ prefijo. |
| `external` | obsidian→`quote`; appflowy→`info`; html_pdf→`info` | `quote` en Obsidian; `info` en AppFlowy/HTML | AppFlowy no tiene `quote` nativo; HTML reusa `callout-info` per F59. F73 ratifica. |
| `version` | obsidian/appflowy/html_pdf→`info` | `info` en todos | Ya unificado; ratificar. |
| `deprecated` | obsidian/appflowy/html_pdf→`warning` | `warning` en todos | Ya unificado; ratificar. |
| `conflict` | obsidian/appflowy/html_pdf→`warning` | `warning` en todos | Ya unificado; ratificar. |
| `question` | obsidian/appflowy/html_pdf→`question` | `question` en todos | Ya unificado; ratificar. |
| `success` | obsidian/appflowy/html_pdf→`success` | `success` en todos | Ya unificado; ratificar. |
| `failure` | obsidian→`failure`; appflowy/html_pdf→`danger` | `danger` en todos | Obsidian tiene `failure` nativo, pero unificar a `danger` mantiene el patrón del resto. Distinguir por emoji (❌). |
| `bug` | obsidian→`bug`; appflowy/html_pdf→`danger` | `danger` en todos | Mismo razonamiento. Distinguir por emoji (🐛). |
| `quote` / `abstract` | obsidian→`quote`/`abstract`; appflowy→`info`/`info`; html_pdf→`note`/`note` | ratificar | Ya unificado por renderer. |

**Impacto en notas pre-existentes:** una nota que usaba `:::caution` antes se renderizaba como `> [!caution]` en Obsidian; ahora se renderiza como `> [!warning]`. El icono y texto del admonition no cambian; solo el nombre del callout type. Riesgo bajo (los 12 nativos de Obsidian 1.5+ siguen siendo válidos como alias, pero la tabla canónica unifica).

## §7 · Casos especiales

### §7.1 · `derived` (asimetría schema/parser)

`derived` aparece en `scripts/authoring/_block_parser.py:202` (12 nombres de directiva de admonition) pero **no** en el enum de `schemas/note-ir.schema.json:114` (10 severidades canónicas). El parser acepta `:::derived` como admonition; el schema lo rechazaría si se validara estrictamente.

**Decisión de F73:** incluir `derived` en la tabla canónica como alias visual de `external` con `_neutral.quote` per F72 §6. El renderer lo trata igual que `external`. La asimetría schema/parser queda documentada como wiring explícito; reabrir F14 si se quiere cerrar (añadir `derived` al enum del schema o eliminarlo del parser).

### §7.2 · `external` vs `derived`

Ambos usan `_neutral.quote` + `_neutral.quoteBorder` per F72 §6. Se distinguen semánticamente por la directiva (`:::external` para knowledge fuera del SDM, `:::derived` para analogías/síntesis del agente). Los iconos (`🔗` vs `✨`) refuerzan la diferencia sin necesidad de colores distintos.

### §7.3 · Severidades Obsidian nativas no canónicas

Obsidian 1.5+ soporta 13 callouts nativos: `note, tip, info, warning, caution, danger, example, question, success, failure, bug, quote, abstract`. F73 unifica 5 de ellos (`caution, failure, bug, quote, abstract`) al patrón del resto. Los 8 restantes (`note, tip, info, warning, danger, example, question, success`) coinciden con severidades canónicas y se mapean 1:1.

**Razón de la unificación:** mantener coherencia entre destinos. Notion API no tiene `failure` ni `bug` como callouts nativos; AppFlowy tiene 6 nativos que no incluyen `quote` ni `abstract`. Unificar reduce la superficie de mapping y permite que el agente invoque severidades Obsidian-específicas sin perderlas en otros destinos.

### §7.4 · `note` con doble mapeo Notion

`note` aparece en la tabla con `notion_color: "default"` (sin color de fondo). Esto es deliberado: en Notion, el callout `default` se ve neutro. Si un agente quiere dar un fondo gris visible, debe usar `quote` o `example`, no `note`. Esta convención viene de la UX de Notion (los callouts `default` son literalmente invisibles visualmente, solo el icono los distingue).

## §8 · Migración de renderers

Los 6 renderers L4 eliminan sus dicts `SEVERITY_TO_*` locales y consumen `scripts/util/style_mapping.py`. Cambios por renderer:

| Renderer | Dict local eliminado | Helper usado | Cambio funcional |
|---|---|---|---|
| `scripts/render/obsidian.py:75-96` `SEVERITY_TO_CALLOUT` | 19 → 0 | `obsidian_callout_for(severity)` | `security` ahora cae a `danger`; `performance` a `warning`; `failure`/`bug` a `danger` (antes: `warning`/`note`/`failure`/`bug`) |
| `scripts/render/notion_api.py:112-132` `SEVERITY_TO_CALLOUT` | 19 → 0 | `notion_callout_for(severity)` → `(icon, color)` | Sin cambio funcional; los hex coinciden |
| `scripts/render/notion_md.py:74-94` `SEVERITY_TO_EMOJI` | 19 → 0 | `icon_for(severity)` | Sin cambio funcional |
| `scripts/render/appflowy.py:80-100` `SEVERITY_TO_CALLOUT` | 19 → 0 | `appflowy_callout_for(severity)` | Sin cambio funcional (AppFlowy ya estaba unificado) |
| `scripts/render/markdown.py:75-95` `SEVERITY_TO_EMOJI` + `:100-106` `SEMANTIC_TOKENS` | 19+5 → 0 | `icon_for`, `html_css_class_for` | Las CSS classes ahora vienen del módulo |
| `scripts/render/html_pdf.py:76-95` `SEVERITY_TO_CSS_CLASS` + `SEVERITY_TO_EMOJI` | 19+19 → 0 | `html_css_class_for`, `icon_for` | Sin cambio funcional |

**Verificación post-migración:**

```bash
rg -n 'SEVERITY_TO_' skill/notemartin-study-notes/scripts/render/ --glob '!*style_mapping.py'
```

Debe devolver **0 ocurrencias**. Si quedan, son residuales a limpiar.

**Regresión:** los 6 evals de renderers (`evals/<renderer>-sample/`) deben seguir pasando después de la migración. Si un eval falla, se diagnostica si la regresión viene del cambio de mapeo (criterio 2 esperado) o del código (regresión a corregir).

## §9 · Wirings

- **F45** `references/04-authoring/block-directives.md` §10 — la lista cerrada de 12 directivas admonition consume esta tabla; el agente las elige consultando `tokens.md` §6 + `style-mapping.md` §2.
- **F53** `references/08-render/contract.md` filas 5/13 — el contrato L4 de "Callouts semánticos" y "Colores semánticos" cita `scripts/util/style_mapping.py` (no solo `assets/tokens.json`).
- **F55-F60** renderers L4 — consumidores primarios de los helpers `icon_for`, `obsidian_callout_for`, `notion_callout_for`, `appflowy_callout_for`, `html_css_class_for`, `semantic_token_for`.
- **F72** `references/07-visual/tokens.md` §6 — la tabla intención→severidad (12 filas) se amplía aquí a 20 filas; los hex de fondo/borde/texto siguen viviendo en `tokens.json`.
- **F74** `assets/notemartin.css` — las CSS classes `callout-<severity>` definidas en §2 se estilizan en F74 con `var(--token)` resuelto por `scripts/render/css_from_tokens.py` (F72 §10). El HTML/PDF renderer (`html_pdf.py`) ya emite `<aside class="callout-<severity>">`; F74 decide los estilos concretos.
- **F75** `references/07-visual/note-templates.md` + `scripts/render/_header.py` — el agente al redactar cabecera consulta §2 para saber qué severidad invocar por tipo de nota; el helper `_header.emit_cabecera` consume los 5 campos canónicos (`summary`, `source*`, `product*`, `status`, `reading-time-minutes`) y los renderiza en los 7 destinos (tabla cerrada, sin literales de color).
- **F77** `evals/visual/` — verificación visual con la tabla §2 como ground truth (cerrado). Las 12 capturas reales confirman: 5 callouts semánticos con colores canónicos, 1 fix trivial aplicado (`<th scope="col">` en `_header.py:204`), 4 defectos asignados a fases futuras.

---

**Verificación al cierre de la fase:**

- `wc -l style-mapping.md` ≤ 400 líneas.
- §2 tabla 20 × 5 con 100 celdas no vacías.
- §3 tabla 20 filas de severidad → token.
- §4 20 iconos listados con justificación de los 3 casos compartidos.
- §5 tabla 9 colores Notion usados + 1 default + nota sobre pink/brown excluidos.
- §6 tabla 12 divergencias cerradas con justificación.
- §7 4 sub-casos (derived, external, nativas Obsidian, note default).
- §8 tabla 6×3 de migración de renderers.
- §9 7 wirings documentados.
