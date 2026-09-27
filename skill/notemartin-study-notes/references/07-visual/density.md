# `references/07-visual/density.md` — Densidad y jerarquía

> Documento normativo de la **Fase 76**. Define las reglas numéricas
> que toda nota debe cumplir en su redacción para garantizar densidad
> visual, variedad estructural y legibilidad. Las reglas son ejecutables
> vía `scripts/validate/density_check.py`.
>
> **Cuándo cargar:** antes de cerrar cualquier nota en L3; durante la
> revisión humana; cuando el validador reporta violaciones R1-R8 y el
> agente necesita saber qué ajustar.
>
> **Wiring:** jerarquía visual en `references/07-visual/note-templates.md`
> (F75); capas L1/L2/L3 en `references/04-authoring/depth-layers.md` (F51);
> marcas inline en `references/04-authoring/inline-marks.md` (F46).

---

## §1 · Propósito y alcance

F76 unifica las reglas dispersas que ya existían como placeholders en
F51 (longitudes de párrafo), F75 §5.2 (frecuencia de anclaje visual y
máximo de callouts consecutivos) y F46 §4 (densidad de marcas `{src:}`).
Las convierte en una tabla cerrada de 8 reglas numéricas, todas
ejecutables por el validador, y documenta las exenciones por tipo.

**Cierra los 3 criterios del ROADMAP §1483-1485:**

1. _Ninguna nota supera el máximo de prosa continua sin anclaje_ → R2 + R3.
2. _Ninguna sección es exclusivamente viñetas_ → R6.
3. _Todas las reglas están en números_ → la tabla §2 con R1-R8.

**Fuera de alcance:**

- Densidad óptima (criterio subjetivo; F77 visual cerrado: las 12 capturas reales de las 2 notas validan la presencia de los anclajes pero la calidad sigue siendo subjetiva).
- Calidad del anclaje (¿la tabla es útil o decorativa?) — F76 mide presencia, no calidad.
- Cálculo automático de `reading-time-minutes` (F75-FUERA).
- Las 15 plantillas individuales F78-F92 — siguen delegando al patrón F75 + a este doc.

---

## §2 · Tabla cerrada de reglas (R1-R8)

| # | Regla | Límite numérico | Severidad¹ | Exenciones | Fuente original |
|---|---|---|---|---|---|
| **R1** | Max párrafo L1 (`## TL;DR`) | **≤ 60 palabras** Y **≤ 8 líneas** | warning | Ninguna | F51 depth-layers.md §3 |
| **R2** | Max párrafo L2 (cuerpo) | **≤ 200 palabras** | error | Ninguna | F75 §5.2 (placeholder) |
| **R3** | Frecuencia mínima de anclaje visual | **≥ 1 callout/tabla/figura/diagrama por cada 200 palabras de prosa continua** | warning | `glossary-term`, `cheatsheet`, `index-moc` | F75 §5.2 (placeholder) |
| **R4** | Max callouts consecutivos sin prosa | **≤ 3** | error | bloques `code` cuentan como prosa intermedia | F75 §5.2 (placeholder) |
| **R5** | Max viñetas consecutivas sin prosa/estructura | **≤ 5** | error | checklists (con `[ ]`) cuentan como estructura intermedia si ≥ 3 items | F76 nuevo |
| **R6** | Sección (H2/H3) no puede ser 100% viñetas | debe tener **≥ 1 párrafo, tabla, callout o figura** | error | `glossary-term` (si ≤ 30 líneas), `cheatsheet` (tablas = estructura) | F75 §5.2 anti-fatiga |
| **R7** | L3 si > 100 líneas → plegable | **longitud > 100 líneas** marca para `:::collapsible` con `default_open: false` | warning | `architecture` (notas extensas permitidas en plano) | F51 depth-layers.md §3 |
| **R8** | Densidad `{src:}` por bloque fáctico | **≥ 0.80 anclas** (de cada 5 bloques fácticos, ≥ 4 llevan al menos un ancla) | warning | bloques puramente estructurales (tablas, listas de config) | F46 inline-marks.md §4 |

¹ **Severidad:** `error` bloquea el cierre de la nota; `warning` se reporta pero no bloquea. El CLI soporta `--strict` para hacer que warnings también exit 1.

**Importante:** las reglas son **acotadas por sección** (H2/H3), no por la nota completa. Una sección puede pasar R3 (≥ 1 anclaje cada 200 palabras) y la siguiente también; el cumplimiento se mide sección a sección.

