# `references/09-study/error-log.md` — Registro de errores propios

> Documento normativo de la **Fase 103** `[ref]`. Define el patrón del
> **living-doc por dominio** para anotar errores propios: estructura del
> archivo, plantilla cerrada de las 5 sub-secciones por entrada, lista
> cerrada de **16 frases de evaluación personal prohibidas** en 4 categorías
> (autoestima negativa, autocrítica emocional, exasperación, derrotismo),
> **7 reglas duras R-E1 a R-E7**, y los algoritmos de los 3 scripts
> (`error_log_query.py` con Q1-Q4; `error_cards.py` con C1-C4;
> `error_log_check.py` con E1-E7).
>
> F103 cierra los 3 criterios del ROADMAP §1720-1722:
> la consulta de repaso vencido funciona donde hay soporte (§6 + script);
> los errores registrados generan tarjetas prioritarias (§7 + script);
> la plantilla no contiene lenguaje de evaluación personal (§4 + lista
> cerrada de 16 frases + AP16).
>
> **Cuándo cargar:** al registrar un error propio del estudiante o al
> consultar el repaso vencido del registro. **No** se carga al redactar
> notas de conocimiento (concept, procedure, etc.) — esas notas no
> contienen el registro subjetivo (ver F103-2 en `error-troubleshooting.md §6`).
>
> **Wirings:**
> - `references/04-authoring/block-directives.md` (F45) §10.4 — `:::question`
>   se reutiliza como contenedor de la tarjeta prioritaria.
> - `references/04-authoring/properties.md` (F47) §5.16 — `review-next`
>   controla el scheduling por entrada.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` y
>   `[[note:id]]` para el enlace a la nota canónica.
> - `references/05-note-types/error-troubleshooting.md` (F82) §6 — checklist
>   extendido con `**F103-1**` y `**F103-2**`.
> - `references/06-writing/anti-patterns.md` (F100) §2 — AP16 "Registro
>   con autocrítica".
> - `references/06-writing/i18n-and-citation.md` (F101) §3 — la lista de
>   45 no-traducibles se aplica al comando erróneo y a la corrección
>   (INV-09 + L1-L2 de F98).
> - `references/09-study/self-evaluation.md` (F102) §7 — F103 publica el
>   segundo archivo de `09-study/`.
> - `scripts/render/flashcards.py` (F55/F56) — F103 introduce el atributo
>   `is_priority_card=true` (extensión compatible con D1) para inyectar
>   las tarjetas prioritarias en el deck estándar.
> - `SKILL.md` §5.3 — wiring añadido en F103.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F103:

1. **El estudiante olvida sus propios errores.** Tras semanas de estudio,
   los mismos errores se repiten porque no hay un registro persistente
   que los diferencie del material original. F103 introduce un **living-doc
   por dominio** (`study/errors/<dominio>.md`) donde cada error se anota
   con su corrección y su enlace a la nota canónica.
2. **Las tarjetas no priorizan lo que el estudiante falla.** El deck de
   repaso estándar (`scripts/render/flashcards.py`) trata todas las
   tarjetas por igual. F103 introduce **tarjetas prioritarias** con tag
   `priority-error` y scheduling `review-next` por entrada, para que el
   repaso enfocado en errores vencidos se adelante al repaso general.
3. **El registro se convierte en diario emocional.** Frases como "soy
   malo en X" o "nunca voy a entender Y" no aportan información y
   dañan la motivación. F103 cierra con la **lista cerrada de 16 frases
   prohibidas** (§4) + el anti-patrón **AP16** (F100 §2).

**F103 NO introduce un 16º `note-type`.** El "registro de errores" es
un **patrón meta-documental** que vive en archivos `study/errors/<dominio>.md`
con frontmatter `note-type: error-log` (valor **fuera** del enum cerrado
de 15). Los renderers L4 lo filtran por este `note-type` y **no lo
publican** como nota de conocimiento (R-E7). Esto preserva la
promesa de F44 (15 tipos cerrados) y la cobertura verificable por
ledger (INV-08).

**Fuera de alcance:**

- Rutas de estudio (F104) — la ruta del estudiante por dominio aún no
  se modela; F103 solo da el living-doc y los scripts.
- Perfiles de objetivo (F105) — `interview` / `certification` / `work`
  pueden pedir Errores-propios en su sección "Errores comunes" — esa
  integración se difiere a F105.
- Detección automática de todos los AP — F112 consolida; F103 entrega
  solo `error_log_check.py` específico.

---

## §2 · Estructura del living-doc

### §2.1 · Frontmatter del archivo (orden canónico)

```yaml
---
title: "Errores propios — <dominio>"
domain: "<slug en kebab-case>"
note-type: error-log
status: published
summary: "<≤ 200 chars: lista los ≥ 1 dominio que cubre el living-doc>"
reading-time-minutes: 2
tags: [study/errors, domain/<slug>]
retrieved: <YYYY-MM-DD>
source-self: "Este living-doc es meta-documental; no se publica como nota de conocimiento (F103 §1)."
---
```

Reglas:

- `domain` (slug kebab-case) es **obligatorio**. Identifica el dominio
  técnico (ej. `postgresql`, `docker`, `kubernetes`, `git`).
- `note-type: error-log` es **obligatorio**. Los renderers L4 lo filtran
  por este valor (R-E7).
- `tags: [study/errors, ...]` es **obligatorio**. El primer tag identifica
  la categoría meta.
- `source-self` declara la naturaleza meta-documental; ningún campo de
  fuente externa aplica.

### §2.2 · Las 4 secciones H2 obligatorias

| # | Sección | Estado | Propósito |
|---|---|---|---|
| 1 | `## Resumen de errores` | obligatoria | 1 párrafo con el conteo total de entradas + dominios cubiertos. ≤ 60 palabras (R1). |
| 2 | `## Errores registrados` | obligatoria | Lista de entradas (H3 `### Error <id>`) con las 5 sub-secciones de §3. |
| 3 | `## Tarjetas prioritarias` | opcional-condicional | Solo si el destino soporta flashcards (Obsidian SR plugin, Anki). Lista las entradas que generan tarjeta con su tag y `review-next`. |
| 4 | `## Repaso vencido` | opcional-condicional | Solo si el destino soporta scheduling. Salida de `error_log_query.py --due`. |

