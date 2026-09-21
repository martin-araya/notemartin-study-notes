# Note IR — `references/04-authoring/ir-spec.md`

> Documento normativo de la Fase 14 del roadmap. Define el catálogo de 33 nodos (20 bloque + 13 inline) que el parser de NoteMark (F48) emite y que los renderers (F54-F60) consumen. Schema JSON formal en [`schemas/note-ir.schema.json`](../../../../schemas/note-ir.schema.json).
>
> Documentos complementarios: `skills/AGENT.md` §13 (forma canónica del nodo IR — este doc la formaliza), `references/04-authoring/notemark.md` §5 (cobertura NoteMark → IR), `references/04-authoring/notemark.ebnf` (las directivas NoteMark mapean 1-a-1 a nodos IR), `references/08-render/capability-matrix.md` (capacidades referenciadas en cada nodo), `references/02-source-model/spec.md` (anclas SDM que `source_refs` apunta).
>
> El IR **no se escribe a mano**: lo produce el parser (F48) consumiendo NoteMark. Lo modifica el agente solo indirectamente, editando NoteMark y re-corriendo el parser.

## §1 · Propósito y alcance

El Note IR es la **representación semántica intermedia** entre NoteMark (prosa del agente) y los dialectos de cada destino (Obsidian, Notion, AppFlowy, Markdown, HTML, PDF, Anki). Lo que el agente escribe en NoteMark se traduce a IR; los renderers traducen el IR al dialecto del destino. Esta indirección es la que mantiene la skill como skill y no como aplicación (ADR-0001 y ADR-0002).

## §2 · Cuándo se aplica

- L3 cuando el parser convierte NoteMark → IR (F48).
- L3 cuando un validador comprueba la fidelidad del IR antes de renderizar (F49).
- L4 cuando un renderer consume el IR para producir un dialecto (F54-F60).
- Cuando un script compara el IR contra otro IR para verificar equivalencia cross-target (F63).

**No se aplica a:** ingesta (L0 produce regiones, L1 produce SDM), ni a la redacción en prosa (el agente escribe NoteMark, nunca IR).

## §3 · Reglas duras (invariantes)

| ID | Invariante | Si se omite… |
|---|---|---|
| **IR-01** | El IR lo genera el parser; el agente nunca escribe IR a mano. | El agente introduce dialectos de plataforma en el IR; los renderers divergen. |
| **IR-02** | Ningún nombre de nodo menciona una plataforma (criterio 1). | Aparece "obsidian-callout" o "notion-toggle" en el contrato; un renderer se vuelve oráculo. |
| **IR-03** | Cada nodo declara `capability`, `allowed_children` y opcionalmente `attrs` específicos. | Un renderer no sabe si puede mostrar el nodo; degrada silenciosamente. |
| **IR-04** | Todo nodo fáctico lleva `source_refs` (puede ser array vacío si `derived: true`). | Trazabilidad rota; la auditoría de no-pérdida (F43) no puede verificar. |
| **IR-05** | `capability` es string libre mapeado al capability-matrix (F8). | El schema no duplica el enum; la validación cruzada queda en F118. |

## §4 · Catálogo de 33 nodos

Cada nodo: discriminador `node`, `attrs` específico + `capability` obligatoria, `children` opcional recursivo, `source_refs` array, flags `derived`/`external`/`layer`.

### 4.1 Bloque (20)

| Nodo | Atributos (sin contar `capability`) | Hijos permitidos | Capability (sugerida) |
|---|---|---|---|
| `section` | `level: 1-6` | cualquiera de bloque | `section-h{level}` |
| `paragraph` | — | inline | `paragraph` |
| `list` | `ordered: bool` | uno o más `list-item` (inline) o `paragraph` | `list` |
| `checklist` | — | `list-item` con flag done/todo | `checklist` |
| `table` | `headers: [string]`, `caption?` | celdas inline | `table` |
| `definition-list` | `entries: [{term, definition}]` | — | `definition-list` |
| `code` | `lang`, `text` | — | `code-block-fenced` |
| `console` | `lines: [string]` | — | `console-block` |
| `equation` | `latex`, `display: bool` | — | `equation-block` o `math-inline` |
| `figure` | `src`, `alt`, `caption?` | — | `figure` |
| `diagram` | `kind: "mermaid"\|"railroad"`, `text`, `alt?` | — | `diagram-mermaid-block` o `diagram-railroad` |
| `admonition` | `severity: 10 valores`, `title?` | bloque o inline | `callout` (10 subtipos en matrix) |
| `collapsible` | `title`, `default_open: bool` | bloque o inline | `collapsible` |
| `quote` | `cite?` | inline o bloque | `quote` |
| `columns` | `count: int ≥ 2` | hijos de bloque | `columns` |
| `divider` | — | — | `divider` |
| `property-block` | `name`, `value` (escalar/objeto/array) | — | `property-table` (rendido como tabla) |
| `question` | `prompt` | inline | `question` |
| `step` | `index: int ≥ 1` | bloque o inline | `step` |
| `parameter-table` | `columns: [string]` | celdas inline | `parameter-table` |

