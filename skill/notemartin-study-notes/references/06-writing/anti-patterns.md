# `references/06-writing/anti-patterns.md` — Anti-patrones

> Documento normativo de la **Fase 100** (con extensiones de **Fase 102**,
> **Fase 103** y **Fase 105**). Define los **19 anti-patrones
> transversales** AP1-AP19 que aplican a cualquier nota (independiente
> del tipo), las **10 señales algorítmicas** S1-S10 que un revisor
> externo aplica sin reabrir el SDM, y el **checklist de 19 items**
> integrable en `concept.md §6`, `procedure.md §6`, etc.
>
> F100 **consolida transversalmente** los anti-patrones. Las fases
> F94-F99 ya cubren AP **específicos** de su dominio (F94 §6, F95 §6,
> F96 §5, F97 §10, F98 §8, F99 §8). F100 los **agrega** los AP
> **transversales** que aplican a **cualquier** prosa pedagógica y
> **los referencia desde el checklist de calidad**.
>
> **Cuándo cargar:** antes de cerrar L3 sobre cualquier nota; cuando el
> revisor detecta patrones que no son específicos de un dominio
> (marketing, volcado de viñetas, callouts decorativos).
>
> **Wirings:**
> - `references/05-note-types/concept.md` (F78) §6 — checklist de cierre
>   de `concept` se **extiende** con los 19 items de F100+F102+F103+F105.
> - `references/06-writing/intuition-first.md` (F94) §6 — D1-D10 específicas.
> - `references/06-writing/analogies.md` (F95) §6 — AP1-AP8 analogías.
> - `references/06-writing/executable-examples.md` (F96) §5 — NE1-NE8 ejemplos.
> - `references/06-writing/comparisons.md` (F97) §10 — AP1-AP8 comparaciones.
> - `references/06-writing/paraphrase.md` (F98) §8 — AP1-AP7 parafraseo.
> - `references/06-writing/voice-style.md` (F99) §8 — AP1-AP8 voz.
> - `evals/rubric.md` (F7) — los 19 AP alimentan la dimensión `componentes`.
- `references/09-study/self-evaluation.md` (F102) — AP13-AP15 específicos
  de autoevaluación.
- `references/09-study/error-log.md` (F103) — AP16 específico del
  registro de errores propios (lenguaje de evaluación personal).
- `references/09-study/goal-profiles.md` (F105) — AP17-AP19 específicos
  de perfiles de objetivo.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F100:

1. **Los AP específicos de F94-F99 no llegan al checklist.** Cada fase
   norma AP de su dominio (analogía sin rotura en F95, transcripción en
   F98, marketing en F98), pero el checklist de cierre de
   `concept.md §6` (13 items) **no** los referencia. F100 los integra en
   un único checklist de 19 items.
2. **Faltan AP transversales que aplican a cualquier prosa.** Marketing
   copiado, volcado de viñetas, callouts decorativos, secciones vacías
   — estos AP no son específicos de analogías o comparaciones, pero
   aparecen en cualquier nota. F100 los norma como transversales.
3. **No hay señal algorítmica única para diagnosticar AP.** Cada fase
   tiene sus propias señales (D*, S*, NE*). F100 unifica las señales
   transversales en **S1-S10** con regex/conteo ejecutable.

**Cierra los 3 criterios del ROADMAP §1692-1694:**

1. _≥ 19 anti-patrones con ejemplo malo y corregido_ → §2 (19 filas AP1-AP19).
2. _Cada uno tiene señal de detección para autorrevisión_ → §3 (S1-S10) + §6 (checklist con señal por item).
3. _Están referenciados desde el checklist de calidad_ → §6 (checklist integrable) + wirings a `concept.md §6`.

**Fuera de alcance:**

- AP específicos de analogías / comparaciones / parafraseo / voz → F94-F99 (F100 los referencia en §5).
- Detección automática de **todos** los AP → F112 (suite de checks).
- Reporte de calidad → F115.
- Idioma bilingüe → F101.

