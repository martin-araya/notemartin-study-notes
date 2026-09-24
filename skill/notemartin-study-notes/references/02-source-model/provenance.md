# Procedencia y versión — reglas del Source Document Model

> Documento normativo de la **Fase 34** del roadmap. Define cómo distinguir los metadatos editoriales leídos de los inferidos, cómo se propagan al cuerpo de la nota en L3, y la política del campo `version` (criterio 3).
>
> Documentos complementarios: `references/02-source-model/spec.md` (F13, shape del `source` en el SDM), `references/02-source-model/anchors.md` (F32, persistencia), `references/02-source-model/build-sdm.md` (F31, mecánica de ensamblado y emisión de `source_provenance`), `references/04-authoring/properties.md` (F47, esquema del frontmatter NoteMark — referencia downstream).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F34`.

## §1 · Propósito y alcance

La **procedencia** de un SDM responde, para cada metadato editorial del `source`, a dos preguntas: **(a) ¿de dónde vino?** y **(b) ¿lo escribió alguien o lo dedujo un script?** Mientras `spec.md` (F13) define el shape JSON de `source`, este doc define cómo se **etiqueta el origen de cada campo** y cómo viaja esa etiqueta al cuerpo de la nota (L3) y al render (L4). El criterio 2 ("los valores inferidos son distinguibles de los leídos") es el corazón de F34.

**No es**: el contrato JSON Schema del `source` (eso es `spec.md` §7), ni el script de extracción (eso es F31), ni el formato del frontmatter NoteMark (eso es F47).

## §2 · Cuándo se aplica

| Capa | Lee este doc cuando… |
|---|---|
| L1 (F31 `build_sdm.py`) | Emite `source_provenance` por cada campo del `source` tras la ingesta. |
| L1 (F34 `provenance.py`) | Valida cada SDM antes de pasar a L2: ¿los inferidos están marcados? ¿algún `version` ausente en documentación? |
| L3 (agente, NoteMark) | Antes de redactar la nota, lee `source` + `source_provenance` para poblar el frontmatter. |
| L4 (renderer) | Honra la marca `inferred`: aplica estilo visual distinto (e.g. badge `~inferida~`) o nota editorial. |
| F15 (Coverage Ledger) | Hereda `source_id` + `source_hash` para que la trazabilidad siga al bloque tras renumeraciones. |

## §3 · Los doce campos contractuales del `source`

El schema define doce campos (per `spec.md` §7). F34 los divide en tres grupos según cómo se propaga y qué pasa cuando están ausentes:

| Grupo | Campos | Required | Nullable | Notas |
|---|---|---|---|---|
| Identidad | `id`, `hash`, `url`, `format` | sí | no | Marca el documento de forma única. Nunca se infieren: si faltan, F31 aborta. |
| Identificación editorial | `vendor`, `product`, `language` | sí | no | Identifica al publicador y al producto. `language` por BCP-47. |
| Versionado / edición | `version`, `edition`, `isbn`, `authors`, `date` | no (criterio 3) | sí | El grupo "información opcional". El criterio 3 exige que **el campo exista** en la nota, aunque su valor sea `null` con marca `inferred`. |

`vendor`, `product` y `version` viajan siempre al frontmatter de la nota (criterio 1). Los demás son opcionales pero, si están en el `source`, también se propagan.

## §4 · Taxonomía de métodos — el corazón del criterio 2

Cada campo lleva un `method` ∈ {taxonomía cerrada} y un `confidence` ∈ [0, 1]. La pareja `(method, confidence)` se registra en `source_provenance[<field>]`. Las dos condiciones siguientes son contractuales:

- `method:"read"` ⇒ `confidence == 1.0`.
- `method:"inferred" | "url_regex" | "cover_or_header" | "web_docs_metadata" | "triage_metadata"` ⇒ `confidence < 1.0`.

| `method` | Significado | `confidence` por defecto | Origen típico |
|---|---|---|---|
| `read` | El valor fue provisto explícitamente por el usuario (CLI `--source-meta` YAML) o por una fuente autoritativa (manifiesto EPUB/OPF). | 1.0 | humano, OPF, package.json |
| `web_docs_metadata` | Detectado por `web_docs.py` (F29) parseando `<meta name="product">`, `<meta name="version">` o regex sobre la URL. | 0.9 | HTML docs |
| `triage_metadata` | Heredado de `triage.json` (F17) cuando la heurística rellenó campos como `hash`. | 1.0 | F17 |
| `cover_or_header` | Detectado en cover/header/footer de la fuente impresa. | 0.7 | PDF/DOCX |
| `url_regex` | Extraído por regex sobre la URL canónica (`v\d+\.\d+`, `/doc/v(.*)$`). | 0.8 | URL |
| `inferred` | Deducido por heurística sin una fuente explícita (e.g. "1st Edition" en title → `version="1st"`). | 0.5 | heurística |
| `default` | Schema default cuando no se pudo determinar nada más (`vendor:""`, `product:""`, `language:"en"`). | 0.0 | default |
| `absent` | No se pudo determinar; el valor es `null`. | 0.0 | n/a |

`read` y `absent` son los dos extremos del espectro: **leído con certeza vs ausente con declaración explícita**. Cualquier otra combinación `(method, value)` es **intermedia y visible** — el criterio 2 descansa en esa visibilidad.

## §5 · Bloque `source_provenance` (shape)

```json
{
  "source": {
    "id": "01-postgresql-chapter",
    "hash": "a8f4ce…",
    "vendor": "PostgreSQL Global Development Group",
    "product": "PostgreSQL 16",
    "version": "16",
    "url": "https://…",
    "language": "en",
    "format": "html",
    "date": "2026-09-21"
  },
  "source_provenance": {
    "id":       {"method": "read",              "value": "01-postgresql-chapter", "confidence": 1.0},
    "hash":     {"method": "triage_metadata",   "value": "a8f4ce…",              "confidence": 1.0},
    "vendor":   {"method": "web_docs_metadata", "value": "PostgreSQL…",           "confidence": 0.9},
    "product":  {"method": "web_docs_metadata", "value": "PostgreSQL 16",         "confidence": 0.9},
    "version":  {"method": "url_regex",         "value": "16",                    "confidence": 0.8, "reason": "url:/docs/16/sql.html:(\\d+)"},
    "edition":  {"method": "default",           "value": null,                    "confidence": 0.0},
    "isbn":     {"method": "absent",            "value": null,                    "confidence": 0.0, "reason": "no_isbn_in_source"},
    "authors":  {"method": "default",           "value": [],                      "confidence": 0.0},
    "url":      {"method": "read",              "value": "https://…",            "confidence": 1.0},
    "language": {"method": "default",           "value": "en",                    "confidence": 0.0},
    "date":     {"method": "inferred",          "value": "2026-09-21",            "confidence": 0.5, "reason": "front_matter_marker"}
  }
}
```

**Regla de bloque**: `source_provenance` es opcional. Si está presente, cubre al menos un campo. Si está ausente, el validador asume `method:"read"` para todos los campos no nulos.

**Reglas duras**:

1. Para cada `field` en `source_provenance`, `value` debe coincidir con `source[<field>]` (o ambos `null`). Verificable trivialmente.
2. `method == "read"` ⇒ `confidence == 1.0`. Mismatched ⇒ `InconsistentRead`.
3. `method ∈ {inferred, url_regex, cover_or_header, web_docs_metadata, triage_metadata}` ⇒ `confidence < 1.0`. Mismatched ⇒ `ConfidentInference`.
4. `method == "default"` o `absent"` ⇒ `value` puede ser `null` o el default del schema.
5. `reason` (opcional) documenta **cómo** se obtuvo — texto libre, idealmente una pista corta (`"url:/docs/16"`, `"cover_page:line_3"`, `"<meta name=version>"`).

