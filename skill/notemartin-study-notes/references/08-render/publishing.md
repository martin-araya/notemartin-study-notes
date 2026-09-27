# Publishing — Publicación idempotente

> Spec normativa para F62. Define el workflow de publicación idempotente con detección de ediciones manuales, preservación de comentarios y publicación parcial.

## Índice

1. [Propósito](#1-propósito) · 2. [Manifiesto de IDs remotos](#2-manifiesto-de-ids-remotos) · 3. [Algoritmo de publicación](#3-algoritmo-de-publicación) · 4. [Detección de ediciones manuales](#4-detección-de-ediciones-manuales) · 5. [Preservación de comentarios](#5-preservación-de-comentarios) · 6. [CLI workflows](#6-cli-workflows) · 7. [Reportes](#7-reportes) · 8. [Verificación](#8-verificación) · 9. [Cambios permitidos](#9-cambios-permitidos)

## 1. Propósito

F54-F61 producen artifacts locales (`render/<destino>/<note-id>.{md,html}`). F62 los publica a destinos remotos:

- **Conservando páginas existentes** — republicar no crea duplicados; PATCH in-place.
- **Preservando comentarios del usuario** — los comentarios y bloques añadidos a mano por el lector se mantienen intactos.
- **Detectando ediciones manuales** — si el usuario editó la página remota, el publisher bloquea la actualización hasta confirmación explícita.
- **Publicando parcialmente** — solo se tocan las notas cuyo `ir_sha256` cambió respecto al último publish; las demás se saltan.

Criterios cubiertos:

- **C1**: republicar 20 notas actualiza 20 páginas, no crea 20.
- **C2**: una página editada a mano no se sobrescribe sin confirmación.
- **C3**: la publicación parcial solo toca lo cambiado.

## 2. Manifiesto de IDs remotos

Archivo: `<out-dir>/.publish/manifest.json`. Estructura:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-09-26T22:00:00Z",
  "destinations": {
    "obsidian": {
      "<note_id>": {
        "remote_path": "notes/<note-id>.md",
        "remote_hash": "<sha256 hex>",
        "ir_sha256": "<sha256 hex>",
        "last_published_at": "2026-09-26T22:00:00Z",
        "edited_by_hand": false
      }
    },
    "notion_api": {
      "<note_id>": {
        "page_id": "...",
        "remote_hash": "<ISO 8601 last_edited_time>",
        "ir_sha256": "<sha256 hex>",
        "last_published_at": "...",
        "edited_by_hand": false
      }
    },
    "markdown":    {"<note_id>": {...}},
    "html_pdf":    {"<note_id>": {...}},
    "notion_md":   {"<note_id>": {...}},
    "appflowy":    {"<note_id>": {...}}
  }
}
```

Ciclo de vida:

- El manifest se carga al inicio de cada operación `publish` o `plan`.
- Se actualiza atómicamente (atomic_write_json) tras cada CREATE/UPDATE exitoso.
- Backup automático `manifest.json.bak` antes de cada save.
- Validación al cargar: si el `schema_version` es desconocido o el JSON está malformado, falla con error claro.

## 3. Algoritmo de publicación

```
para cada (note_id, destination) en el workdir:
  1. cargar artefacto renderizado desde render/<dest>/<note-id>.{md,html}
  2. leer IR; computar ir_sha256_actual
  3. buscar entry en manifest[dest][note_id]
     a) no existe:
        → CREATE
        → POST /pages (Notion API) o escribir archivo nuevo (file-based)
        → registrar entry con ir_sha256_actual, edited_by_hand=False
     b) existe:
        comparar ir_sha256_actual con manifest[note_id].ir_sha256:
        - iguales → SKIP (sin cambios)
        - diferentes:
          fetch remote metadata → detectar edited_by_hand (§4)
          si edited_by_hand y no --confirm-overwrite:
            → BLOCK (warning en report; exit WARN; manifest sin tocar)
          else:
            → UPDATE
            → fetch children remotos; preservar user-added blocks (§5)
            → PATCH (Notion API) o reescribir (file-based)
            → actualizar entry: ir_sha256_actual, remote_hash, last_published_at
```

Para Notion API específicamente:

- **CREATE**: `POST /v1/pages` con `properties` + `children[:100]`; chunks adicionales via `PATCH /v1/blocks/{id}/children` (F55 ya implementa esto).
- **UPDATE**: `DELETE` cada child block existente (excepto user-added); `PATCH /v1/blocks/{id}/children` con los nuevos children; `PATCH /v1/pages/{id}` con properties actualizadas.
- **Backoff**: reintentos con backoff 5s/30s/120s/600s ante 429/5xx (F55 ya tiene esto).

Para destinos file-based (Markdown, HTML/PDF, Notion import, AppFlowy, Obsidian):

- **CREATE**: escribir archivo nuevo en `<remote_path>`.
- **UPDATE**: extraer bloque `<!-- user-content-start -->...<!-- user-content-end -->` del archivo remoto; combinar con contenido generado; reescribir preservando el bloque del usuario.
- **SKIP**: si `ir_sha256` no cambió, no tocar el archivo.

## 4. Detección de ediciones manuales

**File-based (Markdown, HTML/PDF, Notion import, AppFlowy, Obsidian):**

```python
remote_hash = sha256(remote_file_content)
if remote_hash != manifest_entry.remote_hash:
    edited_by_hand = True
```

El `remote_hash` registrado en el manifest es el hash del archivo TAL COMO el renderer lo dejó en el último publish. Si el contenido actual difiere, alguien lo modificó.

**Notion API:**

```python
remote_meta = notion.pages.retrieve(page_id)
remote_last_edited = remote_meta["last_edited_time"]
manifest_published_at = manifest_entry.last_published_at
if remote_last_edited > manifest_published_at + 1s:  # 1s tolerance
    edited_by_hand = True
