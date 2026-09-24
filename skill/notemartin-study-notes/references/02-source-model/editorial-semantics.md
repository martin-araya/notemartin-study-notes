# Semántica editorial de la fuente — reglas del Source Document Model

> Documento normativo de la **Fase 35** del roadmap. Cierra el reconocimiento de las 6 cajas editoriales canónicas (Nota, Precaución, Ejemplo, Consejo, Novedad, Obsoleto), las mapea a tipos de bloque del SDM, define las convenciones por vendor, y establece el canal de registro para convenciones nuevas.
>
> Documentos complementarios: `references/02-source-model/spec.md` (F13, contrato del SDM con tipos `note`/`warning`/`example`), `references/02-source-model/anchors.md` (F32), `references/02-source-model/provenance.md` (F34), `references/02-source-model/build-sdm.md` (F31, detección de regiones `editorial_note`).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F35`.

## §1 · Propósito y alcance

La **semántica editorial** de la fuente distingue las 6 cajas canónicas que aparecen en las documentaciones técnicas (Nota, Precaución, Ejemplo, Consejo, Novedad, Obsoleto) y las convierte en los bloques correctos del SDM. Mientras `spec.md` (F13) define el shape JSON de cada bloque, este doc define **qué caja es cuál, cuándo se considera Caja (no párrafo), cómo se mapea, y cómo registrar convenciones nuevas para ampliar el catálogo**.

**No es**: el render de la caja (eso es L4), ni la decisión de qué notas redactar con cada tipo (eso es L3), ni el formato frontmatter (eso es F47). Tampoco convierte avisos de código (`[WARN]` en stdout) en cajas: ese es el dominio del script de code_ocr (F25) que emite bloque `console` o `code`.

## §2 · Cuándo se aplica

| Capa | Lee este doc cuando… |
|---|---|
| L1 (F31 `build_sdm.py`) | Recibe una región `editorial_note` con `sub_kind="box"` y debe decidir `type` (entre `note`, `warning`, `example`) + `severity`. |
| L3 (agente NoteMark) | Decide qué tipo de `nota` redactar (ejemplo: `note.tip` vs `warning` vs `note.deprecated`) basándose en el bloque SDM. |
| L4 (renderer) | Lee `severity` para estilo visual (color/border). Honra `unknown_convention=true` con badge "⚠ convención desconocida". |
| Validador | El eval `evals/editorial-sample/run_eval.py` verifica que toda editorial_note.box termina como bloque no-`prose`. |

## §3 · Las 6 cajas canónicas y su mapeo

| Caja | Sinónimos aceptados (texto) | SDM `type` | SDM `severity` | `content` adicional |
|---|---|---|---|---|
| **Nota** | "Note:", "Notas:", "INFO:", "[INFO]", "ℹ", "INFO" | `note` | `info` (default) | `{text, severity}` |
| **Precaución** | "WARNING:", "AVISO:", "Caution", "[WARN]", "Danger", "Perigo" | `warning` | `caution` (opcional) | `{text, severity?}` |
| **Ejemplo** | "Example:", "Ejemplo:", "For example", "ex." | `example` | n/a | `{text}` |
| **Consejo** | "Tip:", "Consejo:", "Hint:", "Sugerencia" | `note` | `tip` | `{text, severity:"tip"}` |
| **Novedad** | "New in vN.N", "Novedad en vN.N", "🆕", "Since vN.N", "New" (en change log) | `note` | `novelty` | `{text, severity:"novelty", version_introduced?: <string>}` |
| **Obsoleto** | "Deprecated", "Obsoleto", "Obsolete", "Removed in vN.N", "Legacy", "Do not use" | `warning` (hard) **o** `note` (soft) | `deprecated` o `removed` | según severidad |

**Regla de Obsoleto**: si el texto contiene `Removed`, `Legacy`, o `Will be removed in next major`, el bloque se emite como `type=warning, severity=removed`. Si solo contiene `Deprecated`, `Obsolete`, `Renamed`, `Use X instead` (sin "removed"), emite como `type=note, severity=deprecated`. El criterio 2 exige que **ninguna "hard deprecation" termine como `note`** — siempre es `warning`.

**Mapeo textual (regex)**: las detecciones usan regex case-insensitive sobre el texto completo de la caja (no solo el icono) en este orden de prioridad:

| Patrón | Caja | Notas |
|---|---|---|
| `^(WARNING|AVISO|WARN|DANGER|CAUTION|PERIGO):\s*` | Precaución | |
| `^(DEPRECATED|OBSOLETE|OBSOLETO|RENAMED):\s*` (sin "removed") | Obsoleto (soft) | `type=note` |
| `^(REMOVED|LEGACY|WILL BE REMOVED):\s*` | Obsoleto (hard) | `type=warning` |
| `^(NOTE|NOTA|NOTAS|INFO|INFO:|ℹ):\s*` | Nota | |
| `^(TIP|CONSEJO|HINT|SUGERENCIA):\s*` | Consejo | |
| `^(EXAMPLE|EJEMPLO|FOR EXAMPLE|EX\.):\s*` | Ejemplo | |
| `^(NEW IN|YA DISPONIBLE|NEW|NOVEDAD EN|SINCE)\s+(v?\d+\.[\d.]+)?` | Novedad | extrae `version_introduced` |
| `^>\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]` | GitHub admonition | ver §4 |

Regex adicionales y heurísticas por vendor en §4.

## §4 · Convenciones por vendor built-in

Tabla cerrada; nuevos vendors se añaden al final del catálogo sin reabrir F35.

| Vendor / Doc set | Marcadores | Caja | Notas |
|---|---|---|---|
| PostgreSQL (docs) | `WARNING:` bold, leading; `Note:` bold, leading | Precaución, Nota | HTML hint o PDF bold del primer token. |
| Python (official docs) | `[WARN]` bold, bordered; `Tip:` en admonition admonition-warning | Precaución, Consejo | CSS class `admonition-warning`/`admonition-tip`. |
| Kubernetes docs | CSS class `admonition-note`/`admonition-warning`/`admonition-tip`/`admonition-caution` | por class | Mapeo 1:1; si class desconocida → unknown. |
| GitHub Markdown | `> [!NOTE]` / `[!TIP]` / `[!WARNING]` / `[!IMPORTANT]` / `[!CAUTION]` | por etiqueta | `> [!WARNING]` ⇒ `warning, severity:caution`. |
| AsciiDoc | `[NOTE]`, `[TIP]`, `[WARNING]`, `[IMPORTANT]`, `[CAUTION]` blocks (delimited `====` `....`) | correspondencia 1:1 | Mapeo exacto del nombre entre `[ ]`. |
| DOCX (Microsoft) | Estilo `Heading 5` + background amarillento + texto "Caution"; estilos `Subtle Emphasis` con "Warning" | Precaución (text-only) | Sin icon; depende del estilo detectado por F22. |
| Stripe / API docs | borde amarillo + label `WARNING` | Precaución | |
| Material for MkDocs | `!!! note`, `!!! warning`, `!!! tip`, `!!! danger` | por bloque | Markdown extended admonition. |
| Ruby / Rails | `<div class="warning">` o `<aside class="warning">` | Precaución | |
| Apple Developer | "**WARNING**" bold al inicio | Precaución | |

**Adición de vendor** (criterio 3): cuando un vendor no esté en este catálogo, el helper F31 emite `type=note, severity=info` con `unknown_convention=true` y registra la convención en `unknown_conventions[]` (§7). El agente L3 (o humano) puede entonces añadir el vendor al catálogo y emitir un PR. Cerrar la convención no reabre F35.

## §5 · Algoritmo de detección (invisible al usuario)

Orden estricto, evaluado en cada región `editorial_note` con `sub_kind="box"`:

1. **Vendor match**: si el `vendor` actual aparece en §4, aplicar las reglas de ese vendor (regex o class).
2. **Text regex**: si no hay match vendor, aplicar regex de §3 (`^(WARNING|...):\\s*`). Si matchea, asignar caja según tabla.
3. **Tipo de bloque fallido**: si ninguna regla aplica, **forzar `type=note, severity=info`** con `unknown_convention=true`. **Nunca** emitir `type=prose`.

**Invariante crítica (criterio 2)**: una región `editorial_note.box` **nunca** cae a `type=prose`. Esto es lo que el validador y el eval verifican. El helper `_classify_editorial_box` de F31 implementa este invariante.

## §6 · Severidad por tipo

| Tipo | `severity` permitidos | Comportamiento |
|---|---|---|
| `note` | `info` (default), `tip`, `novelty`, `deprecated` | Si ausente, `severity="info"`. Si `severity="novelty"`, el campo opcional `content.version_introduced` puede contener `"17"`, `"v2.5"`, etc. |
| `warning` | `caution`, `deprecated`, `removed` (o ausente) | Default ausente = "warning plain"; si `severity="deprecated"` u `"removed"` ⇒ texto explícito de migración. |
| `example` | n/a | Sin severidad; el bloque es ejemplo por definición. |
| `syntax-diagram` | n/a | Sin severidad. |

**Reglas duras**:

1. `note` con `severity=novelty` siempre debe ir acompañado de `version_introduced?:string` (opcional, vacío permitido). El validador detecta si está ausente sin causar fallo (es opcional).
2. `note` con `severity=deprecated` ⇒ el texto debería incluir un marcador de reemplazo ("Use X instead"). Detectado por regex (no fallido).
3. `warning` con `severity=removed` ⇒ el texto debería incluir la versión de removal. Detectado por regex.

## §7 · Registro de convenciones desconocidas

Cuando el helper no encuentra match (vendor × texto), registra en `build_sdm_summary.json::unknown_conventions[]`:

```json
{
  "vendor": "Acme Inc",
  "product": "Internal Wiki",
  "instance_kind": "editorial_note.box",
  "text_snippet": "<= 80 chars del texto de la caja",
  "guessed_type": "note",
  "guessed_severity": "info",
  "reason": "no_vendor_match_no_text_regex_match"
}
```

El campo `reason` toma uno de los 3 valores:
- `no_vendor_match` (vendor no en §4)
- `no_text_regex_match` (vendor conocido pero texto no matchea ninguna regla)
- `no_vendor_match_no_text_regex_match` (ambos negativos)

**Política**: si una convención aparece ≥ 3 veces en `unknown_conventions`, el agente L3 debe proponerla para añadirse a §4 (PR al spec). Cerrar la convención **no reabre F35**.

## §8 · Ejemplos de flujo

**Ejemplo 1**: `vendor="PostgreSQL Global Development Group"`, región `editorial_note.box`, texto "WARNING: this query may lock the table for hours." → vendor match + regex `WARNING:` ⇒ `type=warning, severity=caution`.

**Ejemplo 2**: `vendor="GitHub"`, región `editorial_note.box`, texto "> [!TIP]\n> Use --depth 0 to skip submodules." → vendor match + admonition rule ⇒ `type=note, severity=tip`.

**Ejemplo 3**: `vendor="KernelBookPublisher"`, región `editorial_note.box`, texto "Note: this section is informational." → no vendor match + regex `Note:` ⇒ `type=note, severity=info`.

**Ejemplo 4**: `vendor="CustomMadeSoftware"`, región `editorial_note.box`, texto "❖ Important: review the migration guide." → no vendor match + regex no matchea → `type=note, severity=info, unknown_convention=true`; registra en `unknown_conventions[]`.

## §9 · Anti-patrones

- Tratar `[WARN]` en código como caja editorial. Las líneas de código con `[WARN]` son `type=code` o `type=console`, nunca `type=warning`. La caja `[WARN]` en un párrafo descriptivo sí es `warning`.
- Inventar vendor en el spec sin haber visto ≥ 3 ejemplos de la convención en el corpus.
- Convertir un "Heading 3: Caution" en un `heading` con `severity:caution` (severity no es parte del shape `heading`).
- Marcar como `warning` cualquier texto que contenga la palabra "warning" sin heurística de vendor o regex (§5).
- Eliminar la fila `unknown_conventions[]` del summary — esa es la única señal para ampliar el catálogo.
- Emitir `severity=removed` con `type=note` (debe ser `type=warning`).

## §10 · Verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l references/02-source-model/editorial-semantics.md                 # ≤ 230
rg -c '^## §' references/02-source-model/editorial-semantics.md          # 11 secciones

# 2. Los 3 criterios via eval.
python3 evals/editorial-sample/run_eval.py                              # PASS los 3 criterios

# 3. Sin regresión.
python3 scripts/util/validate_sdm.py --validate evals/sdm-sample/*.json # PASS los 15 F13
python3 evals/build-sdm-sample/run_eval.py                               # PASS los 3 F31
python3 evals/anchors-sample/run_eval.py                                 # PASS los 3 F32
python3 evals/assets-sample/run_eval.py                                  # PASS los 3 F33
python3 evals/provenance-sample/run_eval.py                              # PASS los 3 F34
```

