# Linking — Resolución de enlaces por destino

> Spec normativa para F61. Define la estrategia centralizada de resolución de `link-note` y `term-ref` para los 7 destinos (3 con backlinks nativos, 2 con sección generada, 1 con no-op, 1 con mención de página).

## Índice

1. [Propósito](#1-propósito) · 2. [Modelo de datos](#2-modelo-de-datos) · 3. [Algoritmo de resolución](#3-algoritmo-de-resolución) · 4. [Estrategia de dos pasadas](#4-estrategia-de-dos-pasadas) · 5. [Link debt registry](#5-link-debt-registry) · 6. [Backlinks por destino](#6-backlinks-por-destino) · 7. [Verificación](#7-verificación) · 8. [Cambios permitidos](#8-cambios-permitidos)

## 1. Propósito

F54-F60 cada renderer tenía su propia implementación inline de `resolve_links`, `collect_link_targets` y backlinks. Esto generaba ~30 líneas de duplicación por renderer × 6 archivos = ~180 líneas duplicadas, y además inconsistencias (cada renderer gestionaba `unresolved_targets[]` con formatos ligeramente diferentes).

F61 centraliza:

- **API compartida** en `scripts/render/_linking.py` para `collect_link_targets`, `build_link_graph`, `resolve_links` con semántica uniforme.
- **CLI orquestador** en `scripts/render/linking.py` que ejecuta el workflow de dos pasadas sobre todos los renderers.
- **Link debt registry** (`reports/link_debt.json`) que registra los enlaces no resueltos por destino.
- **Backlinks centralizados** — la sección `## Referenciado por` (Markdown) y `<aside class="backlinks">` (HTML/PDF) se generan desde el módulo compartido.

Criterios cubiertos:

- **C1:** cero enlaces rotos en los 3 destinos ricos (Obsidian, Notion API, Markdown).
- **C2:** la segunda pasada resuelve toda la deuda (`unresolved == []` post-pass-2).
- **C3:** destinos sin backlinks nativos (Markdown, HTML/PDF) reciben sección generada.

## 2. Modelo de datos

```python
@dataclass
class LinkTarget:
    target: str              # note_id o term_id
    kind: str                # "note" | "term"
    source_note_id: str
    node_path: str           # path IR del nodo que contiene el link
    text: Optional[str] = None  # texto a mostrar (alias)

@dataclass
class LinkReport:
    resolved: Dict[str, List[str]]   # {target: [source_note_ids]}
    unresolved: List[LinkTarget]

@dataclass
class LinkGraph:
    edges: Dict[str, Set[str]]       # {source_note_id: {target_ids}}
    reverse: Dict[str, Set[str]]     # {target_id: {source_note_ids}} (backlinks)
```

## 3. Algoritmo de resolución

```
1. collect_link_targets(ir_list) → List[LinkTarget]
   Recorre cada IR; extrae todos los `link-note` y `term-ref`.

2. build_link_graph(ir_list) → LinkGraph
   edges[source] = {targets}         (adyacencia forward)
   reverse[target] = {sources}       (adyacencia inversa para backlinks)

3. resolve_links(ir_list, note_ids, term_ids, placeholders=False)
   → Tuple[LinkReport, List[LinkTarget]]:
   - Para cada LinkTarget:
     - Si target ∈ note_ids (o term_ids): marca resolved.
     - Si no: marca unresolved (link debt).
   - Detecta ciclos vía DFS; emite warning pero no falla.
   - Si `placeholders=True`: añade los targets a un set retornado para que el caller los use como placeholders.

4. emit_backlinks_section(note_id, LinkGraph, base_url, format) → Optional[str]:
   Devuelve la sección de backlinks formateada según destino (`## Referenciado por` para Markdown, `<aside>` para HTML, `None` para nativos).
```

## 4. Estrategia de dos pasadas

### Pass 1 (CREATE)

- Cada renderer se invoca con `--pass 1`.
- El renderer emite placeholders consistentes en lugar de sintaxis final:
  - Markdown/Obsidian/Notion import: `[[target|alias]]` (placeholder legible).
  - HTML/PDF: `<a href="<note-id>.html" data-link-status="pending">alias</a>`.
  - Notion API: el renderer F55 ya hace 2-pass internamente; en `--pass 1` omite la mención y deja el alias en rich_text plano.
- Recolecta `{note_id → rendered_path}` por destino en un mapa.

### Pass 2 (LINK)

- `linking.py` invoca cada renderer con `--pass 2 --page-map <json>`.
- El renderer lee el mapa y reemplaza placeholders:
  - Markdown: `[[target|alias]]` se mantiene (Noción: ya es correcto para Obsidian). Para HTML/PDF: `<a href="<note-id>.html">alias</a>` con `data-link-status="resolved"`.
  - Notion API: `alias` → `mention.page` con `id = page_map[target]`. Si no está en page_map, conserva rich_text plano con `data-link-status="pending"`.
- Si el target no existe en el mapa (deuda), emite `data-link-status="unresolved"` y registra en `link_debt.json`.

### Flags nuevos en los renderers

- `--pass N` (1 o 2): indica fase. Default 1 (legacy compat).
- `--page-map <path>`: en pass 2, lee el mapa target→page_id/path/url.

## 5. Link debt registry

`reports/link_debt.json` por destino:

```json
{
  "generated_at": "2026-09-26T22:00:00Z",
  "destinations": {
    "obsidian": {
      "resolved_count": 12,
      "unresolved": [
        {
          "target": "note-xyz",
          "kind": "note",
          "source_note_id": "note-abc",
          "node_path": "0/3",
          "text": "referencia rota"
        }
      ]
    },
    "notion_api": {...},
    "markdown": {...},
    "html_pdf": {...}
  },
  "totals": {
    "resolved": 24,
    "unresolved": 3,
    "destinations_with_debt": 2
  }
}
```

Criterio 2 (segunda pasada resuelve toda la deuda): post-pass-2, `totals.unresolved == 0`. Si > 0, el renderer emite warning con exit code 2 (EXIT_WARN).

## 6. Backlinks por destino

Tabla cerrada (per capability-matrix §2.1 + contract §6 filas 7-10):

| Destino | Estrategia backlinks | Mecanismo |
|---|---|---|
| **Obsidian** | Nativo | Panel "Backlinks" de Obsidian detecta wikilinks `[[id]]` automáticamente. No se modifica el `.md`. |
| **Notion API** | Nativo | Backlinks nativos en cada página. |
| **Notion import** | Nativo | Backlinks nativos. |
| **AppFlowy** | Nativo | Backlinks nativos. |
| **Markdown** (F58) | **Generado** | Sección `## Referenciado por` al final de cada `.md`. Lista de wikilinks resueltos a `[<target>](<target>.md)`. |
| **HTML/PDF** (F59) | **Generado** | `<aside class="backlinks"><h2>Referenciado por</h2><ul>...</ul></aside>` antes del cierre de `<main>`. |
| **Flashcards** (F60) | no-op | Registrado en `degradations[]` con `evidence: "not_applicable"`, `content_intact: true` (sin sección generada). |

## 7. Verificación

Comandos shell para los 3 criterios:

```bash
# C1: cero enlaces rotos en 3 destinos ricos.
rg -c 'data-link-status="unresolved"' render/{obsidian,notion_api,markdown}/<note>.md render/notion_api/payloads/*.json 2>/dev/null
# esperado: 0 o vacío en todos.

# C2: deuda resuelta post-pass-2.
jq '.totals.unresolved' reports/link_debt.json
# esperado: 0

# C3: secciones generadas en destinos sin backlinks nativos.
rg -c '^## Referenciado por' render/markdown/<note>.md
rg -c '<aside class="backlinks"' render/html_pdf/<note>.html
# esperado: ≥ 1 en cada destino
```

## 8. Cambios permitidos sin reabrir

- Añadir nuevos destinos a la tabla §6 sin cambiar la API.
- Cambiar el formato del `link_debt.json` siempre que los 3 criterios se mantengan verificables.
- Cambiar placeholders en pass 1 (siempre que el renderer pueda distinguirlos).

## 9. Cambios que reabren

- Eliminar o renombrar `_linking.py` (rompe import en 6 renderers).
- Eliminar el flag `--pass` (rompe el workflow de 2 pasadas).
- Cambiar el formato de `reports/render-degradation.json` (rompe F53 contract).