### 4.2 Inline (13)

| Nodo | Atributos | Hijos permitidos | Capability |
|---|---|---|---|
| `text` | `text: string` | — | `text` |
| `strong` | — | inline | `strong` |
| `em` | — | inline | `em` |
| `code-inline` | `text: string` | — | `code-inline` |
| `link-external` | `text`, `url` | — | `link-external` |
| `link-note` | `text`, `target: note_id` | — | `link-note` |
| `term-ref` | `text`, `term_id` | — | `link-term` |
| `source-ref` | `block_id` (hex 12), `source_hash` (hex 64) | — | `source-ref` |
| `math-inline` | `latex` | — | `math-inline` |
| `footnote-ref` | `ref_id`, `text?` | — | `footnote-ref` |
| `keyboard` | `text` | — | `keyboard` |
| `placeholder` | `text`, `default_value?` | — | `placeholder` |
| `deleted` | — | inline | `deleted` |

`allowed_children` exacto de cada nodo inline: solo inline (no bloque). Esto permite componer `[text + strong + text]` pero no `[text + section + text]`.

## §5 · Cobertura corpus ↔ IR

Sin nodos "varios" / "misc" / "other". Cada forma de contenido que aparece en el corpus tiene un nodo asignado:

| Forma de contenido en el corpus | Nodo IR | Notas |
|---|---|---|
| Párrafo de prosa | `paragraph` | Caso base; `text` inline para el contenido. |
| Encabezado `# / ## / ###` | `section` con `level: 1-6` | NoteMark heading → IR section. |
| Lista `- / 1.` | `list` con `ordered: false/true` | `list-item` modelado como paragraph hijo. |
| Checklist `- [ ]` / `- [x]` | `checklist` | Flag done en el list-item. |
| Tabla markdown `\| col \|` | `table` con `headers` y filas | `caption` opcional. |
| Definiciones `term: def` | `definition-list` con `entries` | Lista de pares. |
| Bloque de código `` ``` `` | `code` con `lang`, `text` | `lang=""` si desconocida. |
| Bloque de consola | `console` con `lines` | Una línea por prompt+respuesta. |
| Fórmula `$$ ... $$` | `equation` con `latex`, `display: true` | `display: false` para inline. |
| Imagen `![]()` | `figure` con `src`, `alt`, `caption?` | `src` es ruta en workdir. |
| Diagrama Mermaid ` ```mermaid ` | `diagram` con `kind: "mermaid"` | Railroad EBNF también. |
| Caja editorial "Note/Tip/Warning/…" | `admonition` con `severity` (10 valores) | Cada subtipo mapea a su capability. |
| Bloque plegable | `collapsible` con `title`, `default_open` | Hijos visibles cuando `default_open: true`. |
| Cita `>` | `quote` con `cite?` | Atribución opcional. |
| Distribución en columnas | `columns` con `count: 2` | Más usado para layouts 2-col. |
| Separador horizontal `---` | `divider` | Sin atributos. |
| Bloque de propiedad YAML | `property-block` con `name`, `value` | Renderizado como tabla. |
| Pregunta-respuesta | `question` con `prompt` | Respuesta en `children`. |
| Paso numerado | `step` con `index` | Hijos son el contenido del paso. |
| Tabla de parámetros | `parameter-table` con `columns` | Cabeceras canónicas: nombre/tipo/default/rango. |
| Texto plano | `text` | Atributo `text`. |
| **Negrita** | `strong` | Sin atributos extra. |
| *Cursiva* | `em` | Sin atributos extra. |
| `código inline` | `code-inline` con `text` | — |
| Enlace externo `[t](url)` | `link-external` con `text`, `url` | — |
| Enlace a nota `[[note:id]]` | `link-note` con `target` | `target` = note_id. |
| Término canónico `[[term:x]]` | `term-ref` con `term_id` | — |
| Cita a bloque SDM `{src:...}` | `source-ref` con `block_id`, `source_hash` | Conexión SDM → IR. |
| Fórmula inline `$x$` | `math-inline` con `latex` | — |
| Pie `[[fn:id]]` | `footnote-ref` con `ref_id` | — |
| Tecla `[[kbd:Ctrl+S]]` | `keyboard` con `text` | — |
| Placeholder `{{x}}` | `placeholder` con `text` | — |
| Tachado `~~x~~` | `deleted` | Sin atributos. |

Si en una iteración futura aparece una forma de contenido nueva que no mapea, se **añade** un nodo al catálogo y se reabre F14; no se introduce "varios".

## §6 · `source_refs` y procedencia

`source_refs` es un array de objetos `{ block_id, source_hash?, section_path? }` que apuntan al SDM (F13).