```

Notion API actualiza `last_edited_time` en cualquier modificación, incluyendo la del publisher. Pero el publisher también actualiza `manifest.last_published_at` después del publish, así que la próxima comparación será estable.

**Threshold de 1s** para tolerar clock skew entre el cliente y el servidor de Notion.

**Marcado manual** — `publishing.py mark-edited <note_id> --destination <dest>` permite al usuario marcar una página como editada a mano sin verificación de hash (útil para casos donde el hash difiere por razones benignas, p.ej. reordenamiento de bloques por el renderer).

## 5. Preservación de comentarios

**Notion API:** los child blocks de una página tienen un campo `caption` opcional. El publisher marca los bloques añadidos por el usuario con `caption: [{"type": "text", "text": {"content": "user-added"}}]`. Antes del DELETE-all:

```python
for child in remote_children:
    if "user-added" in (caption_text(child) or ""):
        preserved_blocks.append(child)
    else:
        delete(child)
```

Los bloques preservados se re-aplican al inicio del nuevo children.

**File-based (Markdown, HTML/PDF):** el publisher preserva el bloque entre markers:

```markdown
... (contenido del renderer) ...

<!-- user-content-start -->
... (texto del usuario, preservado entre publishes) ...
<!-- user-content-end -->
```

Si el archivo remoto tiene el bloque `user-content`, se extrae, se re-inserta después del nuevo contenido generado, y se reescribe el archivo. Si el archivo no tiene ese bloque, se ignora.

**Inicialización del bloque:** el publisher crea el bloque `<!-- user-content-start -->\n<!-- user-content-end -->` automáticamente la primera vez que publica una nota. Comentarios posteriores del usuario deben ir entre los markers.

## 6. CLI workflows

`scripts/publish/publishing.py` con sub-comandos:

### `publishing.py plan --ir <path> --out-dir <dir> --destinations <csv>`

Dry-run. Muestra qué se crearía, actualizaría, saltaría, bloquearía. Sin tocar el manifest.

### `publishing.py publish --ir <path> --out-dir <dir> --destinations <csv> [--confirm-overwrite] [--force-manual-keep-comments] [--notion-token <token>]`

Ejecuta la publicación. Flags:

- `--confirm-overwrite`: sobrescribe páginas con `edited_by_hand = true`. Sin este flag, se bloquean.
- `--force-manual-keep-comments`: incluso con edited_by_hand, preserva los comentarios del usuario (sin este flag, se sobreescriben junto con el resto).

Códigos de salida: `0` OK · `1` error fatal · `2` OK con bloqueos (páginas editadas a mano).

### `publishing.py status --out-dir <dir>`

Imprime el manifest en formato legible: total por destino, lista de notas con `edited_by_hand=true`, última publicación.

### `publishing.py mark-edited <note_id> --destination <dest> --out-dir <dir>`

Marca manualmente una nota como editada a mano. El próximo `publish` la bloqueará (a menos que `--confirm-overwrite`).

## 7. Reportes

`reports/publish-report.json`:

```json
{
  "schema_version": "1.0.0",
  "generated_at": "...",
  "destinations": ["obsidian", "markdown"],
  "summary": {
    "created": 5,
    "updated": 12,
    "skipped": 3,
    "blocked": 1,
    "errors": 0
  },
  "created": [{"note_id": "...", "destination": "...", "remote_id": "..."}],
  "updated": [{"note_id": "...", "destination": "...", "diff_summary": "..."}],
  "skipped": [{"note_id": "...", "destination": "...", "reason": "ir_sha256 unchanged"}],
  "blocked": [{"note_id": "...", "destination": "...", "reason": "edited_by_hand"}],
  "errors": []
}
```

`reports/publish-report.md`: tabla legible con los mismos datos.

## 8. Verificación

```bash
# C1: republicar 20 notas actualiza 20, no crea.
python3 scripts/publish/publishing.py publish --ir ir-20-notes --out-dir w1 \
                                            --destinations markdown
python3 scripts/publish/publishing.py publish --ir ir-20-notes --out-dir w1 \
                                            --destinations markdown
# esperado: report 1ra corrida: created=20, updated=0
#           report 2da corrida: created=0, updated=0 (todas skipped por ir_sha256 igual)

# C2: editada a mano bloqueada.
echo "manual edit" >> w1/render/markdown/<note>.md
python3 scripts/publish/publishing.py publish --ir ir-20-notes --out-dir w1 \
                                            --destinations markdown
# esperado: blocked=1; exit WARN
python3 scripts/publish/publishing.py publish --ir ir-20-notes --out-dir w1 \
                                            --destinations markdown \
                                            --confirm-overwrite
# esperado: updated=1; exit 0

# C3: publicación parcial.
# 20 notas; cambiar 1 IR.
python3 scripts/publish/publishing.py publish --ir ir-20-notes-v2 --out-dir w1 \
                                            --destinations markdown
# esperado: created=0, updated=1, skipped=19
```

## 9. Cambios permitidos sin reabrir

- Añadir nuevos sub-comandos al CLI (`rollback`, `revert`, `diff`).
- Cambiar el formato del reporte siempre que los 3 criterios sean verificables.
- Añadir nuevas propiedades al `PublishEntry` (con default).

## 10. Cambios que reabren

- Eliminar el flag `--confirm-overwrite` (rompe C2).
- Eliminar la detección de `edited_by_hand` (rompe C2).
- Eliminar el `ir_sha256` del manifest (rompe C3).
- Cambiar el formato del manifest sin versionado (rompe retro-compat).
