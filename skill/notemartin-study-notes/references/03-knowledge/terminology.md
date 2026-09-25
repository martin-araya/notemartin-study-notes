# Terminología y glosario acumulativo — `references/03-knowledge/terminology.md`

> Documento normativo de la **Fase 40** del roadmap. Define el modelo de datos y las reglas del glosario acumulativo que el agente mantiene a lo largo de los capítulos de una obra, con manejo de aliases (EN/ES, siglas, plurales, variantes), resolución de colisiones entre dominios, detección de redefiniciones y normalización retroactiva.
>
> Documentos complementarios: `references/03-knowledge/concept-graph.md` (F39), `references/03-knowledge/ledger.md` (F15), `references/03-knowledge/information-units.md` (F37), `schemas/glossary.schema.json` (este doc), `architecture.md` §4 (`knowledge/glossary.json`), `docs/adr/ADR-0004-glossary-model.md` (justificación de las decisiones cerradas).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F40`. Lo lee el agente en L2 al construir y mantener el glosario; lo consume F44 (note-plan) para normalizar términos; F104 (rutas de lectura) para sinónimos; F43 (auditoría) para detectar redefiniciones; F118 (evals) para verificar los criterios.

## §1 · Propósito y alcance

El glosario acumulativo es el **registro canónico de términos** que el agente mantiene a lo largo de los capítulos de una obra. Cada término tiene una definición, aliases en diferentes formas (inglés, español, siglas, plurales, variantes), y un historial de capítulos donde aparece. Cuando un nuevo capítulo introduce un término, el agente lo busca primero en el glosario: si existe, lo reusa y propaga el canónico; si colisiona con otro dominio, lo desambigua con sufijo; si lo redefine, lo marca para revisión.

**Sí es**:
- La fuente de verdad de la terminología entre capítulos (criterios 1, 2, 3).
- El mecanismo para que el agente normalice retroactivamente términos introducidos con variantes.
- La base de datos que F44 (note-plan) consulta para escribir el término correcto en cada nota.

**No es**:
- Un diccionario de idiomas: el glosario es específico de la obra y acumula solo los términos que aparecen en ella.
- Una fuente de definiciones exhaustivas: cada término tiene UNA definición canónica corta (≤ 500 chars). Definiciones largas van en notas.
- El `manifest.schema.json::glossary` (que sigue siendo un mapa `{term: description}` simple para counters/previsualizaciones). El presente spec define `knowledge/glossary.json`, una estructura rica.

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente al construir el glosario) | Tras procesar cada bloque `definition` (F37), actualiza o añade término al glosario. |
| L2 (agente al introducir un término nuevo) | Antes de declarar un término, busca en el glosario (aliases + canónicos). Si matchea, usa el canónico. |
| F44 (note-plan) | Consulta el glosario para escribir el término canónico en cada nota (evita "transaction" en algunas y "transacción" en otras). |
| F104 (rutas de lectura) | Usa los aliases para matching robusto en queries. |
| F43 (auditoría de no-pérdida) | Verifica que no haya redefiniciones ni colisiones de alias. |
| F118 (suite automatizada) | Corre `evals/terminology-sample/run_eval.py` para verificar los 3 criterios. |

**No se aplica a**: ingesta (L0–L1), autoría (L3), render (L4).

## §3 · Modelo de datos

`glossary.json` es un objeto con dos secciones: `terms` (el glosario en sí) y `build_metadata` (auditoría). Cada término es un objeto con los siguientes campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `canonical` | string | Slug kebab-case, max 64 chars, regex `^[a-z0-9][a-z0-9-]{0,63}$`. Para colisiones, sufijo `-<vendor>` (ver §8). |
| `definition` | string | Definición canónica (≤ 500 chars). UNA por término. |
| `domain` | string | `vendor`, `vendor+product`, o `unknown`. |
| `aliases` | array | Lista de `{alias, kind}`. `kind ∈ {en, es, acronym, plural, variant}`. |
| `definitions` | array | Historial. Mínimo 1 entrada; **exactamente una** con `canonical: true`. Las demás tienen `canonical: false` y `status: historical` o `conflicting`. |
| `needs_review` | boolean | `true` cuando hay redefinición pendiente de juicio humano. |
| `confusables` | array | Términos con los que se suele confundir (e.g., `view` vs `vista-materializada`). |
| `related_concepts` | array | `concept_id`s del grafo (F39) relacionados. |

Cada entry de `definitions[]`:

| Campo | Tipo | Descripción |
|---|---|---|
| `chapter` | string | Ruta canónica del capítulo (`/ch01/intro`, etc.). |
| `definition` | string | Definición propuesta (≤ 500 chars). |
| `canonical` | boolean | Solo `true` para UNA entry por término. |
| `status` | enum | `current` (la canónica activa), `historical` (versión anterior reemplazada), `conflicting` (criterio 3 — redefine otra). |
| `first_seen_at` | string | ISO-8601 UTC. |
| `source_section_path` | string | `source_section_path` de la unidad `definition` que lo origina. |

## §4 · Reglas R1–R8 (cerradas)

- **R1 (kebab-case)**: `canonical` matchea `^[a-z0-9][a-z0-9-]{0,63}$`. Mayúsculas, acentos y espacios se transforman a kebab-case.
- **R2 (sufijo en colisión)**: si un término `T` ya existe con `domain=X`, y se introduce `T` con `domain=Y` distinto, el segundo se almacena como `T-<vendor>` (ver §8).
- **R3 (alias único)**: cada `alias` (string normalizado lowercase) aparece en ≤1 término. El `kind` es metadata (en/es/acronym/plural/variant), no desambiguador. Aliases con el mismo string rompen el glosario aunque difieran en `kind`.
- **R4 (alias kind enum)**: `kind ∈ {en, es, acronym, plural, variant}`. Cualquier otro valor requiere reabrir F40.
- **R5 (definitions ≥ 1)**: cada término tiene al menos una entrada en `definitions[]`.
- **R6 (1 canónica)**: exactamente una entry de `definitions[]` tiene `canonical: true`. La `definition` raíz del término coincide con la de la entry canónica.
- **R7 (redefinición → needs_review)**: si una nueva chapter introduce `T` con `definition` distinta a la canónica existente, se añade una entry `status: conflicting` y `needs_review: true`. NO bloquea; el agente decide.
- **R8 (normalización retroactiva)**: el agente consulta el glosario antes de introducir un término. Si el texto matchea un alias, usa el canónico. Si matchea un canónico, lo reusa. Si colisiona (R2), aplica el sufijo.

## §5 · Forma JSON canónica

```json
{
  "schema_version": "1.0.0",
  "source": { "id": "...", "vendor": "...", "product": "..." },
  "terms": {
    "<canonical>": {
      "canonical": "transaccion",
      "definition": "Una transacción es una unidad atómica de trabajo.",
      "domain": "postgresql",
      "aliases": [
        { "alias": "transaction", "kind": "en" },
        { "alias": "tx", "kind": "acronym" }
      ],
      "definitions": [
        {
          "chapter": "/ch01/intro",
          "definition": "Una transacción es una unidad atómica de trabajo.",
          "canonical": true,
          "status": "current",
          "first_seen_at": "2026-09-25T14:00:00Z",
          "source_section_path": "/ch01/intro"
        }
      ],
      "needs_review": false,
      "confusables": ["vista-materializada"],
      "related_concepts": ["acid", "mvcc"]
    },
    "wal-oracle": {
      "canonical": "wal-oracle",
      "definition": "Write-Ahead Log en Oracle.",
      "domain": "oracle",
      "aliases": [],
      "definitions": [
        {
          "chapter": "/oracle/ch03",
          "definition": "Write-Ahead Log en Oracle.",
          "canonical": true,
          "status": "current",
          "first_seen_at": "2026-09-25T14:00:00Z",
          "source_section_path": "/oracle/ch03"
        }
      ],
      "needs_review": false,
      "confusables": [],
      "related_concepts": []
    }
  },
  "build_metadata": {
    "built_at": "2026-09-25T14:00:00Z",
    "term_count": 2
  }
}
```

## §6 · Procedimiento de uso

1. **Buscar antes de introducir**: cuando el agente procesa un bloque `definition` (F37) o redacta una nota que introduce un término, primero consulta el glosario (R8). Hace matching contra `canonical` + `aliases[*].alias`.
2. **Si matchea canónico**: usa el canónico. Si la `definition` propuesta coincide con la canónica → actualiza `definitions[].first_seen_at` si la chapter es nueva. Si NO coincide → R7 (nueva entry `conflicting`, `needs_review: true`).
3. **Si matchea alias**: usa el canónico del alias. No declares el alias como canónico.
4. **Si no matchea nada**: introduce un nuevo término con `canonical` derivado del texto (R1), `aliases` razonables (al menos el plural y la versión EN si aplica), y una entry `canonical: true` en `definitions[]`.
5. **Al cerrar capítulo**: persiste `glossary.json` con `build_metadata.built_at` actualizado. Si hay `needs_review: true`, emite WARNING al agente (no bloquea).

## §7 · Detección de redefinición (criterio 3)

Algoritmo que aplica el eval (`evals/terminology-sample/run_eval.py`):

1. Por cada término, ordenar `definitions[]` por `first_seen_at`.
2. Para cada entry con `status: conflicting`, comparar su `definition` con la canónica.
3. Si la diferencia es > 0 chars (cualquier diferencia), exit 1 y reportar el par (capítulo original, capítulo redefinidor).
4. En el JSON del término, la entry `conflicting` queda con `canonical: false` y `needs_review: true` permanece hasta que el agente lo resuelve.

**Umbral**: el spec usa diferencia binaria (cualquier diferencia). El agente puede refinar el matching (e.g., diff semántico) sin reabrir el spec.

## §8 · Resolución de colisiones (R2)

Algoritmo:

1. Si `canonical = T` ya existe con `domain = X`.
2. Se introduce `T` con `domain = Y`, donde `Y ≠ X`.
3. Si `Y = "<vendor>"` (sin producto) o `<vendor>+<product>` contiene un `<vendor>` distinto al de `X`:
   - El nuevo se almacena como `T-<vendor>` (lowercase).
   - Ejemplo: `wal` en PostgreSQL → `wal`; `wal` en Oracle → `wal-oracle`.
4. Si `Y` comparte `<vendor>` con `X` pero tiene `<product>` distinto (e.g., `kubernetes-ingress` vs `kubernetes-gateway`):
   - El nuevo se almacena como `T-<vendor>+<product>`.
   - Ejemplo: `ingress` en `kubernetes+nginx` → `ingress-kubernetes+nginx`.
5. Si ya existe el canónico derivado, se marca `needs_review: true` (otra colisión).

## §9 · Aliases: enumeración y matching

**Enum cerrada de `kind`** (R4):

| Kind | Uso | Ejemplo |
|---|---|---|
| `en` | Forma en inglés. | `"transaction"` (canónico: `transaccion`) |
| `es` | Forma en español con tildes. | `"transacción"` |
| `acronym` | Sigla. | `"tx"`, `"db"`, `"mvcc"` (si canónico es `multi-version-concurrency-control`) |
| `plural` | Plural. | `"transacciones"` |
| `variant` | Variante (typo histórico, jerga). | `"transation"` (typo) |

**Matching**: cuando el agente busca un texto `s`:

1. Compara `s` contra todos los `canonical` (case-insensitive).
2. Si no hay match, compara `s` contra todos los `aliases[*].alias` (case-insensitive).
3. Si hay match, devuelve el `canonical` del término que contiene el alias.

**Caso-insensitive**: el matching es siempre CI; el canónico es siempre kebab-case (lowercase). El agente NUNCA escribe el alias en la nota si el canónico difiere.

## §10 · Cómo verificar + cambios permitidos

```bash
# 1. Spec dentro de presupuesto.
wc -l references/03-knowledge/terminology.md                # ≤ 230
rg -c '^## §' references/03-knowledge/terminology.md         # 11 secciones