## §11 · Cambios permitidos · Cambios que reabren F35

**Permitidos (sin reabrir):**

- Añadir un vendor al §4 (incluso con 1 sola regla).
- Añadir una nueva regex en §3 (con ejemplo en `## Examples` para que no falle el eval).
- Renombrar convención (p.ej. "Stripe" → "StripeAPI"). Las reglas internas siguen siendo las mismas.

**Reabren F35:**

- Eliminar `severity` de cualquier tipo de bloque del SDM (romper los 16 dorados que usan `severity: info/tip`).
- Añadir un block type nuevo (e.g. `caveat`).
- Cambiar la tabla §3 de las 6 cajas (añadir/eliminar una caja canónica).
- Cambiar la invariante "ningún editorial_note.box cae a prose".
- Cambiar el shape de `unknown_conventions[]`.

### Documentos que NO reabren F35 al modificarse

- `schemas/sdm.schema.json` (F13): los cambios aditivos (severity enum extendido, fields opcionales) son compatibles con F35. Cambios mayores reabren F13, no F35.
- `scripts/ingest/build_sdm.py` (F31): la edición menor del helper es aditiva. Cambios en la pipeline que no afecten `editorial_note.box` son transparentes.
- Eval `evals/editorial-sample/`: añadir casos por vendor no reabre.
