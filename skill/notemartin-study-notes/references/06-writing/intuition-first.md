# `references/06-writing/intuition-first.md` — Redacción `intuition-first`

> Documento normativo de la **Fase 94**. Define el patrón canónico de
> cinco etapas (**Problema → Intuición → Analogía → Formalismo → Confirmación**)
> que aplica por defecto a las notas de tipo `concept` y a la prosa
> pedagógica en general. Adapta el patrón a **features de producto** mediante
> la fórmula **"¿qué hacía la gente antes de que esto existiera?"** y
> acota la excepción `reference-pure` con cuatro checks binarios.
>
> **Cuándo cargar:** antes de redactar la prosa de cualquier nota que no sea
> `reference-pure`; cuando el agente tiene que decidir si el bloque
> pertenece a `## Problema`, `## Intuición`, `## Analogía`, `## Definición
> formal` o `## Confirmación`; cuando un revisor externo necesita
> diagnosticar si la nota cumple el patrón.
>
> **Wirings:**
> - `references/05-note-types/concept.md` (F78) — instancia las 5 etapas
>   en sus 10 secciones obligatorias (`## Problema`, `## Intuición`,
>   `## Analogía`, `## Definición formal`, …).
> - `references/05-note-types/selector.md` (F93) — decide qué tipo de nota
>   aplica; F94 se invoca solo si el tipo requiere pedagogía (no `api-ref`,
>   `syntax`, `cheatsheet` o `data-model` puros).
> - `references/04-authoring/depth-layers.md` (F51) — `## Intuición` y
>   `## Analogía` son L1; `## Problema` y `## Definición formal` son L2.
> - `references/07-visual/density.md` (F76) — R1-R8 aplican sin exención.
> - `schemas/profile.schema.json` (F11) — enum `writing.style` con
>   `intuition-first` como default.
> - F95 (analogías), F96 (ejemplos), F97 (comparaciones), F98 (parafraseo),
>   F99 (voz), F100 (anti-patrones), F101 (i18n) — citados desde §11.

---

## §1 · Propósito y alcance

F94 fija el patrón de redacción por defecto de la skill. Tres
problemas resueltos:

1. **El agente no sabe por dónde empezar** — tiende a saltar del `## TL;DR`
   al formalismo, omitiendo la intuición. El patrón fuerza el orden.
2. **Las notas de producto (features) suenan a manual de marketing** —
   porque repiten la nomenclatura del vendor sin anclar a un problema
   del usuario. La fórmula **"¿qué hacía la gente antes?"** obliga a
   nombrar el dolor.
3. **El patrón se aplicaba de forma laxa** — `references/05-note-types/concept.md`
   F78 ya menciona `## Problema / ## Intuición / ## Analogía / ## Definición formal`
   como secciones obligatorias, pero sin longitudes, marcas o
   validaciones. F94 las normativiza.

**Cierra los 3 criterios del ROADMAP §1644-1646:**

1. _Ejemplos de base de datos y de redes documentados_ → §7 con 2 notas completas.
2. _La excepción está acotada explícitamente_ → §4 con tabla de 4 checks binarios.
3. _Las señales de diagnóstico son verificables por un revisor externo_ → §6 con 10 señales algorítmicas.

**Fuera de alcance:**

- El catálogo de analogías reutilizables → F95 (`analogies.md`).
- Ejemplos ejecutables con setup/cleanup → F96.
- Comparaciones y trade-offs (la sección `## Comparaciones` de `concept.md`) → F97.
- Parafraseo fiel vs literal → F98.
- Voz y estilo → F99.
- Anti-patrones generales → F100.
- Idioma bilingüe y citación → F101.

F94 es **solo** el patrón de 5 etapas + la excepción acotada + las
señales de diagnóstico + los 2 ejemplos (BD + redes).

---

## §2 · Estructura de las 5 etapas