---

## §2 · Los 19 anti-patrones transversales

Tabla cerrada con **19 anti-patrones**. Cada fila tiene: nombre,
definición, ejemplo malo, ejemplo correcto, señal algorítmica, sección
de origen cuando ya existe en F94-F99, F102, F103 o F105.

| # | Nombre | Definición | Ejemplo malo | Ejemplo correcto | Señal algorítmica | Origen |
|---|---|---|---|---|---|---|
| **AP1** | Transcripción disfrazada de resumen | El `## Resumen` copia ≥ 50% de un párrafo del SDM verbatim sin reescritura. | "PostgreSQL implementa MVCC con HeapTuple visible/no visible por xmin/xmax en cada fila." (copia literal) | "MVCC usa marcas de versión por fila; el lector ve un snapshot estable." (3 unidades reescritas) | regex contra coincidencia literal de bloque SDM en `## Resumen` | F98 §8 AP1 |
| **AP2** | Definición circular | La definición usa el término definido ("X es un X que…"). | "MVCC es un mecanismo de MVCC que permite versiones múltiples." | "MVCC es un protocolo de control de concurrencia que mantiene múltiples versiones de cada fila." | regex `r"\b(\w+)\s+es\s+(?:un|una)\s+\1\b"` (palabra X + "es un" + misma X) | F98 §8 AP2 |
| **AP3** | Callout decorativo | `:::note` / `:::tip` con cuerpo trivial (< 30 caracteres) sin propósito. | `:::note\nVer.\n:::` | `:::tip\nPostgreSQL usa MVCC por defecto; Oracle lo llama "consistent reads".\n:::` | regex contra admonition con cuerpo < 30 chars y sin verbo de acción | F45 §6 (sin doc) |
| **AP4** | Tabla de una fila útil | Tabla con 1 fila de datos + 1 header (es una lista con overhead). | `\| Modelo \| Tipo \|\n\| MVCC \| Por fila \|` | Convertir a frase: "MVCC es por fila (vs bloque de MyISAM)." | regex contra tabla con 1 fila de datos | F97 §10 AP4 (cubierto parcialmente) |
| **AP5** | Analogía sin mapeo | Analogía sin rotura explícita (no dice dónde se rompe). | "Una biblioteca con tarjetas." (sin rotura) | "Una biblioteca con tarjetas de préstamo — se rompe porque MVCC sí acumula copias." | regex contra analogía sin frase de rotura (`se rompe / no se parece / la diferencia / en cambio`) | F95 §6 AP3, F99 §8 AP5 |
| **AP6** | Diagrama que repite el texto | `:::diagram` que dice lo mismo que el párrafo adyacente. | Párrafo: "PostgreSQL crea HeapTuple con xmin." + Diagrama: `flowchart: T → HeapTuple → xmin` (mismo info) | Párrafo: "PostgreSQL crea HeapTuple con xmin." + Diagrama: `flowchart` mostrando el flujo de visibilidad (info distinta) | inspección visual + `scripts/validate/mermaid.py` | F66 §6 (sin doc) |
| **AP7** | Enlace sin contexto | `[[note:id]]` sin frase introductoria (≥ 5 palabras antes). | "Ver [[note:vacuum]]." | "Para profundizar en el reciclaje de versiones, consulta [[note:vacuum]]." | regex `\[\[note:[a-z0-9_-]+\]\]` sin ≥ 5 palabras antes | F78 §4.2 (mención) |
| **AP8** | Volcado de viñetas | Sección con ≥ 10 viñetas consecutivas sin prosa intermedia. | `## Lista:\n- item 1\n- item 2\n... (15 items sin prosa)` | `## Lista:\n\nPostgreSQL soporta 3 tipos de replica:\n\n- física\n- lógica\n- slot-based` | regex contra `^(\s*[-*]\s+.+\n){10,}` sin párrafo intermedio | F76 R5 |
| **AP9** | Marketing copiado | Frases vacías tipo "solución innovadora que transforma su negocio". | "PostgreSQL es la solución innovadora que transforma la gestión de datos moderna." | "PostgreSQL soporta tipos JSONB, rangos, geometría y vectores desde 2014." | regex contra lista cerrada de frases vacías | F98 §8 AP5 (marketing) |
| **AP10** | Código sin caption | `:::example` con código que no tiene salida esperada ni explicación. | `:::example\n```sql\nSELECT 1;\n```\n:::` (sin output ni caption) | `:::example\n```sql\nSELECT 1;\n-- → 1\n```\n:::` | regex contra `:::example` sin bloque de output | F96 §5 NE6 |
| **AP11** | Mermaid syntax error silencioso | `:::diagram` que `scripts/validate/mermaid.py` marca como `error` pero la nota sigue adelante. | `:::diagram\nflowchart\n  A -->\n:::` (sintaxis rota) | Validar con `mermaid.py` antes de publicar; corregir errores antes de cerrar L3. | ejecución de `scripts/validate/mermaid.py --fail-on error` | F67 §3 (sin doc) |
| **AP12** | Sección vacía o de relleno | `##` con 1 párrafo trivial (< 30 caracteres) que no añade contenido. | `## Pendiente\n\nEsta sección está en construcción.\n` (sin contenido) | Eliminar la sección hasta tener contenido sustantivo. | regex contra `^##\s+.+\n[^#\n]*\s*(\n\s*){0,2}$` con párrafo trivial | F78 §6 (implícito) |
| **AP13** | Autoevaluación con respuesta copiada | El bloque `:::collapsible` de `## Autoevaluación` contiene una respuesta que es copia literal (Jaccard > 0.8 sobre palabras no técnicas) del bloque referenciado por `> Fundamento: …`. | Pregunta: "¿Cuál es el propósito de MVCC?" Respuesta: "MVCC es un mecanismo de control de concurrencia multiversión que mantiene múltiples versiones de cada fila." (copia literal de `## Definición formal`) | Reformular la respuesta: "MVCC evita que las lecturas se bloqueen: cada transacción observa un snapshot estable al inicio, sin esperar a que otras terminen." (reordenada, parafraseada). | Jaccard > 0.8 entre respuesta y bloque referenciado (excluyendo 45 no-traducibles de F101 §3) | F102 §6 V4 + §7 AP13 |
| **AP14** | Autoevaluación sin fundamento | El bloque `:::collapsible` no termina con la línea `> Fundamento: {src:blk_xxxx}` o `> Fundamento: [[note:id#§N]]`. | Pregunta + respuesta sin línea final. | Añadir `> Fundamento: {src:blk_k901}` (o `[[note:concept-x#§3]]`) al final del colapsable. | regex contra collapsibles dentro de `## Autoevaluación` sin línea `> Fundamento:` | F102 §6 V3 + §7 AP14 |
| **AP15** | Recuerdo en referencia pura | La nota es `glossary-term`, `cheatsheet`, `index-moc`, o tipo-asignado-a-solo-diagnóstico, y la sección `## Autoevaluación` contiene una H3 `### Recuerdo`. | `glossary-term` con `## Autoevaluación` y `### Recuerdo` (la respuesta de recuerdo es la fila literal de la tabla → copia). | `glossary-term` con `## Autoevaluación` y `### Diagnóstico` o `### Decisión` (no recuerdo). | regex contra nota `note-type ∈ {glossary-term, cheatsheet, index-moc}` con H3 `### Recuerdo` en `## Autoevaluación` | F102 §4 regla de referencia pura + §7 AP15 |
| **AP16** | Registro con autocrítica | Una entrada del living-doc (`note-type: error-log`) contiene lenguaje de evaluación personal de la lista cerrada de F103 §4 (≥ 16 frases en 4 categorías: autoestima negativa, autocrítica emocional, exasperación, derrotismo). | `### Error PG-001 › ### Concepto`: "No entiendo MVCC, soy malo en esto." | `### Concepto`: "MVCC y snapshot isolation." (factual). | regex cerrada contra las 16 frases prohibidas (F103 §4) en prosa narrativa fuera de bloques `:::code` | F103 §4 lista cerrada + §7 AP16 |
| **AP17** | Perfil que reduce cobertura | Un perfil de objetivo activo (`interview` / `certification` / `work`) excluye una sección obligatoria del `note-type` o relaja una regla R-* no permitida (R2, R4, R6, R7, R8, INV-08, INV-09, INV-P6). | `goal_profile: interview` con nota `concept` sin `## TL;DR` (sección obligatoria del note-type). | `goal_profile: interview` con nota `concept` que mantiene `## TL;DR` + `## Mecanismo` y **añade** `## Decisiones de diseño` + `## Explicación oral`. | regex contra secciones obligatorias del note-type + reglas R-* relajadas contra la lista permitida de F105 §3 | F105 §3 INV-GP1 + §7 V1 |
| **AP18** | Perfil que omite `adds[]` declarado | Una nota tiene `goal_profile` activo que declara `adds[]` en su perfil, pero la nota NO incluye las secciones correspondientes. | `goal_profile: certification` con nota que NO incluye `## Objetivos oficiales`. | `goal_profile: certification` con nota que incluye `## Objetivos oficiales` (tabla con `objetivo_id` + `cobertura`) + declara `certification-objective` en frontmatter. | regex contra secciones declaradas en `adds[]` del perfil activo | F105 §5 R-G4 + R-G5 + §7 V1 |
| **AP19** | `goal_profile` no canónico | `profile.yaml::goal_profile` o frontmatter `goal-profile-override` tiene un valor fuera del enum cerrado `{hybrid, interview, certification, work}`. | `goal_profile: production` en `profile.yaml`. | `goal_profile: work` (valor canónico). | regex contra enum cerrado de F105 §2 | F105 §5 R-G1 + §7 V5 |

