# Checklists por tipo — `references/10-quality/checklists-by-type.md`

> Documento normativo de la **Fase 112** del roadmap. Define el checklist
> consolidado de cierre para los 15 tipos de nota del catálogo. Estructura:
> checklist común (universal), bloque específico por tipo, nota mínima
> viable embebida, separación bloqueantes [B] / recomendados [R], reglas
> por perfil (study / reference / hybrid) y orden de verificación de lo
> barato a lo caro.
>
> **Cuándo cargar:** en la verificación de cierre de cualquier nota,
> tras redactar la última sección específica del tipo y antes de cambiar
> `status: draft` → `published`. En modo incremental (F111) también se
> aplica al diff.
>
> **Wirings:**
> - `references/05-note-types/<tipo>.md` (F78-F92) — origen de cada bloque;
>   este archivo los consolida, no los duplica.
> - `references/07-visual/density.md` (F76) — reglas R1–R8 ejecutables por `density_check.py`.
> - `references/07-visual/note-templates.md` (F75) — patrón de cabecera y jerarquía visual.
> - `references/04-authoring/properties.md` (F47) — frontmatter canónico.
> - `references/04-authoring/inline-marks.md` (F46) — marcas `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::warning`, `:::example`, etc.
> - `references/06-writing/anti-patterns.md` (F100) — base de los [B] por AP transversal.
> - `references/06-writing/goal-profiles.md` (F105) — reglas por perfil (criterio 3).
> - `references/09-study/self-evaluation.md` (F102) — `## Autoevaluación` opt-in por perfil.
> - `assets/profile.template.yaml` (F11) — defaults por tipo.
> - `references/10-quality/fidelity-rules.md` (F42) — fuente de `{src:}` obligatoria en bloques fácticos.
> - `references/10-quality/completeness-audit.md` (F43) — auditoría de no-pérdida.
> - F113 `scripts/validate/` — suite consolidada que ejecuta este checklist.
> - F114 quality gate — mide cobertura de [B]/[R] cumplidos.
> - F118 evals — suite automatizada.

---

## §1 · Propósito y alcance

Cerrar una nota implica verificar **al menos 25 criterios** que viven
actualmente dispersos en los §6 de los 15 archivos `05-note-types/*.md`.
Este documento:

- **Consolida** el checklist común (universal) y los 15 bloques específicos.
- **Separa** explícitamente bloqueantes [B] de recomendados [R] con un prefijo
  literal que un script puede parsear (`^- \[ \] \[(B|R)\] `).
- **Ordena** los pasos de verificación de lo más barato a lo más caro
  (§6), permitiendo early-exit en el primer [B] que falla.
- **Condiciona** por perfil (`study` | `reference` | `hybrid`): el criterio 3
  del ROADMAP prohíbe que el perfil `reference` exija secciones pedagógicas
  (Analogía, Intuición, Comparaciones ≥ 2, Autoevaluación, Práctica, etc.).

**Sí es**: el contrato de cierre de cualquier nota del catálogo.

**No es**: el validador (F113) ni la quality gate (F114); este documento los
**define**, no los **implementa**.

---

## §2 · Cuándo se aplica

| Capa / fase | Lee este doc cuando… |
|---|---|
| Agente al cerrar L3 | Tras redactar la última sección específica del tipo, antes de `status: published`. |
| F43 auditoría | Al auditar cobertura del ledger contra nota. |
| F113 validadores | Para extraer la lista cerrada de [B] por tipo. |
| F114 quality gate | Para calcular % de [B] cumplidos y reportar [R] como warnings. |
| F111 incremental | Para diff de cierre entre versión vieja y nueva. |
| F118 evals | Como golden list de cierre de los golden files. |

**No se aplica a**: ingesta (L0–L1), render puro (L4), notas sin clasificar.

---

## §3 · Checklist común (universal, sin perfil)

Aplica a los 15 tipos. Los [B] fallidos retornan exit ≠ 0 en el validador
consolidado (F113); los [R] son warnings.

### §3.1 · Bloqueantes [B] (orden cheap → expensive)