---

## §3 · Definiciones operativas

### §3.1 · "Anclaje visual"

Un **anclaje visual** es cualquier bloque que rompe visualmente la pared de prosa y aporta estructura semántica. Cuenta como anclaje:

| Bloque | Cuenta como anclaje | Notas |
|---|---|---|
| Callout (`> [!info]`, `> [!warning]`, etc.) | ✅ | cualquier severity F73 |
| Tabla (`\| ... \|` o `:::param-table`) | ✅ | incluida la tabla Markdown estándar |
| Figura (`:::figure` con caption) | ✅ | las imágenes decorativas sin caption NO cuentan |
| Diagrama (`:::diagram`, Mermaid) | ✅ | bloque pre-renderizado |
| Code con caption | ✅ | fence ``` con título/descripción explícito |
| Ecuación (`:::equation`, `$$...$$`) | ✅ | matemática con número o caption |

**No cuentan como anclaje:**

- Headings (`## H2`, `### H3`).
- Blockquotes (`>`).
- Listas de viñetas (son prosa estructurada pero no son anclaje).
- Bold/italic/inline marks (`**bold**`, `{{ph}}`, etc.).
- Code fence sin caption.
- Imágenes sin caption.

### §3.2 · "Sección" (H2/H3)

Una sección es el rango de bloques entre dos headings del mismo nivel (o superior). Ejemplo:

```markdown
## Procedimiento                              ← sección 1
1. Paso uno.
2. Paso dos.

## Solución                                 ← sección 2
Texto introductorio.
- Viñeta 1
- Viñeta 2
```

Cada sección tiene:
- 1 heading raíz (H2 o H3).
- N bloques hijos (paragraph, list, table, callout, etc.).
- Una profundidad de anidación (cuántos H2 padre tiene).

### §3.3 · "Bloque fáctico" (para R8)

Un bloque es **fáctico** si afirma algo verificable (no estructura). Lista cerrada:

- `paragraph` con contenido declarativo (no transaccional).
- `callout` con severity `info`, `warning`, `danger`, `security`, `performance`, `deprecated` (los `note` y `example` son ilustrativos, no fácticos).
- `code` con caption (firma de función, ejemplo ejecutable, etc.).
- `equation`.
- `figure` con caption fáctica (no decorativa).
- `list` con items declarativos (no transaccional como "comprar X, Y, Z").

**No son fácticos** (exentos de R8): `table` (datos, no hechos), `list` transaccional, `quote` (cita de otro), `collapsible` (sub-jerarquía).

### §3.4 · "L1/L2/L3" (delega a F51)

Las 3 capas se definen formalmente en `references/04-authoring/depth-layers.md` §3:

- **L1 (`## TL;DR`):** el resumen de 60 palabras, autónoma sin leer el resto.
- **L2 (cuerpo H2/H3):** el contenido principal de la nota, 30-70% del total.
- **L3 (plegable o sub-nota):** detalle exhaustivo, edge cases, historia.

F76 hereda las longitudes de F51: L1 ≤ 60 palabras (R1), L2 ≤ 200 palabras (R2), L3 plegable si > 100 líneas (R7).

---

## §4 · Exenciones por tipo de nota

Los 3 tipos siguientes están parcial o totalmente exentos de las reglas R3, R5 y R6:

| `note-type` | Exenciones | Justificación |
|---|---|---|
| `glossary-term` | R3 (frecuencia mínima), R6 (sección 100% viñetas OK si ≤ 30 líneas) | El contenido del término es por definición denso en entradas cortas; cada bullet es una definición autónoma. R5 sí aplica (listas > 5 sin prosa son OK en este tipo). |
| `cheatsheet` | R3 (las tablas cuentan como anclaje aunque no haya callout), R5 (largas listas de comandos OK sin párrafo intermedio), R6 (la tabla principal = estructura) | El contenido es por definición una lista densa de comandos/atajos; el valor está en la compacidad. |
| `index-moc` | R3 + R5 + R6 (todo el contenido son links; no aplica ninguna de las 3) | Un MOC es estructuralmente un índice; su "prosa" son bullets de links. |

Los otros 12 tipos (concept, api-reference, procedure, configuration, error-troubleshooting, architecture, syntax, data-model, chapter-digest, comparison, version-delta, practice) aplican **todas** las reglas R1-R8 sin exención.

---

## §5 · Algoritmo de medición