**Reglas duras:**

- Cada AP tiene **al menos una señal algorítmica** ejecutable.
- Si el AP ya está cubierto por F94-F99, F100 §5 lo referencia sin
  duplicar la definición.
- El checklist §6 lista los 19 AP como items binarios; cada item
  cita la señal algorítmica que lo verifica.

---

## §3 · Señales de diagnóstico (S1-S10)

Tabla cerrada de **10 señales algorítmicas**. Cada señal con método
(regex/conteo) y qué AP detecta.

| ID | Señal | Método | PASS si | Detecta AP |
|---|---|---|---|---|
| **S1** | Definición circular | regex `r"\b(\w+)\s+es\s+(?:un|una)\s+\1\b"` (palabra X + "es un" + misma X) sobre todo el texto | 0 matches | AP2 |
| **S2** | Marketing copiado | regex contra lista cerrada: `r"\b(soluci[oó]n innovadora\|transforma su negocio\|cambia las reglas\|revolucionari[oa]\|l[ií]der del mercado\|de vanguardia\|estado del arte\|game[- ]?changer\|pr[oó]xima generaci[oó]n)\b"` | 0 matches | AP9 |
| **S3** | Volcado de viñetas | regex contra bloque `^(\s*[-*]\s+.+\n){10,}` sin párrafo intermedio | no hay 10+ viñetas consecutivas sin prosa | AP8 |
| **S4** | Enlace sin contexto | regex `\[\[note:[a-z0-9_-]+\]\]` precedido de < 5 palabras | cada `[[note:]]` tiene ≥ 5 palabras introductorias | AP7 |
| **S5** | Transcripción disfrazada | comparar el `## Resumen` con un bloque SDM: ≥ 50% de palabras del bloque aparecen verbatim | ratio de copia literal < 50% | AP1 |
| **S6** | Callout decorativo | admonition con cuerpo < 30 caracteres y sin verbo de acción | cada admonition tiene ≥ 30 chars y un verbo | AP3 |
| **S7** | Tabla de una fila útil | tabla markdown con ≤ 1 fila de datos | cada tabla tiene ≥ 2 filas de datos | AP4 |
| **S8** | Sección vacía | regex contra `^##\s+.+\n[^#\n]*\s*\n{0,3}$` (H2 + 1 línea trivial) | cada `##` tiene ≥ 1 párrafo sustantivo (≥ 30 chars) | AP12 |
| **S9** | Mermaid syntax error | ejecución de `scripts/validate/mermaid.py --fail-on error` | exit 0 | AP11 |
| **S10** | Código sin caption | regex contra `:::example` sin bloque de output (regex contra ```` después de ````sql) | cada `:::example` tiene ≥ 1 bloque de output esperado | AP10 |

