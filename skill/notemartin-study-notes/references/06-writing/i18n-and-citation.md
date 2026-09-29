# `references/06-writing/i18n-and-citation.md` — Idioma bilingüe y citación

> Documento normativo de la **Fase 101** `[núcleo]`. Define las reglas
> de idioma del perfil, la **lista cerrada de 45 no-traducibles**, el
> formato de **primera aparición bilingüe** con `[[en:term]]` y
> `[[es:term]]`, la **plantilla del bloque de procedencia** al pie de
> cada nota, las **8 señales algorítmicas** S1-S8 que un revisor externo
> aplica y los **6 anti-patrones** específicos de i18n.
>
> F101 **formaliza** la promesa de fidelidad i18n de la skill. La prosa
> va en el idioma del perfil; los identificadores, parámetros, errores,
> comandos y código **nunca** se traducen (INV-09 ampliado a nivel de
> idioma); los términos técnicos se introducen bilingües en su primera
> aparición; cada nota lleva un bloque de procedencia al pie con 4 campos.
>
> **Cuándo cargar:** antes de redactar cualquier nota bilingüe; cuando
> el revisor detecta parámetros traducidos, primera aparición sin marca,
> o ausencia de bloque de procedencia.
>
> **Wirings:**
> - `references/04-authoring/properties.md` (F47) §5.13 — enum `language`
>   ∈ {`es`, `en`, `es-en`, `en-es`}.
> - `references/02-source-model/provenance.md` (F26/F27) — BCP-47, source-bearing.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}`,
>   `[[term:nombre]]`, `{external}`.
> - `references/06-writing/paraphrase.md` (F98) §2 — 8 tipos de literales
>   protegidos L1-L8 (mensajes, parámetros, sintaxis, etc.).
> - `references/06-writing/anti-patterns.md` (F100) §2 — 12 AP transversales.
> - `SKILL.md` §2 INV-09 — literales verbatim.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F101:

1. **El agente traduce nombres técnicos.** "Connection refused" se convierte
   en "conexión rechazada" (F98 §2 AP5). `--max-connections` se convierte
   en `--max-conexiones`. F101 cierra la invariante: nombres técnicos
   **nunca** se traducen, en cualquier idioma.
2. **Las notas bilingües introducen el término solo en un idioma.**
   "MVCC" aparece como "Control de concurrencia multiversión" en español
   sin la marca `[[en:mvcc]]`; el lector inglés no encuentra la
   correspondencia. F101 introduce la marca bilingüe de primera aparición.
3. **Las notas olvidan la procedencia.** El frontmatter tiene `source`,
   `source-type`, `retrieved`, pero el lector humano no abre el YAML.
   F101 introduce un **bloque de procedencia al pie** con 4 campos
   visibles.

**Cierra los 4 criterios del ROADMAP §1700-1703:**

1. _Ningún nombre técnico aparece traducido_ → §3 (lista cerrada de 45 no-traducibles) + §6 S1.
2. _Términos introducidos bilingües en primera aparición_ → §4 (formato `[[en:term]]` / `[[es:term]]`) + §6 S2.
3. _Lista de no-traducibles ≥ 40 entradas_ → §3 (45 entradas en 8 categorías).
4. _Bloque de procedencia con fuente, versión y fecha_ → §5 (plantilla cerrada con 4 campos) + §6 S4.

**Fuera de alcance:**

- Definición del enum `language` → F47 `properties.md` §5.13.
- INV-09 (literales verbatim) → F98 (F101 lo amplía a nivel de idioma).
- OCR multi-idioma → F20.
- Detección automática de todos los AP → F112.
- Reporte de calidad → F115.

---

## §2 · Idioma del perfil y de la prosa

Tabla cerrada con los **4 valores** del enum `language` y la regla de
prosa para cada uno.

| `language` | Prosa | Marcas bilingües | Glosario al pie |
|---|---|---|---|
| `es` | Solo español | No | No |
| `en` | Solo inglés | No | No |
| `es-en` | Español (primario) + anexo inglés | `[[es:term]]` en la primera mención, `[[en:term]]` en secciones bilingües | Sí, en español-primario |
| `en-es` | Inglés (primario) + anexo español | `[[en:term]]` en la primera mención, `[[es:term]]` en secciones bilingües | Sí, en inglés-primario |

**Reglas:**

- En `language: es` o `language: en`, las marcas `[[en:]]` / `[[es:]]`
  están **prohibidas** (la nota es monolingüe).
- En `language: es-en` o `language: en-es`, la **primera aparición**
  de un término técnico lleva la marca del idioma primario.
- Las secciones largas (≥ 5 párrafos) pueden tener un anexo bilingüe
  opcional, marcado con `:::external` (conocimiento del agente
  traducido del SDM, no del propio SDM).

**Detección algorítmica (S6):** si `language: en` aparece una palabra
clave en español (`el servidor`, `la aplicación`, `mediante`), se
detecta mismatch.

---

## §3 · Lista cerrada de no-traducibles (≥ 40 entradas)

**45 entradas** distribuidas en **8 categorías**. La métrica es
**0 ocurrencias de traducción prohibida** por nota (regex S1 en §6).

### §3.1 · Identificadores (12)

| # | Nombre | Categoría | Original | Por qué no se traduce |
|---|---|---|---|---|
| 1 | `xmin` | identificador PG | `xmin` | Literal en el código fuente de PostgreSQL; traducción rompe grep. |
| 2 | `xmax` | identificador PG | `xmax` | Idem. |
| 3 | `xid` | identificador PG | `xid` | Idem. |
| 4 | `tid` | identificador PG | `tid` | Idem. |
| 5 | `cid` | identificador PG | `cid` | Idem. |
| 6 | `oid` | identificador PG | `oid` | Idem. |
| 7 | `relname` | identificador PG | `relname` | Idem. |
| 8 | `relkind` | identificador PG | `relkind` | Idem. |
| 9 | `pg_class` | identificador PG | `pg_class` | Idem. |
| 10 | `HeapTuple` | identificador PG | `HeapTuple` | Idem (PascalCase). |
| 11 | `xlog` | identificador PG | `xlog` | Idem. |
| 12 | `LSN` | identificador PG | `LSN` | Acrónimo en mayúsculas. |

### §3.2 · Parámetros CLI (8)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 13 | `--rm` | `--rm` | Flag CLI case-sensitive. |
| 14 | `-it` | `-it` | Idem. |
| 15 | `-d` | `-d` | Idem. |
| 16 | `--max-connections` | `--max-connections` | Configuración de PostgreSQL; parámetro del CLI `postgres`. |
| 17 | `--volume` | `--volume` | Flag de `docker run` / `docker create`. |
| 18 | `-p` | `-p` | Puerto, flag corto. |
| 19 | `--name` | `--name` | Flag CLI. |
| 20 | `--env` | `--env` | Flag CLI. |

### §3.3 · Mensajes de error (6)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 21 | `Connection refused` | `Connection refused` | Mensaje de `connect()` en POSIX. |
| 22 | `ORA-29701` | `ORA-29701` | Código de error Oracle con formato propio. |
| 23 | `ImagePullBackOff` | `ImagePullBackOff` | Estado de pod Kubernetes. |
| 24 | `CrashLoopBackOff` | `CrashLoopBackOff` | Idem. |
| 25 | `ENOENT` | `ENOENT` | Código POSIX `errno 2`. |
| 26 | `EADDRINUSE` | `EADDRINUSE` | Código POSIX `errno 98`. |

### §3.4 · Códigos de retorno HTTP (3)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 27 | `404 Not Found` | `404 Not Found` | Estándar RFC 9110 §15.5.5. |
| 28 | `500 Internal Server Error` | `500 Internal Server Error` | Estándar RFC 9110 §15.6.1. |
| 29 | `422` | `422` | Estándar RFC 9110 §15.5.21. |

### §3.5 · Comandos shell (6)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 30 | `docker run` | `docker run` | Comando CLI de Docker. |
| 31 | `kubectl apply` | `kubectl apply` | Comando CLI de Kubernetes. |
| 32 | `psql` | `psql` | Comando CLI de PostgreSQL. |
| 33 | `pg_dump` | `pg_dump` | Comando CLI de PostgreSQL. |
| 34 | `tar -czf` | `tar -czf` | Comando CLI con flags. |
| 35 | `ssh -i` | `ssh -i` | Comando CLI con flag. |

### §3.6 · Sintaxis / firmas (3)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 36 | `func (ctx context.Context, id string) error` | Go signature | Sintaxis literal del lenguaje Go. |
| 37 | `def __init__(self, ...):` | Python signature | Idem. |
| 38 | `public static void main(String[] args)` | Java signature | Idem. |

### §3.7 · Versiones de protocolo (3)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 39 | `RFC 9293` | `RFC 9293` | RFC de IETF. |
| 40 | `HTTP/1.1` | `HTTP/1.1` | Versión de protocolo. |
| 41 | `TLS 1.3` | `TLS 1.3` | Versión de protocolo. |

### §3.8 · Nombres de propiedad / header HTTP (4)

| # | Nombre | Original | Por qué no se traduce |
|---|---|---|---|
| 42 | `content-type` | `content-type` | Header HTTP. |
| 43 | `Authorization` | `Authorization` | Header HTTP. |
| 44 | `Cache-Control` | `Cache-Control` | Header HTTP. |
| 45 | `max-age` | `max-age` | Directiva de `Cache-Control`. |

**Detección algorítmica (§6 S1):** regex contra la lista cerrada de 45
nombres; alerta si el texto contiene la **traducción** (ej. `--max-conexiones`,
`errores` en código, `issues` en código, `funciones` en código).

---

## §4 · Primera aparición bilingüe

### §4.1 · Formato de las marcas

- `[[en:term]]` — primera aparición del término en inglés.
- `[[es:term]]` — primera aparición del término en español.
- `[[term:term]]` — marca canónica unificada (F46), independiente del idioma.
  Se usa en el glosario al pie de la nota.

### §4.2 · Reglas algorítmicas

1. **Detección de primera aparición:** regex contra el texto de la nota
   desde el inicio; primera ocurrencia de la palabra o frase objetivo
   lleva la marca bilingüe del idioma primario.
2. **Orden por `language`:**
   - `language: es` → no usa marcas bilingües (la nota es monolingüe).
   - `language: en` → no usa marcas bilingües.
   - `language: es-en` → primera aparición usa `[[es:term]]`; secciones
     bilingües pueden usar `[[en:term]]`.
   - `language: en-es` → primera aparición usa `[[en:term]]`; secciones
     bilingües pueden usar `[[es:term]]`.
3. **Glosario al pie:** la nota bilingüe **debe** tener un bloque
   `## Glosario` al final con las marcas y su definición.