Este pseudocódigo es el **single source of truth** que `scripts/validate/density_check.py` implementa. El validador real es una traducción literal de este algoritmo a Python.

```
function measure(note_path):
    parsed = parse_note(note_path)
    note_type = parsed.frontmatter.note-type
    rules = default_rules()  # ver §2
    issues = []
    exempt = note_type in rules.exempt_note_types

    # 1. R1 — max párrafo L1
    if not exempt:
        l1 = parsed.section_by_heading("## TL;DR")
        if l1 and l1.paragraphs:
            for p in l1.paragraphs:
                if p.words > 60 or p.lines > 8:
                    issues.append(Issue("R1", "warning", p.path, ...))
        elif not l1:
            issues.append(Issue("R1-missing", "warning", "/", ...))

    # 2. R2 — max párrafo L2
    if not exempt:
        for section in parsed.sections:
            if section.heading == "## TL;DR":
                continue
            for p in section.paragraphs:
                if p.words > 200:
                    issues.append(Issue("R2", "error", p.path, ...))

    # 3. R3 — frecuencia mínima de anclaje
    if note_type not in exempt:
        for section in parsed.sections:
            run_prose = 0
            for block in section.blocks:
                if block.is_prose and not block.is_anchor:
                    run_prose += block.words
                    if run_prose > 200:
                        issues.append(Issue("R3", "warning", section.path,
                                            measured=run_prose, limit=200))
                else:
                    run_prose = 0  # reset on anchor

    # 4. R4 — max callouts consecutivos
    if not exempt:
        for section in parsed.sections:
            run = 0
            for block in section.blocks:
                if block.kind == "callout":
                    run += 1
                    if run > 3:
                        issues.append(Issue("R4", "error", block.path, ...))
                else:
                    run = 0

    # 5. R5 — max viñetas consecutivas
    if note_type not in {"cheatsheet", "index-moc"}:
        for section in parsed.sections:
            run = 0
            for block in section.blocks:
                if block.kind == "list" and not block.is_checklist:
                    run += len(block.items)
                    if run > 5:
                        issues.append(Issue("R5", "error", block.path, ...))
                else:
                    run = 0

    # 6. R6 — sección 100% viñetas
    if note_type not in {"glossary-term", "cheatsheet", "index-moc"}:
        for section in parsed.sections:
            total = len(section.blocks)
            if total == 0:
                continue
            prose_or_struct = sum(
                1 for b in section.blocks
                if b.kind in ("paragraph", "table", "callout", "figure", "diagram", "equation", "code")
            )
            if prose_or_struct == 0 and total > 0:
                issues.append(Issue("R6", "error", section.path, ...))

    # 7. R7 — L3 si > 100 líneas
    if note_type != "architecture":
        for section in parsed.sections:
            if section.lines > 100 and not section.is_collapsible:
                issues.append(Issue("R7", "warning", section.path,
                                    measured=section.lines, limit=100))

    # 8. R8 — densidad {src:}
    if not exempt:
        factual_count = 0
        anchored_count = 0
        for section in parsed.sections:
            for block in section.blocks:
                if block.is_factual:
                    factual_count += 1
                    if block.has_src_mark:
                        anchored_count += 1
        if factual_count >= 5:
            density = anchored_count / factual_count
            if density < 0.80:
                issues.append(Issue("R8", "warning", "/",
                                    measured=density, limit=0.80))

    return issues
```

---

## §6 · Procedimiento de revisión humana

1. **Antes de cerrar la nota**, correr `density_check.py --note <path>`.
2. **Si exit 0:** la nota cumple todas las reglas; publicar.
3. **Si exit 1 (algún error R2/R4/R5/R6):** editar y re-correr. No hay atajo: las reglas R2/R4/R5/R6 son duras por diseño (anti-fatiga, anti-muro-de-texto).
4. **Si exit 0 con warnings (R1/R3/R7/R8):** revisar manualmente. R1 a veces necesita partir el L1 en dos párrafos; R3 puede satisfacerse añadiendo 1 tabla o callout; R7 pide un `:::collapsible`; R8 pide más marcas `{src:}`.
5. **Override humano explícito** con `--allow-violations R2,R5` (lista separada por comas). Usar solo en casos extremos (notas de F19 `concept` con matemática simbólica que requiere párrafo largo para una sola demostración; notas heredadas que no se pueden re-redactar por ahora).

---

## §7 · Anti-patrones comunes