# 2. Schema JSON válido.
python3 -c "import json; json.load(open('schemas/glossary.schema.json'))"

# 3. Eval de los 3 criterios del roadmap.
python3 evals/terminology-sample/run_eval.py                 # exit 0

# 4. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json
python3 evals/information-units-sample/run_eval.py
python3 evals/ledger-operativo-sample/run_eval.py
python3 evals/concept-graph-sample/run_eval.py

# 5. Cero mención a plataformas (INV-06).
rg -i 'obsidian|notion|appflowy' references/03-knowledge/terminology.md   # vacío
```

**Permitidos sin reabrir F40** (versión menor):
- Añadir un campo opcional a `terms[*]` (e.g., `examples[]`).
- Añadir un valor a `definitions[*].status` (e.g., `proposed`).
- Refinar el wording de §1.

**Reabren F40** (versión mayor):
- Cambiar la regex de `canonical`.
- Cambiar la estrategia de colisión (R2).
- Añadir un valor a `aliases[*].kind` enum.
- Cambiar la regla "1 canónica" (R6).
- Eliminar `needs_review`.

## §11 · Cambios que reabren + glosario

**Reabren F40 además de §10**:
- Cambiar el threshold de redefinición (default: cualquier diferencia).
- Eliminar `confusables`, `related_concepts` o `needs_review`.
- Cambiar el formato de `domain`.

**No reabren F40**: refinar mensajes de error; cambiar el path del workdir.

**Glosario**:

| Término | Significado |
|---|---|
| **Canónico** | Slug kebab-case que identifica unívocamente un concepto en el glosario. |
| **Alias** | Forma secundaria que apunta a un canónico (EN, ES, sigla, plural, variante). |
| **Colisión** | Mismo texto designa conceptos distintos en vendors/products diferentes; se resuelve con sufijo `-<vendor>`. |
| **Redefinición** | Capítulo nuevo introduce un término existente con `definition` distinta; marca `needs_review: true`. |
| **Normalización retroactiva** | El agente consulta el glosario antes de escribir; si matchea un alias, usa el canónico. |
| **`needs_review`** | Flag del término; requiere decisión humana (rechazar, refinar, descartar). |
