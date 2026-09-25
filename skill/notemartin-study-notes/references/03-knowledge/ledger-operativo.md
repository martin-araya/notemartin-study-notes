# Ledger operativo — `references/03-knowledge/ledger-operativo.md`

> Documento normativo de la **Fase 38** del roadmap. Define cómo opera el script `scripts/util/ledger.py` que el agente usa durante L2 para mantener el Coverage Ledger (creado y validado en F15). Lo complementa, no lo sustituye: `ledger.md` (F15) describe la forma del JSON; este doc describe **cómo se usa el CLI**.
>
> Documentos complementarios: `references/03-knowledge/ledger.md` (F15, forma e invariantes), `references/03-knowledge/information-units.md` (F37, taxonomía y reglas R1–R5 que el script aplica), `schemas/ledger.schema.json` (F15 + endurecido en F38 al enum cerrado de 14 tipos), `schemas/manifest.schema.json` (F16, `units_processed` y `last_modified`), `scripts/util/validate_ledger.py` (F15, linter read-only; convive con este), `scripts/util/unit_rules.py` (F37/F38, fuente única de R1–R5), `docs/adr/ADR-0002-ledger-split.md` (justifica por qué hay dos CLIs).
>
> Enrutado desde N2: `docs/skill-anatomy.md` §6 fila `F38`. Lo lee el agente en L2 para construir y mantener el ledger; lo lee F43 (auditoría) para validar el reporte; F118 (suite automatizada) corre el eval de §10.

## §1 · Propósito y alcance

El Coverage Ledger es la **fuente de verdad de la puerta de fidelidad** (architecture.md §3.3). F15 define el JSON, los estados terminales y la lista cerrada de motivos de descarte; este spec define la **mecánica operativa**: cómo el agente añade entradas, transiciona estados, genera el reporte y sincroniza con el manifiesto.

**Sí es**: la herramienta que el agente invoca desde L2 para no manipular el JSON a mano.

**No es**:
- El validador de CI. `validate_ledger.py` (F15) sigue siendo el linter read-only.
- La decisión de qué unidades extraer o qué criticidad asignar; eso es del agente siguiendo `information-units.md` (F37).
- La redacción de notas (L3) ni el render (L4).

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| L2 (agente extrayendo unidades) | Inicia con `init`, añade con `add`, transiciona con `mark`, sincroniza el manifiesto con `manifest`. |
| L2 (agente consultando cobertura) | Ejecuta `report` o `check` antes de decidir que L2 terminó. |
| F43 (auditoría de no-pérdida) | Ejecuta `check --strict` para confirmar que no hay huérfanos ni gaps. |
| F118 (suite automatizada) | Corre `evals/ledger-operativo-sample/run_eval.py` para verificar los criterios del roadmap. |

**No se aplica a**: ingesta (L0–L1), autoría (L3), render (L4).

## §3 · Subcomandos del CLI

CLI con `argparse` subparsers. Patrón: `ledger.py [--workdir PATH] <subcommand> [args]`. Códigos: `0` ok, `1` validación, `2` uso.

| Subcomando | Propósito | Salida | Exit |
|---|---|---|---|
| `init` | Crea `knowledge/ledger.json` vacío a partir del SDM (replica `source.id`/`source.hash`). | Ledger skeleton | 0/1/2 |
| `add` | Añade una entrada. Aplica R1–R5 mecánicamente. | Ledger actualizado en disco (escritura atómica) | 0/1/2 |
| `mark` | Transiciona una entrada a `written` / `merged` / `discarded` (con motivo). | Ledger actualizado | 0/1/2 |
| `report` | Imprime el reporte de cobertura (4 vistas: global / por estado / por motivo / por sección con must-keep pending). Funciona en cualquier punto del proceso. | Texto a stdout | 0 |
| `check` | Detecta huérfanos (entries con `source_block_ids` inexistente en SDM) y gaps (bloques del SDM sin entry). | Texto a stdout; con `--strict` rompe si hay desviaciones | 0/1 |
| `manifest` | Parchea `manifest.json`: actualiza `units_processed` y `last_modified`. No toca otros campos. | Manifest actualizado (o `--dry-run` imprime patch) | 0/1/2 |

Uso:

```bash
python3 scripts/util/ledger.py --help
python3 scripts/util/ledger.py init --workdir .notes-work/<source_hash>
python3 scripts/util/ledger.py add --unit-id u_001 \
    --source-block-ids a8f4ce140580 \
    --type parameter \
    --section-path /ch02/intro \
    --content '{"name": "shared_buffers", "description": "Tamaño del caché."}'
python3 scripts/util/ledger.py mark u_001 --state written --target-note postgres-config
python3 scripts/util/ledger.py report --workdir .notes-work/<source_hash>
python3 scripts/util/ledger.py check --strict
python3 scripts/util/ledger.py manifest --dry-run
```

## §4 · Forma del workdir y paths por defecto

Default `--workdir`: directorio actual. El script espera este árbol (architecture.md §4):

```
<workdir>/
├── sdm.json                  # entrada para init y check
├── knowledge/
│   └── ledger.json           # entrada/salida de add/mark/report/check/manifest
└── manifest.json             # salida de manifest
```

Flags de override:

- `--workdir PATH` cambia la raíz.
- `--sdm PATH` cambia la ubicación de `sdm.json` (relativa al workdir).
- `--ledger PATH` cambia la ubicación de `knowledge/ledger.json`.
- `--manifest PATH` cambia la ubicación de `manifest.json`.

Si falta `sdm.json` para `init` o `check`, exit 2. Si falta `ledger.json` para `add`/`mark`/`report`, exit 2.

## §5 · Escritura atómica

Invariante L-04 de `ledger.md` (F15). Patrón obligatorio:

1. Serializar el ledger a un `tempfile.NamedTemporaryFile` en el mismo directorio que el destino (para que `rename` sea atómico en el mismo FS).
2. Validar el JSON serializado contra `schemas/ledger.schema.json` (cuando exista `jsonschema`); si falla, abortar sin escribir.
3. `Path.replace(temp_path, destino)` (atómico en POSIX y Windows).
4. No se hace backup automático: el invariante de atomicidad hace innecesario el `.bak`.

El subcomando `init` con `--force` sobrescribe; sin él, exit 1 si el ledger ya existe.

## §6 · Detección de huérfanos y gaps

Definiciones (cierra ADR-0001 sobre el contrato inverso):

- **Huérfana**: `entries[i].source_block_ids[j]` no aparece en ningún `block.id` de `sdm.sections[*].blocks[*]`. El agente introdujo una entrada que apunta a un bloque inexistente o el bloque fue renumerado entre extracciones.
- **Sin respaldo** (gap): `sdm.sections[*].blocks[*].id` no aparece en ningún `entries[*].source_block_ids[*]`. El bloque existe en la fuente pero el agente no lo ha extraído como unidad.

Algoritmo O(n+m): dos `set` lookups por entrada / bloque.

**Bloques `prose`** (F13 tipo `prose`): por defecto **no** cuentan como gap. Un bloque de prosa introductoria no requiere unidad. Flag `--include-prose` los incluye (útil cuando se quiere detectar contenido sin respaldo de manera exhaustiva).

El reporte de `check` lista cada huérfano / gap con `unit_id` / `block_id`, `section_path` y `type`. Con `--strict`, exit 1 si hay desviaciones; sin él, exit 0 con detalle.

## §7 · Sincronización con `manifest.json`

Subcomando `manifest`. Lee `knowledge/ledger.json`, cuenta entradas en estado terminal (`written`, `merged`, `discarded`), y aplica el patch a `manifest.json`:

```json
{
  "units_processed": <count>,
  "last_modified": "<ISO-8601 UTC>"
}
```

**Solo se tocan esos dos campos.** El resto (`source`, `current_stage`, `stage_progress`, `published_notes`, `glossary`, `naming_decisions`, `link_debt`, `hash_mismatch`) permanece intacto. El agente es quien decide cuándo marcar `stage_progress.l2 = "done"`; el script no tiene esa visión.

Algoritmo de patch: cargar `manifest.json` (si no existe, exit 2); `merge` superficial solo de los dos campos; escritura atómica (mismo patrón que §5).

`--dry-run` imprime el diff propuesto sin escribir.

## §8 · Aplicación mecánica de R1–R5

El subcomando `add` consulta `scripts/util/unit_rules.py::is_must_keep(unit)`:

- Si retorna regla (`R1`–`R5`):
  - El agente declara `criticality=context` con `--rationale <str>` → se acepta con `WARNING` en stderr y se exige `criticality_rationale` no vacío.
  - El agente declara `criticality=must-keep` (o lo omite, default `must-keep`) → se acepta sin warning.
- Si retorna `None`:
  - El agente declara `criticality=must-keep` sin rationale → se acepta con `WARNING` (elevación sin justificación).
  - El agente declara `criticality=context` (o lo omite, default `context`) → se acepta sin warning.

El subcomando `mark` valida que `target_note` esté poblado si el destino es `must-keep` (regla de F15 §3 L-05).

## §9 · Anti-patrones

- Editar `knowledge/ledger.json` directamente sin pasar por el script → viola escritura atómica (L-04) y la aplicación de R1–R5.
- Usar `mark --state written` en una unidad `must-keep` sin `--target-note` → falla la validación (L-05).
- Correr `manifest` antes de cerrar todas las `must-keep` en estado terminal → infra-reporta `units_processed`.
- Fusionar dos `must-keep` en una sola entrada → viola F37 §6 y el invariante INV-08.
- Declarar `discard_reason` fuera de la lista cerrada (`"redundant-with:..."` con typo, `"outdated"`, etc.) → falla la validación del schema.
- Pasar `--workdir` relativo fuera del workdir canónico (`./.notes-work/...`) → el script acepta pero F43 puede no encontrar el manifest. Mantener paths absolutos o seguir el default.

## §10 · Cómo verificar + cambios permitidos

Comandos grepeables:

```bash
# 1. Spec dentro de presupuesto.
wc -l references/03-knowledge/ledger-operativo.md            # ≤ 230
rg -c '^## §' references/03-knowledge/ledger-operativo.md     # 11 secciones

# 2. CLI funcional.
python3 scripts/util/ledger.py --help                         # imprime los 6 subcomandos

# 3. Eval de los 3 criterios del roadmap.
python3 evals/ledger-operativo-sample/run_eval.py            # exit 0

# 4. Sin regresión.
python3 scripts/util/validate_ledger.py --validate evals/ledger-sample/*.json   # F15 OK
python3 evals/information-units-sample/run_eval.py                              # F37 OK

# 5. Cero mención a plataformas (INV-06).
rg -i 'obsidian|notion|appflowy' references/03-knowledge/ledger-operativo.md   # vacío
```

**Cambios permitidos sin reabrir F38** (versión menor):
- Añadir un subcomando nuevo (e.g., `rollback`).
- Añadir una vista al reporte de `report`.
- Añadir un campo opcional al patch de `manifest` (e.g., `units_total`).
- Refinar el wording de §1.

**Reabren F38** (versión mayor):
- Eliminar un subcomando.
- Cambiar el patrón de escritura atómica.
- Cambiar las definiciones de "huérfana" o "sin respaldo".
- Tocar campos distintos a `units_processed`/`last_modified` en `manifest`.
- Eliminar la aplicación mecánica de R1–R5 en `add`.
- Cambiar el contrato de `--strict` en `check`.

## §11 · Cambios permitidos vs que reabren + glosario

**Reabren F38 además de los de §10**:
- Cambiar los códigos de exit de un subcomando.
- Modificar el path por defecto del workdir.
- Cambiar la firma de `is_must_keep` en `unit_rules.py` (afecta a `add` y al eval de F37).

**No reabren F38**:
- Añadir un campo opcional al JSON del ledger (`additionalProperties: false` exige bumpear `schema_version`, pero sigue siendo cambio aditivo compatible).
- Cambiar mensajes de error de un subcomando.

**Glosario operativo**:

| Término | Significado |
|---|---|
| **Workdir** | `.notes-work/<source_hash>/`; raíz de un proyecto de notas por fuente. |
| **Subcomando** | Cada uno de los 6 verbos del CLI (`init`, `add`, `mark`, `report`, `check`, `manifest`). |
| **Huérfana** | Entry con `source_block_ids` que no existe en el SDM. |
| **Sin respaldo (gap)** | Bloque del SDM no cubierto por ninguna entry. |
| **Patch de manifest** | Subset de `manifest.json` (`units_processed`, `last_modified`) que el script `manifest` actualiza. |