- [ ] [B] YAML frontmatter parsea sin error y contiene los 5 campos en orden: `title`, `note-type`, `status`, `summary`, `reading-time-minutes` (F75 §2.1, INV-P5).
- [ ] [B] `note-type` ∈ enum cerrado de 15 valores (F47, F93).
- [ ] [B] `status` ∈ {`draft`, `published`}; los demás campos obligatorios solo se exigen en `published`.
- [ ] [B] JSON Schema del frontmatter valida contra `schemas/properties.schema.json` (F47, paso < 5 ms).
- [ ] [B] `## TL;DR` presente y ≤ 60 palabras / 8 líneas (R1, F76), salvo `chapter-digest` que admite ≤ 120 (F75 §6.9).
- [ ] [B] `## Cabecera` presente con tabla 5 filas: Resumen, Procedencia, Versión, Estado, Tiempo de lectura (F75 §2.1).
- [ ] [B] El orden de las secciones obligatorias del tipo coincide con el patrón de F75 §6.X para ese tipo.
- [ ] [B] Densidad `{src:blk_xxxx}` ≥ 0.80 sobre bloques fácticos (R8, F76) — verificable con `density_check.py --note <path>`.
- [ ] [B] `scripts/validate/density_check.py --note <path>` retorna exit 0 sin violaciones (F76).
- [ ] [B] `scripts/validate/validate_ir.py --ir <path>` retorna exit 0 — parser acepta la nota (F14).
- [ ] [B] `scripts/validate/mermaid.py --fail-on error` retorna exit 0 — ningún Mermaid roto (F100 §3 S9, F66).

### §3.2 · Recomendados [R] (orden cheap → expensive)

- [ ] [R] Ningún color literal en el cuerpo; tokens via `assets/tokens.json` (INV-14, F72).
- [ ] [R] Todas las menciones a términos canónicos en `[[term:nombre]]` en su primera aparición (INV-I2, F46).
- [ ] [R] `## Procedencia` al pie con 4 campos cerrados: Fuente, Versión, Fecha ISO YYYY-MM-DD, URL/anchor (F101 §3).
- [ ] [R] Notas con `language == es-en` o `en-es` introducen términos bilingües con `[[en:term]]` o `[[es:term]]` en primera mención + bloque `## Glosario` (F101 §4).
- [ ] [R] Sin anti-patrones transversales AP1–AP12 del F100 §3 (transcripción disfrazada, definiciones circulares, callouts decorativos, tabla de 1 fila, analogía sin rotura, diagrama redundante, enlace sin frase, volcado de viñetas, marketing, `:::example` sin caption, sección vacía).
- [ ] [R] `## Backlinks` + `## Queries` cuando hay aristas o queries activas (F75 §6.X convención por tipo; algunos tipos lo tienen como [B], ver §4.X).
- [ ] [R] Ninguna sección vacía: cada `##` lleva ≥ 1 párrafo sustantivo ≥ 30 caracteres (AP12).

---

## §4 · Bloques por tipo

Cada subsección es normativa para su tipo. Los ítems aquí listados se
**suman** al checklist común de §3; no lo sustituyen. Los `## §7 · Nota
mínima viable` que aparecen al pie de cada archivo `05-note-types/<tipo>.md`
se conservan **verbatim** allí; este archivo los referencia, no los copia.

### §4.1 · `concept` (F78)

Fuente normativa detallada: `references/05-note-types/concept.md`.

#### Bloqueantes [B]

- [ ] [B] Las 10 secciones obligatorias (Problema → Relacionados) presentes y en orden.
- [ ] [B] `## Límites y alternativas` presente con ≥ 1 fila (ROADMAP F78).
- [ ] [B] `## Resumen` con 3–5 viñetas y `{src:}` ≥ 0.80 (R8).
- [ ] [B] `## Cuándo NO usarlo` con ≥ 1 bullet + `[[note:id]]`.
- [ ] [B] `## Trampas` con ≥ `min_traps` (default 1) bloque `:::warning` (R8).
- [ ] [B] `## Práctica` presente solo si `profile.notes.types.concept.include_practice: true` (F11, F92) — **OMIT en `reference`**.

#### Recomendados [R]

- [ ] [R] `## Comparaciones` con ≥ `min_comparisons` conceptos comparados (default 2) — **OMIT en `reference`**.
- [ ] [R] `## Intuición` presente — **OMIT en `reference`**.
- [ ] [R] `## Analogía` con rotura explícita (F95 §4) — **OMIT en `reference`**.
- [ ] [R] Si `## Práctica` está presente, lleva `{layer:l3}` y `:::collapsible` si > 100 líneas (R7).
- [ ] [R] `## Autoevaluación` con H3 `### Recuerdo`, `### Aplicación`, `### Decisión`, cada una con 3–7 `:::collapsible{default_open=false}` (F102) — **OMIT en `reference`**.
- [ ] [R] `## Decisiones de diseño` + `## Explicación oral` si `goal_profile == interview` (F105 R-G4).
- [ ] [R] `## Objetivos oficiales` + `certification-objective` en frontmatter si `goal_profile == certification` (F105 R-G5).
- [ ] [R] `## Backlinks` (si hay aristas) + `## Queries` (si hay queries).

#### Nota mínima viable

Referencia: `references/05-note-types/concept.md` §7 (concepto auto-definido
"Pipeline L0–L4", ~30 líneas, pasa `density_check.py --strict` exit 0).

---

### §4.2 · `api-reference` (F79)

