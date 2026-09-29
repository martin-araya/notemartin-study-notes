# `references/06-writing/voice-style.md` — Voz y estilo

> Documento normativo de la **Fase 99**. Define las **8 reglas
> verificables** de voz y estilo (R1-R8), la **lista cerrada de ≥ 15
> adjetivos valorativos prohibidos**, la **tabla de persona gramatical
> por sección**, la **regla de tiempos verbales consistentes**, **8
> anti-patrones** y la **plantilla de verificación** con 8 preguntas
> binarias que un revisor externo aplica sin reabrir el SDM.
>
> F99 **NO** redefine el contenido (eso es F98 — literales verbatim,
> enumeraciones cerradas). Cubre la **forma** sobre el mismo párrafo.
> F94 §6 D10 ya tenía una señal parcial de adjetivos valorativos; F99
> la eleva a norma del banco con lista cerrada explícita.
>
> **Cuándo cargar:** antes de cerrar cualquier nota en L3; cuando el
> revisor detecta inconsistencias de estilo entre notas de fuentes
> distintas; cuando la prosa tiene relleno, voz pasiva, o tiempos
> mezclados.
>
> **Wirings:**
> - `references/06-writing/intuition-first.md` (F94) §6 D10 — señal
>   parcial de adjetivos valorativos; F99 la completa.
> - `references/06-writing/paraphrase.md` (F98) — norma el **contenido**;
>     F99 norma la **forma**.
> - `references/06-writing/analogies.md` (F95) §4 — patrón de lista
>     cerrada + verificación algorítmica.
> - `references/05-note-types/procedure.md` (F80) — segunda persona en
>     procedimientos.
> - `references/07-visual/density.md` (F76) — R1-R8 sin exención.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3.
> - `references/10-quality/fidelity-rules.md` (F42) — citas a bloques SDM.
> - F100 anti-patrones generales (cubrirá los de fondo, no los de voz).

---

## §1 · Propósito y alcance

Tres problemas resueltos por F99:

1. **Las notas suenan distintas según la fuente.** Una nota sobre
   PostgreSQL suena "técnica y seca"; otra sobre Kubernetes suena
   "marketera y entusiasta". F99 unifica el estilo: las 8 reglas
   aplican por igual a todas las notas, independientemente de la fuente.
2. **Las reglas de estilo son consejos, no métricas.** "Escribe frases
   cortas" es consejo. "≤ 25 palabras por frase, ≤ 30% por encima del
   umbral" es métrica. F99 convierte cada regla en una pregunta binaria
   con método algorítmico.
3. **El agente llena la prosa con adjetivos valorativos.** "PostgreSQL
   es una herramienta poderosa y elegante" — no dice nada. F99 prohibe
   explícitamente ≥ 15 adjetivos y mide la densidad.

**Cierra los 3 criterios del ROADMAP §1684-1686:**

1. _Las reglas son verificables, no consejos_ → §2 (tabla R1-R8) + §9 (8 preguntas binarias).
2. _Hay ejemplos de antes/después por regla_ → §2 (cada regla con par antes/después) + §8 (8 anti-patrones).
3. _El estilo es idéntico entre notas de fuentes distintas_ → §2 (R1-R8 universales) + §6 (persona por sección).

**Fuera de alcance:**

- Contenido (literales verbatim, enumeraciones) → F98.
- Anti-patrones generales (volcado de viñetas, marketing copiado) → F100.
- Idioma bilingüe y citación → F101.
- Estilo visual (tokens, colores, tipografía) → F72-F74.
- Detección de plagio → fuera del alcance.

---

## §2 · Las 8 reglas verificables (R1-R8)

Tabla cerrada. Cada regla tiene **definición operacional**, **señal
algorítmica** y **ejemplo antes/después**.