**Reglas:**

- Las señales S1-S10 son **algorítmicas** (regex, conteo, ejecución).
- Un AP puede ser detectado por **varias** señales (AP2 por S1, AP8 por S3, etc.).
- Una señal puede detectar **varios** AP (S6 detecta AP3, pero también AP11 si el mermaid va dentro del callout).

---

## §4 · Lista cerrada de los 19 AP

Enumeración compacta para usar en checklist o revisión rápida:

```
AP1.  Transcripción disfrazada de resumen
AP2.  Definición circular
AP3.  Callout decorativo
AP4.  Tabla de una fila útil
AP5.  Analogía sin mapeo
AP6.  Diagrama que repite el texto
AP7.  Enlace sin contexto
AP8.  Volcado de viñetas
AP9.  Marketing copiado
AP10. Código sin caption
AP11. Mermaid syntax error silencioso
AP12. Sección vacía o de relleno
AP13. Autoevaluación con respuesta copiada       (F102)
AP14. Autoevaluación sin fundamento              (F102)
AP15. Recuerdo en referencia pura                (F102)
AP16. Registro con autocrítica                   (F103)
AP17. Perfil que reduce cobertura                (F105)
AP18. Perfil que omite adds[] declarado          (F105)
AP19. goal_profile no canónico                   (F105)
```