### §4.3 · Plantilla del glosario

```markdown
## Glosario

| Término | ES | EN |
|---|---|---|
| `mvcc` | Control de concurrencia multiversión | Multi-Version Concurrency Control |
| `three-way-handshake` | Apertura de conexión TCP en 3 pasos | TCP three-way handshake |
```

**Detección algorítmica (§6 S2):** regex contra presencia de `[[en:term]]`
o `[[es:term]]` en notas con `language == es-en` o `en-es`; ≥ 1 match.

---

## §5 · Bloque de procedencia al pie de cada nota

### §5.1 · Plantilla cerrada

```markdown
## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 Server Administration · docs |
| **Versión** | PostgreSQL 16.3 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `page=37,section_path=/ch13/concurrency` |
```

### §5.2 · Reglas duras

- El bloque **siempre** tiene 4 campos (fuente, versión, fecha, URL/anchor).
- La fecha usa formato ISO `YYYY-MM-DD`.
- La fuente es el nombre editorial + producto + tipo (no la URL sola).
- El bloque **complementa** el frontmatter `source`, `source-type`,
  `source-anchor`, `retrieved`: frontmatter es metadata para máquinas;
  bloque es metadata para humanos que no abren YAML.
- Si la URL es privada (libro DRM), se sustituye por `local: archivo
  /path/al/libro.pdf, capítulo 13`.
