# `references/06-writing/paraphrase.md` — Parafraseo fiel vs literal

> Documento normativo de la **Fase 98** `[núcleo]`. Define la **lista
> cerrada de literales protegidos** (8 tipos que NUNCA se reformulan), la
> **técnica de enumeración de unidades** (4 pasos para verificar que un
> parafraseo cubre todo el original), la **tabla de reformulaciones
> prohibidas** (≥ 10 pares), **6 anti-patrones** y las **3 verificaciones
> algorítmicas V1-V3** correspondientes a los 3 criterios del ROADMAP.
>
> F98 **normativiza** los invariantes **INV-09** (literales del SDM
> verbatim) e **INV-10** (enumeraciones cerradas no truncadas). No los
> redefine; los hace ejecutables.
>
> **Cuándo cargar:** antes de cualquier operación de parafraseo en L3;
> cuando el revisor detecta que un mensaje de error fue reformulado, una
> enumeración fue truncada, o una unidad del original desapareció en el
> parafraseo.
>
> **Wirings:**
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}`
>   ancla el literal al bloque del SDM; `{external}` para conocimiento
>   fuera del SDM.
> - `references/04-authoring/block-directives.md` (F45) §10.4 —
>   `:::example` con salida verbatim.
> - `references/06-writing/intuition-first.md` (F94) §5 — reglas P1-P2
>   y C1-C2 del patrón de 5 etapas; F98 norma cómo se mezclan con el
>   parafraseo.
> - `references/06-writing/analogies.md` (F95) §4 — plantilla cerrada
>   para reglas con verificación algorítmica; F98 reusa el patrón.
> - `references/06-writing/executable-examples.md` (F96) §2 — `## Resultado`
>   con output verbatim del SDM.
> - `references/06-writing/comparisons.md` (F97) §10 AP9 — anti-patrón
>   "opinión"; F98 lo extiende con "adición/elisión de unidades".
> - `references/07-visual/density.md` (F76) — R1-R8 sin exención.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F98:

1. **El agente reformula mensajes de error.** "Connection refused" se
   convierte en "conexión rechazada" — la nota "explica" cosas que la
   fuente no dice. F98 define la **lista cerrada de literales
   protegidos** (8 tipos) y prohíbe reformularlos.
2. **Las enumeraciones se truncan con `etc.`.** El SDM lista 5 cosas;
   el parafraseo lista 3 y termina en `etc.`. F98 prohíbe explícitamente
   `etc.`, `entre otros`, `los más relevantes`, `y más`, `etcétera`,
   `…` (como elipsis de enumeración).
3. **El parafraseo cubre solo una parte del original.** El agente
   "entiende" la idea general pero omite 1-2 unidades. F98 introduce la
   **técnica de enumeración de unidades** en 4 pasos: leer → listar →
   reescribir → verificar.

**Cierra los 3 criterios del ROADMAP §1676-1678:**

1. _Ningún mensaje de error ni nombre técnico aparece reformulado_ → §2 + §7 + §10 V1.
2. _Ninguna enumeración cerrada aparece truncada_ → §5 + §7 + §10 V2.
3. _Un párrafo reescrito cubre todas las unidades del original, verificado en tres casos_ → §4 + §10 V3.

**Fuera de alcance:**

