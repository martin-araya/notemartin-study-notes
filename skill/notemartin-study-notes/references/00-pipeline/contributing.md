# Estilo de referencias — `references/00-pipeline/contributing.md`

> Documento normativo de la **Fase 124** del roadmap. Define el estilo de escritura de los archivos de `references/` (N3 del proyecto: prosa normativa que el agente lee en runtime). El alcance normativo principal está en este archivo; el procedimiento de contribución (cómo abrir PR, triada regla→motivación→prueba, checklist) vive en [`CONTRIBUTING.md`](../../../CONTRIBUTING.md).
>
> Documentos complementarios: [`CONTRIBUTING.md`](../../../CONTRIBUTING.md) §1 (estilo de referencias — resumen ejecutivo), [`docs/skill-anatomy.md`](../../../docs/skill-anatomy.md) §2 (anatomía de N3), [`docs/repo-layout.md`](../../../docs/repo-layout.md) §5 (regla de ubicación), [`references/00-pipeline/responsibilities.md`](responsibilities.md) (qué escribe cada capa).

## Índice

1. [Propósito](#1-propósito) · 2. [Audiencia y tono](#2-audiencia-y-tono) · 3. [Estructura canónica por archivo](#3-estructura-canónica-por-archivo) · 4. [Convenciones de redacción](#4-convenciones-de-redacción) · 5. [Anclas y referencias cruzadas](#5-anclas-y-referencias-cruzadas) · 6. [Marcas y directivas](#6-marcas-y-directivas) · 7. [Diagramas y ejemplos](#7-diagramas-y-ejemplos) · 8. [Anti-patrones](#8-anti-patrones) · 9. [Cómo verificar + cambios permitidos](#9-cómo-verificar--cambios-permitidos)

## 1. Propósito

`references/` contiene la prosa normativa que el agente lee cuando dispara la skill. Cada archivo es una pieza autocontenida con su contrato, sus reglas, sus anti-patrones y su procedimiento de verificación. El estilo busca: (a) minimizar el coste de lectura, (b) hacer verificable lo declarado, (c) mantener la prosa portable entre agentes y versiones.

## 2. Audiencia y tono

- **Audiencia primaria**: el agente en runtime (N2 router + N3 prosa).
- **Audiencia secundaria**: el agente desarrollador humano (mantenedor del proyecto), para entender qué hace cada pieza.
- **Tono**: instructivo, no argumentativo. "El agente debe X" en lugar de "creemos que X".
- **Voz**: impersonal. Sin segunda persona. Sin emojis en prosa.
- **Idioma**: español. Terminología técnica canónica en inglés cuando es término internacional (`IR`, `SDM`, `NoteMark`, `ledger`, `OCR`).
- **Densidad**: alta. La prosa debe ser escaneable. Un párrafo de 60 palabras es lo normal; uno de 200 es demasiado.

## 3. Estructura canónica por archivo

Cada archivo de `references/0X-*/` sigue la siguiente plantilla (patrón cerrado, ver `references/01-ingest/triage.md` como referencia canónica):

1. **Título H1** con el nombre del archivo (`# Nombre — \`references/XX-name/<file>.md\``).
2. **Bloque de metadata** (después del H1): "Documento normativo de Fase N del roadmap." + 2-4 anclas a documentos complementarios.
3. **Índice** con 5-15 secciones `## §N · <título>`.
4. **Cuerpo**: 8-12 secciones `## §N · <título>`, cada una con su contenido normativo.
5. **Cierre obligatorio**: `## §N · Cómo verificar + cambios permitidos` (ver §3.1).

### 3.1 · Sección de cierre obligatoria

Las dos últimas secciones de cada archivo son siempre:

- `## §M-1 · Cómo verificar`: comando(s) ejecutable(s) que validan lo declarado. Típicamente un `python3 <validator>` o `bash <check>`.
- `## §M · Cambios permitidos`: lista explícita de qué cambios reabren la fase (regla cerrada) y cuáles no.

Si un archivo no tiene estas dos secciones, no está listo para revisión (ver `scripts/check_pr.py` item 5).

## 4. Convenciones de redacción

- **Imperativo positivo**: "el script debe validar" en lugar de "se debe validar" o "hay que validar".
- **No adverbios vacíos**: evitar "básicamente", "esencialmente", "generalmente", "más o menos", "digamos", "realmente". Cada adverbio debe añadir información.
- **No voz pasiva con agente implícito**: "el validador falla" en lugar de "se falla la validación".
- **No listas anidadas de 3+ niveles**: si una lista necesita sub-sub-listas, conviértela en una tabla o un árbol.
- **No anglicismos innecesarios**: preferir "lista" a "array", "diccionario" a "dict", "tabla hash" a "hashtable". Pero los términos técnicos del campo (CI, JSON, YAML, schema) se preservan.

## 5. Anclas y referencias cruzadas

- **Anclas Markdown estándar**: `[texto](path/to/file.md#section-id)` — kebab-case del título.
- **Anclas entre docs**: preferir el path relativo desde el archivo actual. Para docs raíz → docs: `../docs/`. Para docs → references: `../skill/notemartin-study-notes/references/`.
- **Anclas a ADRs**: `[ADR-0001](../adr/ADR-0001-units-closed-enum.md)` — incluir el número + slug.
- **Anclas a invariantes**: citar como `INV-NN` (per `skills/AGENT.md` §2). El número es estable; el archivo puede cambiar.
- **Anclas a fases**: citar como `FN` (sin descripción). El nombre de la fase está en `ROADMAP.md`.

No usar anclas a URLs externas en prosa normativa (son frágiles); en docs raíz (`docs/`, raíz) sí se permite.

## 6. Marcas y directivas

Las directivas viven en NoteMark (`references/04-authoring/notemark.md`); en `references/` no se usan, pero sí:

- **`:::note`**, **`:::warning`**, **`:::danger`** — no se usan en prose de `references/`; la prosa debe ser clara sin ellas. Si necesitas enfatizar, usa H3 + bloque de párrafo corto.
- **Blockquotes `>`** — sí se permiten para citas literales (e.g. ADR textual, JSON de ejemplo).
- **Code fences** — siempre con lenguaje: ` ```json `, ` ```yaml `, ` ```bash `, ` ```python `, ` ```text ` (este último para ASCII diagrams).

## 7. Diagramas y ejemplos

- **ASCII art** permitido para diagramas pequeños (≤ 15 líneas). Sin unicode decorativo.
- **Mermaid** permitido en bloques ` ```mermaid `. Solo para diagramas estructurales (no para ilustraciones).
- **Tablas** permitidas cuando hay ≥ 3 columnas o ≥ 3 filas; preferir listas si la información es jerárquica.
- **Ejemplos de código** deben ser ejecutables. Si no lo son, declararlo explícitamente con `> Nota: este ejemplo no es ejecutable; ver ... para la versión real.`

## 8. Anti-patrones

- ❌ "Este documento es un *work in progress* y puede cambiar." — si está WIP, márcalo en el header `**Estado:** WIP`.
- ❌ "TODO: ..." inline — los TODOs viven en `ROADMAP.md` o en issues, no en la prosa normativa.
- ❌ Empezar con "En este documento vamos a ver..." — empezar declarando el contrato.
- ❌ "Como se mencionó anteriormente..." — referencia el anchor explícito: "ver `INV-08` (§3.2)".
- ❌ Repetición de la misma idea en dos secciones — si la repetición es deliberada (énfasis), decláralo.

## 9. Cómo verificar + cambios permitidos

### 9.1 · Cómo verificar

```bash
# Cada archivo de references/ debe tener las dos secciones de cierre obligatorias.
python3 -c "
import re, pathlib
ok = 0
total = 0
for f in pathlib.Path('skill/notemartin-study-notes/references').rglob('*.md'):
    text = f.read_text()
    has_verify = bool(re.search(r'## §N.+C[oó]mo verificar', text))
    has_changes = 'Cambios permitidos' in text
    total += 1
    if has_verify and has_changes:
        ok += 1
    else:
        print(f'FALTA cierre: {f}')
print(f'{ok}/{total} archivos con cierre completo')
"

# Linter de tono: detectar segunda persona y adverbios vacíos.
python3 -c "
import re, pathlib
bad = ['básicamente', 'esencialmente', 'generalmente']
for f in pathlib.Path('skill/notemartin-study-notes/references').rglob('*.md'):
    text = f.read_text().lower()
    for b in bad:
        if b in text:
            print(f'{f}: adverbio vacío \"{b}\"')
"

# Anclas rotas: cada [texto](path) debe apuntar a un archivo existente.
# (F124 lo deja como follow-up; ver scripts/check_pr.py item 5.)
```

### 9.2 · Cambios permitidos

**No reabren F124:**
- Añadir una sección nueva a un archivo existente.
- Añadir un ejemplo o diagrama a una sección existente.
- Añadir un anchor o referencia cruzada.
- Corregir typos.
- Cambiar el wording de una regla existente sin alterar su semántica.

**Reabren F124:**
- Cambiar el patrón de las 5 secciones estructurales (Título / metadata / índice / cuerpo / cierre).
- Cambiar la regla de cierre obligatorio (§3.1) — e.g. hacerlo opcional.
- Cambiar la plantilla de §1-§9 — sería rehacer el patrón normativo.
- Eliminar una convención de §4 (e.g. permitir segunda persona).