Las secciones 3 y 4 son opcionales-condicionales: aparecen si el destino
lo soporta (criterio #1 ROADMAP: "donde hay soporte"). En destinos sin
scheduling (HTML/PDF, MD simple) se omiten.

---

## §3 · Plantilla cerrada de una entrada

Cada entrada es un H3 `### Error <id>` con un identificador local estable
(ej. `ERROR-PG-001`, `ERROR-DOCKER-003`). Dentro, **5 sub-secciones H3
fijas** en este orden estricto:

```notemark
### Error <DOMAIN>-<NNN>

#### Concepto

Nombre canónico del concepto que se intentaba aplicar. ≤ 1 línea.

#### Comando erróneo

:::code
<comando verbatim que produjo el error — INV-09 + F98 L1-L2>
:::

Salida literal (verbatim; mensajes con caracteres especiales preservados):

:::code
<mensaje de error verbatim>
:::

#### Corrección

Comando corregido:

:::code
<comando correcto verbatim>
:::

Por qué funciona: <1-2 frases factuales>. {src:blk_xxxx}

Nota canónica: [[note:concept-id#§N]] o `[[note:error-troubleshooting-id]]`.

#### Origen

Fecha del error: <YYYY-MM-DD>. Contexto: <1 frase factual — "intentaba
configurar X" / "ejecutaba un backup de Y" / etc.>. Sin autocrítica.

#### Repaso

Próximo repaso: review-next: <YYYY-MM-DD> (≤ 14 días desde el error;
ajustar según dificultad). Tarjeta prioritaria: sí/no.
```

**Reglas duras de la plantilla:**

- Las 5 H4 (`#### Concepto`, `#### Comando erróneo`, `#### Corrección`,
  `#### Origen`, `#### Repaso`) son **obligatorias** en ese orden estricto
  dentro de la entrada H3 (R-E1). H4 mantiene la jerarquía correcta
  respecto al H3 `### Error <id>`.
- El comando erróneo y la corrección van en bloques `:::code` para que
  los renderers L4 los preserven verbatim (INV-09).
- El mensaje de error literal se preserva carácter por carácter (INV-09
  + F98 L1).
- La corrección enlaza a la nota canónica con `[[note:id#§N]]` (R-E4).
- El origen es **factual**: "ejecutaba un backup con `pg_dump -Fc`",
  NO "intentaba hacerlo bien pero me equivoqué".
- El repaso declara `review-next: <YYYY-MM-DD>` ISO 8601 (R-E3, INV-P6).

**Ejemplo positivo (extracto):**

```notemark
### Error POSTGRES-001

#### Concepto

MVCC y snapshot isolation.

#### Comando erróneo

:::code
psql -h 127.0.0.1 -p 5432 -U postgres
:::

Salida literal:

:::code
psql: error: connection to server at "127.0.0.1" (127.0.0.1), port 5432 failed: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
:::

#### Corrección

:::code
sudo systemctl start postgresql
ss -tln | grep 5432
psql -h /var/run/postgresql -U postgres
:::

PostgreSQL no escuchaba en TCP/IP porque `listen_addresses` excluye
`127.0.0.1` por defecto en algunas distribuciones; usar socket Unix
mientras tanto. {src:blk_c11f8e02c1d3}

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-15. Contexto: configurar acceso remoto a
PostgreSQL 16 tras instalar el paquete `postgresql-16`.

#### Repaso

Próximo repaso: review-next: 2026-09-22. Tarjeta prioritaria: sí.
```

**Ejemplo negativo (NO usar):**

```notemark
### Error POSTGRES-002

#### Concepto

No entiendo MVCC, soy malo en esto.

#### Comando erróneo

Modifiqué el archivo de configuración sin cuidado.
:::
```

Este ejemplo viola R-E1 (falta `### Comando erróneo` con bloque verbatim),
R-E5 (autocrítica en `### Concepto`), y R-E4 (sin `[[note:id]]`).

---

## §4 · Lenguaje de evaluación personal: lista cerrada de prohibidos {#lista-cerrada-prohibidos}

**Tabla cerrada con 16 frases/expresiones prohibidas** organizadas en
**4 categorías** (4 entradas cada una). El validador `error_log_check.py`
carga esta tabla al inicio y aplica la regex contra la prosa narrativa
del living-doc (no contra bloques `:::code` verbatim — ver R6 del plan,
mitigación de falsos positivos).

| # | Categoría | Frase prohibida | Por qué se prohíbe | Reemplazo factual |
|---|---|---|---|---|
| 1 | Autoestima negativa | "soy malo en X" / "soy mala en X" | Sesgo emocional sin información; deteriora la motivación. | "El comando `X` falló porque…" (solo el comando + causa). |
| 2 | Autoestima negativa | "no se me da X" / "no se me da bien X" | Idem: confunde aptitud con ejecución de un caso concreto. | "La salida fue `Y` y la esperada era `Z`" (factual). |
| 3 | Autoestima negativa | "soy incapaz de X" | Generalización absoluta; vulnera el principio factual. | "El comando `X` requiere permisos `sudo`" (causa concreta). |
| 4 | Autoestima negativa | "no sirvo para X" | Idem. | Reescribir en términos del comando, no del estudiante. |
| 5 | Autocrítica emocional | "me equivoqué mucho" / "me equivoqué bastante" | Cuantificación emocional subjetiva; cero información. | "El error ocurrió N veces en la sesión del <fecha>." |
| 6 | Autocrítica emocional | "soy un desastre" / "soy un caso" | Generalización absoluta. | Eliminar; el registro es del error, no de la persona. |
| 7 | Autocrítica emocional | "siempre fallo en X" / "siempre me falla X" | Generalización absoluta. | "El error se repitió en las sesiones del <fecha1>, <fecha2>, <fecha3>." |
| 8 | Autocrítica emocional | "odio X" / "detesto X" | Emocional; cero valor informativo. | Reescribir como "El comando `X` es propenso al error Y" (impersonal). |
| 9 | Exasperación | "esto es imposible" | Absoluto; vulnera factualidad. | "El comando `X` no funciona en este entorno; requiere Z." |
| 10 | Exasperación | "no tiene sentido" | Subjetivo; el comando sí tiene una causa documentada. | "La causa raíz es <causa> (ver [[note:id]])." |
| 11 | Exasperación | "es absurdo" / "es ridículo" | Subjetivo. | Reescribir como observación técnica: "El comando falla porque…". |
| 12 | Exasperación | "esto no hay quien lo entienda" | Emocional. | Reescribir: "El comportamiento documentado es X (ver fuente)." |
| 13 | Derrotismo | "nunca voy a entender X" | Generalización absoluta; cierra la puerta al aprendizaje. | Reescribir como objetivo: "Volver a revisar [[note:id]] el <fecha>." |
| 14 | Derrotismo | "no tiene solución" | Absoluto; toda tecnología tiene solución documentada. | "La solución está en [[note:id#§N]] (verificado el <fecha>)." |
| 15 | Derrotismo | "renuncio a X" | Derrotismo; no aporta al registro. | "Pausar X y retomar en <fecha> tras repasar [[note:id]]." |
| 16 | Derrotismo | "ya no puedo más" | Idem. | "Hacer pausa; continuar la siguiente sesión." |

**Reglas algorítmicas:**

- **R-E5** _Detección_ — la regex busca las 16 frases en la prosa
  narrativa del living-doc (líneas fuera de bloques `:::code`,
  `:::`directive`, o ` ``` ` fences). Si matchea, falla con
  `autocritica-detected`.
- **R-E6** _Exención de INV-09_ — los bloques verbatim del comando
  erróneo pueden contener palabras como "fail", "failure", "error" (que
  son parte de los mensajes de error literales) y **no** disparan AP16.
  La regex tiene negative lookbehind `(?<!`) ` para evitar matches
  dentro de code fences.
- **R-E7** _Lista cerrada_ — las 16 frases son las únicas prohibidas.
  Si se identifica una frase nueva, abrir F103-bis (no añadir ad-hoc).

---

## §5 · Reglas duras (R-E1 a R-E7)

| ID | Regla | Si se omite… |
|---|---|---|
| **R-E1** | Cada entrada tiene las 5 H4 obligatorias en orden estricto: `#### Concepto`, `#### Comando erróneo`, `#### Corrección`, `#### Origen`, `#### Repaso`. | El validador `error_log_check.py` falla con `missing-section`. |
| **R-E2** | El comando erróneo y la corrección van en bloques `:::code` y se preservan verbatim (INV-09 + F98 L1-L2). El mensaje de error se preserva carácter por carácter. | El validador falla con `verbatim-violation` (detecta reformulación). |
| **R-E3** | Cada entrada tiene `### Repaso` con `review-next: <YYYY-MM-DD>` ISO 8601 (INV-P6). | El validador falla con `missing-review-next`. |
| **R-E4** | Cada corrección enlaza a la nota canónica con `[[note:id#§N]]` o `[[note:error-troubleshooting-id]]`. Sin este enlace, la corrección flota sin fundamento. | El validador falla con `missing-canonical-link`. |
| **R-E5** | Cero lenguaje de evaluación personal (lista cerrada §4). | El validador falla con `autocritica-detected` (AP16). |
| **R-E6** | Las tarjetas generadas tienen `tag: priority-error` (no compiten con el deck estándar de `scripts/render/flashcards.py`). El script `error_cards.py` añade el tag automáticamente; el living-doc no necesita declararlo. | El script `error_cards.py` falla con `missing-priority-tag`. |
| **R-E7** | El living-doc **no se publica** como nota de conocimiento en los destinos L4. Los renderers filtran por `note-type: error-log` (fuera de los 15 cerrados). | El agente debe añadir `note-type: error-log` al filtro del renderer antes de iterar el plan; documentado en SKILL.md §6 para futura actualización de F62/F63. |