- Analogías → F95.
- Ejemplos ejecutables → F96.
- Comparaciones → F97.
- Voz y estilo → F99.
- Anti-patrones generales → F100.
- Idioma bilingüe y citación → F101.
- Verificación semántica profunda (entender que "el sistema" y "la
  plataforma" son sinónimos contextuales) → F118.

---

## §2 · Lista cerrada de literales protegidos

Tabla cerrada con los **8 tipos** que NUNCA se reformulan. Cada fila
tiene: tipo, ejemplo del SDM, ejemplo mal reformulado, ejemplo correcto.

| # | Tipo | Ejemplo del SDM | Reformulación incorrecta | Conservar verbatim |
|---|---|---|---|---|
| **L1** | Mensajes de error | `Connection refused` | `conexión rechazada` / `connection failed` | `Connection refused` |
| **L2** | Nombres de parámetro | `--max-connections` | `--max-conexiones` / `--maxConnections` | `--max-connections` |
| **L3** | Sintaxis (firma, declaración) | `func (ctx context.Context, id string) error` | `función que recibe un contexto y un ID` | `func (ctx context.Context, id string) error` |
| **L4** | Defaults | `max_connections = 100` | `alrededor de 100` / `por defecto 100` | `max_connections = 100` |
| **L5** | Advertencias de seguridad | `WARNING: connecting to untrusted server` | `cuidado al conectar a servidores no confiables` | `WARNING: connecting to untrusted server` |
| **L6** | Comandos (shell) | `docker run --rm alpine:3.19 echo hello` | `docker ejecuta alpine` / `docker run` (sin el `--rm`) | `docker run --rm alpine:3.19 echo hello` |
| **L7** | Versiones de protocolo | `RFC 9293`, `HTTP/1.1`, `TLS 1.3` | `la nueva versión del protocolo TCP` / `HTTP` (sin versión) | `RFC 9293`, `HTTP/1.1`, `TLS 1.3` |
| **L8** | Códigos de retorno / error | `404 Not Found`, `errno 2` (ENOENT) | `página no encontrada` / `archivo inexistente` | `404 Not Found`, `ENOENT` |

**Reglas:**

- Los literales L1-L8 van **siempre** entre comillas invertidas
  (backticks) en NoteMark, salvo que el SDM los presente en otro formato
  (en cuyo caso se conserva el formato original).
- Si el SDM tiene **doble** formato (`Error: connection refused` Y
  `connection refused`), se conserva el que está más cerca de la
  definición.
- La marca `{src:blk_xxxx}` se coloca al final de la unidad verbatim.

---

## §3 · Lista cerrada de "se reescribe"

Categorías de prosa que **se pueden** (y suelen **deberse**) reescribir:

| # | Categoría | Por qué se reescribe | Cómo reescribir |
|---|---|---|---|
| **R1** | Prosa explicativa (definiciones, mecanismos) | Parafrasear es el valor de la nota | Mantener todas las unidades (§4); cambiar la forma |
| **R2** | Marketing (anuncios, "solución poderosa") | Es opinión, no información | Convertir en hecho o eliminar |
| **R3** | Repeticiones (el SDM repite 2 veces la misma idea) | Ruido; el lector no necesita 2 copias | Consolidar en 1 mención |
| **R4** | Introducciones transicionales ("En esta sección veremos…") | No añaden contenido | Eliminar o reemplazar por TL;DR |

**Reglas:**

- Reescribir ≠ resumir. Reescribir mantiene **todas** las unidades (§4).
- Resumir (eliminar unidades) **solo** se permite si la unidad está
  marcada `boilerplate`, `navigation` u `out-of-scope-by-user` en el
  ledger (F15).
- Reescribir ≠ parafraseo parcial. Reescribir cubre **100%** de las
  unidades; el parafraseo parcial es anti-patrón AP2/AP3 (§8).

---

## §4 · Técnica de enumeración de unidades

Algoritmo cerrado en **4 pasos** que cualquier parafraseo debe seguir:

```
PASO 1: LEER el párrafo original del SDM.
        Identificar las unidades explícitas:
          - Sustantivos clave (conceptos, productos, comandos).
          - Verbos (acciones que ejecuta el sistema).
          - Números (versiones, defaults, latencias, conteos).
          - Nombres propios (RFC, productos, flags).
          - Mensajes literales (errores, warnings, success).
          - Enumeraciones (listas cerradas del SDM).

PASO 2: LISTAR las unidades en una tabla:

        | # | Unidad | Forma en el SDM | Tipo (L1-L8 / R1-R4) |
        |---|--------|------------------|----------------------|
        | 1 | "Connection refused" | string literal | L1 |
        | 2 | 100 | número (default) | L4 |
        | 3 | --rm | flag CLI | L6 |
        | 4 | Docker 24.0 | versión | L7 |
        | 5 | 5 segundos | cuantificador | (preservar) |

PASO 3: REESCRIBIR el párrafo cubriendo TODAS las unidades:
        - Forma narrativa libre.
        - Cada unidad del paso 2 está presente en el parafraseo.
        - Los literales L1-L8 van verbatim.
        - Las categorías R1-R4 se reescriben libremente.
        - Las unidades de tipo "preservar" (cuantificadores, versiones
          que NO están en L7) se mantienen como números explícitos
          ("5 segundos" no se convierte en "inmediatamente").

PASO 4: VERIFICAR una a una:
        - Para cada unidad del paso 2, ¿está en el parafraseo?
        - Si falta una → reescribir (volver a paso 3).
        - Si una unidad fue reformulada → restaurar el literal.
        - Si la enumeración cerrada terminó en `etc.` → expandir.
```

**Tabla de verificación al cierre:**

```
| # | Unidad del original | ¿En el parafraseo? | Forma en el parafraseo |
|---|----------------------|--------------------|------------------------|
| 1 | "Connection refused" | sí | "Connection refused" (verbatim) |
| 2 | 100 | sí | "el default de 100 conexiones" |
| 3 | --rm | sí | "`--rm`" |
| ... |
```

Si alguna fila tiene `no` en la columna "¿En el parafraseo?", el
parafraseo **no** pasa el criterio #3 (V3).

---

## §5 · Enumeraciones cerradas

### §5.1 · Definición cerrada

Una **enumeración cerrada** es una lista finita explícita en el SDM:

- "PostgreSQL soporta 4 tipos de replicación: síncrona, asíncrona,
  lógica, física." (4 ítems, todos explícitos)
- "Los flags válidos son `--rm`, `-d`, `-it`, `--name`." (4 ítems)

NO es enumeración cerrada:
- "Hay varios tipos de bases de datos…" (cantidad indeterminada).
- "Como cualquier sistema distribuido, PostgreSQL presenta desafíos…"
  (categoría general, no lista).

### §5.2 · Palabras prohibidas (INV-10)

En **enumeraciones cerradas**, las siguientes palabras están **prohibidas**
al final de la lista (sirven para indicar continuación, lo cual es
contrario al carácter cerrado):

- `etc.` / `etcétera`
- `entre otros`
- `los más relevantes`
- `y más`
- `…` (elipsis Unicode) cuando cierra una enumeración
- `and so on`, `among others` (inglés)

**Detección algorítmica:**

```python
import re
PROHIBITED = re.compile(
    r"\betc\.?\b|\bentre otros\b|\blos m[áa]s relevantes\b|\by m[áa]s\b|\betc[eé]tera\b|…$",
    re.IGNORECASE,
)
```

Si el patrón matchea al final de una línea de enumeración o al final
del párrafo, V2 falla.

### §5.3 · Técnica de conteo

Para verificar que la enumeración está completa:

1. Contar bullets (`- `, `* `, `1.`, `2.`).
2. Contar ítems separados por `;` o `,` en prosa.
3. Comparar con el conteo del SDM (si el SDM dice "4 tipos", debe haber
   4 ítems).

**Anti-patrón:** el SDM dice "4 tipos" pero el parafraseo lista 3 y
agrega `etc.` → V2 falla.

---

## §6 · Verificación algorítmica (V1, V2, V3)

Los **3 criterios del ROADMAP** convertidos en checks algorítmicos:

### §6.1 · V1 — Mensajes de error y nombres técnicos verbatim

**Método:**

1. Extraer todos los literales L1-L8 del SDM (regex específicos por
   tipo).
2. Buscar cada literal en el parafraseo.
3. Si un literal aparece **reformulado** (sinónimo, traducción,
   simplificación), V1 falla.

**Reformulaciones comunes a detectar:**

```python
REFORMULATIONS = {
    # mensaje de error → sinónimo
    r"\brefused\b": "Connection refused",
    r"\bnot found\b": "Not Found",
    r"\bunauthorized\b": "Unauthorized",
    # parámetro → traducción
    r"--max-connections\b": "--max-connections",
    r"--max-conexiones\b": "--max-connections",
    # versión → genérica
    r"\bHTTP\b(?!\s*/\s*\d)": "HTTP (sin versión)",
    # código → descripción
    r"\b404\b.*p[áa]gina": "404",
    r"\b404\b.*not found": "404 Not Found",
}
```

**PASS:** todos los literales del SDM aparecen verbatim en el parafraseo.
**FAIL:** ≥ 1 literal reformulado.

### §6.2 · V2 — Enumeraciones cerradas no truncadas

**Método:**

1. Detectar enumeraciones en el SDM (regex contra "tipos de…", "flags
   válidos son…", "soporta N cosas…").
2. Contar ítems en el SDM.
3. Buscar palabras prohibidas al final del párrafo del parafraseo.
4. Contar ítems en el parafraseo; debe coincidir con el SDM.

**PASS:** ninguna palabra prohibida + conteo coincide.
**FAIL:** ≥ 1 palabra prohibida o conteo no coincide.

### §6.3 · V3 — Cobertura de unidades (3 casos verificados)

**Método (técnica de enumeración §4):**

1. Listar las unidades del SDM original (≥ 5 unidades para que sea un
   test significativo).
2. Verificar una a una en el parafraseo.
3. **3 casos verificados:** cada caso tiene una tabla de unidades del
   original vs parafraseo, con conteo de cobertura.

**PASS:** ≥ 80% de las unidades del SDM presentes en el parafraseo.
**FAIL:** < 80% de cobertura o ≥ 1 unidad crítica ausente.

---

## §7 · Tabla de reformulaciones prohibidas

Tabla cerrada con **≥ 12 pares** `(reformulación incorrecta, original
correcto, regla violada)`. Cada par es objetivo: una palabra cambia por
otra, y la regla violada es explícita.

| # | Original correcto | Reformulación incorrecta | Regla violada |
|---|---|---|---|
| **P1** | `Connection refused` | `conexión rechazada` | L1 — mensaje de error verbatim |
| **P2** | `errores` (en código) | `issues` (en código) | L8 — código de retorno verbatim |
| **P3** | `funciones` | `methods` | L2/L3 — término del dominio no se traduce |
| **P4** | `--max-connections` | `--maxConnections` | L2 — flag CLI case-sensitive |
| **P5** | `100 ms` | `muy rápido` | cuantificador a adverbio |
| **P6** | `5 réplicas` | `varias réplicas` | R3 — enumeración cerrada |
| **P7** | `404 Not Found` | `página no encontrada` | L8 — código HTTP verbatim |
| **P8** | `localhost` | `127.0.0.1` | L7 — alias no es literal |
| **P9** | `ConnectionPool` | `pool` | abreviación no documentada |
| **P10** | `customer` | `user` | cambio de término del dominio |
| **P11** | `WARNING: ...` | `cuidado: ...` | L5 — advertencia verbatim |
| **P12** | `available on macOS` | `available` | eliminación de plataforma |
| **P13** | `3 réplicas` | `3+ réplicas` | adición de cuantificador |

**Detección algorítmica:** el revisor compara cada par (palabra A
esperada vs palabra B encontrada en el parafraseo). Si B aparece
sustituyendo a A → V1 falla con código `reformulation:P<N>`.

---

## §8 · Anti-patrones (≥ 6)

| # | Anti-patrón | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | Reformulación cosmética | "Connection refused" → "conexión rechazada" | Conservar `Connection refused` verbatim | V1 (regex contra `rechazada\|failed\|error`) |
| **AP2** | Elisión de unidades | SDM dice 5, parafraseo dice 4 | Mantener 5 | V3 (tabla de unidades) |
| **AP3** | Adición de unidades | SDM dice 5, parafraseo dice 6 (1 inventada) | Mantener 5 exactas | V3 (tabla de unidades) |
| **AP4** | Truncado por `etc.` | "...flags: --rm, -d, -it, etc." | "...flags: --rm, -d, -it, --name" (los 4) | V2 (regex `\betc\.?\b`) |
| **AP5** | Reformulación de mensaje de error | `Error: connection refused` → `Error: no se pudo conectar` | `Error: connection refused` | V1 (regex contra `no se pudo\|falló\|rechazada`) |
| **AP6** | Traducción de parámetro | `--max-connections` → `--max-conexiones` | `--max-connections` | V1 (regex contra `\-\-max[\-_]conexiones`) |
| **AP7** | Cuantificador a adverbio | `100 ms` → `inmediatamente` | `100 ms` | V3 (la unidad numérica está ausente) |

---

## §9 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` | El parafraseo aplica a todos los perfiles; `writing.style = "tutorial"` permite más literalidad. |
| F45 | `references/04-authoring/block-directives.md` §10.4 | `:::example` con salida verbatim del SDM. |
| F46 | `references/04-authoring/inline-marks.md` | `{src:blk_xxxx}` ancla el literal al SDM. |
| F76 | `references/07-visual/density.md` | R1-R8 aplican al parafraseo. |
| F78 | `references/05-note-types/concept.md` §4.2 | Marcas inline; F98 las usa para anclar literales. |
| F94 | `references/06-writing/intuition-first.md` §5 | Reglas P1-P2 y C1-C2 del patrón de 5 etapas; F98 norma cómo mezclar literal y parafraseo. |
| F95 | `references/06-writing/analogies.md` §4 | Plantilla cerrada para reglas con verificación algorítmica; F98 reusa. |
| F96 | `references/06-writing/executable-examples.md` §2 | `## Resultado` con output verbatim. |
| F97 | `references/06-writing/comparisons.md` §10 AP9 | Anti-patrón "opinión"; F98 lo extiende con "adición/elisión de unidades". |
| F100 | `references/06-writing/anti-patterns.md` | Anti-patrones generales; F98 cubre los específicos de parafraseo. |
| F101 | `references/06-writing/i18n-and-citation.md` | Términos canónicos bilingües; F98 los trata como L2/L3 verbatim. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/paraphrase.md`
aparece en §5.2 con la entrada _"Reescribir prosa preservando literales
y enumeraciones cerradas"_, entre F97 y F65.

---

## §10 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Mensajes de error y nombres técnicos verbatim | `evals/paraphrase-sample/run_eval.py` C6 verifica que el fixture `paraphrase-bad-1-reformulated.md` (con un mensaje reformulado) es detectado por V1. Adicionalmente, `paraphrase-good-1.md` retiene los literales verbatim. |
| **C2** Enumeraciones cerradas no truncadas | C7: el fixture `paraphrase-bad-2-truncated.md` (con `etc.` al final) es detectado por V2. |
| **C3** Cobertura de unidades en 3 casos | C5 + C8: `paraphrase-good-1.md` cubre las 5 unidades de `source-1.txt` (V3 — el caso crítico). Las otras 2 fuentes (`source-2.txt`, `source-3.txt`) se usan en C8 para cross-check. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l paraphrase.md` ≤ 600.
- **D2.** 10 secciones canónicas §1-§10 presentes.
- **D3.** §4 técnica de enumeración tiene 4 pasos numerados con plantilla cerrada.
- **D4.** §6 V1-V3 tienen método algorítmico (regex/conteo) y PASS/FAIL.
- **D5.** §7 tabla tiene ≥ 10 filas de reformulaciones prohibidas.
- **D6.** Wirings cerrados (C10).