| # | Regla | Definición operacional | Señal algorítmica | Antes | Después |
|---|---|---|---|---|---|
| **R1** | Frases cortas | ≤ 25 palabras por frase; ≤ 30% de frases por encima del umbral | `re.split(r"[.!?]+\s+", text)` + conteo | "Es importante destacar que PostgreSQL es un ORDBMS que soporta tipos avanzados y extensibilidad." (18 palabras) | "PostgreSQL es un ORDBMS. Soporta tipos avanzados." (2 frases, 6 + 4 palabras) |
| **R2** | Voz activa | ≥ 80% de frases en voz activa | regex `r"\b(es\|fue\|será\|era\|sería|ha sido|han sido|había sido)\s+\w+(ado\|ido|ada|idos|adas)\b"` contra regex de activa | "La tabla es creada por el usuario." | "El usuario crea la tabla." |
| **R3** | Sin adjetivos valorativos | ≤ 2 adjetivos valorativos por cada 200 palabras de prosa | regex contra lista cerrada §3 | "PostgreSQL es una herramienta poderosa." | "PostgreSQL soporta índices B-tree, hash, GIN y BRIN." |
| **R4** | Sin relleno | ≤ 1 frase de relleno por cada 10 párrafos | regex `r"\b(es importante destacar\|vale la pena mencionar\|cabe se[ñn]alar\|es necesario subrayar\|es menester destacar)\b"` | "Es importante destacar que PostgreSQL usa MVCC." | "PostgreSQL usa MVCC." |
| **R5** | Segunda persona en procedimientos | ≥ 80% verbos en 2ª persona en secciones `## Procedimiento` / `## Práctica` / `## Confirmación` ejecutable | regex de imperativo + `tú` / `usted` | "El usuario debe abrir el archivo." (en `## Procedimiento`) | "Abre el archivo con `docker run --rm`." |
| **R6** | Tiempos verbales consistentes | 1 tiempo base por sección; el cambio solo se permite para hechos históricos explícitos | regex de conjugación por tiempo (presente / pasado / futuro) | "PostgreSQL crea la tabla. El usuario la modificó. La aplicación consultará los datos." (3 tiempos mezclados) | "PostgreSQL crea la tabla. El usuario la modifica. La aplicación consulta los datos." (todo presente) |
| **R7** | Sin nominalizaciones | ≤ 2 nominalizaciones por cada 200 palabras | regex `r"\w+(ación\|amiento\|imiento)\b"` en verbos | "La realización de la operación tarda 5 ms." | "Ejecutar la operación tarda 5 ms." |
| **R8** | Sin subjuntivo dudoso | ≤ 1 subjuntivo dudoso por cada 200 palabras | regex `r"\bojal[aá]\b\|\bquiz[aá]s\b\|\btal vez\b\|\bquiz[aá]\b"` | "Quizás el sistema responda de forma diferente." | "El sistema responde en < 5 ms para claves primarias." |

**Nota sobre métricas:** las cuentas (≤ 25 palabras, ≤ 2 adjetivos por 200 palabras, etc.) son **objetivos medibles**. El revisor aplica el método y reporta PASS/FAIL sin ambigüedad.

---

## §3 · Lista cerrada de adjetivos valorativos prohibidos

**20 adjetivos** prohibidos. La métrica es **≤ 2 ocurrencias por cada
200 palabras de prosa**. Cualquier ocurrencia por encima del umbral
cuenta como violación de R3.

| # | Adjetivo | Categoría |
|---|---|---|
| **V1** | `sencillo` | accesibilidad |
| **V2** | `poderoso` / `potente` | capacidad |
| **V3** | `elegante` | estética |
| **V4** | `simple` | accesibilidad |
| **V5** | `robusto` | fiabilidad |
| **V6** | `increíble` | hype |
| **V7** | `mágico` / `mágica` | hype |
| **V8** | `revolucionario` | hype |
| **V9** | `brutal` | hype |
| **V10** | `bestial` | hype |
| **V11** | `killer` (anglicismo) | hype |
| **V12** | `awesome` / `fantastic` / `amazing` (anglicismos) | hype |
| **V13** | `game-changer` | hype |
| **V14** | `indispensable` | necesidad |
| **V15** | `vital` | necesidad |
| **V16** | `premium` | marketing |
| **V17** | `top` | marketing |
| **V18** | `leading` | marketing |
| **V19** | `imprescindible` | necesidad |
| **V20** | `revolucionario` (duplicado de V8; alias) | hype |