---

## §5 · Anti-patrones específicos cubiertos por F94-F99

Tabla de referencias cruzadas. Los AP **específicos** ya están normados
por las fases F94-F99; F100 los **referencia** sin duplicar.

| AP específico | Fase de origen | Sección | Relación con F100 |
|---|---|---|---|
| Analogía sin rotura explícita | F95 §6 AP3, F99 §8 AP5 | F100 AP5 | Reusado como AP5 transversal |
| Tabla sin síntesis | F97 §10 AP1 | F100 §5 | Específico de comparaciones, no transversal |
| Fila decisiva al medio | F97 §10 AP2 | F100 §5 | Específico de comparaciones |
| Criterios no paralelos | F97 §10 AP3 | F100 §5 | Específico de comparaciones |
| Setup ausente en ejemplo | F96 §5 NE1 | F100 §5 | Específico de ejemplos ejecutables |
| Limpieza ausente en ejemplo | F96 §5 NE2 | F100 §5 | Específico de ejemplos |
| Reformulación de mensaje de error | F98 §8 AP5 | F100 §5 | Forma parte del **contenido**; F100 norma el **volcado de marketing** |
| Truncado por `etc.` | F98 §8 AP4 | F100 §5 | Forma parte del parafraseo |
| Elisión de unidades | F98 §8 AP2 | F100 §5 | Específico de parafraseo |
| Adición de unidades | F98 §8 AP3 | F100 §5 | Específico de parafraseo |
| Frase larga (> 25 palabras) | F99 §8 AP1 | F100 §5 | Específico de voz (F99 R1) |
| Voz pasiva | F99 §8 AP2 | F100 §5 | Específico de voz (F99 R2) |
| Relleno ("es importante destacar…") | F99 §8 AP3 | F100 §5 | Forma parte de **voz**; F100 norma **marketing** que es distinto |
| Adjetivo valorativo | F99 §8 AP4 | F100 §5 | Forma parte de **voz**; F100 §5 lo deja a F99 |