Fuente normativa detallada: `references/05-note-types/api-reference.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio: `source`, `source-type`, `source-anchor`, `retrieved`, `vendor`, `product`, `product-version` (F75 §6.4).
- [ ] [B] Las 9 secciones obligatorias (Sintaxis → Gotchas) presentes y en orden.
- [ ] [B] `## Sintaxis` con bloque `code` con la firma completa (incluye alternativas, modificadores, defaults posicionales).
- [ ] [B] `## Parámetros` con tabla 5-col: `Parámetro`, `Tipo`, `Obligatorio`, `Default`, `Descripción`; cero celdas vacías en Tipo/Obligatorio/Default/Descripción.
- [ ] [B] SDM lista N parámetros → tabla tiene N filas.
- [ ] [B] `## Retornos` con tipo de retorno y descripción de flujo de salida (stdout, exception, side-effect).
- [ ] [B] `## Excepciones` con tabla o `:::danger` (nunca prosa).
- [ ] [B] `## Ejemplos` con ≥ `min_examples` bloques `:::example` o `code` con caption.
- [ ] [B] `## Gotchas` con ≥ 1 `:::warning` (recomendado 3–5).
- [ ] [B] Si ≥ 15 subprogramas en el mismo SDM, cada uno tiene `### Subprograma: <nombre>` con firma + tabla.
- [ ] [B] `## Privilegios` ≠ `## Precondiciones` (sin duplicar contenido).

#### Recomendados [R]

- [ ] [R] Si `## Parámetros` > 100 líneas, `:::collapsible` con `default_open: true` (R7).
- [ ] [R] `## Notas` solo si hay material del SDM y `include_notes: true` (F11).
- [ ] [R] `## Backlinks` + `## Queries` cuando hay aristas.

#### Nota mínima viable

Referencia: `references/05-note-types/api-reference.md` §7 (`docker run`,
~50 líneas de cuerpo, pasa `density_check.py --strict` exit 0).

---

### §4.3 · `procedure` (F80)

Fuente normativa detallada: `references/05-note-types/procedure.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` recomendado.
- [ ] [B] Las 8 secciones obligatorias (Objetivo → Errores frecuentes) presentes y en orden.
- [ ] [B] `## Objetivo` con 1 frase medible (qué cambia, en qué condiciones).
- [ ] [B] `## Aplicabilidad` con lista explícita de SÍ/NO (cuándo aplica y cuándo no).
- [ ] [B] `## Precondiciones verificadas` con ≥ 1 condición testeable.
- [ ] [B] `## Procedimiento` con pasos numerados (≥ `min_steps`, default 2).
- [ ] [B] Cada paso tiene `**Verificación:**` explícita que confirme el efecto esperado.
- [ ] [B] Pasos destructivos envueltos en `:::danger` con resumen del riesgo.
- [ ] [B] `## Impacto y reversibilidad` con tabla que incluye columna Rollback **o** declaración explícita de irreversibilidad.
- [ ] [B] `## Verificación final` con ≥ 1 criterio global post-procedimiento.
- [ ] [B] `## Errores frecuentes` con ≥ 1 `:::danger` o `:::warning`.

#### Recomendados [R]

- [ ] [R] ≤ 10 pasos por bloque en `## Procedimiento` (anti-patrón §6.3).
- [ ] [R] Cada paso con bloque `code` con lenguaje explícito.
- [ ] [R] `## Backlinks` + `## Queries` si queries activas.

#### Nota mínima viable

