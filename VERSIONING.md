# Versionado — `VERSIONING.md`

> Documento normativo de F123. Define la convención de versionado de la skill `notemartin-study-notes`. El source of truth es el archivo [`VERSION`](VERSION) (1 línea) en la raíz del repo. `scripts/build_skill.py` (F122) lo lee y lo vuelca en `manifest.json::version`.
>
> Documentos complementarios: [`CHANGELOG.md`](CHANGELOG.md) (F123, bitácora de releases), [`COMPATIBILITY.md`](COMPATIBILITY.md) (F123, matriz por artefacto).

## Índice

1. [Formato](#1-formato) · 2. [Cuándo bumpear](#2-cuándo-bumpear) · 3. [Ejemplos concretos](#3-ejemplos-concretos) · 4. [Pre-releases](#4-pre-releases) · 5. [Cómo bumpear](#5-cómo-bumpear) · 6. [Cambios permitidos](#6-cambios-permitidos)

## 1. Formato

SemVer 2.0.0 ([semver.org](https://semver.org/spec/v2.0.0.html)).

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: entero ≥ 0, sin ceros a la izquierda.
- **MINOR**: entero ≥ 0, sin ceros a la izquierda.
- **PATCH**: entero ≥ 0, sin ceros a la izquierda.
- **PRERELEASE** (opcional): secuencia de identificadores separados por `.`, p. ej. `-dev`, `-rc.1`, `-alpha.2`.
- **BUILD** (opcional): metadata separada por `+`, p. ej. `+sha.aa033a4`.

Ejemplos válidos: `1.0.0`, `0.1.0-dev`, `0.2.0-rc.1`, `1.0.0+sha.aa033a4`.
Ejemplos inválidos: `1.0`, `01.0.0`, `1.0.0.0`, `1.0.0-`.

## 2. Cuándo bumpear

### 2.1 · MAJOR (`X.0.0`) — contrato roto

Bumpear MAJOR cuando cambia el contrato de **al menos uno** de:

- Los 14 schemas del paquete (`schemas/*.schema.json`): `sdm`, `note-ir`, `note-plan`, `ledger`, `glossary`, `concept-graph`, `conflicts`, `profile`, `quality-gate`, `manifest`, `book-map`, `book-state`, `chunk-state`, `version-delta`. Cambio de `schema_version` const de `X.0.0` a `Y.0.0` con `X != Y`.
- Eliminación de un tipo de nota del enum cerrada de 15 (F44).
- Eliminación de un destino soportado (Obsidian, Notion, AppFlowy, Markdown, HTML/PDF, Notion-md, flashcards).
- Cambio en el formato NoteMark que rompa parseo (cambio en directivas, no en número de directivas).
- Cambio en el contrato del renderer protocol (tabla de capacidades en `references/08-render/capability-matrix.md`).

### 2.2 · MINOR (`0.X.0`) — aditivo retrocompatible

Bumpear MINOR cuando se añade:

- Un nuevo tipo de nota al enum cerrada (actualmente 15; llegaría a 16).
- Un nuevo destino (e.g. Spaced Repetition plugin para Obsidian, Joplin, Bear).
- Un nuevo flag opcional en un schema existente (un campo nuevo en `properties` con `additionalProperties: true` en alguna rama).
- Un nuevo motor OCR soportado (e.g. PaddleOCR si se añade a `references/01-ingest/ocr-engines.md`).
- Una nueva fixture del corpus.
- Una nueva assertion en la suite de F118 que antes no existía.

El cambio debe ser aditivo: nada existente deja de funcionar.

### 2.3 · PATCH (`0.0.X`) — bugfix sin contrato

Bumpear PATCH cuando es:

- Bug fix sin cambio de contrato (e.g. un validador que aceptaba `null` y ahora rechaza).
- Documentación nueva o corregida.
- Refactor interno (mover archivos, renombrar funciones) sin cambio observable.
- Mejora de performance.
- Typo fix.

Si dudas entre PATCH y MINOR: ¿un consumidor del paquete tendría que cambiar algo? Si sí → MINOR. Si no → PATCH.

## 3. Ejemplos concretos

| Cambio | Versión anterior → nueva | Tipo |
|---|---|---|
| Cierre de F125 (verificación final) | `0.1.0-dev` → `0.1.0` | de `-dev` a estable (no es bump en sí; F123.4 lo documenta) |
| Añadir destino "Spaced Repetition" como perfil nuevo de Obsidian | `0.1.0` → `0.2.0` | MINOR |
| Añadir un tipo de nota nuevo (`runbook`, 16º) | `0.2.0` → `0.3.0` | MINOR |
| Cambiar el formato NoteMark: introducir `:::collapsible` (no rompe parseo) | `0.3.0` → `0.4.0` | MINOR |
| Cambiar el formato NoteMark: introducir sintaxis obligatoria que rompe IR de notas viejas | `0.4.0` → `1.0.0` | MAJOR |
| Bajar el threshold de Tesseract confidence | `1.0.0` → `1.0.1` | PATCH |
| Documentar mejor la API del renderer en `references/08-render/contract.md` | `1.0.1` → `1.0.2` | PATCH |
| Eliminar el destino `notion_md` (era bonus; se quita) | `1.0.2` → `2.0.0` | MAJOR |
| Mover F116 `failure-modes.md` a otra sección | `1.0.2` → `1.0.3` | PATCH |

## 4. Pre-releases

Identificadores canónicos pre-1.0:

| Tag | Significado |
|---|---|
| `-dev` | En desarrollo activo; el paquete funciona pero hay features pendientes. |
| `-rc.N` | Release candidate; listo para release salvo blockers menores. |
| `-alpha.N` | Alpha cerrada; solo para testers designados. |

Pre-1.0 el proyecto se considera "inestable" (semver §4). Cualquier bump antes de `1.0.0` puede romper compat incluso sin cambio de major.

Tras `1.0.0`, el proyecto sigue SemVer estricto: `0.x.y` termina.

## 5. Cómo bumpear

Procedimiento paso a paso (humano + herramienta):

1. **Detectar el bump type**:

   ```bash
   python3 scripts/check_version.py --propose-bump
   # Salida esperada: "Proposed bump: MAJOR|MINOR|PATCH based on N schemas modified."
   ```

   El script compara `git diff <last-tag>..HEAD -- schemas/` y propone tipo.

2. **Editar VERSION**:

   ```bash
   # De 0.1.0-dev a 0.2.0 (ejemplo MINOR):
   echo "0.2.0" > VERSION
   git add VERSION
   ```

3. **Editar CHANGELOG.md**: añadir nueva entrada `## [X.Y.Z] - YYYY-MM-DD` debajo de `## [Unreleased]`, mover items del `[Unreleased]` a la nueva release.

4. **Validar**:

   ```bash
   python3 scripts/check_version.py
   # Exit 0 si VERSION parsea + manifest.json coincide + schemas OK.
   ```

5. **Commitear + tag**:

   ```bash
   git commit -m "release: 0.2.0"
   git tag -a v0.2.0 -m "Release 0.2.0: añade destino Spaced Repetition"
   ```

6. **Publicar**:

   ```bash
   python3 scripts/build_skill.py --version 0.2.0
   python3 scripts/smoke_test.py --skill dist/notemartin-study-notes-0.2.0.skill
   # Subir el .skill a GitHub Releases u otro canal.
   ```

## 6. Cambios permitidos

**No reabren F123:**
- Añadir una entrada al `CHANGELOG.md` siguiendo el formato Keep-a-Changelog.
- Cambiar el orden de las fases en el bloque `### Closed`.
- Añadir un nuevo identificador pre-release (e.g. `-beta.N`) en §4.
- Añadir un nuevo ejemplo concreto en §3.
- Corregir typos en cualquier sección.

**Reabren F123:**
- Cambiar el formato SemVer (D2): pre-releases, build metadata, separadores.
- Cambiar el criterio de MAJOR/MINOR/PATCH (D3/D4/D5).
- Cambiar la regla de compat de artefactos (D6, ver COMPATIBILITY.md).
- Cambiar el formato del CHANGELOG (D7).
- Cambiar el procedimiento de bump de §5.
- Cambiar `VERSION` sin documentar en CHANGELOG (rompe invariante).