---

## §6 · Algoritmo del script `scripts/study/error_log_query.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/study/error_log_query.py`.
**CLI:** `--list` / `--due` / `--domain <slug>` / `--as-of <YYYY-MM-DD>`
(default hoy) / `--errors-dir <dir>` (default `study/errors/`) / `--json`.
**Salida:** Markdown (default) o JSON (`--json`).
**Exit codes:** 0 = OK, 1 = no hay entradas vencidas (solo con `--due`),
2 = error de uso.

**Cuatro reglas Q1-Q4:**

### Q1 — Lectura del directorio

- Iterar todos los `*.md` en `--errors-dir` (default `study/errors/`).
- Parsear frontmatter mínimo (5 campos: `title`, `domain`, `note-type`,
  `tags`, `retrieved`).
- Filtrar archivos con `note-type: error-log`.

### Q2 — Extracción de entradas

- Por cada archivo, identificar H3 `### Error <id>` y extraer las 5 H3
  hijas (`### Concepto`, `### Comando erróneo`, `### Corrección`,
  `### Origen`, `### Repaso`).
- Resolver `review-next` por entrada (busca en `### Repaso` el campo
  `review-next: <YYYY-MM-DD>`).

### Q3 — Filtro `--due`

- Si `--due`, filtrar entradas con `review-next < --as-of` (default hoy).
- Si `--as-of` futura explícita, documentar como "vista previa de
  repaso próximo" (no error).