## §6 · Política de `version` (criterio 3)

El campo `version` es el único que el criterio 3 trata de forma estricta. La regla de tres pasos:

1. **El campo siempre existe** en el SDM y en el frontmatter NoteMark. Si no se pudo determinar, `version: null` con `method: "absent"` y `reason` no vacío.
2. **Sin `--require-version`**: el validador emite warning (exit 2) cuando `vendor + product` no triviales Y `version` ausente. El agente L3 propaga `version: null` y un human override posible.
3. **Con `--require-version`**: el validador exit 1. Útil como gate de release ("no se publica documentación sin versión").

**Definición de "no trivial"**: `vendor` y `product` no son `""` ni `"Unknown"`. Si ambos son defaults, la fuente no es "documentación" en el sentido que el criterio 3 exige (un whitepaper sin vendor no es documentación-de-producto).

**Tabla de fuentes vs comportamiento**:

| Tipo de fuente | Política |
|---|---|
| Documentación de producto (vendor+product presentes) | `version` obligatorio (advertencia o gate con `--require-version`) |
| Blog / whitepaper sin vendor | `version` puede ser `null` sin warning |
| RFC / estándar | `version` típicamente en el id (e.g. "RFC 7231") → propagar como `version` |
| Paper académico | `version` puede ser `null` o `"vN"` (preprint) |
| Foro / thread | `version` no aplica; omitir sin warning |

## §7 · Propagación al L3

El agente que redacta notas en NoteMark consulta `source` + `source_provenance` antes de poblar el frontmatter. Las reglas:

1. Los siguientes campos **deben** derivarse del SDM (criterio 1, "sin intervención manual"): `source_id`, `source_hash`, `vendor`, `product`, `version`.
2. Si un campo es `method:"read"`, se copia verbatim al frontmatter **sin marca** (es lectura).
3. Si un campo es `method` distinto de `"read"`, se copia al frontmatter con `inferred: true` + `reason` corto (≤ 32 chars).
4. Si un campo es `method:"absent"`, el frontmatter lleva `version: null` + `inferred: true` + `reason:"see_provenance"`. El agente decide si rellenar manualmente o dejarlo `null`.
5. Si un campo no está en `source_provenance`, se asume `method:"read"` (compatibilidad con SDMs anteriores a F34).

**Frontmatter mínimo**:

```yaml
---
source_id: "01-postgresql-chapter"
source_hash: "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657"
vendor: "PostgreSQL Global Development Group"
product: "PostgreSQL 16"
version: "16"            # o null + inferred:true
---
```

## §8 · Inferencia automática (heurísticas documentadas)

F34 **no implementa** heurísticas; las documenta para futuras versiones. Lista cerrada:

| Patrón | Heurística | `confidence` |
|---|---|---|
| `v\d+(\.\d+)*` en URL path | `url_regex` | 0.8 |
| `<meta name="version">` | `web_docs_metadata` | 0.9 |
| `<meta name="product">` | `web_docs_metadata` | 0.9 |
| Cover/header "Edition N" | `cover_or_header` | 0.7 |
| `"1st/2nd/3rd Edition"` en title | `inferred` | 0.5 |
| "Version X.Y" en front matter / copyright | `cover_or_header` | 0.7 |
| ISBN en página legal | `read` | 1.0 |

Si F35+ (semántica editorial) o F38 (heurísticas morfológicas) deciden implementar estas reglas, deben respetar la tabla de `confidence` y registrar `reason` con la pista concreta.

## §9 · Anti-patrones

- Inventar versión cuando la fuente no la trae (viola fidelidad, INV-03).
- Marcar `method:"read"` para un valor que realmente fue inferido (rompe el criterio 2).
- Marcar `confidence: 1.0` para `method:"inferred"` (inconsistencia mecánica).
- Propagar `version` al frontmatter sin su `inferred` (cuando aplique) — el render no puede estilizar la inferencia.
- Usar `source_provenance` con campos que no existen en `source` (desincronización; el validador lo detecta).
- Omitir `source_provenance` por completo cuando el SDM se generó con fallback heurístico (F31 debe poblarlo siempre que el método no sea `read`).

## §10 · Verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l references/02-source-model/provenance.md                         # ≤ 230
rg -c '^## §' references/02-source-model/provenance.md                  # 11 secciones

# 2. Validador: 3/3 criterios PASS sobre los 3 fixtures.
python3 scripts/validate/provenance.py --sdm \
    evals/provenance-sample/build/source-full/sdm.json                 # OK (read)
python3 scripts/validate/provenance.py --sdm \
    evals/provenance-sample/build/source-version-absent/sdm.json \
    --require-version                                                  # exit 1 (gate)
python3 evals/provenance-sample/run_eval.py                             # PASS los 3 criterios

# 3. Sin regresión.
python3 evals/build-sdm-sample/run_eval.py                              # PASS los 3 F31
python3 evals/anchors-sample/run_eval.py                                # PASS los 3 F32
python3 evals/assets-sample/run_eval.py                                 # PASS los 3 F33
python3 scripts/util/validate_sdm.py --validate evals/sdm-sample/*.json # PASS los 15 F13
```

## §11 · Cambios permitidos sin reabrir F34 · Cambios que reabren F34

**Permitidos (sin reabrir):**

- Añadir valores a la taxonomía `method` (nuevas heurísticas) — siempre que conserven las reglas de §4.
- Hacer `--require-version` el comportamiento por defecto del validador.
- Añadir `source_provenance` para campos no contractuales (p.ej. `cover_image_hash`).

**Reabren F34:**

- Romper la regla `(method:"read") ⇒ confidence == 1.0`.
- Romper la regla `confidence < 1.0` para métodos distintos de `read` y `triage_metadata`.
- Eliminar el bloque `source_provenance` (rompe distinguibilidad).
- Mover `version` a required-del-schema (cambia contrato schema, no reabre F34 — reabre F13).
- Cambiar la propagación del frontmatter sin consultar `source_provenance`.

### Documentos que NO reabren F34 al modificarse

- `schemas/sdm.schema.json` (F13): F34 se integra como bloque opcional; cambios al schema existentes no rompen la taxonomía de métodos.
- `scripts/ingest/build_sdm.py` (F31): populate `source_provenance` es una mejora aditiva. Cambios en algoritmos que no añadan campos a `source_provenance` son transparentes.