Referencia: `references/05-note-types/procedure.md` §7 ("Rotar logs de nginx
sin reiniciar", ~50 líneas, pasa `density_check.py --strict` exit 0).

---

### §4.4 · `configuration` (F81)

Fuente normativa detallada: `references/05-note-types/configuration.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio: `source`, `source-type`, `source-anchor`, `retrieved`, `vendor`, `product`, `product-version`.
- [ ] [B] `## Configuración` con bloque `code` comentado (idioma explícito: `ini`, `yaml`, `toml`, `conf`).
- [ ] [B] `## Parámetros` con tabla en orden: Parámetro, Ámbito, Tipo, Default, Rango, Hot reload, Reinicio, Versión, Impacto; cero celdas vacías en Parámetro / Ámbito / Tipo / Default / Impacto.
- [ ] [B] `## Ejemplo completo` con `:::example` + bloque `code` real (no abstracto).
- [ ] [B] `## Combinaciones peligrosas` con ≥ 1 `:::danger` (no `:::warning`).
- [ ] [B] `## Interacciones` documenta toda interacción del SDM entre parámetros.
- [ ] [B] `## Diagrama de dependencias` con `:::diagram` Mermaid ≥ 3 nodos cuando hay ≥ 3 parámetros interrelacionados.
- [ ] [B] Ninguna recomendación sin respaldo: cada `recomendamos|sugerido|usar` lleva `{src:}` o `:::external` (F42).

#### Recomendados [R]

- [ ] [R] Si tabla > 30 filas, `:::collapsible` con `default_open: false` (R7).
- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/configuration.md` §7
("postgresql.conf — 4 parámetros críticos de memoria", ~50 líneas).

---

### §4.5 · `error-troubleshooting` (F82)

Fuente normativa detallada: `references/05-note-types/error-troubleshooting.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio.
- [ ] [B] `## Síntomas` con ≥ 1 bloque `code` con mensaje literal **idéntico carácter por carácter** al SDM.
- [ ] [B] `## Causa raíz` con párrafo por cada error cubierto.
- [ ] [B] `## Diagnóstico ordenado` con pasos numerados para confirmar la causa (cada paso con verificación).
- [ ] [B] `## Solución` con pasos numerados por error.
- [ ] [B] `## Prevención` con `:::tip` por error.
- [ ] [B] `## Confundibles` con `[[note:id]]`; confundibles **bidireccionales** (la nota target tiene backlink).
- [ ] [B] `## Árbol de diagnóstico` con `:::diagram` Mermaid.
- [ ] [B] `## Tabla índice` con ≥ 1 fila por mensaje literal (mensaje exacto → sección).
- [ ] [B] Pasos destructivos envueltos en `:::danger`.

#### Recomendados [R]

- [ ] [R] Enlace opcional desde `## Síntomas` o `## Causa raíz` al living-doc de errores propios del estudiante (`[[study-error:<dominio>:<id>]]`) si existe (F103).
- [ ] [R] Esta nota NO contiene el registro subjetivo: solo el error objetivo + corrección + enlaces canónicos (F103 §1).
- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/error-troubleshooting.md` §7
("PostgreSQL — 3 errores de conexión", ~70 líneas).

---

### §4.6 · `architecture` (F83)

Fuente normativa detallada: `references/05-note-types/architecture.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` recomendado.
- [ ] [B] `## Vista general` con `:::diagram` Mermaid (1 diagrama mínimo del sistema completo).
- [ ] [B] `## Componentes y responsabilidades` con tabla 3-col (Componente, Responsabilidad, Ubicación); cada responsabilidad ≤ 30 palabras en su primera frase.
- [ ] [B] `## Flujo paso a paso` con ≥ 3 pasos numerados Y diagrama Mermaid `sequenceDiagram`.
- [ ] [B] `## Interacciones` con tabla o diagrama detallado de protocolos y frecuencias.
- [ ] [B] `## Estructuras en memoria y disco` con 2 sub-secciones (memoria, disco) y tamaño típico por entrada.
- [ ] [B] `## Puntos de fallo` con `:::warning`/`:::danger` con `{src:blk_xxxx}` por punto.
- [ ] [B] `## Cuellos de botella` con `:::warning` y métrica concreta (qps, latencia, throughput).

#### Recomendados [R]

- [ ] [R] `## Decisiones de diseño` con lista numerada y trade-off aceptado — **OMIT en `reference`** (F105 R-G4).
- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/architecture.md` §7
("Redis — arquitectura interna", ~70 líneas con 4 componentes).

---

### §4.7 · `syntax` (F84)

Fuente normativa detallada: `references/05-note-types/syntax.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio.
- [ ] [B] `## Convención de metasímbolos` con tabla de cada metasímbolo (`::=`, `|`, `[...]`, `{...}`, `(...)`, `<...>`) y su significado.
- [ ] [B] `## Sintaxis` con bloque `code` con BNF/EBNF/JSON Schema completa (idioma explícito).
- [ ] [B] `## Cláusula por cláusula` con tabla `Token / Descripción / Ejemplo`.
- [ ] [B] Cada cláusula `[]` en BNF tiene `###` sub-sección.
- [ ] [B] `## Diagramas de sintaxis` con `:::diagram` Mermaid ≥ 3 nodos.
- [ ] [B] `## Ejemplos graduales` con ≥ 3 ejemplos en `:::example` (mínimo → completo).
- [ ] [B] `## Contraejemplos` con ≥ 1 `:::warning` con input + error literal.

#### Recomendados [R]

- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/syntax.md` §7
("SQL SELECT — sintaxis BNF (PostgreSQL 16)", ~80 líneas).

---

### §4.8 · `data-model` (F85)

Fuente normativa detallada: `references/05-note-types/data-model.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` recomendado.
- [ ] [B] `## Modelo` con `:::diagram` Mermaid `erDiagram`.
- [ ] [B] `## Entidades` con ≥ 3 sub-secciones H3 (una por entidad).
- [ ] [B] `## Campos` con tabla 4-col; cada fila tiene Tipo y Restricciones no vacíos.
- [ ] [B] `## Relaciones` con tabla y cardinalidad explícita; las relaciones coinciden con el ER.
- [ ] [B] `## Claves e índices` con tabla (PK + secundarios por entidad).
- [ ] [B] `## Integridad` con `:::warning`/`:::danger` por tipo (PK, FK, UNIQUE, NOT NULL, CHECK) con `{src:}`.
- [ ] [B] `## Consultas típicas` con ≥ 3 queries SQL en `:::example`.
- [ ] [B] `## Evolución` con ≥ 1 cambio documentado (versión + diff).

#### Recomendados [R]

- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/data-model.md` §7
("Biblioteca — modelo de datos", ~85 líneas con 4 entidades).

---

### §4.9 · `chapter-digest` (F86)

Fuente normativa detallada: `references/05-note-types/chapter-digest.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio.
- [ ] [B] `coverage: summary` declarado en frontmatter (F75 §6.9).
- [ ] [B] `## TL;DR` ≤ 120 palabras (F75 §6.9: L1 extendida).
- [ ] [B] `## Resumen ejecutivo` con 1–2 párrafos.
- [ ] [B] `## Continuidad` con `### Hacia atrás` Y `### Hacia adelante`.
- [ ] [B] `## Puntos clave` con 3–7 bullets.
- [ ] [B] `## Conceptos nuevos` con ≥ 3 conceptos con `[[note:id]]` o `[[term:nombre]]`.
- [ ] [B] `## Citas textuales` con ≥ 1 `:::external` con cita literal.
- [ ] [B] `## Énfasis del autor` con ≥ 1 `:::note`.
- [ ] [B] `## Detalles` con sub-secciones H3 (mecanismos / código / diagramas).
- [ ] [B] `## Conexiones` con ≥ 1 `:::derived`.
- [ ] [B] `## Erratas` con ≥ 1 `:::warning`.
- [ ] [B] `## Ejercicios` con ≥ 1 ejercicio en `:::example`.
- [ ] [B] `## Ver también` siempre presente (F75 §6.9).

#### Recomendados [R]

- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/chapter-digest.md` §7
("PostgreSQL 16 — Ch 13: Concurrency Control (digest)", ~95 líneas).

---

### §4.10 · `comparison` (F87)

Fuente normativa detallada: `references/05-note-types/comparison.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` recomendado.
- [ ] [B] `## Comparativa` con tabla; ≥ 4 criterios; última fila con `:::tip` (fila decisiva).
- [ ] [B] `## Síntesis` con ≥ 2 similitudes + 1 diferencia clave.
- [ ] [B] Criterios paralelos: cada opción tiene valor en cada criterio (sin celdas vacías).
- [ ] [B] `## Criterios` con bullets explicando cada criterio.
- [ ] [B] `## Matriz de decisión por escenario` con ≥ 3 escenarios.
- [ ] [B] `## Trade-offs` con ≥ 3 filas.
- [ ] [B] `## Veredicto` con 1–2 párrafos.
- [ ] [B] Afirmaciones derivadas marcadas con `:::derived` o `:::external`.

#### Recomendados [R]

- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/comparison.md` §7
("PostgreSQL vs MySQL (comparativa)", ~80 líneas).

---

### §4.11 · `version-delta` (F88)

Fuente normativa detallada: `references/05-note-types/version-delta.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` obligatorio.
- [ ] [B] `product-version` (NUEVA) declarada en frontmatter.
- [ ] [B] `## Cambios` con tabla 4-col: Versión exacta, Tipo, Área, Descripción.
- [ ] [B] Cada fila tiene Versión exacta con formato semver.
- [ ] [B] Cada fila tiene Tipo ∈ {`nuevo`, `cambiado`, `deprecado`, `eliminado`, `default alterado`}.
- [ ] [B] `## Breaking changes` con `:::danger`.
- [ ] [B] `## Cambios de default` con sección propia cuando hay ≥ 1 cambio de default.
- [ ] [B] `## Migración` con pasos numerados y bloques `code`.
- [ ] [B] `## Trampas de migración` con ≥ 1 `:::warning`.
- [ ] [B] `## Notas afectadas` con ≥ 2 `[[note:id]]` (enlaces bidireccionales).

#### Recomendados [R]

- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/version-delta.md` §7
("PostgreSQL 16 — delta v15 → v16", ~95 líneas).

---

### §4.12 · `glossary-term` (F89)

Fuente normativa detallada: `references/05-note-types/glossary-term.md`.

#### Bloqueantes [B]

- [ ] [B] `## TL;DR` = 1–2 frases = definición del término.
- [ ] [B] `## Definición` con 1 frase ≤ 30 palabras.
- [ ] [B] `## Formas` con ≥ 2 formas (inglés + español o forma + sigla).
- [ ] [B] `## Aliases` con ≥ 1 alias.
- [ ] [B] `## Contexto` con `:::tip` por dominio (si aplica).
- [ ] [B] `## Ejemplos` con ≥ 1 `:::example`.
- [ ] [B] `## Confundibles` con ≥ 1 confundible con `[[note:]]` o `[[term:]]`.
- [ ] [B] `## Notas donde aparece` con ≥ 1 `[[note:id]]`.
- [ ] [B] `## Backlinks` obligatorio.
- [ ] [B] **≤ 30 líneas totales** (F75 §6.12 anti-patrón duro).

#### Recomendados [R]

- [ ] [R] `density_check.py --note <path>` exit 0.

#### Nota mínima viable

Referencia: `references/05-note-types/glossary-term.md` §7
("MVCC", ~25 líneas).

---

### §4.13 · `cheatsheet` (F90)

Fuente normativa detallada: `references/05-note-types/cheatsheet.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` recomendado.
- [ ] [B] `## TL;DR` con 1 frase ≤ 30 palabras.
- [ ] [B] `## Comandos` con tabla 3-col; ≥ 10 filas; ≤ 30 filas (F75 §6.13).
- [ ] [B] Cada fila de `## Comandos` tiene `[[note:id]]` o `[[term:X]]`.
- [ ] [B] `## Atajos` con tabla 2-col ≥ 5 filas si aplica al dominio (F75 §6.13).
- [ ] [B] **Sin párrafos de prosa > 50 palabras** (anti-patrón).
- [ ] [B] **≤ 80 líneas totales** (≤ 2 pantallas).

#### Recomendados [R]

- [ ] [R] `## Errores comunes` con `:::warning` por código (opcional, no obligatorio).
- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/cheatsheet.md` §7
("PostgreSQL 16 cheatsheet", ~70 líneas).

---

### §4.14 · `index-moc` (F91)

Fuente normativa detallada: `references/05-note-types/index-moc.md`.

#### Bloqueantes [B]

- [ ] [B] `source-bearing` opcional (F75 §6.14).
- [ ] [B] `## Introducción` con 1–2 párrafos.
- [ ] [B] `## Mapa conceptual` con `:::diagram` Mermaid.
- [ ] [B] `## Índice` con links agrupadas por H3; cada `[[note:id]]` con descripción de 1 frase.
- [ ] [B] `## Prerrequisitos` con lista de notas.
- [ ] [B] `## Rutas de lectura` con ≥ 3 rutas.
- [ ] [B] `## Estado de cobertura` con tabla (Notas creadas, Pendientes, Planeadas).
- [ ] [B] `## Cobertura de la fuente` con keywords "cubre" + "no cubre".
- [ ] [B] `## Pendientes` con notas en `status: draft`.
- [ ] [B] `## Consulta rápida` con tabla.
- [ ] [B] **≤ 200 líneas totales**.
- [ ] [B] **Sin contenido fáctico** (F75 §6.14 anti-patrón).

#### Recomendados [R]

- [ ] [R] Sin `## Backlinks` (F75 §6.14 convención).
- [ ] [R] `density_check.py --note <path>` exit 0.

#### Nota mínima viable

Referencia: `references/05-note-types/index-moc.md` §7
("PostgreSQL 16 — Map of Content", ~115 líneas).

---

### §4.15 · `practice` (F92)

Fuente normativa detallada: `references/05-note-types/practice.md`.

#### Bloqueantes [B]

- [ ] [B] `difficulty` (1–5) declarado en frontmatter (F75 §6.15).
- [ ] [B] `source-bearing` recomendado.
- [ ] [B] `## Enunciado` con 1 párrafo (qué se hace, con qué datos, en qué entorno).
- [ ] [B] `## Entorno` con tabla y ≥ 3 componentes (Sistema, Producto, Recursos).
- [ ] [B] `## Objetivo` con 1–2 frases medibles.
- [ ] [B] `## Solución` con pasos numerados.
- [ ] [B] Cada paso destructivo con `:::warning` antes del code block.
- [ ] [B] `## Qué observar` con `:::note` o lista (qué cambia, qué logs mirar).
- [ ] [B] `## Verificación` con 1 frase (cómo saber si el lab salió bien).
- [ ] [B] `## Limpieza` con ≥ 1 paso (devolver el sistema al estado original).
- [ ] [B] `## Lo que NO debe correrse en producción` con `:::danger` — **OMIT en `reference`**.
- [ ] [B] `## Cuándo omitir este lab` con ≥ 1 criterio — **OMIT en `reference`** si el criterio es pedagógico.

#### Recomendados [R]

- [ ] [R] `## Pistas` con `:::tip` cuando el lab es no trivial — **OMIT en `reference`**.
- [ ] [R] `## Backlinks` + `## Queries`.

#### Nota mínima viable

Referencia: `references/05-note-types/practice.md` §7
("PostgreSQL — backup + restore con pg_dump/pg_restore", ~60–100 líneas).

---

## §5 · Reglas por perfil

El criterio 3 del ROADMAP es: **ningún criterio del checklist exige elementos
académicos en perfil `reference`**. Esta tabla codifica qué secciones se
**deben omitir** (no exigir, no penalizar) cuando el perfil activo es
`reference`.

### §5.1 · Tabla tipo × omit-en-`reference`

La columna `[B]` en `study`/`reference`/`hybrid` se detalla en §4.X; aquí
solo se lista qué secciones se **omiten** en `reference` (es decir, no se
exigen y no se penaliza su ausencia). El verificador `check_reference_profile.py`
garantiza que ninguna de estas secciones aparece como `[B]` en `§4.X`.

| Tipo | OMIT en `reference` |
|---|---|
| `concept` | `## Analogía`, `## Intuición`, `## Comparaciones` (≥ 2), `## Práctica`, `## Autoevaluación`, `## Decisiones de diseño`, `## Objetivos oficiales` |
| `api-reference` | (ninguno: tipo operacional puro) |
| `procedure` | (ninguno: tipo operacional puro) |
| `configuration` | (ninguno) |
| `error-troubleshooting` | (ninguno) |
| `architecture` | `## Decisiones de diseño` (reflexiva, no factual) |
| `syntax` | (ninguno: tipo técnico puro) |
| `data-model` | (ninguno) |
| `chapter-digest` | `## Énfasis del autor`, `## Conexiones`, `## Erratas`, `## Ejercicios` |
| `comparison` | (ninguno: tipo operativo) |
| `version-delta` | (ninguno: tipo técnico) |
| `glossary-term` | (ninguno: tipo definicional) |
| `cheatsheet` | (ninguno: tipo referencial puro) |
| `index-moc` | (ninguno) |
| `practice` | `## Lo que NO debe correrse en producción`, `## Cuándo omitir este lab`, `## Pistas` |

### §5.2 · Verificación mecánica del criterio 3

`evals/checklists-sample/check_reference_profile.py` valida:

1. La columna `[B]` en `reference` NO contiene ninguna de las 7 secciones
   pedagógicas OMIT: `Intuición`, `Analogía`, `Comparaciones` (≥ 2),
   `Autoevaluación`, `Práctica`, `Decisiones de diseño`, `Objetivos
   oficiales`, `Lo que NO debe correrse en producción`, `Cuándo omitir este
   lab`, `Pistas`, `Ejercicios`, `Énfasis del autor`, `Conexiones`.
2. Las secciones OMIT marcadas como `[R]` en `study` (Analogía, Intuición,
   Comparaciones, Autoevaluación, Práctica, Decisiones de diseño, Objetivos
   oficiales) tampoco se trasladan a `[B]` en `reference`.
3. Cada tipo tiene al menos 1 ítem `[B]` que **sí** se exige en `reference`
   (verificación de cobertura no-vacía).

Salida: PASS si los 15 tipos cumplen; FAIL con lista de tipos y reglas
incumplidas en otro caso.

---

## §6 · Orden de verificación (cheap → expensive)

El validador consolidado (F113) ejecuta los pasos en este orden. Cada paso
debe poder ejecutarse sin cargar la nota completa en memoria más de una
vez; el primero que falla aborta la verificación.

| # | Paso | Coste | Acción | Falla ⇒ |
|---|---|---|---|---|
| 1 | YAML frontmatter | < 1 ms | Parse + 5 campos obligatorios (F75 §2.1) | abort |
| 2 | JSON Schema frontmatter | < 5 ms | `schemas/properties.schema.json` (F47) | abort |
| 3 | Densidad R1–R8 | < 50 ms | `density_check.py` (F76) | abort |
| 4 | Validación IR | < 100 ms | `validate_ir.py --ir <path>` (F14) | abort |
| 5 | Mermaid parse | < 500 ms | `mermaid.py --fail-on error` por bloque (F100 §3 S9, F66) | abort |
| 6 | AP locales | < 1 s | AP1, AP3, AP4, AP8, AP12 (F100 §3) | abort |
| 7 | AP con cálculo global | 1–5 s | AP2 (Jaccard), AP7 (introducción ≥ 5 palabras), AP10, AP11 | warn |
| 8 | AP con análisis semántico | segundos | AP5 (analogía con rotura), AP6 (diagrama vs párrafo) | warn |
| 9 | Backlinks remotos | red | `curl` a destinos publicados para backlinks/queries (F77) | warn |

**Early-exit:** si el paso N falla con severidad `[B]`, los pasos N+1..9 no
se ejecutan para esa nota. Los warnings (severidad `[R]` fallida) se
acumulan y se reportan al final sin abortar.

**Notas que el validador reporta aparte:**
- Pasos 7–8 pueden omitirse si el agente declara `profile.review.fast: true`.
- Paso 9 se omite si la nota no tiene destinos publicados.

---

## §7 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults por tipo (`min_comparisons`,
  `min_traps`, `min_steps`, `min_examples`, `include_practice`,
  `include_notes`).