**Regla:** F100 norma los **transversales**; las fases F94-F99 conservan
sus AP específicos. El checklist §6 los integra.

---

## §6 · Checklist de cierre (19 items)

Antes de cerrar L3, verificar los **19 items binarios**. Cada item
mapea a un AP transversal con su señal algorítmica.

```
## §6 · Checklist de cierre (19 items, uno por AP transversal)

Antes de cerrar L3, verificar:

- [ ] **AP1** No hay transcripción disfrazada: el `## Resumen` no copia
      ≥ 50% de un párrafo del SDM verbatim sin reescritura (S5).
- [ ] **AP2** No hay definiciones circulares: las definiciones no usan
      el término definido ("X es un X que…") (S1).
- [ ] **AP3** No hay callouts decorativos: cada `:::note` / `:::tip`
      / `:::warning` informa, advierte o guía con ≥ 30 caracteres de
      cuerpo y un verbo de acción (S6).
- [ ] **AP4** No hay tabla de una fila útil: las tablas tienen
      ≥ 2 filas de datos (S7).
- [ ] **AP5** Las analogías tienen rotura explícita: cada analogía
      incluye una frase que matchea D5 (F95 §4 / F99 §5).
- [ ] **AP6** Los diagramas Mermaid añaden información no presente en
      el párrafo adyacente (inspección visual).
- [ ] **AP7** Los enlaces entre notas llevan frase introductoria de
      ≥ 5 palabras antes del `[[note:id]]` (S4).
- [ ] **AP8** No hay volcado de viñetas: las secciones con ≥ 5
      viñetas consecutivas tienen prosa intermedia (S3 / F76 R5).
- [ ] **AP9** No hay marketing copiado: ausencia de "solución
      innovadora", "transforma su negocio", "cambia las reglas",
      etc. (S2).
- [ ] **AP10** Los bloques `:::example` tienen caption o salida
      esperada (S10).
- [ ] **AP11** `scripts/validate/mermaid.py --fail-on error` retorna
      exit 0 (S9).
- [ ] **AP12** No hay secciones vacías: cada `##` tiene ≥ 1 párrafo
      sustantivo de ≥ 30 caracteres (S8).
- [ ] **AP13** Las respuestas de autoevaluación no son copia literal:
      Jaccard ≤ 0.8 entre respuesta y bloque referenciado por
      `> Fundamento:` (palabras no técnicas; F102 §6 V4).
- [ ] **AP14** Toda pregunta plegable de `## Autoevaluación` cierra
      con `> Fundamento: {src:blk_xxxx}` o `> Fundamento: [[note:id#§N]]`
      (F102 §6 V3).
- [ ] **AP15** Las notas de referencia pura (`glossary-term`,
      `cheatsheet`, `index-moc`) no tienen preguntas de recuerdo en
      `## Autoevaluación` (F102 §4).
- [ ] **AP16** El registro de errores propios no contiene lenguaje de
      evaluación personal (16 frases prohibidas en F103 §4); las
      entradas son factuales (F103 §5 R-E5 / §7 AP16).
- [ ] **AP17** El perfil de objetivo activo no reduce cobertura: las
      secciones obligatorias del note-type siguen presentes y las
      reglas R-* no relajadas se mantienen estrictas (F105 §3
      INV-GP1 + §5 R-G3 + §7 V1).
- [ ] **AP18** Si el perfil activo declara `adds[]`, las secciones
      correspondientes están presentes en la nota (F105 §5 R-G4/R-G5
      + §7 V1).
- [ ] **AP19** `goal_profile` ∈ `{hybrid, interview, certification,
      work}` (enum cerrado F105 §2).