- Bloques nativos o con respaldo textual: `source_refs` no vacío.
- Bloques derivados (analogías, interpretaciones propias): `derived: true`, `source_refs` puede ser vacío si la analogía no se ata a un bloque específico.
- Bloques externos al documento: `external: true`, `source_refs` puede ser vacío.
- La combinación `derived: true && external: true` indica conocimiento completamente nuestro (analogía propia + sin respaldo). El renderer lo marca visiblemente.

## §7 · `capability`

`capability` es **string libre** dentro de `attrs`. Los valores canónicos viven en `references/08-render/capability-matrix.md` (F8) y se enumeran ahí — duplicarlos en el schema IR sería duplicación. Cada nodo del IR declara UNA capability (la que necesita para renderizarse). Si un renderer no soporta esa capability, degrada al `degraded` con tabla del capability-matrix (F53).

La validación cruzada IR ↔ capability-matrix queda diferida a F118.

## §8 · Recursión y `children`

`children` es un array de nodos (mismo esquema). Esto permite:
- `section` que contiene `paragraph` que contiene `text` y `strong`.
- `section` que contiene `admonition` que contiene `paragraph` que contiene `term-ref`.
- `admonition` que contiene `code` (ejemplo de código dentro de un callout).

`allowed_children` exacto por nodo está en la tabla §4. El script `validate_ir.py` lo verifica adicionalmente al schema.

## §9 · Ejemplo de IR mínimo

7 nodos. Ejemplo sobre `01-postgresql-chapter`:

```json
{
  "schema_version": "1.0.0",
  "note_id": "postgres-shared-buffers",
  "title": "PostgreSQL 16 — shared_buffers",
  "layer": "l2",
  "blocks": [
    {
      "node": "section",
      "attrs": { "level": 2, "capability": "section-h2" },
      "source_refs": [{ "block_id": "a8f4ce140580", "source_hash": "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657" }],
      "children": [
        {
          "node": "paragraph",
          "attrs": { "capability": "paragraph" },
          "source_refs": [{ "block_id": "a8f4ce140581", "source_hash": "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657" }],
          "children": [
            { "node": "text", "attrs": { "text": "PostgreSQL reserva ", "capability": "text" }, "source_refs": [] },
            { "node": "term-ref", "attrs": { "text": "shared_buffers", "term_id": "shared-buffers", "capability": "link-term" }, "source_refs": [] },
            { "node": "text", "attrs": { "text": " en memoria compartida.", "capability": "text" }, "source_refs": [] }
          ]
        }
      ]
    }
  ]
}
```

## §10 · Anti-patrones

- ~~`obsidian-callout` / `notion-toggle` / `appflowy-grid` como nombre de nodo~~ → usar `admonition` con `severity`.
- ~~Nodo genérico `misc` o `other` para contenido no categorizado~~ → clasificar el contenido en uno de los 33 nodos; si no encaja, añadir nodo y reabrir F14.
- ~~`attrs` con claves específicas de plataforma (`obsidianDatabase`, `notionPageId`)~~ → usar `capability` y dejar que el renderer decida.
- ~~`source_refs` con id no hex 12~~ → el schema lo rechaza.
- ~~IR escrito a mano por el agente~~ → el parser (F48) es la única vía de generación.
- ~~`capability` ausente en `attrs`~~ → el schema lo rechaza (requerido por nodo).
- ~~Mezcla de tipos incompatibles en `children` (e.g., `paragraph` con `section` hijo)~~ → el script `--validate` lo detecta contra la tabla §4.

## §11 · Cómo verificar + cambios permitidos

Comandos grepeables:

1. `python3 -c "import json; json.load(open('schemas/note-ir.schema.json'))"` → OK.
2. `wc -l references/04-authoring/ir-spec.md` ≤ 300.
3. `python3 scripts/util/validate_ir.py --validate evals/ir-sample/*.json` → 5 OK, exit 0.
4. Enum del schema tiene 33 nodos: `python3 -c "import json; print(len(json.load(open('schemas/note-ir.schema.json'))['\$defs']['nodeType']['enum']))"`.
5. Tabla §4 tiene 33 filas (un grep por nodo del catálogo).
6. `rg -i 'obsidian|notion|appflowy|anki' schemas/note-ir.schema.json references/04-authoring/ir-spec.md` → 0 en nombres de nodo/atributo (las menciones en §10 anti-patrones están tachadas).

**Cambios permitidos sin reabrir F14:**
- Añadir un campo opcional a `attrs` de un nodo existente (versión menor).
- Añadir un valor nuevo al enum de `admonition.severity` (versión menor).
- Añadir un valor nuevo al enum de `diagram.kind` (versión menor).

**Reabren F14:** añadir un nodo, cambiar el discriminador, mover `capability` fuera de `attrs`, eliminar un nodo, introducir platform-syntax.