- **F14** `references/04-authoring/ir-spec.md` y `schemas/note-ir.schema.json` — paso 4 de §6.
- **F42** `references/10-quality/fidelity-rules.md` — base del paso 1 de §6
  (prohibiciones absolutas de valores técnicos sin respaldo).
- **F43** `references/10-quality/completeness-audit.md` — auditoría de no-pérdida.
- **F45** `references/04-authoring/block-directives.md` — directivas usadas en
  los ítems `[B]` (especialmente `:::warning`, `:::danger`, `:::example`).
- **F46** `references/04-authoring/inline-marks.md` — marcas usadas en los
  ítems `[B]` (`{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`).
- **F47** `references/04-authoring/properties.md` y `schemas/properties.schema.json` — paso 2 de §6.
- **F66** `references/07-visual/mermaid-portable.md` — paso 5 de §6.
- **F75** `references/07-visual/note-templates.md` — patrón cabecera, jerarquía,
  tabla 5 filas de `## Cabecera`, convención por tipo.
- **F76** `references/07-visual/density.md` — R1–R8 ejecutables; paso 3 de §6.
- **F78–F92** `references/05-note-types/<tipo>.md` — fuentes de §4.1–§4.15;
  este archivo los **consolida**, no los duplica.
- **F93** `references/05-note-types/selector.md` — entrada al catálogo de tipos.
- **F95** `references/06-writing/analogies.md` — base del ítem [B] Analogía con rotura (paso 8 de §6).
- **F100** `references/06-writing/anti-patterns.md` — base de los pasos 6–8 de §6.
- **F101** `references/06-writing/i18n-and-citation.md` — `## Procedencia`, bilingüismo.
- **F102** `references/09-study/self-evaluation.md` — `## Autoevaluación` opt-in.
- **F103** `references/09-study/error-log.md` — living-doc de errores del estudiante.
- **F105** `references/06-writing/goal-profiles.md` — `goal_profile` interview/certification.
- **F113** `scripts/validate/` — implementa el paso 1–9 de §6 con severidades
  error/warning/info; exit ≠ 0 ante [B] fallido.