| # | Etapa | Capa | Pregunta | Forma canónica | Marca por defecto |
|---|---|---|---|---|---|
| 1 | `## Problema` | L2 | ¿Qué necesidad existía antes de esta feature? | 1-2 párrafos narrativos (≤ 200 palabras cada uno) | `{src:blk_xxxx}` (lo nombra la fuente) o `:::external` (lo nombra el mundo real) |
| 2 | `## Intuición` | L1 | ¿Por qué la solución tiene esta forma y no otra? | 1 párrafo, ≤ 200 palabras | `[[term:nombre]]` en la primera aparición; sin `{src:}` (la intuición es del agente) |
| 3 | `## Analogía` | L1 | ¿A qué situación conocida se parece? | 1 analogía con dominio conocido distinto | `:::derived` (analogía propia basada en SDM) o `:::external` (referencia cultural); declarar dónde se rompe |
| 4 | `## Definición formal` | L2 | ¿Cuáles son los términos precisos, las propiedades, los invariantes? | Prosa + tabla o fórmula; ≥ 1 anclaje visual cada 200 palabras (R3) | `{src:blk_xxxx}` obligatorio en cada hecho no obvio |
| 5 | `## Confirmación` | L2/L3 | ¿Cómo verifico que entendí bien? | 1 caso real del SDM o `:::example` con salida esperada | `{src:blk_xxxx}` o `:::example` |

**Reglas de la tabla:**

- El orden es fijo: invertir las etapas es el anti-patrón D1 (§6).
- En perfil `reference-pure`, solo etapas 1 y 4 son obligatorias (§4).
- Etapas 2, 3, 5 no llevan `{src:blk_xxxx}` a no ser que la fuente
  las sugiera **literalmente**; la intuición y la analogía son del agente,
  no de la fuente. Excepción: si el SDM literalmente dice "el motivo es…",
  ese texto va a `## Problema` con `{src:}`.

---

## §3 · Adaptación a features de producto

Para features de producto (clases, métodos, parámetros, herramientas,
flags), la bisagra entre `## Problema` y `## Intuición` es responder
una pregunta: **¿qué hacía la gente antes de que esto existiera?**
Plantilla cerrada:

```
Antes de <feature>, <audiencia> hacía <flujo manual>.
Eso causaba <consecuencia medible o cualitativa>.
<Feature> sustituye ese flujo por <mecanismo>.
El cambio neto es que <ahora se puede / ya no hay que>.
```

Tres sub-casos cubiertos por la misma plantilla:

| Sub-caso | Ejemplo DB | Ejemplo redes |
|---|---|---|
| **Sustitución de flujo manual** | `pg_dump` consistente con LVM snapshots reemplazando `cp -r` nocturno | `tcpdump` reemplazando lectura manual de bytes en `ethereal` |
| **Sustitución de cálculo manual** | `SELECT count(*) FROM ...` reemplazando `wc -l archivo.tsv` | `traceroute` reemplazando prueba-y-error con `ping` |
| **Sustitución de convención ad-hoc** | Esquema relacional formal reemplazando "cada equipo escribe su CSV" | RFC estandarizada reemplazando el "protocolo casero" del proveedor |

Si la unidad no es una feature de producto (ej. teorema matemático puro),
la pregunta se reformula: **¿qué problema resolvía este resultado?**

---

## §4 · Excepción acotada: `reference-pure`

`reference-pure` omite `## Intuición`, `## Analogía` y `## Confirmación`.
Solo conserva `## Problema` (opcional) y `## Definición formal` (obligatoria).
La excepción **solo** aplica si las **cuatro** condiciones se cumplen:

| # | Check | Cómo se verifica |
|---|---|---|
| **R1** | `profile.use_case_profile == "reference-pure"` | Inspección del perfil resuelto (F11 §7.4) |
| **R2** | El `note-type` resuelto NO es `concept` (es `api-reference`, `syntax`, `cheatsheet`, `configuration`, `data-model`, `error-troubleshooting`) | Selector F93 §4 |
| **R3** | La unidad es atómica y no pedagógica: no existe una analogía razonable sin inventar | Inspección: la fuente describe **qué es** y **cómo se usa**, no **por qué** |
| **R4** | La fuente no contiene un ejemplo canónico ejecutable que merezca la etapa de Confirmación | Inspección: 0 `:::example` adyacentes en el SDM |