- El bloque **no** es opcional: cualquier nota sin bloque falla el criterio #4.

### §5.3 · Discrepancia frontmatter ↔ bloque

Si `frontmatter.retrieved` ≠ bloque `## Procedencia.fecha`, el eval
detecta la discrepancia con S8.

**Detección algorítmica (§6 S4):** regex contra `^##\s+Procedencia\s*$` con
≥ 4 campos `| **Campo** |` en formato markdown.

---

## §6 · Señales de diagnóstico (S1-S8)

Tabla cerrada de **8 señales algorítmicas**. Cada señal con método
(regex/conteo) y PASS/FAIL.

| ID | Señal | Método | PASS si | Detecta criterio |
|---|---|---|---|---|
| **S1** | Traducción de nombre técnico | regex contra lista cerrada §3 (45 entradas); alerta si encuentra `--max-conexiones`, `--max-conexion`, `funciones` en código, `errores` en código, `issues` en código | 0 matches de traducción prohibida | C1 |
| **S2** | Primera aparición bilingüe presente | regex `\[\[(en|es):[a-z0-9_-]+\]\]` ≥ 1 en notas con `language == es-en` o `en-es`; ≥ 0 en notas monolingües | ratio cumple | C2 |
| **S3** | Lista cerrada ≥ 40 entradas | regex contra filas de §3 con formato `\| \d+ \|` y columna "Original" | count(entradas) ≥ 40 | C3 |
| **S4** | Bloque de procedencia completo | regex `^##\s+Procedencia\s*$` + tabla con 4 campos (`Fuente`, `Versión`, `Fecha de recuperación`, `URL/anchor`) | 4 campos presentes | C4 |
| **S5** | Glosario presente en notas bilingües | regex `^##\s+Glosario\s*$` con ≥ 2 entradas en notas con `language == es-en` o `en-es` | presencia condicional al `language` | C2 |
| **S6** | Idioma consistente en secciones | regex contra palabras clave en español (`el servidor`, `la aplicación`, `mediante`) en secciones declaradas `language: en` | 0 matches en secciones EN | C1 |
| **S7** | `properties.md §5.13` referencia F101 | regex contra el archivo `properties.md` buscando `F101` | ≥ 1 match | wirings |
| **S8** | Coherencia frontmatter ↔ bloque | regex comparando `frontmatter.retrieved` con bloque `## Procedencia` | fechas coinciden | C4 |