- **F114** `scripts/quality_gate.py` — mide cobertura de [B]/[R] cumplidos.
- **F118** `evals/` — corre la suite automatizada sobre el corpus y golden files.

---

## §8 · Verificación al cierre de la fase

- `wc -l references/10-quality/checklists-by-type.md` ≤ 600 líneas.
- §3 con subsecciones §3.1 ([B]) + §3.2 ([R]); cada ítem con prefijo `[B]` o `[R]`.
- §4 con 15 subsecciones (concept, api-reference, procedure, configuration,
  error-troubleshooting, architecture, syntax, data-model, chapter-digest,
  comparison, version-delta, glossary-term, cheatsheet, index-moc,
  practice), cada una con `[B]` + `[R]` + referencia al `## §7 · Nota mínima
  viable` del archivo del tipo.
- §5 con tabla 15 filas (tipos) × 5 columnas (perfiles + omit) verificable
  mecánicamente.
- §6 con 9 filas (cheap → expensive) y script concreto en cada fila.
- §7 con al menos 16 wirings documentados (F11, F14, F42–F47, F66, F75–F76,
  F78–F93, F95, F100–F103, F105, F113, F114, F118).
- `evals/checklists-sample/run_eval.py` con **3/3 PASS** (check_blockers +
  check_recommended_separation + check_reference_profile).
- Wirings actualizados en `references/05-note-types/README.md`,
  `references/10-quality/README.md`, `SKILL.md` (tabla de enrutado N2) y
  `docs/skill-anatomy.md` §6 fila F112.

**Criterios de aceptación del ROADMAP F112:**

1. _Cada tipo tiene su bloque y su nota mínima viable._ → §4.1–§4.15 cada
   una con `[B]` + `[R]` + enlace al `## §7 · Nota mínima viable` del
   archivo del tipo (verbatim, no parafraseado). `check_blockers.py`
   PASS 15/15.
2. _Los bloqueantes están marcados y son objetivos._ → prefijo `[B]`
   literal en todos los ítems; separación estricta `[B]`/`[R]` en
   `§3.1`/`§3.2` y en cada `§4.X`. Cada [B] tiene un verificador concreto
   (script + exit code, o condición booleana explícita en el ítem).
   `check_recommended_separation.py` PASS 15/15.
3. _Ningún criterio exige elementos académicos en perfil `reference`._
   → tabla §5.1 columna `[B]` en `reference` no contiene ninguna
   sección pedagógica OMIT. `check_reference_profile.py` PASS 15/15.