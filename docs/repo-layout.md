# Layout del repositorio y del paquete — `docs/repo-layout.md`

> Documento normativo de la Fase 5 del roadmap. Declara la geometría del repositorio y del paquete `skill/notemartin-study-notes/`, fija la regla de ubicación y la regla de fuente única.
>
> Documentos complementarios: `skills/AGENT.md` §7 (reglas de contenido), `ROADMAP.md` §6 (árbol declarado sin READMEs), `docs/skill-anatomy.md` §6 (mapeo declarado a `references/`). Este doc los **referencia y completa**, no los repite.

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Árbol del repositorio](#2-árbol-del-repositorio) · 3. [Árbol del paquete](#3-árbol-del-paquete) · 4. [Qué viaja en el .skill](#4-qué-viaja-en-el-skill) · 5. [Regla de ubicación](#5-regla-de-ubicación) · 6. [Regla de fuente única](#6-regla-de-fuente-única) · 7. [Plantilla READMEs de references/](#7-plantilla-para-readmes-de-references) · 8. [Plantilla READMEs de schemas/ scripts/ assets/](#8-plantilla-para-readmes-de-schemas-scripts-assets) · 9. [README raíz del paquete](#9-readme-raíz-del-paquete) · 10. [docs/adr/](#10-docsadr) · 11. [Validación al cerrar](#11-validación-al-cerrar)

## 1. Propósito y alcance

Declarar la geometría del repositorio y del paquete `skill/notemartin-study-notes/`, fijar la regla de ubicación (qué va en cada carpeta) y la regla de fuente única (qué archivo es canónico para cada regla).

**No es** la anatomía (`docs/skill-anatomy.md`, F2), no es el manifiesto (`docs/product-manifesto.md`, F1), no es el contrato del workdir (`skill/notemartin-study-notes/references/00-pipeline/architecture.md`, F4). Esos tres docs definen qué hace la skill; este define dónde vive.

## 2. Árbol del repositorio

| Ruta | Rol | Estado |
|---|---|---|
| `README.md` (raíz) | Para contribuidores del proyecto | `[existente, vacío]` |
| `ROADMAP.md` | Roadmap de 125 fases; fuente de verdad de qué construir | `[existente]` |
| `CHANGELOG.md` | Bitácora de releases | `[pendiente F123]` |
| `CONTRIBUTING.md` | Guía de contribución | `[pendiente F124]` |
| `agent.md` | Contrato del agente desarrollador (humano) | `[pendiente]` |
| `PROGRESS.md` | Estado entre sesiones | `[pendiente]` |
| `docs/product-manifesto.md` | Manifiesto del producto | `[existente]` (F1) |
| `docs/skill-anatomy.md` | Anatomía y divulgación progresiva | `[existente]` (F2) |
| `docs/repo-layout.md` | Este doc | `[existente]` (F5) |
| `docs/adr/` | ADRs del proyecto | `[existente, vacío]` (F5) |
| `skill/notemartin-study-notes/` | Paquete instalable (`.skill`) | `[existente]` (F5) |
| `examples/` | Casos end-to-end con artefactos intermedios | `[pendiente F120]` |
| `evals/` | Corpus, rúbrica, suites, resultados | `[pendiente F6-F8, F118]` |
| `tests/` | Fixtures y golden files de los scripts | `[pendiente F48+]` |
| `.kilo/` | Configuración local de Kilo | `[existente, fuera del paquete]` |
| `.git/` | Metadatos de Git | `[existente, fuera del paquete]` |

## 3. Árbol del paquete

Subárbol de `skill/notemartin-study-notes/` que viaja dentro del `.skill` generado por F122.

| Ruta | Rol | Estado |
|---|---|---|
| `README.md` | Resumen para el usuario de la skill | `[existente]` (F5) |
| `SKILL.md` | Router N2; < 500 líneas | `[pendiente F9]` |
| `references/` | Prosa normativa N3 | `[existente, 13 archivos]` (F5) |
| `references/README.md` | Convención de la carpeta | `[existente]` |
| `references/00-pipeline/` | División, arquitectura, manifiesto | `[existente]` (F3, F4) |
| `references/01-ingest/` | OCR, layout, formatos | `[existente, vacío de archivos]` (F5) |
| `references/02-source-model/` | SDM, anclas, procedencia, semántica editorial | `[existente, vacío de archivos]` (F5) |
| `references/03-knowledge/` | Unidades, ledger, grafo, plan, terminología, conflictos | `[existente, vacío de archivos]` (F5) |
| `references/04-authoring/` | NoteMark, IR, marcas, propiedades, capas | `[existente, vacío de archivos]` (F5) |
| `references/05-note-types/` | Plantillas por tipo de nota | `[existente, vacío de archivos]` (F5) |
| `references/06-writing/` | Redacción, analogías, ejemplos, comparaciones | `[existente, vacío de archivos]` (F5) |
| `references/07-visual/` | Diagramas, figuras, tokens, densidad | `[existente, vacío de archivos]` (F5) |
| `references/08-render/` | Capacidades, contrato, enlaces, publicación | `[existente, vacío de archivos]` (F5) |
| `references/09-study/` | Estudio activo, autoevaluación, errores, rutas | `[existente, vacío de archivos]` (F5) |
| `references/10-quality/` | Fidelidad, auditoría de no-pérdida | `[existente, vacío de archivos]` (F5) |
| `references/11-i18n/` | Idioma bilingüe, citación | `[existente, vacío de archivos]` (F5) |
| `schemas/` | JSON Schema versionados | `[existente, vacío]` (F5) |
| `scripts/` | Ejecutables invocables | `[existente, vacío]` (F5) |
| `assets/` | Material copiable (tokens, CSS, plantillas) | `[existente, vacío]` (F5) |

## 4. Qué viaja en el `.skill`

Lista exhaustiva. Sin "etc.", sin "todo lo demás".

### 4.1 Sí viaja

| Archivo / carpeta | Origen en el repo | Motivo |
|---|---|---|
| `SKILL.md` | `skill/notemartin-study-notes/SKILL.md` | Router N2; única carga obligatoria al disparar la skill (F9) |
| `references/**` (toda la carpeta, raíz + 12 subcarpetas + archivos) | `skill/notemartin-study-notes/references/**` | Prosa normativa N3 que el agente lee en runtime |
| `schemas/**` (a medida que se creen) | `skill/notemartin-study-notes/schemas/**` | Validación de artefactos del workdir (F11-F16) |
| `scripts/**` + `scripts/README.md` | `skill/notemartin-study-notes/scripts/**` | Ejecutables invocables; catálogo legible (F17-F117) |
| `assets/**` | `skill/notemartin-study-notes/assets/**` | Material copiable (tokens, CSS, plantillas, paletas) (F11, F70-F76) |
| `README.md` (raíz del paquete) | `skill/notemartin-study-notes/README.md` | Versión "para el usuario de la skill", no la del repo |

### 4.2 No viaja

| Archivo / carpeta | Origen en el repo | Motivo |
|---|---|---|
| `ROADMAP.md` | raíz | Es para contribuidores; el usuario de la skill no lo necesita |
| `CHANGELOG.md` | raíz | Igual; pendiente F123 |
| `CONTRIBUTING.md` | raíz | Igual; pendiente F124 |
| `skills/AGENT.md` | `skills/` | Contrato del agente desarrollador, no del usuario |
| `docs/product-manifesto.md` | `docs/` | Doc del proyecto, no del paquete |
| `docs/skill-anatomy.md` | `docs/` | Doc del proyecto, no del paquete |
| `docs/adr/**` | `docs/adr/` | Decisiones del proyecto, no del paquete |
| `examples/` | raíz | Material de evaluación, no del paquete (F120) |
| `evals/` | raíz | Material de evaluación, no del paquete |
| `tests/` | raíz | Material de desarrollo, no del paquete |
| `agent.md`, `PROGRESS.md` | raíz | Cuando se creen, son del repo |
| `.kilo/`, `.git/` | raíz | Metadatos del repo y de la herramienta local |

## 5. Regla de ubicación

Tabla normativa. Cada nuevo archivo del proyecto se asigna por la primera columna que aplique.

| Tipo de contenido | Ubicación | Ejemplos |
|---|---|---|
| Prosa normativa para el agente (instrucciones en runtime) | `references/` | `references/04-authoring/notemark.md` |
| Contrato formal de un artefacto (JSON Schema) | `schemas/` | `schemas/sdm.schema.json` |
| Ejecutable invocable por su comando | `scripts/` | `scripts/ingest/ocr.py` |
| Material copiable (token, plantilla, CSS, paleta) | `assets/` | `assets/tokens.json` |
| Decisión arquitectónica del proyecto | `docs/adr/` | `docs/adr/ADR-0001-notemark.md` |
| Documento de referencia para el repo (no para el agente) | `docs/` | `docs/product-manifesto.md` |
| README raíz para el usuario de la skill | raíz del paquete | `skill/notemartin-study-notes/README.md` |
| README raíz para contribuidores del proyecto | raíz del repo | `README.md` (raíz) |

Tres casos canónicos resueltos:

- **Duda entre `references/` y `docs/`.** Si el lector primario es el **agente en runtime**, va a `references/`. Si el lector primario es un **humano revisando el proyecto**, va a `docs/`.
- **README del paquete vs README del repo.** Existen dos: el del paquete (`skill/notemartin-study-notes/README.md`) es para el usuario de la skill; el del repo (raíz) es para contribuidores. Cada uno viaja en su sitio (§4.1 y §4.2).
- **ADR dentro del repo.** Un ADR documenta una decisión del proyecto, no de la skill; vive en `docs/adr/` aunque `docs/` no viaje en el `.skill` (§4.2).

## 6. Regla de fuente única

Cada regla del proyecto tiene **un archivo canónico** y, opcionalmente, N archivos puntero. Un puntero se limita a citar la regla (por `INV-xx`, por ruta, o por frase corta) sin reproducir su contenido.

Auditoría de las reglas potencialmente duplicadas a la luz de los docs vigentes (`AGENT.md`, `ROADMAP.md`, los tres `docs/` y los `references/` ya entregados):

| Regla | Archivo canónico | Archivos puntero |
|---|---|---|
| Skill ≤ 500 líneas (`INV-02`) | `skills/AGENT.md` §2 | `ROADMAP.md` §3, `docs/skill-anatomy.md` §2.2 (cita `INV-02`) |
| 100 % `must-keep` antes de cerrar (`INV-08`) | `skills/AGENT.md` §2 | `ROADMAP.md` §1, `docs/product-manifesto.md` §3.1 (cita "puerta de fidelidad") |
| El agente escribe NoteMark, nunca JSON ni Markdown de destino (`INV-05`) | `skills/AGENT.md` §2 | `ROADMAP.md` §4 (Por qué NoteMark) |
| Una degradación nunca elimina contenido (`INV-07`) | `skills/AGENT.md` §2 | `ROADMAP.md` §1, `docs/product-manifesto.md` §3.4 |
| Test de tres preguntas para decidir script vs instrucción | `references/00-pipeline/responsibilities.md` §3.1 | `skills/AGENT.md` §3 (versión corta con referencia) |
| Modo degradado tiene umbral numérico | `references/00-pipeline/architecture.md` §8 | (sin duplicación actual) |
| Una capa lee su artefacto de entrada y el perfil, nada más | `references/00-pipeline/architecture.md` §5 | `skills/AGENT.md` §5 |
| Tabla de enrutado N3 → SKILL.md | `docs/skill-anatomy.md` §5 | (sin duplicación actual) |
| Fidelidad > cobertura > pedagogía | `docs/product-manifesto.md` §5 | (sin duplicación actual) |
| Las 4 garantías (fidelidad, cobertura, trazabilidad, portabilidad) | `docs/product-manifesto.md` §3 | (sin duplicación actual) |

Reglas derivadas:

- Las **invariantes** viven en `skills/AGENT.md` §2 (`INV-01` a `INV-17`) y se referencian desde otros archivos mediante el identificador `INV-xx`. Cualquier archivo que reproduzca una invariante sin citarla reabre este layout y se le pide reducir el texto a una referencia.
- Las **reglas operativas de la skill** viven en `references/` y se referencian desde `AGENT.md` o `ROADMAP.md` solo cuando hace falta cita; nunca se reproducen.
- Las **garantías del producto** viven en `docs/product-manifesto.md` y no se duplican en ningún otro archivo.

Spot-check al cerrar (criterio 2): tomar 5 invariantes al azar de `skills/AGENT.md` y buscar su contenido literal en otros archivos del repo; las menciones en otros archivos deben ser referencias a `INV-xx`, no reproducciones.

## 7. Plantilla para READMEs de `references/`

Cada subcarpeta de `references/` tiene un `README.md` con cuatro secciones:

1. **Propósito** (1-3 líneas): qué norma vive aquí.
2. **Orden de lectura** (cuándo cargar): capa del pipeline (L0-L4) y modo (nota rápida / capítulo / obra / actualización / re-render).
3. **Estado actual**: lista de archivos con `[existente]` o `[pendiente Fxxx]`.
4. **Quién lee / quién produce**: tabla con archivo → quién lo lee y qué fase lo entrega.

Las 12 subcarpetas usan esta plantilla con su contenido propio. El `README.md` raíz de `references/` describe la convención general y lista las subcarpetas.

## 8. Plantilla para READMEs de `schemas/`, `scripts/`, `assets/`

Tres secciones, distintas a las de `references/`:

1. **Propósito**: qué vive en esta carpeta.
2. **Qué vivirá aquí**: tabla de archivos previstos con la fase creadora.
3. **Cuándo se crea**: la fase que puebla la carpeta por primera vez.

Estas carpetas no son N3 leíbles: los schemas se validan, los scripts se ejecutan, los assets se cargan como dato. Por tanto no requieren "orden de lectura".

## 9. README raíz del paquete

`skill/notemartin-study-notes/README.md` es la versión "para el usuario de la skill": qué es, cómo se instala, cómo se invoca, cómo se contribuye, enlaces a los demás READMEs. Distinto del `README.md` raíz del repo (para contribuidores del proyecto).

## 10. `docs/adr/`

Casa de las decisiones arquitectónicas del proyecto. Cada ADR es un markdown corto con tres secciones (Contexto → Decisión → Consecuencias). Numeración correlativa `ADR-NNNN`. Las decisiones cerradas hoy viven en `skills/AGENT.md` §8; cuando alguna se reabre formalmente, se promueve a ADR aquí. Ver [`docs/adr/README.md`](adr/README.md).

## 11. Validación al cerrar

Comprobaciones grepeables que un revisor externo debe poder ejecutar:

1. `test -f docs/repo-layout.md` → existe.
2. `find skill/notemartin-study-notes -name README.md` → ≥ 17 archivos (1 raíz paquete + 1 raíz references + 12 subcarpetas + 3 subcarpetas de paquete = 17).
3. `find skill/notemartin-study-notes -type d -name 'NN-*'` → ≥ 12 directorios prefijados (uno por subcarpeta de `references/`).
4. `test -f docs/adr/README.md` → existe.
5. `wc -l docs/repo-layout.md` → ≤ 400.
6. `rg -c '^## ' docs/repo-layout.md` → ≥ 11 secciones.
7. §4 — `rg -c '^\| .+\..+` docs/repo-layout.md` en §4 → ≥ 14 filas (6 sí viaja + 8 no viaja, mínimo).
8. §6 — `rg 'fuente única|canónico|puntero' docs/repo-layout.md` → confirma la sección.
9. Spot-check — elegir 5 invariantes (`INV-01` a `INV-05`) de `AGENT.md` y buscar su contenido literal en otros archivos; las menciones en otros archivos deben ser referencias a `INV-xx`, no reproducciones.
10. `rg '^- \[ \]' ROADMAP.md` → no devuelve las tres casillas de Fase 5.

Si cualquiera falla, la fase no se marca como completa.