---

## §7 · Anti-patrones (≥ 6)

| # | Anti-patrón | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | Traducción de parámetro CLI | `--max-conexiones` | `--max-connections` | S1 |
| **AP2** | Bloque de procedencia ausente | nota sin `## Procedencia` | nota con bloque de 4 campos | S4 |
| **AP3** | Término bilingüe fuera de orden | `language: en-es` con primera aparición `[[es:term]]` | primera aparición `[[en:term]]` | S2 |
| **AP4** | Glosario ausente en nota bilingüe | `language: es-en` sin `## Glosario` | nota bilingüe con glosario ≥ 2 entradas | S5 |
| **AP5** | Idioma incorrecto en sección mecánica | `language: en` con "el servidor ejecuta..." | `language: en` con "the server executes..." | S6 |
| **AP6** | Discrepancia frontmatter ↔ bloque | `retrieved: 2026-09-29` + `## Procedencia` con `Fecha: 2025-01-01` | fechas coinciden | S8 |
| **AP7** | Traducción de código en cuerpo | "errores" en lugar de "errores" como sustantivo en español, pero `errors` como nombre técnico | código verbatim, prosa en español | S1 |

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.yaml` | `use_case_profile` y `language` controlan la prosa y las marcas bilingües. |
| F20 | `references/01-ingest/ocr-engines.md` | OCR multi-idioma `spa+eng`. F101 norma la salida, F20 la ingesta. |
| F26/F27 | `references/02-source-model/provenance.md` | BCP-47, source-bearing. F101 añade bloque `## Procedencia` para humanos. |
| F45 | `references/04-authoring/block-directives.md` §10.11-§10.12 | `:::external` para contenido traducido del SDM. |
| F46 | `references/04-authoring/inline-marks.md` | `[[term:nombre]]` canónica; F101 introduce `[[en:]]` / `[[es:]]`. |
| F47 | `references/04-authoring/properties.md` §5.13 | Enum `language`; F101 norma cómo redactar. |
| F51 | `references/04-authoring/depth-layers.md` | Las marcas bilingües viven en L1 (apertura pedagógica). |
| F76 | `references/07-visual/density.md` | R1-R8 aplican; el bloque de procedencia se cuenta como anclaje visual. |
| F78 | `references/05-note-types/concept.md` §6 | Checklist de cierre se extiende con 4 items de F101. |
| F94 | `references/06-writing/intuition-first.md` §2 | F101 introduce marcas bilingües en `## Intuición` y `## Analogía`. |
| F95 | `references/06-writing/analogies.md` §4 | La rotura de analogía puede ser bilingüe (mapa ES↔EN). |
| F96 | `references/06-writing/executable-examples.md` §2 | Comandos verbatim (`docker run`, `psql`); F101 refuerza §3.5. |
| F97 | `references/06-writing/comparisons.md` §9 | Comparaciones derivadas pueden ser bilingües (`:::external`). |
| F98 | `references/06-writing/paraphrase.md` §2 | L1-L8 literales protegidos ampliados a §3 de F101 (45 no-traducibles). |
| F99 | `references/06-writing/voice-style.md` §5 | Voz activa con nombres técnicos verbatim. |
| F100 | `references/06-writing/anti-patterns.md` §6 | Checklist ampliado con 4 items de F101. |
| F112 | F112 (suite de checks automatizados) | Las señales S1-S8 son la base para los checks automáticos de F112. |
| F115 | F115 (reporte de calidad) | El reporte cita el bloque de procedencia de cada nota. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/i18n-and-citation.md`
aparece en §5.2 con la entrada _"Redactar prosa en el idioma del perfil
con primera aparición bilingüe + bloque de procedencia al pie"_, entre F100
y F65.

---

## §9 · Verificación al cierre de la fase

Los **4 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Ningún nombre técnico aparece traducido | `evals/i18n-and-citation-sample/run_eval.py` C8 detecta `i18n-bad-1-translated.md` con `--max-conexiones` mediante S1. Las 3 notas positivas pasan S1. |
| **C2** Términos introducidos bilingües en primera aparición | C8 detecta `i18n-bad-3-no-bilingual.md` sin marcas `[[en:]]` / `[[es:]]` mediante S2. Las 2 notas positivas bilingües (good-2, good-3) tienen ≥ 2 marcas. |
| **C3** Lista de no-traducibles ≥ 40 | C3 cuenta las filas de §3 con formato de tabla cerrada. |
| **C4** Bloque de procedencia con 4 campos | C8 detecta `i18n-bad-2-no-citation.md` sin `## Procedencia` mediante S4. Las 3 notas positivas tienen bloque con 4 campos. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l i18n-and-citation.md` ≤ 600.
- **D2.** 9 secciones canónicas §1-§9 presentes.
- **D3.** §3 lista cerrada ≥ 40 entradas (alias C3).
- **D4.** §5 plantilla de procedencia con 4 campos `Fuente`, `Versión`, `Fecha de recuperación`, `URL/anchor`.
- **D5.** Wirings cerrados (C9).
- **D6.** Las 6 notas fixture pasan `density_check.py --strict` (C10).