- Si `--domain <slug>`, filtrar archivos cuyo frontmatter `domain:` matchee.

### Q4 — Emisión

- **Markdown:** tabla con columnas `Dominio | Error ID | Concepto | Review-next |
  Vencido (sí/no)`. Encabezado: `# Repaso vencido de errores propios
  (as-of <fecha>)`.
- **JSON:** lista de dicts `{domain, error_id, concepto, review_next,
  overdue_days}`.

---

## §7 · Algoritmo del script `scripts/study/error_cards.py`

**Ubicación:** `skill/notemartin-study-notes/scripts/study/error_cards.py`.
**CLI:** `--domain <slug>` / `--format obsidian-sr|anki-csv` (default
`obsidian-sr`) / `--errors-dir <dir>` (default `study/errors/`) /
`--out-dir <dir>`.
**Salida:** `priority-error-<domain>.<ext>` en `--out-dir`. Para
`obsidian-sr`: líneas `¿<comando erróneo>? :: <corrección + [[note:id]]>`
con tag `#priority-error`. Para `anki-csv`: RFC 4180 con 4 columnas
`Pregunta,Respuesta,Tags,Review-next`.
**Exit codes:** 0 = OK, 1 = alguna entrada no genera tarjeta (C1-C4
falla), 2 = error de uso.