Si **cualquier** check falla → aplicar el patrón completo (5 etapas).

**Límite duro (override):** aunque R1-R4 se cumplan, los perfiles
`study` y `hybrid` **jamás** activan `reference-pure`. El perfil gana
sobre el contenido. Razón: la rúbrica F7 §3 penaliza la ausencia de
analogía en perfiles pedagógicos, así que la promesa de la skill
queda rota si esos perfiles eluden la intuición.

**Confirmación negativa obligatoria:** incluso dentro de
`reference-pure`, la nota debe terminar con un único bloque
"`## Notas`" que **cite literalmente** la fuente descartando la
intuición (`> "el manual no ofrece una motivación pedagógica; ver p.X"`).
Esa cita es la única ancla que justifica la omisión.

---

## §5 · Reglas de redacción por etapa

Reglas verificables (no consejos), con ejemplo malo y ejemplo correcto,
y con la señal de §6 que las caza.

### §5.1 · `## Problema`

| Regla | Ejemplo malo | Ejemplo correcto | Señal |
|---|---|---|---|
| **P1**: 1-2 párrafos narrativos, no lista | `## Problema\n- Lento\n- Caro\n- Difícil` | `## Problema\nAntes de X, los usuarios hacían Y. Eso causaba Z.` | D2 (≤ 200 palabras) + D6 (≥ 1 ancla `{src:}` o `:::external`) |
| **P2**: anclar al SDM o al mundo real, no a "muchos usuarios" | `Muchos usuarios querían esto.` | `pg_dump con pg_locks=BLOCKED detenía inserciones de un e-commerce durante minutos. {src:blk_a3f1}` | D4 (densidad `{src:}` ≥ 0.80) |

### §5.2 · `## Intuición`

| Regla | Ejemplo malo | Ejemplo correcto | Señal |
|---|---|---|---|
| **I1**: ≤ 200 palabras en total | Párrafo de 350 palabras que cubre 4 ideas | `MVCC da a cada transacción un snapshot: cada fila lleva xmin y xmax, y el lector solo ve las filas cuyo rango cae dentro del snapshot.` | D2 |
| **I2**: introduce el término canónico con `[[term:]]` | `Este mecanismo llamado MVCC.` | `Este mecanismo se llama [[term:mvcc]] y se basa en…` | D7 |
| **I3**: NO `{src:blk_xxxx}` (la intuición es del agente) | `PostgreSQL internamente dice que MVCC es… {src:blk_x}` | `MVCC da a cada transacción un snapshot…` (sin marca) | D4 — menos de 1 match de `{src:}` dentro de la sección |

### §5.3 · `## Analogía`

| Regla | Ejemplo malo | Ejemplo correcto | Señal |
|---|---|---|---|
| **A1**: dominio conocido **distinto** del concepto | `Una base de datos es como una hoja de cálculo.` | `Una biblioteca donde cada libro lleva tarjeta de préstamo con fecha de inicio y fin.` | D6 (no match léxico con dominio del concepto) |
| **A2**: declarar explícitamente dónde se rompe | `Imagina una biblioteca.` (sin rotura) | `Imagina una biblioteca… Difiere en que la biblioteca no acumula copias; MVCC sí, hasta el VACUUM.` | D5 (≥ 1 match con `se rompe / no se parece / la diferencia / en cambio / difiere`) |
| **A3**: directiva `:::derived` (analogía propia) o `:::external` (referencia cultural) | `:::example\nComo una biblioteca…\n:::` (mal: no es un ejemplo ejecutable) | `:::derived\nComo una biblioteca…\n:::` | Inspección visual — solo D5/D6 son algorítmicos |

### §5.4 · `## Definición formal`

