# `references/06-writing/anti-patterns.md` — Anti-patrones

> Documento normativo de la **Fase 100** (con extensiones de **Fase 102**,
> **Fase 103**, **Fase 105**, **Fase 106**, **Fase 107**, **Fase 108**,
> **Fase 109**, **Fase 110** y **Fase 111**). Define los **34
> anti-patrones transversales** AP1-AP34 que aplican a cualquier nota
> (independiente del tipo), las **10 señales algorítmicas** S1-S10 que un
> revisor externo aplica sin reabrir el SDM, y el **checklist de 34
> items** integrable en `concept.md §6`, `procedure.md §6`, etc.
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
| **AP20** | Concepto redefinido fuera del capítulo canónico | En una obra procesada en modo libro (F106), un concepto definido en el capítulo canónico (`shared_concepts[id].canonical_chapter`) se reescribe en otro capítulo sin usar `[[note:concept-id]]`. | Nota `concept` "MVCC" en ch09 con `## Definición` que copia la definición del ch02 verbatim, sin `[[note:mvcc]]`. | Nota `concept` "MVCC" en ch09 con `## Definición` propia + bloque `## Notas` con `Para la definición base véase [[note:mvcc]].` | `difflib.SequenceMatcher.ratio() > 0.5` entre `## Definición` canónica y la nota del otro capítulo, sin `[[note:concept-id]]` | F106 §5 + §10 AP-BM1 |
| **AP21** | Unidad cruzada duplicada (chunk-loop) | En una fuente procesada por chunks (F107), una unidad con `source_block_ids[]` que abarca ≥ 2 chunks se documenta en más de una nota (el script crea 2+ notas para la misma unidad). | `chunk-state.json.cross_chunk_units` tiene 2 entradas con el mismo `note_id` apuntando a la misma unidad `mvcc`. | `chunk-state.json.cross_chunk_units` tiene 1 sola entrada para `mvcc` con `primary_chunk` + `secondary_chunks[]`; una sola nota cubre la unidad completa. | `len(set(cross_chunk_units[].note_id)) < len(cross_chunk_units)` | F107 §7 + §10 AP-CHK1 |
| **AP22** | Carga completa del documento fuera de L0 (chunk-loop) | Cualquier script L0–F3 abre el archivo de texto original (`.pdf`, `.epub`, `.docx`, `.pptx`, `.html`) fuera de la frontera de capa L0 (F18/F20). El SDM es el boundary canónico; recargar el texto crudo rompe la promesa de presupuesto. | `chunk_loop.py walk` lee `source.pdf` desde fuera de L0. | `chunk_loop.py walk` consume solo `sdm.json` filtrado al rango del chunk; el texto crudo nunca se abre fuera de L0. | `<audit-loads>.jsonl` contiene path con extensión `.pdf`/`.epub`/`.docx`/`.pptx`/`.html`/`.txt` | F107 §3 CHK-R2 + §10 AP-CHK2 |
| **AP23** | Fusión con pérdida de unidades (dedup) | `apply merge` produce una nota C donde `source_refs(C) ⊉ source_refs(A) ∪ source_refs(B)`. El orquestador F108 debe abortar con exit 1 + `DEDUP_R1_SOURCE_REFS_LOST` (F50 `transform.py merge` ya detecta la pérdida). | F108 `apply merge --a A --b B` produce C sin los `source_refs` de A. | F108 `apply merge` preserva la unión de `source_refs`; DEDUP-R1 verificado por `completeness.py --before --after`. | `merged_refs ⊉ original_union` (verificable con `_collect_source_refs`) | F108 §6 DEDUP-R1 + §10 |
| **AP24** | Enlace entrante no redirigido (dedup) | Tras `apply merge A+B→C`, existe IR externo (o NoteMark) que contiene `[[note:A]]` o `[[note:B]]` sin reescribir a `[[note:C]]`. El orquestador F108 debe reescribir el workdir completo (DEDUP-R2). | F108 `apply merge` no pasa `--irs-glob` → 0 IRs reescritos; los enlaces externos quedan rotos. | F108 `apply merge --irs-glob 'ir/*.json'` reescribe el workdir; `manifest.json::link_debt[]` registra 2 entradas `redirected`. | grep `\[\[note:(A\|B)\]\]` post-apply | F108 §6 DEDUP-R2 + §10 |
| **AP25** | Detector omite duplicado canónico (dedup) | El detector F108 tiene recall < 80% en fixture de pares inyectados; o emite `suggested_action: "merge"` para un par que debería ser `conflict` (F41). | 5 pares inyectados, el detector encuentra 2/5 (recall 40%). | El detector alcanza recall ≥ 4/5 (80%) sobre `evals/dedup-sample/`; los pares con `similarity` baja pero match canónico/alias NO se reportan como `merge` sino como `review`. | `len(detected_pairs ∩ expected_pairs) / len(expected_pairs) < 0.8` | F108 §4 + §10 V3 |
| **AP26** | Pase de consolidación no idempotente | Un pase F109 produce un output con `sha256_output` distinto entre 2 ejecuciones consecutivas de `run-all` sin cambios en los inputs (CON-R1 violado). | `report-link-debt.json` incluye `generated_at` en el hash → `after_sha256` difiere cada run. | El reporte excluye `generated_at` del hash semántico; `after_sha256` es estable. | `runs[-1].after_sha256 != runs[-2].after_sha256` (sin cambios en inputs) | F109 §4 CON-R1 + §9 V3 |
| **AP27** | Re-ejecución con side-effects (consolidate) | Un pase F109 modifica un input (IR, NoteMark, glossary, etc.) fuera de `reports/` y `manifest.json` (CON-R3 violado). | `pass-link-debt` reescribe IRs para eliminar broken-wikilinks. | Cada pase solo escribe en `<workdir>/reports/` y `manifest.json`; los inputs no se modifican. | `git diff` o checksum de `ir/*.json` antes/después muestra cambios | F109 §4 CON-R3 + §9 |
| **AP28** | Término con 2 definiciones canónicas (consolidate) | El mismo alias normalizado aparece en ≥ 2 términos del glosario (F40 R3 violado); o F109 pase 2 no lo detecta. | `glossary.json` tiene alias "mv" en términos "mvcc" y "wal". | `report-glossary.json` lista la violación R3 con `terms: ["mvcc", "wal"]`. | `len(r3_violations) == 0` cuando hay alias duplicado | F109 §3 pase 2 + §9 V2 |