Una nota pasa F100 si los 19 items devuelven PASS.
```

**Integración con `concept.md §6`:** este checklist se añade **al final**
del checklist existente de `concept.md`. AP13-AP15 son específicos de
autoevaluación y se duplican del ítem `**F102-1**` / `**F102-2**` ya
integrado en `concept.md §6`. AP16 aplica solo a living-docs con
`note-type: error-log`. AP17-AP19 aplican a notas con `goal_profile`
activo distinto de `hybrid`.

---

## §7 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.yaml` | Los 19 AP aplican a todos los perfiles; `reference-pure` puede eximir AP3, AP8, AP9, AP15. |
| F45 | `references/04-authoring/block-directives.md` §6 | AP3 "callout decorativo" se detecta por admonition trivial. |
| F46 | `references/04-authoring/inline-marks.md` | AP5 / AP7 (analogías y enlaces). |
| F67 | `references/07-visual/` + `scripts/validate/mermaid.py` | AP11 (mermaid syntax error). |
| F76 | `references/07-visual/density.md` | AP8 (volcado de viñetas → R5). |
| F78 | `references/05-note-types/concept.md` §6 | El checklist de cierre de `concept` se extiende con los 19 items de F100+F102+F103+F105 (AP1-AP19). |
| F94 | `references/06-writing/intuition-first.md` §6 D1-D10 | F100 §5 referencia D1-D10. |
| F95 | `references/06-writing/analogies.md` §6 | F100 AP5 cubre AP3 de F95 (analogía sin rotura). |
| F96 | `references/06-writing/executable-examples.md` §5 | F100 AP10 cubre NE6 de F96 (código sin caption). |
| F97 | `references/06-writing/comparisons.md` §10 | F100 §5 referencia AP1-AP8 de F97. |
| F98 | `references/06-writing/paraphrase.md` §8 | F100 AP9 cubre marketing de F98 AP5; AP1 cubre transcripción de F98 AP1. |
| F99 | `references/06-writing/voice-style.md` §8 | F100 §5 referencia AP1-AP8 de F99. |
| F101 | `references/06-writing/i18n-and-citation.md` | F100 wirings sin solapamiento con i18n. |
| F112 | F112 (suite de checks automatizados) | Las señales S1-S10 son la base para los checks automáticos de F112. |
| F115 | F115 (reporte de calidad) | El checklist de F100 se reporta en el reporte de calidad. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/anti-patterns.md`
aparece en §5.2 con la entrada _"Diagnosticar anti-patrones transversales
(19 AP + checklist de calidad)"_, entre F99 y F65.

---

## §8 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** ≥ 19 anti-patrones con ejemplo malo y corregido (12 de F100 + 3 de F102: AP13, AP14, AP15 + 1 de F103: AP16 + 3 de F105: AP17, AP18, AP19) | `evals/anti-patterns-sample/run_eval.py` C2 verifica que §2 tabla tiene ≥ 19 filas AP1-AP19 con 6 columnas no vacías por fila. `evals/self-evaluation-sample/run_eval.py` C13 verifica que §2 lista AP13, AP14, AP15. `evals/error-log-sample/run_eval.py` C11 verifica que §2 lista AP16. `evals/goal-profiles-sample/run_eval.py` C14 verifica que §2 lista AP17, AP18, AP19. |
| **C2** Cada uno tiene señal de detección para autorrevisión | C3 verifica que §3 tiene ≥ 10 señales S1-S10 con método y PASS/FAIL. C8 verifica que las 6 notas fixture negativas son detectadas por al menos 1 señal cada una. |
| **C3** Referenciados desde el checklist de calidad | C11 + C12 verifican que `concept.md §6` lista los 19 AP como items del checklist. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l anti-patterns.md` ≤ 600.
- **D2.** 8 secciones canónicas §1-§8 presentes.
- **D3.** §6 checklist tiene exactamente 19 items binarios.
- **D4.** §5 referencias cruzadas a F94-F99 cubre ≥ 4 fases.
- **D5.** Wirings cerrados (C9).
- **D6.** Las 7 notas fixture pasan `density_check.py --strict` (C10).