**Detección algorítmica:**

```python
import re
PROHIBITED_ADJECTIVES = re.compile(
    r"\b(sencill[oa]|poderos[oa]|potent[e]|elegante|simple|robust[oa]|"
    r"incre[ií]ble|m[aá]gic[oa]|revolucionari[oa]|brutal|bestial|"
    r"killer|awesome|fantastic|amazing|game[- ]?changer|"
    r"indispensable|vital|premium|leading|imprescindible)\b",
    re.IGNORECASE,
)
```

**Reglas de oro:** si el adjetivo se puede sustituir por un dato
concreto (índice `B-tree`, latencia `5 ms`, throughput `100k/s`), se
sustituye. Si no se puede, se elimina.

---

## §4 · Longitud de frase (R1)

### §4.1 · Definición cerrada

- **Umbral:** ≤ 25 palabras por frase.
- **Tolerancia:** ≤ 30% de las frases pueden estar por encima del
  umbral (para acomodar frases técnicas largas inevitables, ej.
  definiciones formales con múltiples variables).
- **Excepción:** las fórmulas matemáticas, las URLs y los mensajes
  verbatim del SDM **no** se cuentan como frases del autor.

### §4.2 · Técnica de conteo

```python
import re

def sentence_lengths(text: str) -> list[int]:
    # Divide por `.` `!` `?` seguidos de espacio o fin de párrafo.
    sentences = re.split(r"[.!?]+\s+", text)
    # Filtra vacíos y mide palabras por frase.
    return [len(s.split()) for s in sentences if s.strip()]

def passes_r1(text: str, threshold: int = 25, max_over: float = 0.30) -> bool:
    lengths = sentence_lengths(text)
    if not lengths:
        return True
    over = sum(1 for n in lengths if n > threshold)
    return (over / len(lengths)) <= max_over
```

### §4.3 · Aplicación por capa

- **L1** (`## TL;DR`): ≤ 60 palabras en total (R1 + F76 R1).
- **L2** (resto de secciones): párrafo ≤ 200 palabras (F76 R2); cada
  frase ≤ 25 palabras (R1).

---

## §5 · Voz activa vs pasiva (R2)

### §5.1 · Definición cerrada

- **≥ 80%** de las frases deben estar en voz activa.
- Voz activa: el sujeto realiza la acción (`El servidor crea la tabla`).
- Voz pasiva: el sujeto recibe la acción (`La tabla es creada por el
  servidor`).

### §5.2 · Detección algorítmica

```python
import re

PASSIVE_RE = re.compile(
    r"\b(es|fue|será|era|sería|ha sido|han sido|había sido|"
    r"estaba siendo|fue siendo)\s+\w+(ado|ido|ada|idos|adas)\b",
    re.IGNORECASE,
)

def voice_score(text: str) -> tuple[int, int]:
    """Devuelve (frases_activas, total_frases)."""
    sentences = re.split(r"[.!?]+\s+", text)
    sentences = [s for s in sentences if s.strip()]
    if not sentences:
        return 0, 0
    active = sum(1 for s in sentences if not PASSIVE_RE.search(s))
    return active, len(sentences)

def passes_r2(text: str, min_active_ratio: float = 0.80) -> bool:
    active, total = voice_score(text)
    return (active / total) >= min_active_ratio if total else True
```

### §5.3 · Excepciones