| Regla | Ejemplo malo | Ejemplo correcto | Señal |
|---|---|---|---|
| **F1**: ≥ 1 anclaje visual cada 200 palabras (R3) | 250 palabras de prosa continua | Tabla de variables + ecuación + diagrama | D3 |
| **F2**: densidad `{src:}` ≥ 0.80 sobre hechos no obvios | Solo 1 ancla en 5 hechos | Cada propiedad lleva su `{src:blk_xxxx}` | D4 |
| **F3**: si hay fórmula, usar `:::equation`; si hay tabla de variables, tabla GFM | Fórmula inline `$x = y$` | `:::equation\nx = y\n:::` | Inspección visual |

### §5.5 · `## Confirmación`

| Regla | Ejemplo malo | Ejemplo correcto | Señal |
|---|---|---|---|
| **C1**: caso real del SDM, no ejemplo inventado | `Podrías probar con cualquier tabla.` | `En PostgreSQL 16, BEGIN; SELECT …; abre el snapshot; un UPDATE concurrente no afecta al lector. {src:blk_a3f1}` | D8 (≥ 1 `{src:}` o `:::example`) |
| **C2**: ≤ 200 palabras; no es un tutorial completo | Cómo instalar PostgreSQL paso a paso | Una sola operación que demuestra la intuición | D2 |

---

## §6 · Señales de diagnóstico (criterio #3)

Tabla cerrada de **10 señales algorítmicas** que un revisor externo
puede aplicar sin reabrir el SDM. Cada señal tiene un método
(regex, conteo, presencia, ratio) y un criterio PASS/FAIL.

| ID | Señal | Método | PASS si |
|---|---|---|---|
| **D1** | Orden de las 5 etapas | Regex `^## (Problema\|Intuición\|Analogía\|Definición formal\|Confirmación)` en orden ascendente | 5 matches en orden canónico (o 2 matches `Problema`+`Definición formal` en orden, si `reference-pure`) |
| **D2** | Longitud de cada párrafo L2 | `wc -w` sobre cada `## Problema` / `## Definición formal` / `## Confirmación` | ≤ 200 palabras por párrafo (R2) |
| **D3** | Anclaje visual en `## Definición formal` | Conteo de `:::equation` / `:::diagram` / tablas GFM / `:::figure` cada 200 palabras de la sección | ≥ 1 por cada 200 palabras (R3) |
| **D4** | Densidad `{src:}` en bloques fácticos | `len(regex \{src:blk_[0-9a-f]{12}\}) / total bloques fácticos` | ≥ 0.80 (R8). Excepción: `## Intuición` admite 0 anclas (es contenido del agente). |
| **D5** | Analogía declara su rotura | Regex dentro de `## Analogía`: `se rompe\|no se parece\|la diferencia\|en cambio\|difiere\|difiere de\|a diferencia de` (case-insensitive) | ≥ 1 match |
| **D6** | Analogía usa dominio distinto | Inspección léxica: las palabras del dominio del concepto (`base de datos`, `red`, `kernel`, `tabla`, `socket`) no aparecen como núcleo de la analogía | Coincidencia léxica = 0 (criterio subjetivo cuantificado: se cuentan ocurrencias y se exige ≤ 1 palabra clave del dominio) |
| **D7** | Término canónico en `## Intuición` | Regex `\[\[term:[a-z0-9_-]+\]\]` dentro de la sección | ≥ 1 (INV-I2) |
| **D8** | `## Confirmación` con caso real | Presencia de `{src:blk_xxxx}` o bloque `:::example` | ≥ 1 ancla real |
| **D9** | Excepción acotada presente | Inspección: existe `## §4` o equivalente con tabla de 4 checks binarios + override textual `study`+`hybrid` | Presencia verificada |
| **D10** | Sin relleno valorativo | Ratio de adjetivos valorativos (`sencillo`, `poderoso`, `elegante`, `simple`, `robusto`, `increíble`) por cada 200 palabras | ≤ 2 por cada 200 palabras |

