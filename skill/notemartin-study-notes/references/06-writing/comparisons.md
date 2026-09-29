# `references/06-writing/comparisons.md` — Comparaciones y trade-offs

> Documento normativo de la **Fase 97**. Define las **5 formas canónicas**
> de comparación (tabla lado a lado, jerarquía por relajación de
> restricciones, matriz de decisión por escenario, tabla de trade-offs,
> párrafo de síntesis), **≥ 3 plantillas** cerradas (DB / protocolos /
> arquitectura), **5 marcas de "comparación derivada"**, **6 anti-patrones**
> y **≥ 8 señales de diagnóstico algorítmicas**.
>
> **Cuándo cargar:** antes de redactar cualquier sección de comparación
> (`## Comparaciones` en `concept.md`, `## Comparativa` en `comparison.md`,
> `## Trade-offs` en `architecture.md`, o un párrafo comparativo inline
> en `## Analogía` o `## Definición formal`); cuando un revisor detecta
> que una tabla comparativa no tiene síntesis, no marca filas derivadas,
> o no tiene fila decisiva.
>
> **Wirings:**
> - `references/05-note-types/comparison.md` (F87) §2.3, §3.1-§3.2 — patrón
>   del tipo de nota `comparison`; F97 norma el artefacto transversal.
> - `references/05-note-types/concept.md` (F78) §3 fila `## Comparaciones`
>   — se construye con las formas de F97.
> - `references/05-note-types/architecture.md` (F83) `## Trade-offs` —
>   usa la forma F4 de F97.
> - `references/04-authoring/block-directives.md` (F45) §10.11-§10.12 —
>   `:::derived` / `:::external` para marcar comparaciones del agente.
> - `references/04-authoring/inline-marks.md` (F46) — `{derived}` /
>   `{external}` inline complementario.
> - `references/07-visual/density.md` (F76) — R1-R8 sin exención; tablas
>   cuentan como anclaje visual (R3).
> - F94 (intuición), F95 (analogías), F96 (ejemplos) — citados desde §12.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F97:

1. **Las comparaciones no tienen síntesis.** El agente pone una tabla
   y se va; el lector tiene que extraer las similitudes y diferencias
   por su cuenta. F97 obliga al **párrafo de síntesis** tras cada
   tabla (criterio #1 ROADMAP).
2. **Las comparaciones se inventan sin marcar.** "PostgreSQL es más
   maduro que MySQL" es una afirmación del agente basada en su
   conocimiento, no del SDM. F97 obliga a marcar toda comparación
   que no aparece literal en la fuente con `:::derived` o `:::external`
   (criterio #2).
3. **No se usa el patrón "matriz de decisión por escenario".** El
   agente solo conoce la tabla lado a lado y la tabla de trade-offs.
   F97 introduce la **jerarquía por relajación** y la **matriz de
   decisión** como patrones canónicos (criterio #3).

**Cierra los 3 criterios del ROADMAP §1668-1670:**

1. _Toda tabla va seguida del párrafo de síntesis_ → §8 + §11 D1-D2.
2. _Las comparaciones no presentes en la fuente están marcadas como derivadas_ → §9 + §11 D3.
3. _Hay al menos una matriz de decisión de ejemplo técnico_ → §6 + §13 C8.

**Fuera de alcance:**

- El tipo de nota `comparison` (su estructura, sus secciones, su frontmatter) → F87.
- La sección `## Comparaciones` de la nota `concept` → F78 (F97 norma el artefacto que la puebla).
- Parafraseo de las celdas de la tabla → F98.
- Anti-patrones generales → F100.
- Idioma bilingüe → F101.

---

## §2 · Las 5 formas canónicas

Tabla cerrada con las **5 formas** que toda comparación correcta puede
combinar. Una nota puede usar 1, 2, 3 o más; las combinaciones típicas son
**tabla + síntesis** (F1+F5), **trade-offs + matriz + síntesis** (F4+F3+F5)
y **jerarquía + tabla + síntesis** (F2+F1+F5).

| # | Forma | Capa | Marca preferida | Regex de detección | Cuándo usar |
|---|---|---|---|---|---|
| **F1** | Tabla lado a lado | L2 | sin marca (default) o `:::derived` si la construye el agente | `^\|.+\|.+\|$\n\|---` con ≥ 3 filas | Cuando los **criterios son fijos** y las opciones no cambian. |
| **F2** | Jerarquía por relajación | L2 | `:::derived` (siempre la construye el agente) | `\| Nivel \|` o `\| Restricci[oó]n \|` | Cuando hay una **familia de sistemas** y cada nivel relaja una restricción. |
| **F3** | Matriz de decisión por escenario | L2 | sin marca o `:::derived` | `\| Escenario \|` con ≥ 3 filas | Cuando la **mejor opción depende del contexto** (escenario del usuario). |
| **F4** | Tabla de trade-offs | L2 | `:::derived` | `\| Trade-off \|` con ≥ 3 filas | Cuando cada opción **gana algo y pierde algo** en cada dimensión. |
| **F5** | Párrafo de síntesis | L2 | sin marca (parte del flujo) o `{src:blk_xxxx}` si viene del SDM | `^##\s+S[ií]ntesis\s*$` o párrafo inmediatamente tras tabla | **Siempre** tras cada tabla de F1-F4. Criterio #1 ROADMAP. |

**Reglas de combinación:**

- F1 + F5 es el mínimo (tabla + síntesis).
- F4 + F3 + F5 es la combinación recomendada para `comparison.md` (F87).
- F2 + F1 + F5 es la combinación recomendada para mostrar la evolución de
  una familia de sistemas.

---

## §3 · Plantillas canónicas (≥ 3)

### §3.1 · T1 · DB vs DB (PostgreSQL vs MySQL)

```notemark
## Comparativa

| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Modelo | ORDBMS | RDBMS |
| Consistencia | ACID por defecto | ACID con InnoDB |
| JSON nativo | `jsonb` (binario, indexable) | `json` (texto) |
| Replicación lógica | nativa (`pgoutput`) | nativa (`binlog`) |
| Madurez (años en producción) | 28 | 29 |
| Ecosistema (extensiones) | amplio (PostGIS, pgvector) | amplio (MySQL Shell, HeatWave) |

:::tip
**Fila decisiva — Madurez.** Ambas tienen ≥ 25 años; la elección suele
venir del ecosistema (PostGIS para geo, MySQL Shell para DBA legacy).
:::

## Síntesis

Ambas opciones comparten {consistencia ACID con su motor por defecto} y
{madurez superior a 25 años con amplia base instalada}. La diferencia
clave es que {PostgreSQL ofrece `jsonb` indexable mientras MySQL tiene
`json` textual}, lo que cambia el rendimiento en queries JSON. {src:blk_xxxx}
:::
```

### §3.2 · T2 · Protocolo vs protocolo (REST vs gRPC)

```notemark
## Comparativa

| Criterio | REST sobre HTTP/1.1 | gRPC sobre HTTP/2 |
|---|---|---|
| Formato | texto (JSON, XML) | binario (Protobuf) |
| Contrato | OpenAPI (opcional) | Protobuf (obligatorio) |
| Streaming | no nativo | bidireccional nativo |
| Latencia (p50) | ~20 ms (HTTP/1.1) | ~5 ms (HTTP/2) |
| Debugging | `curl`, navegador | `grpcurl`, reflección |
| Madurez (años) | 24 | 9 |

:::tip
**Fila decisiva — Streaming.** gRPC gana si la app necesita
streaming bidireccional; REST gana para APIs públicas legibles por humanos.
:::

## Jerarquía por relajación

| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | REST sobre HTTP/1.1 | legibilidad humana | latencia, streaming |
| 1 | REST sobre HTTP/2 | multiplexing | sin cambios en semántica |
| 2 | REST + Protobuf en body | tamaño binario | legibilidad |
| 3 | gRPC sobre HTTP/2 | streaming + contrato estricto | legibilidad, tooling |

## Síntesis

REST y gRPC comparten {modelo request-response y autenticación por
headers}, pero {REST usa texto y gRPC usa Protobuf binario}. La diferencia
clave es que {gRPC soporta streaming bidireccional nativo, REST no}.
{src:blk_xxxx}
:::
```

### §3.3 · T3 · Arquitectura vs arquitectura (monolito vs microservicios)

```notemark
## Trade-offs

| Trade-off | Monolito | Microservicios |
|---|---|---|
| Latencia interna | baja (in-process) | alta (red) |
| Despliegue | atómico (todo a la vez) | independiente (1 servicio) |
| Consistencia de datos | fuerte (misma DB) | eventual (sagas, CDC) |
| Coste operativo inicial | bajo | alto |
| Coste operativo a escala | alto | bajo |
| Madurez del equipo | júnior suficiente | requiere plataforma |

## Matriz de decisión por escenario

| Escenario | Mejor opción | Justificación |
|---|---|---|
| Startup con 1-3 devs y 1 producto | Monolito | Coste operativo bajo, latencia baja |
| Empresa con 10+ devs y 2+ productos | Microservicios | Despliegue independiente, escala por equipo |
| Compliance estricto (banca, salud) | Monolito | Consistencia fuerte, auditabilidad simple |
| Carga global con SLA por región | Microservicios | Latencia regional, degradación contenida |

:::tip
**Fila decisiva — Madurez del equipo.** Un monolito bien hecho es mejor
que 50 microservicios mal mantenidos. :::derived
:::

## Síntesis

Monolito y microservicios comparten {el mismo modelo de programación
(request-response) y el mismo almacenamiento de datos}, pero {el
monolito asume 1 proceso mientras los microservicios asumen N procesos
con red}. La diferencia clave es que {el monolito tiene consistencia
fuerte trivial; los microservicios requieren saga, CDC o event sourcing}.
:::derived :::external
{src:blk_xxxx}
:::
```

Las 3 plantillas comparten 5 propiedades:
- Tabla con criterios comparables (paralelismo, criterio #3 de F87).
- Fila decisiva con `:::tip`.
- ≥ 1 forma complementaria (síntesis siempre; trade-offs o jerarquía si aplica).
- Marca explícita del origen (`:::derived` o `:::external` cuando no viene del SDM).
- Ancla `{src:blk_xxxx}` en la síntesis cuando algún dato viene literal del SDM.

---

## §4 · Tabla lado a lado

### §4.1 · Definición cerrada

```
| Criterio | Opción A | Opción B | [+ Opción C opcional] |
|---|---|---|---|
| … | … | … | … |
```

**Reglas duras:**

1. **≥ 4 criterios** (F87 §3.1). Por debajo, no es comparación, es lista.
2. **Cero criterios no paralelos**: cada opción DEBE tener valor en cada
   criterio, o `n/a` explícito si genuinamente no aplica.
3. **Fila decisiva al final**, envuelta en `:::tip`.
4. **Criterios medibles**, no adjetivos. Válido: `writes/s = 50k`.
   Inválido: `rendimiento alto`.

### §4.2 · Fila decisiva

```
:::tip
**Fila decisiva — <nombre del criterio>.** <Justificación en 1 frase>.
:::
```

La fila decisiva va **siempre** al final de la tabla. El agente debe
poder decir en 1 frase por qué esa fila es la que más pesa en la
decisión final.

---

## §5 · Jerarquía por relajación de restricciones

### §5.1 · Definición cerrada

Patrón que muestra la **evolución de una familia de sistemas**: cada fila
relaja una restricción previa y muestra lo que se gana y se pierde.

```
| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | (caso base) | … | … |
| 1 | relaja X | Y | Z |
| 2 | relaja X + W | … | … |
```

### §5.2 · Cuándo usar

- Cuando hay una **familia de sistemas** (REST, REST+JSON, gRPC, GraphQL).
- Cuando el lector quiere **entender el espacio de diseño** y por qué
  cada nivel existe.
- Cuando la decisión entre opciones no es "A vs B" sino "qué nivel de
  relajación necesito para mi caso".

### §5.3 · Reglas

- Cada fila DEBE relajar **al menos una** restricción de la fila anterior.
- "Lo que se gana" y "lo que se pierde" son **concretas**, no genéricas.
- La fila 0 suele ser el caso base del dominio.

---

## §6 · Matriz de decisión por escenario

### §6.1 · Definición cerrada

```
| Escenario | Mejor opción | Justificación |
|---|---|---|
| Escenario 1 | Opción A | <1 frase> |
| Escenario 2 | Opción B | <1 frase> |
| … | … | … |
```

### §6.2 · Cuándo usar

- Cuando la **mejor opción depende del contexto del usuario** (escenario).
- Cuando el lector tiene que elegir **su** mejor opción y la tabla
  lado a lado no le alcanza.
- Cuando la fila decisiva de §4 puede **invertirse** según el escenario.

### §6.3 · Reglas

- **≥ 3 escenarios** (F87 §2.3 fila 5). Por debajo, no es matriz, es opinión.
- Cada escenario DEBE ser **distinguible** del siguiente por al menos
  un criterio explícito (tamaño, latencia, equipo, etc.).
- La justificación va en 1 frase por escenario; si necesita más, es
  otra tabla o un párrafo.

### §6.4 · Ejemplo canónico (3 escenarios mínimos)

```
| Escenario 1 | Opción A | <1 frase> |
| Escenario 2 | Opción B | <1 frase> |
| Escenario 3 | Opción A | <1 frase> |
```

---

## §7 · Tabla de trade-offs

### §7.1 · Definición cerrada

```
| Trade-off | Opción A | Opción B |
|---|---|---|
| Consistencia vs disponibilidad | ACID | eventual |
| Madurez vs innovación | 25 años | 5 años |
| … | … | … |
```

### §7.2 · Cuándo usar

- Cuando cada opción **gana una propiedad y pierde otra** en la misma
  dimensión (es el patrón "no hay almuerzo gratis").
- Cuando la tabla lado a lado muestra solo "A gana en X, B gana en Y"
  sin explicitar el coste.

### §7.3 · Reglas

- **≥ 3 filas** (F87 §2.3 fila 6).
- Cada fila nombra **explícitamente la propiedad que se gana** y **la
  que se pierde** (no vale "diferente", vale "consistencia por
  disponibilidad").
- Las opciones A y B son las **mismas** que en la tabla lado a lado
  de §4 (no se mezclan comparaciones).

---

## §8 · Párrafo de síntesis obligatorio (criterio #1)

### §8.1 · Plantilla cerrada

```
## Síntesis

Ambas opciones comparten {similitud 1} y {similitud 2}. La diferencia
clave es que {A se enfoca en X mientras B optimiza Y}. {1 frase resumen
con la decisión típica}. {src:blk_xxxx (si algún dato viene del SDM)}
```

### §8.2 · Reglas algorítmicas

- ≥ 2 similitudes explícitas con palabras como `comparten`, `ambas`,
  `también`, `igual`.
- 1 diferencia clave con `diferencia clave`, `mientras`, `frente a`,
  `a diferencia de`.
- 1 frase resumen al final.
- Total ≥ 30 palabras (plantilla cerrada).
- Si la tabla viene del SDM y la síntesis la construye el agente, la
  síntesis lleva `:::derived` o `{derived}` inline.

### §8.3 · Cuándo NO aplica

- Cuando la tabla es **explícitamente derivada** y se etiqueta como
  tal (`:::derived` + 1 frase "Comparación construida por el agente a
  partir de la documentación oficial, no del SDM").
- En perfiles `reference-pure` (F94 §4): la síntesis puede ser
  opcional si la nota es de tipo `api-reference` o `syntax`.

---

## §9 · Marcado de comparaciones derivadas (criterio #2)

### §9.1 · Lista cerrada de marcas

| Marca | Cuándo aplicar | Ejemplo |
|---|---|---|
| `:::derived` | Comparación que el agente construye **basada en el SDM** (síntesis, jerarquía por relajación, fila decisiva) | "PostgreSQL es más maduro que MySQL" extraído del SDM (release notes históricos). |
| `:::external` | Comparación que el agente trae **de fuera del SDM** (conocimiento general, benchmark público, RFC) | "PostgreSQL es más rápido en TPC-C" basado en un benchmark público. |
| `:::external` + eliminar | Comparación que es **opinión del modelo**, no verificable | "PostgreSQL tiene mejor DX que MySQL" → eliminar. |

### §9.2 · Lista cerrada de "siempre derivadas"

Estas comparaciones se construyen casi siempre desde fuera del SDM y
deben marcarse con `:::external`:

- **MD1** Benchmarks de rendimiento (`TPC-C`, `YCSB`, `sysbench`).
- **MD2** Popularidad o adopción (`Stack Overflow survey`, `DB-Engines ranking`).
- **MD3** Ecosistema / comunidad (número de extensiones, plugins, integraciones).
- **MD4** Madurez expresada en años (no siempre literal en el SDM).
- **MD5** Latencia / throughput / coste medido en producción (no en el SDM).

Las comparaciones que el agente deduce del SDM (release notes,
sección "comparison" oficial del manual) se marcan `:::derived`.

---

## §10 · Anti-patrones (≥ 6)

| # | Anti-patrón | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | Tabla sin síntesis | `## Comparativa\n| A | B |\n|---|---|\n` y siguiente H2 sin párrafo intermedio | Tabla + `## Síntesis` con ≥ 2 similitudes + 1 diferencia | D1 (presencia de `## Síntesis`) + D2 (≥ 30 palabras en la síntesis) |
| **AP2** | Fila decisiva al medio | Fila decisiva en la posición 3 de 6 | Fila decisiva **siempre** al final de la tabla (F87 §3.1) | D4 (regex `:::tip` aparece tras la última fila) |
| **AP3** | Criterios no paralelos | `\| Popularidad \| alta \| n/a \|` (n/a sin justificación) | Criterio paralelo o se omite la fila | Inspección visual + criterio #3 de F87 |
| **AP4** | Comparación inventada sin marca | "PostgreSQL es 3x más rápido" sin `{src:}` ni `:::external` | `:::external` + benchmark citado | D3 (presencia de `:::derived` o `:::external`) |
| **AP5** | Síntesis con opinión | "Personalmente prefiero PostgreSQL." | Eliminar la opinión o `:::external` "fuera del SDM" | D5 (regex contra `personalmente\|prefiero\|creo que\|opino`) |
| **AP6** | Jerarquía monotónica sin branching | Nivel 0 → 1 → 2 todos relajando la misma restricción | Cada nivel relaja una restricción **distinta** | Inspección visual: cada celda "Restricción relajada" es distinta |
| **AP7** | Criterios cualitativos sin número | "rendimiento alto" | "writes/s = 50k" | Inspección visual (no regex) |
| **AP8** | Matriz con escenario repetido | "Startup pequeño" + "Startup mediano" con la misma recomendación | Escenarios **distinguibles** | D6 (regex contra escenarios duplicados) |

---

## §11 · Señales de diagnóstico (≥ 8)

Tabla cerrada de **10 señales algorítmicas** que un revisor externo aplica
sin tener que reabrir el SDM.

| ID | Señal | Método | PASS si |
|---|---|---|---|
| **D1** | Toda tabla va seguida de `## Síntesis` | Regex `^##\s+S[ií]ntesis\s*$` después de cada tabla `\|---\|` | ≥ 1 `## Síntesis` tras cada tabla detectada |
| **D2** | Párrafo de síntesis con ≥ 2 similitudes + 1 diferencia | Regex `comparten\|ambas\|tambi[ée]n\|igual` ≥ 2 + `diferencia\|mientras\|frente a\|a diferencia de` ≥ 1 | ≥ 2 matches del primer grupo + ≥ 1 match del segundo |
| **D3** | Comparaciones no del SDM llevan `:::derived` o `:::external` | Regex `:::derived\|:::external` en bloques con afirmaciones tipo benchmark/popularidad/madurez | ≥ 1 match por bloque |
| **D4** | Fila decisiva con `:::tip` al final | Regex `:::tip` después de la última fila `\|---\|` y antes de la siguiente `\|---\|` o fin de tabla | Presencia + posición |
| **D5** | Sin opinión personal | Regex `personalmente\|prefiero\|creo que\|opino que\|en mi opini[oó]n` | 0 matches en comparaciones (las opiniones se eliminan o se marcan `:::external`) |
| **D6** | Escenarios distinguibles en matriz | Inspección de la columna `Escenario`: cada celda es única | ≥ 3 celdas únicas |
| **D7** | Criterios medibles en tabla lado a lado | Regex contra celdas con números, unidades, años, o `n/a` | ≥ 80% de celdas no vacías contienen número/unidad/`n/a` |
| **D8** | Marca `{src:}` o `:::derived` en la síntesis | Regex `\{src:blk_[0-9a-f]{12}\}` o `:::derived` en el párrafo `## Síntesis` | ≥ 1 match cuando algún dato de la síntesis viene del SDM |
| **D9** | Sin enumeraciones cerradas truncadas | Regex `\betc\b\|\bentre otros\b\|\blos m[aá]s relevantes\b` | 0 matches en comparaciones (F98 + INV-10) |
| **D10** | Anclajes visuales en tablas | Conteo de tablas GFM por cada 200 palabras en secciones comparativas | ≥ 1 tabla por cada 200 palabras (R3) |

---

## §12 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` | El tipo de comparación aplica a todos los perfiles; la síntesis obligatoria puede relajarse en `reference-pure` (§8.3). |
| F45 | `references/04-authoring/block-directives.md` §10.11-§10.12 | `:::derived` / `:::external` para marcar comparaciones del agente. |
| F46 | `references/04-authoring/inline-marks.md` | `{derived}` / `{external}` inline complementario. |
| F51 | `references/04-authoring/depth-layers.md` | F1-F4 viven en L2; F5 (síntesis) también L2. |
| F76 | `references/07-visual/density.md` + `scripts/validate/density_check.py` | R1-R8 sin exención; tablas cuentan como anclaje visual (R3). |
| F78 | `references/05-note-types/concept.md` §3 fila `## Comparaciones` | Se construye con F1+F5 (mínimo). |
| F83 | `references/05-note-types/architecture.md` `## Trade-offs` | Usa la forma F4 de F97. |
| F87 | `references/05-note-types/comparison.md` | Tipo de nota dedicado; F97 norma el artefacto transversal. |
| F94 | `references/06-writing/intuition-first.md` | Las comparaciones pueden aparecer en `## Analogía` (como contraejemplo) o `## Definición formal` (como propiedades comparadas). |
| F95 | `references/06-writing/analogies.md` | Una analogía mal construida se ve como una comparación pobre; F95/F97 cubren dimensiones ortogonales. |
| F96 | `references/06-writing/executable-examples.md` | Las comparaciones pueden referenciar ejemplos (`## Confirmación` con código) para mostrar diferencias prácticas. |
| F98 | `references/06-writing/paraphrase.md` | Celdas de tabla con datos del SDM son literales (INV-09); F98 norma el parafraseo. |
| F100 | `references/06-writing/anti-patterns.md` | Anti-patrones generales (volcado de viñetas, marketing copiado); F97 cubre los específicos de comparaciones. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/comparisons.md`
aparece en §5.2 con la entrada _"Construir comparación correcta (tabla
lado a lado / jerarquía por relajación / matriz de decisión / trade-offs
/ síntesis)"_, entre F96 y F65.

---

## §13 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Toda tabla va seguida del párrafo de síntesis | `evals/comparisons-sample/run_eval.py` C6 verifica que las 4 notas base tienen tabla + `## Síntesis` ≥ 30 palabras con ≥ 2 similitudes + 1 diferencia. C11 verifica que `anti-missing-sintesis.md` falla a propósito. |
| **C2** Comparaciones no presentes en la fuente marcadas como derivadas | C7: cada nota base tiene ≥ 1 `:::derived` o `:::external` cuando la comparación la construye el agente. |
| **C3** ≥ 1 matriz de decisión de ejemplo técnico | C8: `cmp-sql-vs-nosql-hierarchy.md` contiene jerarquía por relajación con ≥ 3 niveles. C12: `cmp-mono-vs-micro.md` contiene ≥ 1 matriz `Escenario / Mejor opción / Justificación` con ≥ 3 filas. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l comparisons.md` ≤ 600.
- **D2.** Las 13 secciones canónicas §1-§13 presentes.
- **D3.** §5 jerarquía por relajación tiene ≥ 3 niveles con la regla "cada fila relaja una restricción".
- **D4.** §11 tiene ≥ 8 señales algorítmicas D1-D10 con método y PASS/FAIL.
- **D5.** Wirings cerrados (C9).
- **D6.** Las 4 notas base pasan `density_check.py --strict` (C10).
