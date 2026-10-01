# Extender la skill — `EXTEND.md`

> Documento normativo de F121. Tutorial para añadir un tipo de nota nuevo a la skill `notemartin-study-notes`. El tutorial es procedimiento; el contenido normativo vive en `skill/notemartin-study-notes/references/05-note-types/` (F78-F92) y este documento ancla sobre él.
>
> Documentos complementarios: `references/05-note-types/` (F78-F92, los 15 tipos cerrados), `references/04-authoring/notemark.md` (F12, formato NoteMark), `references/10-quality/checklists-by-type.md` (F112, checklist por tipo), `schemas/note-plan.schema.json` (F44, enum cerrada de tipos en note-plan).

## Índice

1. [Por qué añadir un tipo de nota](#1-por-qué-añadir-un-tipo-de-nota) · 2. [Los 5 pasos](#2-los-5-pasos) · 3. [Tutorial: `cheatsheet-ejemplo`](#3-tutorial-cheatsheet-ejemplo) · 4. [Errores comunes y anti-patrones](#4-errores-comunes-y-anti-patrones) · 5. [Verificación](#5-verificación) · 6. [Cambios permitidos](#6-cambios-permitidos)

## 1. Por qué añadir un tipo de nota

La skill viene con **15 tipos cerrados** (F44): `concept`, `api-reference`, `procedure`, `configuration`, `error-troubleshooting`, `architecture`, `syntax`, `data-model`, `chapter-digest`, `comparison`, `version-delta`, `glossary-term`, `cheatsheet`, `index-moc`, `practice`. Estos cubren los casos más comunes.

Hay motivos legítimos para añadir un tipo nuevo:

- La fuente tiene una estructura que ninguno de los 15 captura (p. ej. "ficha de paciente" para fuentes médicas, "caso legal" para jurisprudencia).
- El usuario necesita una forma específica que mejore la legibilidad en su destino favorito.
- El equipo ha descubierto un patrón recurrente en su dominio y quiere estandarizarlo.

**No añadir un tipo nuevo** si la diferencia se puede resolver con una variante del tipo existente (perfil, sección opcional, directivas NoteMark). El sistema se mantiene simple cuantos menos tipos haya.

## 2. Los 5 pasos

```
1. Definir la sección en references/05-note-types/<tipo>.md
2. Cerrar la plantilla canónica (secciones obligatorias + opcionales)
3. Validar contra references/10-quality/checklists-by-type.md (F112)
4. Registrar en note-plan.schema.json §3 (enum cerrada de tipos)
5. Añadir al set de regresión (evals/regression/cases/) con caso sintético
```

### Paso 1 · Definir la sección en `references/05-note-types/<tipo>.md`

Cada tipo de nota tiene un archivo en `skill/notemartin-study-notes/references/05-note-types/`. Sigue la estructura fija (per `skills/AGENT.md` §7.2):

- **Propósito** — 1-3 líneas; qué es este tipo.
- **Cuándo se aplica** — disparador; qué fuentes lo piden.
- **Reglas** — checklist [B] bloqueantes + [R] recomendados.
- **Ejemplos** — al menos 2 de dominios distintos (INV-15).
- **Anti-ejemplos** — qué NO es este tipo.
- **Cómo verificar** — qué validador lo cierra.

### Paso 2 · Cerrar la plantilla canónica

La plantilla se cierra declarando las secciones obligatorias y opcionales. Ejemplo para `cheatsheet` (ya existe, se reusa como referencia):

```markdown
# §1 · Cheatsheet canónica
## §2 · Comandos / atajos / fragmentos
## §3 · Errores frecuentes (opcional)
## §4 · Referencias
```

Las secciones siguen la regla F75: máx 80 líneas, TL;DR ≤ 30 palabras, llamadas a bloques `:::note`/`:::warning` cuando aplica.

### Paso 3 · Validar contra `checklists-by-type.md`

`references/10-quality/checklists-by-type.md` (F112) define para cada tipo un bloque `[B]` (bloqueante) + `[R]` (recomendado). Cualquier nota nueva debe pasar su checklist antes de declararse cerrada.

```bash
python3 skill/notemartin-study-notes/scripts/validate/density_check.py \
  --note examples/<caso>/artifacts/notemark/<note-id>.nm \
  --strict
```

Si la checklist tiene reglas que no aplican al tipo nuevo, **añadir reglas** (no eliminar las existentes) y abrir un PR con ADR.

### Paso 4 · Registrar en `note-plan.schema.json`

`schemas/note-plan.schema.json` (F44) tiene una enum cerrada de tipos en `notes[].type`. Añadir el tipo nuevo:

```json
{
  "enum": ["concept", "api-reference", "procedure", "configuration", "...",
           "mi-tipo-nuevo"]
}
```

Este cambio es **breaking** para notas que tengan `type` antiguo; bumpear `schema_version` (de "1.0.0" a "1.1.0", por ejemplo).

### Paso 5 · Añadir al set de regresión

`evals/regression/cases/` (F119) contiene los casos que se ejecutan N veces antes de cada release. Añadir un caso para el tipo nuevo:

```yaml
# evals/regression/cases/case-mi-tipo-nuevo.yaml
id: case-mi-tipo-nuevo
version: 1.0.0
corpus_source: <un id del corpus o uno sintético>
profile: reference
prompt: |
  <prompt realista que dispara la nota mi-tipo-nuevo>
expected_outputs:
  notes_min: 1
assertions:
  automatic:
    - id: type-is-correct
      type: ledger_coverage
      spec: {...}
      validator: scripts/util/validate_ledger.py
  human:
    - id: rubric-application
      spec:
        anchors_used: [ANC-XX]
```

Documentar el caso en `evals/regression/SET.md` (F119) con su `regression_role` y motivo.

## 3. Tutorial: `cheatsheet-ejemplo`

`cheatsheet` ya existe en los 15 tipos cerrados. Lo usamos como ejemplo de cómo se ve un tipo bien definido, no como caso para añadir.

### 3.1 · Estructura del archivo `references/05-note-types/cheatsheet.md`

```markdown
# Cheatsheet

## §1 · Propósito
Notas compactas de referencia rápida (≤ 80 líneas). Comandos, atajos,
fragmentos de código, tablas de búsqueda. Sin analogías, sin narrativa.

## §2 · Cuándo se aplica
- El usuario pide "una hoja de referencia rápida"
- La fuente es una referencia CLI / cheat sheet / tabla de búsqueda
- El destino es Obsidian o similar (las cheatsheets largas no encajan en Notion API)

## §3 · Plantilla canónica
### §3.1 · Bloqueantes [B]
- [ ] [B] `# §1 · Cheatsheet canónica` con TL;DR ≤ 30 palabras
- [ ] [B] `## §2 · Comandos / atajos / fragmentos` con ≥ 5 entradas
- [ ] [B] Cada comando con ejemplo mínimo ejecutable
- [ ] [B] No exceder 80 líneas

### §3.2 · Recomendados [R]
- [ ] [R] Sección "Errores frecuentes" si aplica
- [ ] [R] Anclas `{src:blk_xxx}` en ≥ 80% de comandos
- [ ] [R] Tabla resumen al inicio con nombre → descripción

## §4 · Ejemplos
- [PostgreSQL CLI cheatsheet](../examples/) — comandos pg_*
- [Docker CLI cheatsheet](../examples/) — docker run/build/compose

## §5 · Anti-ejemplos
- Una nota `cheatsheet` de 200 líneas → usar `procedure` o `api-reference`.
- Una nota sin comandos → usar `concept`.

## §6 · Cómo verificar
python3 scripts/validate/density_check.py --note <path> --strict
python3 scripts/validate/validate_notemark.py --validate <path>
```

### 3.2 · Cómo se nota la diferencia con `procedure`

- **`procedure`** — pasos numerados con precondiciones + verificación + rollback. Larga.
- **`cheatsheet`** — comandos/atajos sin orden narrativo. Compacta.

Si dudas, empieza con `procedure` y refactoriza a `cheatsheet` solo cuando la notes se use como referencia rápida, no como guía.

## 4. Errores comunes y anti-patrones

| Error | Cómo evitarlo |
|---|---|
| Añadir un tipo nuevo cuando uno existente cubre el caso | Releer la lista de 15 tipos antes; usar `configuration` o `cheatsheet` con secciones opcionales. |
| Tipo nuevo con menos de 2 dominios cubiertos (INV-15) | Esperar a tener ≥ 2 corpus entries donde aplique. |
| Tipo nuevo sin checklist `[B]/[R]` (F112) | Cerrar el bloque §3 antes de abrir PR. |
| Tipo nuevo sin caso en el set de regresión (F119) | El tipo entra sin verificación de varianza → regresión silenciosa. |
| Tipo nuevo con sintaxis NoteMark propia | Reutilizar directivas existentes (`:::note`, `:::warning`, `:::collapsible`, etc.); no añadir vallas. |
| Tipo nuevo con mención de plataforma | INV-06: `references/04-authoring/` (donde vive la spec NoteMark) no menciona plataformas; si tu tipo lo hace, es bug. |

## 5. Verificación

Tras añadir el tipo, ejecutar en orden:

1. **Validar NoteMark**: `python3 scripts/validate/validate_notemark.py --validate <caso>/artifacts/notemark/<id>.nm`.
2. **Validar densidad**: `python3 scripts/validate/density_check.py --note <mismo> --strict`.
3. **Validar IR**: `python3 scripts/util/validate_ir.py --validate <caso>/artifacts/ir/<id>.json`.
4. **Renderizar**: `python3 examples/build_examples.py --example <caso>` → ver 5 capturas SVG.
5. **Aplicar rúbrica**: leer `evals/rubric.md` §3.4 (perfil study/reference/hybrid) y puntuar la nota generada.
6. **Añadir al set de regresión**: regenerar `evals/runs/<tag>/variance.json` con `python3 evals/suite/runner/run_regression.py --release-tag <tag>`.

Si alguna falla, revisar `evals/quality-gate.md` (F115) y `evals/fidelity-sample/` (F114) para los criterios de aceptación.

## 6. Cambios permitidos

**No reabren F121:**
- Añadir una variante de un tipo existente (p. ej. `cheatsheet-amplia`).
- Añadir un dominio al §4 de un tipo ya existente.
- Corregir errores tipográficos en los 5 pasos o en el tutorial.

**Reabren F121:**
- Cambiar el orden o la cantidad de los 5 pasos.
- Cambiar la lista de errores comunes de §4.
- Eliminar el tutorial de §3.
- Cambiar la anatomía general del proceso.