1. **"Muro de texto"** — párrafo > 200 palabras sin anclaje visual intermedio. Solución: partir en 2 párrafos con 1 callout o tabla entre ellos.
2. **"Lluvia de callouts"** — 5+ callouts consecutivos (R4). Solución: añadir 1 párrafo introductorio o de transición entre cada 3.
3. **"Lista infinita"** — 8+ viñetas consecutivas sin párrafo (R5). Solución: agrupar en sub-secciones H3 con párrafo introductorio cada 5.
4. **"Sección fantasma"** — H2 con 1-2 viñetas y nada más (R6). Solución: añadir 1 párrafo introductorio de 2-3 frases.
5. **"L3 sin plegable"** — sección > 100 líneas en plano (R7). Solución: envolver en `:::collapsible` con `default_open: false`.
6. **"Notas sin anclas"** — bloques fácticos sin `{src:}` (R8). Solución: revisar la cobertura de F46; cada hecho verificable lleva al menos un ancla.

---

## §8 · Wirings

- **F46** `references/04-authoring/inline-marks.md` §4 → R8 (densidad `{src:}` ≥ 0.80). F76 ratifica el límite numérico.
- **F51** `references/04-authoring/depth-layers.md` §3 → R1 (L1 ≤ 60 palabras) + R2 (L2 ≤ 200 palabras) + R7 (L3 plegable si > 100 líneas). F76 formaliza los números que F51 definía conceptualmente.
- **F75** `references/07-visual/note-templates.md` §5.2 → tabla cerrada R1-R8 (delega). F76 sustituye los placeholders de F75 por reglas ejecutables.
- **F75** `_header.py:233` → el `profile` del usuario (F11) puede ajustar `max_l2_paragraph_words` o `min_anchors_per_words` por `density` (compact/normal/spacious). F76-FUERA.
- **F77** `evals/visual/` → captura de notas que cumplen R1-R8 visualmente (cerrado; 12 artefactos reales validan R1-R8 a nivel de artefacto; la métrica de presencia es estructural, F77 midió calidad visual con `visual_inspect.py`).
- **F78-F92** `references/05-note-types/*.md` → §4 lista las exenciones por tipo; cada plantilla individual respeta la exención declarada.

---

## §9 · Apéndice: tabla maestra R1-R8 con notas históricas

| # | Límite | Origen histórico | Consecuencia al violar |
|---|---|---|---|
| R1 | ≤ 60 palabras / ≤ 8 líneas | F51 §3 (depth-layers.md L1); F38 §3 lo sugería como guía; F76 lo ratifica | TL;DR pierde autonomía; lector abandona |
| R2 | ≤ 200 palabras | F75 §5.2 (placeholder "F76 ajustará este número") | "Muro de texto"; fatiga visual |
| R3 | ≥ 1 anclaje por cada 200 palabras | F75 §5.2 (placeholder) | "Lluvia de prosa"; lector no concreta visualmente |
| R4 | ≤ 3 callouts consecutivos | F75 §5.2 (anti-fatiga) | "Lluvia de callouts"; el color satura |
| R5 | ≤ 5 viñetas consecutivas | F76 nuevo (consolida F75 §5.2 anti-patrón) | "Lista infinita"; lector pierde hilo |
| R6 | sección debe tener ≥ 1 estructura | F75 §5.2 anti-fatiga + F51 §3 (capa L2 debe tener contenido fáctico) | "Sección fantasma"; la sección parece vacía |
| R7 | > 100 líneas → plegable | F51 §3 (L3 collapsible) | "Muro de scroll"; lector abandona antes del final |
| R8 | ≥ 0.80 anclas por bloque fáctico | F46 §4 (inline-marks.md); F49 lo mide | Trazabilidad rota; F39 grafo de conceptos pierde arcos |

---

**Verificación al cierre de la fase:**

- `wc -l references/07-visual/density.md` ≤ 500 líneas.
- §2 tabla con 8 reglas numeradas (R1-R8) y severidades.
- §3 con 4 subsecciones (anclaje visual, sección, bloque fáctico, capas L1/L2/L3).
- §4 exenciones para 3 tipos (glossary-term, cheatsheet, index-moc).
- §5 pseudocódigo paso 1-12 (algoritmo de medición).
- §6 procedimiento de revisión humana con override explícito.
- §7 6 anti-patrones comunes.
- §8 6 wirings documentados.
- §9 tabla maestra con notas históricas.