**Cuatro reglas C1-C4:**

### C1 — Una entrada, una tarjeta

- Por cada H3 `### Error <id>` extraer **exactamente una tarjeta**. Si
  la entrada no genera tarjeta (falla C2-C4), reportar `card-rejected`.

### C2 — Anverso verbatim

- Anverso = contenido del primer bloque `:::code` dentro de
  `### Comando erróneo`. Validar ≥ 3 palabras (mensajes muy cortos no
  generan tarjeta; reportar `anverso-too-short`).

### C3 — Reverso factual

- Reverso = contenido del primer bloque `:::code` dentro de
  `### Corrección` + el `[[note:id]]` extraído. Validar que el `[[note:id]]`
  exista en el reverso (regex contra el bloque `### Corrección`).

### C4 — Tag y scheduling

- Tag = `priority-error` (siempre, sin importar formato).
- Scheduling = `review-next` de la entrada. Si falta (R-E3 falla),
  reportar `missing-review-next`.

**Formatos:**

- `obsidian-sr`: 1 línea por tarjeta en formato Spaced Repetition plugin:
  ```
  ¿<comando erróneo>? :: <corrección>  📚 [[note:id]]  #priority-error ⏰ <YYYY-MM-DD>
  ```
- `anki-csv`: 1 fila por tarjeta en formato RFC 4180:
  ```
  "<anverso>","<reverso>","priority-error","<YYYY-MM-DD>"
  ```