---

## §7 · Ejemplos completos (criterio #1)

### §7.1 · Base de datos: PostgreSQL — MVCC

```notemark
## Problema
Antes de MVCC, los motores como MySQL con MyISAM o PostgreSQL ≤ 8 usaban
locks de tabla para que un `SELECT` no viera escrituras concurrentes. Eso
provocaba que un `pg_dump` bloqueara todas las inserciones de un e-commerce
durante minutos, y que un reporte diario compitiera con la carga OLTP. {src:blk_a3f1}

## Intuición
En lugar de "copia la fila y bloquéala hasta que termine la lectura", MVCC le
da a cada transacción un **snapshot**: cada fila lleva dos marcas de versión,
`xmin` y `xmax`, y el lector solo ve las filas cuyo rango cae dentro de su
snapshot. [[term:mvcc]]

## Analogía
Imagina una biblioteca donde cada libro tiene una tarjeta de préstamo con
fecha de inicio y fecha de fin. Para saber si un libro está disponible, miras
la tarjeta en el instante en que entras: si tu instante está dentro del
rango, lo tienes; si no, ya se fue. :::derived
**Dónde se rompe:** la biblioteca no acumula copias; MVCC sí, la fila vieja
se conserva en disco hasta el `VACUUM`.

## Definición formal
Para una transacción `T` con snapshot en `S(T)` y una fila `R` con versiones
`[xmin_R, xmax_R]`:
- `R` es visible para `T` si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a3f1}
- El `xmax` lo fija la transacción que borra o reemplaza la fila. {src:blk_a3f1}
- `VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a3f1}

:::equation
visible(T, R) := xmin_R < S(T) ∧ (xmax_R = ∞ ∨ xmax_R > S(T))
:::

:::diagram
flowchart LR
    T[Transacción T] -->|snapshot S T| V{visible T R}
    V -->|sí| Visible[Lectura visible]
    V -->|no| Hidden[Lectura oculta]
:::

## Confirmación
En PostgreSQL 16, `BEGIN; SELECT * FROM accounts WHERE id = 1;` abre el
snapshot en ese instante. Una transacción concurrente que ejecuta
`UPDATE accounts SET balance = 0 WHERE id = 1; COMMIT;` después no afecta
al lector hasta su próximo `BEGIN`. {src:blk_a3f1}
```

### §7.2 · Redes: TCP three-way handshake

```notemark
## Problema
Antes del handshake de tres pasos, los primeros protocolos (ej. TFTP sobre
datagrama único) abrían una conexión enviando datos directamente. El problema
es que un datagrama de petición podía ser duplicado por la red y el servidor
entregaba el archivo dos veces si lo procesaba dos veces. {src:blk_b712}

## Intuición
La conexión TCP necesita probar que ambos lados pueden enviar y recibir en
ese instante. Eso requiere tres mensajes: el cliente dice "quiero hablar"
(SYN), el servidor reconoce y propone parámetros (SYN+ACK), y el cliente
reconoce a su vez (ACK). [[term:three-way-handshake]]

## Analogía
Como una llamada telefónica: tú marcas mi número, yo descuelgo y digo
"¿Hola?", tú dices "Hola, soy yo". Solo después de los tres "habla" sabemos
que los dos podemos oír y ser oídos. :::external
**Dónde se rompe:** en una llamada no se negocian números de secuencia;
TCP sí, porque los paquetes pueden llegar fuera de orden.

## Definición formal
Estados y transiciones del cliente:
| Estado cliente | Evento | Estado siguiente | Envía |
|---|---|---|---|
| CLOSED | enviar SYN | SYN-SENT | SYN seq=ISN_c |
| SYN-SENT | recibir SYN+ACK, enviar ACK | ESTABLISHED | ACK seq=ISN_c+1, ack=ISN_s+1 |
| ESTABLISHED | datos | ESTABLISHED | — |

{src:blk_b712}