- `## Mecanismo` puede usar voz pasiva para describir lo que el
  sistema "hace automáticamente" (ej. "La conexión es cifrada por
  TLS 1.3"). Esto es admisible **solo** si la prosa activa no lo
  cubre.
- Las definiciones formales en `## Definición formal` usan voz
  impersonal (`Sea X un entero positivo`).

---

## §6 · Persona gramatical

Tabla cerrada de **persona por sección** de la nota. La convención se
mantiene dentro de cada sección; el cambio entre secciones es legítimo.

| Sección | Persona | Ejemplo |
|---|---|---|
| `## TL;DR` | Neutra o impersonal | "PostgreSQL usa MVCC." |
| `## Problema` | Tercera persona o impersonal | "El sistema falla bajo carga concurrente." |
| `## Intuición` | Tercera persona o impersonal | "MVCC da a cada transacción un snapshot." |
| `## Analogía` | Tercera persona o impersonal | "Una biblioteca lleva una tarjeta por libro." |
| `## Definición formal` | Impersonal o matemática | "Sea T una transacción con snapshot en S(T)." |
| `## Mecanismo` | Tercera persona o impersonal | "PostgreSQL implementa MVCC con `HeapTuple`." |
| `## Procedimiento` | **Segunda persona** | "Abre el archivo con `docker run --rm`." |
| `## Práctica` | **Segunda persona** | "Responde la pregunta sin mirar la fuente." |
| `## Confirmación` | **Segunda persona** (si ejecutable) o impersonal | "Ejecuta el comando y verifica el output." |
| `## Resumen` | Neutra o impersonal | "Las 3 ideas clave son X, Y, Z." |
| `## Trampas` | Segunda persona (consejo operativo) | "No confundir `xmin` con `xmax`." |
| `## Cuándo NO usarlo` | Segunda persona o impersonal | "No uses MVCC si…" |
| `## Veredicto` | Neutra o impersonal | "PostgreSQL conviene si…; MySQL conviene si…." |

**Detección algorítmica (R5):**

```python
import re

SECOND_PERSON_RE = re.compile(
    r"\b(tú|usted|vos|ti|su|your|you|abre|ejecuta|haz|considera|"
    r"usa|comprueba|verifica|compara|añade|elimina|cambia|"
    r"pulsa|selecciona|introduce|introduzca)\b",
    re.IGNORECASE,
)

def persona_ratio_in_section(text: str) -> float:
    sentences = [s for s in re.split(r"[.!?]+\s+", text) if s.strip()]
    if not sentences:
        return 0.0
    matches = sum(1 for s in sentences if SECOND_PERSON_RE.search(s))
    return matches / len(sentences)
```

**Métrica:** en `## Procedimiento` / `## Práctica` / `## Confirmación`
ejecutable, **≥ 80%** de las frases deben usar segunda persona. En
otras secciones, **≤ 20%** (porque prima tercera persona o impersonal).

---

## §7 · Tiempos verbales consistentes (R6)

### §7.1 · Definición cerrada

Una nota (o una sección) **elige un tiempo base** y **lo mantiene**:

- **Presente** (más común para notas técnicas): "PostgreSQL crea la
  tabla. El servidor responde. La aplicación consulta los datos."
- **Pasado** (para reproducir un hecho histórico): "En 2001, MySQL
  cambió de licencia. PostgreSQL adoptó MVCC en la versión 6.5."
- **Futuro** (para planes o deprecation): "PostgreSQL 17 cambiará la
  sintaxis de `MERGE`."

### §7.2 · Cambio de tiempo permitido

Solo se permite cambiar de tiempo cuando la sección describe explícitamente
un hecho histórico o un plan. Si la sección `## Mecanismo` está toda en
presente y la sección `## Historia` está toda en pasado, esto es admisible.
Lo que **NO** es admisible: mezclar tiempos dentro de la misma sección sin
justificación.

### §7.3 · Detección algorítmica

```python
import re
from collections import Counter

# Regex simplificada para verbos conjugados en presente, pasado y futuro.
PRESENT_RE = re.compile(r"\b\w+(a|an|amos|áis|an|o|as|amos|éis|os|e|es|imos|ís|en)\b", re.IGNORECASE)
PAST_RE = re.compile(r"\b\w+(ó|aron|ieron|aba|aban|í|imos|iste|ió|imos|isteis|ieron)\b", re.IGNORECASE)
FUTURE_RE = re.compile(r"\b\w+(rá|rán|ré|remos|rás|réis|ará|aremos|aráis|erán)\b", re.IGNORECASE)

def dominant_tense(text: str) -> str:
    counts = Counter()
    counts["presente"] = len(PRESENT_RE.findall(text))
    counts["pasado"] = len(PAST_RE.findall(text))
    counts["futuro"] = len(FUTURE_RE.findall(text))
    return counts.most_common(1)[0][0] if counts else "presente"

def passes_r6(text: str, max_alt_ratio: float = 0.20) -> bool:
    """PASS si un tiempo cubre ≥ 80% de las conjugaciones."""
    counts = Counter()
    counts["presente"] = len(PRESENT_RE.findall(text))
    counts["pasado"] = len(PAST_RE.findall(text))
    counts["futuro"] = len(FUTURE_RE.findall(text))
    total = sum(counts.values())
    if total == 0:
        return True
    dominant_pct = counts.most_common(1)[0][1] / total
    return dominant_pct >= (1 - max_alt_ratio)
```

---

## §8 · Anti-patrones de voz (≥ 6)

| # | Anti-patrón | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | Frase larga | "Es importante destacar que PostgreSQL es un ORDBMS que soporta tipos avanzados y extensibilidad vía extensiones y plugins en un solo binario, lo cual lo diferencia de los RDBMS tradicionales." (33 palabras) | "PostgreSQL es un ORDBMS. Soporta tipos avanzados y extensiones en un solo binario." | D1 (R1) |
| **AP2** | Voz pasiva | "La tabla es creada por el usuario cuando se ejecuta el comando." | "El usuario crea la tabla al ejecutar el comando." | D2 (R2) |
| **AP3** | Relleno | "Es importante destacar que PostgreSQL usa MVCC para evitar locks de lectura." | "PostgreSQL usa MVCC para evitar locks de lectura." | D3 (R4) |
| **AP4** | Adjetivo valorativo | "PostgreSQL es una herramienta poderosa y elegante para datos complejos." | "PostgreSQL soporta tipos JSONB, rangos, geometría y vectores." | D4 (R3) |
| **AP5** | Persona incorrecta en procedimiento | "El usuario debe abrir el archivo con `docker run --rm`." (en `## Procedimiento`) | "Abre el archivo con `docker run --rm`." | D5 (R5) |
| **AP6** | Tiempos mezclados | "PostgreSQL crea la tabla. El usuario la modificó. La aplicación consultará los datos." (presente + pasado + futuro) | "PostgreSQL crea la tabla. El usuario la modifica. La aplicación consulta los datos." | D6 (R6) |
| **AP7** | Nominalización | "La realización de la operación tarda 5 ms." | "Ejecutar la operación tarda 5 ms." | D7 (R7) |
| **AP8** | Subjuntivo dudoso | "Quizás el sistema responda de forma diferente en producción." | "El sistema responde en < 5 ms para claves primarias en producción." | D8 (R8) |

---

## §9 · Plantilla cerrada de verificación

**8 preguntas binarias** que un revisor externo aplica. Cada pregunta
mapea a una regla R1-R8 con su método algorítmico.

```
[ ] P1. ¿La nota tiene ≥ 80% de frases en voz activa? (R2)
       Verificar: regex de pasiva sobre el texto; contar pasivas; ratio.
       PASS si ratio activas ≥ 0.80.

[ ] P2. ¿La nota tiene ≤ 2 adjetivos valorativos por cada 200 palabras? (R3)
       Verificar: regex contra lista cerrada §3 sobre la prosa.
       PASS si count / palabras ≤ 0.01 (≤ 2 / 200).

[ ] P3. ¿La nota tiene ≤ 1 frase de relleno por cada 10 párrafos? (R4)
       Verificar: regex contra "es importante destacar", "vale la pena mencionar", etc.
       PASS si count_fill / count_paragraphs ≤ 0.10.

[ ] P4. ¿Las secciones ## Procedimiento / ## Práctica usan segunda persona? (R5)
       Verificar: regex de imperativo / 2ª persona en esas secciones.
       PASS si ratio ≥ 0.80.

[ ] P5. ¿La nota tiene 1 tiempo verbal base por sección? (R6)
       Verificar: contar verbos por tiempo en cada sección.
       PASS si el tiempo dominante cubre ≥ 80% en cada sección.

[ ] P6. ¿La nota tiene ≤ 30% de frases > 25 palabras? (R1)
       Verificar: dividir por `[.!?]+\s+`, contar palabras por frase.
       PASS si count_over_25 / count_total ≤ 0.30.

[ ] P7. ¿La nota tiene ≤ 2 nominalizaciones por cada 200 palabras? (R7)
       Verificar: regex contra terminación `-ación` / `-amiento` / `-imiento`.
       PASS si count / palabras ≤ 0.01.

[ ] P8. ¿La nota tiene ≤ 1 subjuntivo dudoso por cada 200 palabras? (R8)
       Verificar: regex contra "ojalá", "quizás", "tal vez".
       PASS si count / palabras ≤ 0.005.
```

**Una nota pasa F99 si las 8 preguntas devuelven PASS.**

---

## §10 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` | El estilo aplica a todos los perfiles; el `writing.style` del enum interactúa con F99. |
| F42 | `references/10-quality/fidelity-rules.md` | Citas a bloques SDM; las marcas `{src:blk_xxxx}` no cuentan como adjetivos valorativos. |
| F46 | `references/04-authoring/inline-marks.md` | `{src:}` inline; no afecta R2 (no es voz pasiva). |
| F51 | `references/04-authoring/depth-layers.md` | Las reglas R1-R8 aplican por igual a L1/L2/L3; las capas no eximen. |
| F76 | `references/07-visual/density.md` | R1-R8 sin exención; F99 refuerza la prosa, F76 refuerza la estructura. |
| F78 | `references/05-note-types/concept.md` §3 | Las 10 secciones obligatorias de `concept` se redactan con F99. |
| F80 | `references/05-note-types/procedure.md` | Segunda persona obligatoria en `## Procedimiento` (R5). |
| F94 | `references/06-writing/intuition-first.md` §6 D10 | F99 amplía D10 (adjetivos valorativos) a una lista cerrada de 20. |
| F95 | `references/06-writing/analogies.md` §4 | Plantilla cerrada + verificación algorítmica; F99 reusa el patrón. |
| F96 | `references/06-writing/executable-examples.md` | Las secciones `## Setup` / `## Acción` aplican R5 (segunda persona en ejecutables). |
| F97 | `references/06-writing/comparisons.md` | Las secciones `## Comparativa` aplican R2 (voz activa). |
| F98 | `references/06-writing/paraphrase.md` | F98 norma el **contenido**; F99 norma la **forma** sobre el mismo párrafo. |
| F100 | `references/06-writing/anti-patterns.md` | F100 cubre patrones de fondo (marketing copiado, volcado de viñetas); F99 cubre patrones de voz. |
| F101 | `references/06-writing/i18n-and-citation.md` | Primera aparición bilingüe del término; no es adjetivo valorativo. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/voice-style.md`
aparece en §5.2 con la entrada _"Aplicar voz y estilo consistentes
(frases cortas, voz activa, segunda persona en procedimientos, sin
adjetivos valorativos)"_, entre F98 y F65.

---

## §11 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Reglas verificables, no consejos | `evals/voice-style-sample/run_eval.py` C2 verifica que §2 tiene 8 reglas con regex/señal algorítmica. C9 verifica que §9 tiene 8 preguntas binarias con método algorítmico. C4-C8 aplican las reglas a las notas fixture. |
| **C2** Ejemplos de antes/después por regla | C2: cada fila R1-R8 en §2 incluye ejemplo antes + después. Las notas fixture positivas (style-good-1.md, style-good-2.md) están "en el lado correcto"; las negativas (style-bad-*) "en el lado malo". |
| **C3** Estilo idéntico entre notas de fuentes distintas | C4: `style-good-1.md` (concept PostgreSQL) y `style-good-2.md` (procedure Kubernetes) pasan **las mismas** 8 reglas. El eval las aplica a ambas y compara el perfil de cumplimiento. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l voice-style.md` ≤ 500.
- **D2.** 11 secciones canónicas §1-§11 presentes.
- **D3.** §3 tiene ≥ 15 adjetivos valorativos prohibidos.
- **D4.** §6 tabla de persona por sección tiene ≥ 4 secciones mapeadas.
- **D5.** §7 regla de tiempos tiene regex concreto.
- **D6.** Wirings cerrados (C10).