**Notas:**
- La lista cerrada de 16 frases prohibidas (§4) se carga al inicio
  del script desde el anchor `{#lista-cerrada-prohibidos}` del presente
  doc. Si el anchor no se encuentra, fail con `prohibited-list-not-found`.
- El script detecta AP16 (lenguaje de evaluación personal en la prosa)
  **antes** de generar la tarjeta y la rechaza con `card-rejected-autocritica`.

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F45 | `references/04-authoring/block-directives.md` §10.4 | `:::code` y `:::question` se reutilizan para bloques verbatim y tarjetas. |
| F46 | `references/04-authoring/inline-marks.md` | `{src:blk_xxxx}` y `[[note:id]]` para el enlace canónico. |
| F47 | `references/04-authoring/properties.md` §5.16 | `review-next` controla scheduling por entrada. |
| F62 | `scripts/publish/publishing.py` + `scripts/render/flashcards.py` | Las tarjetas de F103 se inyectan en el deck con `is_priority_card=true`. |
| F78-F92 | `references/05-note-types/*.md` | El registro es meta-documental; **no** modifica los 15 tipos cerrados. |
| F82 | `references/05-note-types/error-troubleshooting.md` §6 | Checklist extendido con `**F103-1**` (enlace al registro si existe) y `**F103-2**` (la nota canónica no contiene el registro). |
| F98 | `references/06-writing/paraphrase.md` §2 L1-L2 | El comando erróneo y la corrección son literales protegidos. |
| F100 | `references/06-writing/anti-patterns.md` §2 | AP16 específico del registro. |
| F101 | `references/06-writing/i18n-and-citation.md` §3 | Lista de 45 no-traducibles aplica al comando y la corrección. |
| F102 | `references/09-study/self-evaluation.md` §7 | F103 publica el segundo archivo de `09-study/`. |
| F104 | (futuro) `references/09-study/study-paths.md` | Las rutas de estudio incluirán "errores vencidos" como fuente. |
| F105 | (futuro) `references/09-study/goal-profiles.md` | `interview` puede pedir "errores comunes" en la sección. |
| F112 | (futuro) suite consolidada | `error_log_check.py` se invocará desde la suite. |
| F115 | (futuro) reporte de calidad | El reporte cita el conteo de entradas y vencidos. |

**Invocación desde SKILL.md:** la fila de `references/09-study/error-log.md`
aparece en §5.3 con la entrada _"Al registrar un error propio o
consultar el repaso vencido del registro"_, entre la fila de
`self-evaluation.md` (F102) y la fila de F104.

---

## §9 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** La consulta de repaso vencido funciona donde hay soporte | `evals/error-log-sample/run_eval.py` C4 verifica que §6 describe Q1-Q4; C6 ejecuta `error_log_query.py --due` con el living-doc bueno y devuelve ≥ 1 entrada vencida. |
| **C2** Los errores registrados pueden generar tarjetas | C5 verifica que §7 describe C1-C4; C7 ejecuta `error_cards.py --format obsidian-sr` con el living-doc bueno y genera ≥ 1 tarjeta con tag `priority-error`. |
| **C3** La plantilla no contiene lenguaje de evaluación personal | C3 verifica que §4 lista cerrada tiene ≥ 12 entradas en 4 categorías; C8 verifica que `error_log_check.py --strict` pasa en los living-docs buenos; C9 verifica que falla en los 4 negativos (incluido `autocritica.md`). |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l error-log.md` ≤ 600 (INV-02).
- **D2.** 9 secciones canónicas §1-§9 presentes.
- **D3.** §3 plantilla NoteMark con los 5 H3 obligatorios en orden estricto.
- **D4.** §4 lista cerrada ≥ 16 frases en 4 categorías (alias C3, mínimo 12).
- **D5.** §5 reglas R-E1 a R-E7 (7 reglas).
- **D6.** §6 algoritmo Q1-Q4 (4 reglas de `error_log_query.py`).
- **D7.** §7 algoritmo C1-C4 (4 reglas de `error_cards.py`).
- **D8.** Wirings cerrados (alias C11 + C12).