:::equation
SYN:        cliente → servidor, seq = ISN_c
SYN+ACK:    servidor → cliente, seq = ISN_s, ack = ISN_c + 1
ACK:        cliente → servidor, seq = ISN_c + 1, ack = ISN_s + 1
:::

## Confirmación
`tcpdump -i any -nn -S port 80` durante `curl https://example.com` muestra
las tres líneas con flags `S`, `S.`, `.` (SYN, SYN+ACK, ACK) en orden. {src:blk_b712}
```

---

## §8 · Activación por perfil y estilo

`schemas/profile.schema.json` (F11) define el enum cerrado `writing.style`:
`intuition-first` (default), `reference-pure`, `tutorial`, `summary`.
La tabla siguiente indica qué versión del patrón aplica:

| `use_case_profile` | `writing.style` | Versión del patrón | Etapas obligatorias |
|---|---|---|---|
| `study` | `intuition-first` (default) | 5 etapas completas | Problema + Intuición + Analogía + Definición formal + Confirmación |
| `hybrid` | `intuition-first` (default) | 5 etapas completas | 5 etapas |
| `operator` | `reference-pure` | 2 etapas | Problema + Definición formal + bloque `## Notas` con cita literal que descarta la intuición |
| `developer` | `tutorial` | 5 etapas, énfasis en Confirmación | 5 etapas, `## Confirmación` con `:::example` ejecutable obligatorio |
| `engineer` | `summary` | 3 etapas | Problema + Definición formal + Confirmación (sin Intuición ni Analogía) |
| `study` / `hybrid` | `reference-pure` | **NUNCA** — override por perfil | 5 etapas completas (perfil gana sobre contenido) |

**Límite duro:** la fila 6 (override) aplica aunque `writing.style`
sea `reference-pure`. El agente **no** debe acatar `reference-pure`
cuando el `use_case_profile` es `study` o `hybrid`.

---

## §9 · Anti-patrones

| # | Nombre | Anti-ejemplo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | "Orden invertido" | Definición formal antes de Problema | Problema → … → Definición formal | D1 |
| **AP2** | "Intuición de 400 palabras" | Párrafo único de 400 palabras | 1-2 párrafos ≤ 200 palabras | D2 |
| **AP3** | "Analogía del mismo dominio" | "MVCC es como una transacción" (no es analogía, es redundancia) | Analogía con biblioteca / cocina / banco / biblioteca | D6 |
| **AP4** | "Analogía sin rotura" | "Como una biblioteca. Fin." | "Como una biblioteca… Difiere en que…" | D5 |
| **AP5** | "Problema sin ancla" | "Antes esto era lento." (sin `{src:}` ni `:::external`) | "pg_dump bloqueaba inserciones durante minutos. {src:blk_a3f1}" | D4 |
| **AP6** | "Confirmación inventada" | "Podrías verificarlo tú mismo con cualquier tabla." | "En PostgreSQL 16, BEGIN; SELECT… abre el snapshot. {src:blk_a3f1}" | D8 |
| **AP7** | "Reference-pure en study" | Nota `concept` de MVCC sin `## Intuición` en perfil `study` | Aplicar las 5 etapas completas | Inspección: R1 del override §4 |
| **AP8** | "Relleno valorativo" | "MVCC es una solución sencilla, poderosa y elegante." | "MVCC le da a cada transacción un snapshot." | D10 |

---

## §10 · Checklist de cierre

Antes de cerrar L3 sobre una nota `concept` o `comparison` con prosa
pedagógica, el agente verifica:

- [ ] Las 5 etapas aparecen en orden canónico (D1).
- [ ] `## Problema` está anclado al SDM (`{src:}`) o al mundo real (`:::external`) (D4).
- [ ] `## Intuición` ≤ 200 palabras y lleva el término canónico con `[[term:nombre]]` (D2 + D7).
- [ ] `## Analogía` usa un dominio distinto (D6), declara dónde se rompe (D5) y lleva `:::derived` o `:::external`.
- [ ] `## Definición formal` tiene ≥ 1 anclaje visual cada 200 palabras (D3) y densidad `{src:}` ≥ 0.80 (D4).
- [ ] `## Confirmación` cita un caso real del SDM (D8).
- [ ] El ratio de adjetivos valorativos ≤ 2 por 200 palabras (D10).
- [ ] Si `use_case_profile == "reference-pure"` y `note-type != "concept"`: R1-R4 cumplidos + bloque `## Notas` con cita literal que descarta la intuición.
- [ ] Si `use_case_profile ∈ {"study", "hybrid"}`: las 5 etapas obligatorias aunque el `writing.style` declarado sea `reference-pure`.
- [ ] El `density_check.py --strict` (F76) retorna exit 0.

---

## §11 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` enum `writing.style` | Define los 4 estilos; `intuition-first` es default |
| F45 | `references/04-authoring/block-directives.md` | `:::derived` / `:::external` se explican en §10.11-§10.12 |
| F46 | `references/04-authoring/inline-marks.md` | `{src:blk_xxxx}` (INV-I5), `[[term:nombre]]` (INV-I2), `[[note:id]]` |
| F47 | `references/04-authoring/properties.md` | Frontmatter canónico con `use_case_profile` |
| F51 | `references/04-authoring/depth-layers.md` | `## Intuición` y `## Analogía` son L1; el resto L2/L3 |
| F76 | `references/07-visual/density.md` + `scripts/validate/density_check.py` | R1-R8 sin exención |
| F78 | `references/05-note-types/concept.md` §3 tabla de componentes | Instancia las 5 etapas en sus 10 secciones obligatorias |
| F93 | `references/05-note-types/selector.md` §3 matriz | Decide si la nota requiere intuición o `reference-pure` |
| F95 | `references/06-writing/analogies.md` | Catálogo de analogías reutilizables |
| F96 | `references/06-writing/executable-examples.md` | Setup/cleanup de ejemplos en `## Confirmación` |
| F97 | `references/06-writing/comparisons.md` | Tablas de trade-offs para `## Comparaciones` |
| F98 | `references/06-writing/paraphrase.md` | Parafraseo de `## Problema` y `## Definición formal` |
| F99 | `references/06-writing/voice-style.md` | Reglas R1-R8 verificables |
| F100 | `references/06-writing/anti-patterns.md` | Catálogo general de anti-patrones |
| F101 | `references/06-writing/i18n-and-citation.md` | Primera aparición bilingüe del término canónico |

**Invocación desde SKILL.md:** la fila de `references/06-writing/intuition-first.md`
aparece en §5.2 con la entrada _"Estilo `intuition-first` para nota `concept`"_.

---

## §12 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Ejemplos de base de datos y de redes documentados | `evals/intuition-first-sample/run_eval.py` busca `### §7.1` con término `PostgreSQL\|mvcc` y `### §7.2` con término `TCP\|three.?way\|handshake` |
| **C2** La excepción está acotada explícitamente | Búsqueda de `## §4 Excepción acotada` + tabla de 4 columnas booleanas + override textual con los literales `study` y `hybrid` |
| **C3** Señales de diagnóstico verificables por revisor externo | Búsqueda de `## §6 Señales de diagnóstico` + tabla con ≥ 8 filas, columnas `Método` y `PASS si` no vacías y método algorítmico |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l` sobre `intuition-first.md` ≤ 500.
- **D2.** Las 5 secciones aparecen en orden correcto en `db-mvcc.md` y `net-tcp-3whs.md`.
- **D3.** En ambos ejemplos, `## Analogía` contiene ≥ 1 frase que matchea D5.
- **D4.** En ambos ejemplos, `## Intuición` contiene ≥ 1 `[[term:...]]`.
- **D5.** Wirings cerrados (`references/06-writing/README.md` ya no marca F94 como pendiente; `SKILL.md` §5.2 referencia el archivo).
- **D6.** Override textual presente (regex sobre `study.*hybrid.*no activan|reference-pure.*único|override.*perfil`).
