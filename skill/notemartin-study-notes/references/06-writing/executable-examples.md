# `references/06-writing/executable-examples.md` — Ejemplos ejecutables

> Documento normativo de la **Fase 96**. Define la **anatomía del mínimo
> reproducible** (Setup → Acción → Resultado → Limpieza), las **3 plantillas
> canónicas** (DB, redes/sistemas, CLI/producto), los **3 niveles de escalado**
> (mínimo / realista / límite), **5+ anti-ejemplos** con el error concreto
> y la versión correcta, la **cabecera de declaración de entorno** y las
> **8+ señales de diagnóstico algorítmicas** que un revisor externo aplica
> sin ejecutar el ejemplo.
>
> **Cuándo cargar:** antes de redactar `## Confirmación` o cualquier
> `:::example` que acompañe a una nota pedagógica; cuando un revisor detecta
> que un ejemplo no es reproducible o depende de estado implícito.
>
> **Wirings:**
> - `references/04-authoring/block-directives.md` (F45) §10.4 — `:::example`
>   admite 1 snippet por admonition; F96 norma **qué** contiene el snippet.
> - `references/06-writing/intuition-first.md` (F94) §2, §5.4 — la etapa
>   `## Confirmación` es donde viven los ejemplos; F94 exige caso real del SDM.
> - `references/06-writing/analogies.md` (F95) §7 — plantilla cerrada; F96
>   reutiliza el estilo de plantilla con 4 propiedades obligatorias.
> - `references/07-visual/density.md` (F76) — R3 anclajes visuales cada 200
>   palabras; `:::example` cuenta como anclaje.
> - `references/04-authoring/inline-marks.md` (F46) — `{src:blk_xxxx}` para
>   código del SDM, `:::derived` para setup construido por el agente.
> - `references/05-note-types/concept.md` (F78) §3 — la nota `concept`
>   usa ejemplos en `## Confirmación` y `## Mecanismo`.

---

## §1 · Propósito y alcance

Tres problemas resueltos por F96:

1. **El agente copia ejemplos del SDM sin contexto.** Ejemplos como
   `SELECT count(*) FROM pg_class WHERE relkind = 'r';` sin declarar
   que asumen una conexión psql abierta, una DB concreta y un usuario
   con permisos. F96 obliga a **declarar el entorno** y **crear el
   setup** que el ejemplo necesita.
2. **Los ejemplos no son reproducibles.** El agente escribe un output
   esperado hardcodeado en lugar de ejecutar y capturar; o asume un
   orden que no es determinista. F96 introduce la sección
   `## Resultado` con output capturado del SDM o ejecución real, y
   reglas de orden determinista (`ORDER BY` en SQL, `--time` en lugar
   de timestamps).
3. **Los ejemplos dejan basura.** `docker run` sin `--rm`, archivos
   `/tmp/*.pcap` que se acumulan, tablas TEMP que sobreviven a la sesión.
   F96 obliga a `## Limpieza` o declara explícitamente que no la
   necesita.

**Cierra los 3 criterios del ROADMAP §1660-1662:**

1. _Todo ejemplo ejecutable incluye setup y limpieza o declara que no los necesita_ → §2 + §3 + §7 D2.
2. _Cada concepto mayor tiene ejemplo mínimo y realista_ → §3 con 3 plantillas + §4 con 3 niveles de escalado.
3. _Ningún ejemplo depende de estado no declarado_ → §6 cabecera de entorno + §7 D4-D7.

**Fuera de alcance:**

- Analogías y banco → F95.
- Comparaciones lado a lado → F97.
- Parafraseo fiel vs literal → F98.
- Voz y estilo → F99.
- Anti-patrones generales → F100.
- Idioma bilingüe y citación → F101.
- Ejecución real de los ejemplos (sandbox, fixtures automatizadas) → F118.

---

## §2 · Anatomía del mínimo reproducible

Un ejemplo ejecutable tiene **4 secciones obligatorias** en este orden,
dentro de un bloque `:::example` (F45 §10.4) o como headings `##`
hermanos si el ejemplo ocupa más de 30 líneas (F76 R7 → `:::collapsible`).

| # | Sección | Capa | Forma canónica | Marca preferida | Regex de detección |
|---|---|---|---|---|---|
| 1 | `## Setup` | L2 | 1-5 comandos/bloques que crean el estado necesario | `{src:blk_xxxx}` (del SDM) o `:::derived` (construido por el agente) | `^##\s+Setup\s*$` |
| 2 | `## Acción` | L2/L3 | 1 comando/bloque que ejecuta el ejemplo | `{src:blk_xxxx}` (literal del SDM) | `^##\s+Acci[oó]n\s*$` |
| 3 | `## Resultado` | L3 | Output esperado verbatim, capturado de la fuente o de ejecución real | `{src:blk_xxxx}` (output del SDM) o **sin marca** (ejecutado y capturado) | `^##\s+Resultado\s*$` |
| 4 | `## Limpieza` | L2 | 1-3 comandos que deshacen el setup | `{src:blk_xxxx}` o **sin marca** | `^##\s+Limpieza\s*$` o `^>\s+No requiere limpieza` |

**Reglas duras:**

- El orden es **fijo**: Setup antes de Acción, Acción antes de Resultado,
  Resultado antes de Limpieza. Invertir es anti-patrón NE7 (no listado en
  §5 porque es obvio, pero el eval lo caza con D1).
- Si el ejemplo **no** requiere una sección (ej. `docker run --rm` no
  necesita Setup ni Limpieza manual), se sustituye por
  `> No requiere setup: la flag --rm cubre la limpieza.`
  Esto cuenta como cumplimiento del criterio #1.
- `## Resultado` debe incluir el **output verbatim** cuando viene del
  SDM (entre triple-backtick). No vale "Output: 5" sin captura.
- Si `## Acción` es multilínea (> 5 líneas), debe plegarse en
  `:::collapsible` con `default_open: true` (F76 R7 permite > 100 líneas
  pero con plegado).

---

## §3 · Plantillas canónicas

### §3.1 · DB (PostgreSQL, MySQL, MongoDB)

```notemark
> **Entorno:** <producto> <versión> · <OS> · <cliente> <versión> · DB seed `<nombre>` con N filas.

:::example
## Setup
```sql
CREATE TEMP TABLE <nombre> (<columnas>);
INSERT INTO <nombre> VALUES (<seed>);
```
{src:blk_<id>}

## Acción
```sql
<UPDATE/SELECT/INSERT/etc.>
```

## Resultado
```sql
<output verbatim>
```

## Limpieza
```sql
DROP TABLE <nombre>;
```
:::
```

### §3.2 · Redes / sistemas (`tcpdump`, `ip`, `iptables`)

```notemark
> **Entorno:** Linux kernel <ver> · <herramienta> <ver> · iface `<nombre>` · permisos root.

:::example
## Setup
```bash
<crea interface, namespace, archivo de captura, etc.>
```

## Acción
```bash
<comando que genera el tráfico o aplica el cambio>
```

## Resultado
```bash
<captura verbatim con ≥ 3 líneas>
```

## Limpieza
```bash
<borra archivos, interfaces, namespaces>
```
:::
```

### §3.3 · CLI / producto (`docker run`, `kubectl apply`, `terraform`)

```notemark
> **Entorno:** <herramienta> <ver> · <OS> · imagen/recurso `<nombre>`.

:::example
## Setup
```bash
<pull de imagen, login, init>
```

## Acción
```bash
<comando principal>
```

## Resultado
```
<output verbatim>
```

## Limpieza
> No requiere limpieza: <justificación> (ej. `--rm`, `kubectl delete` ya
> aplicado, `terraform destroy` ya ejecutado).
:::
```

Las 3 plantillas comparten 4 secciones; las diferencias son:

| Diferencia | DB | Redes | CLI |
|---|---|---|---|
| Output en bloque | triple-backtick `sql` | triple-backtick `bash` | triple-backtick sin lang o texto plano |
| Limpieza típica | `DROP TABLE` | `rm archivo.pcap`, `ip netns del` | `--rm` o destroy ya aplicado |
| Setup típico | `CREATE TABLE` + `INSERT` | `ip link add`, `tcpdump -w` | `docker pull` |
| Permisos | DB user con grants | root o `CAP_NET_RAW` | usuario normal |

---

## §4 · Escalado mínimo / realista / límite

Tabla cerrada con umbrales numéricos:

| Nivel | Líneas de código | Tiempo de ejecución | Cuándo usar | Marca |
|---|---|---|---|---|
| **mínimo** | ≤ 5 | < 1 s | Demostrar la mecánica básica; aparece en `## Confirmación` | `:::example` simple |
| **realista** | 5-30 | 1-30 s | Demostrar el caso de uso típico del usuario; aparece en `## Confirmación` o `## Práctica` | `:::example` simple |
| **límite** | > 30 o > 30 s | variable | Demostrar escalabilidad / stress / comportamiento en bordes; aparece en `:::collapsible` con `default_open: false` | `:::example` + `:::collapsible` + `:::warning` con motivo |

**Reglas:**

- El nivel **mínimo** es obligatorio en toda nota `concept` que tenga
  `## Confirmación` con caso real.
- El nivel **realista** aparece en notas `procedure` y `practice`.
- El nivel **límite** aparece solo en `practice` o `cheatsheet` (cuando
  documenta parámetros de tuning); nunca en notas `concept` ni `comparison`.
- Mezclar niveles en el mismo ejemplo es anti-patrón NE8.

---

## §5 · Ejemplos negativos (≥ 5)

| # | Anti-ejemplo | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **NE1** | Setup ausente | `:::example\nSELECT * FROM users;\n:::` (no crea `users`) | `:::example\n## Setup\nCREATE TABLE users (...);\nINSERT INTO users VALUES (...);\n## Acción\nSELECT * FROM users;\n:::` | D1 (orden canónico) + D2 (presencia de `## Setup`) |
| **NE2** | Limpieza ausente | `:::example\ndocker run alpine echo hi\n:::` (contenedor queda colgado) | `:::example\ndocker run --rm alpine echo hi\n## Limpieza\n> No requiere limpieza: --rm\n:::` | D2 (presencia de `## Limpieza` o "No requiere limpieza") |
| **NE3** | Estado implícito | `psql -c "SELECT 1"` sin declarar DB ni usuario | `:::example\n## Setup\npsql -U demo -d notemartin_demo -c "SELECT 1"\n## Acción\n...` | D4 (cabecera `> **Entorno:**` con DB + OS) |
| **NE4** | Orden no determinista | `SELECT * FROM events LIMIT 10` sin `ORDER BY` (output varía entre ejecuciones) | `SELECT * FROM events ORDER BY id LIMIT 10` | D7 (regex `ORDER BY` en SQL / `--time` en shell) |
| **NE5** | Comando no portable | `head -n 5` en GNU funciona; en macOS BSD también, pero `tail -n +2` no (BSD usa `-n +2` vs GNU `+2`) | Anclar a GNU coreutils o usar `tail -n 2` (portable) | D6 (regex contra flags específicos de GNU) |
| **NE6** | Salida hardcodeada | `## Resultado\nOutput: 5 rows.` | `## Resultado\n```\n id | name\n----+-------\n  1 | alice\n  2 | bob\n(2 rows)\n```` | D5 (`## Resultado` con bloque de código verbatim) |
| **NE7** | Orden invertido | `## Acción` antes de `## Setup` | Orden canónico §2 | D1 |
| **NE8** | Mezcla de niveles | Mínimo + realista en el mismo `:::example` | Dos `:::example` hermanos | Inspección visual + D3 |

---

## §6 · Declaración de entorno

Cada ejemplo ejecutable va precedido por una cabecera `> **Entorno:**`
con **4 campos cerrados**:

```
> **Entorno:** PostgreSQL 16.3 · Ubuntu 24.04 LTS · psql 16.3 ·
> DB seed `notemartin_demo` con 1000 filas pre-cargadas.
```

| Campo | Forma | Ejemplo |
|---|---|---|
| Producto + versión | `<producto> <ver>` | `PostgreSQL 16.3` |
| OS + versión | `<distro> <ver>` o kernel | `Ubuntu 24.04 LTS` o `Linux kernel 6.8` |
| Cliente / herramienta | `<cli> <ver>` | `psql 16.3` |
| Datos semilla | `DB seed <nombre> con N filas` o `iface <X>` o `imagen <X>` | `DB seed notemartin_demo con 1000 filas` |

**Reglas:**

- Los 4 campos son obligatorios; si alguno no aplica (ej. un comando
  puro no tiene DB seed), se sustituye por `N/A (comando puro)` o se
  omite con justificación `> N/A: el comando no requiere DB`.
- La cabecera va **antes** del bloque `:::example`, no dentro.
- Las versiones son **literales** del SDM o de la documentación oficial
  (INV-09), no "latest" ni "~16".

---

## §7 · Señales de diagnóstico (≥ 8)

Tabla cerrada de **10 señales algorítmicas** que un revisor externo
aplica sin ejecutar el ejemplo.

| ID | Señal | Método | PASS si |
|---|---|---|---|
| **D1** | Orden canónico de las 4 secciones | Regex `^##\s+(Setup\|Acci[oó]n\|Resultado\|Limpieza)\s*$` en orden ascendente | 4 matches en orden o 3 + `> No requiere limpieza` |
| **D2** | `## Limpieza` o "No requiere limpieza" presente | Regex `^##\s+Limpieza\s*$\|^>\s+No requiere (setup\|limpieza)` | ≥ 1 match en el ejemplo (criterio #1 ROADMAP) |
| **D3** | Una sola escala por ejemplo | Inspección: 1 bloque `:::example` con 1 setup, 1 acción, 1 resultado | El número de `## Acción` = 1 por bloque `:::example` |
| **D4** | Cabecera de entorno antes del ejemplo | Regex `^>\s+\*\*Entorno:\*\*` antes del primer `:::example` | ≥ 1 match |
| **D5** | `## Resultado` con bloque de código verbatim | Regex `^##\s+Resultado\s*$\n[\s\S]*?```[\s\S]*?``` ` | Bloque de código tras `## Resultado` |
| **D6** | Sin flags no portables | Regex contra `head -[0-9]\|tail -[0-9]\+\|sed -i ''\|\\bsed -E\\b` (estilo GNU/BSD) en bash | 0 matches que no estén precedidos de justificación |
| **D7** | Orden determinista en SQL | Regex `ORDER BY` cuando hay `LIMIT` o `OFFSET` | `ORDER BY` presente si hay `LIMIT`/`OFFSET` |
| **D8** | Sin estado implícito | Regex contra `\b(asumiendo|suponiendo|depende de|se asume)\b` sin bloque `## Setup` o cabecera `> **Entorno:**` cercano | 0 ocurrencias sin justificación |
| **D9** | `## Setup` con marca `{src:}` o `:::derived` | Inspección del bloque `## Setup`: presencia de `{src:blk_xxxx}` o directiva `:::derived` que envuelve | ≥ 1 marca cuando el setup viene del SDM |
| **D10** | Anchors visuales (R3 F76) en `## Resultado` | Conteo de `:::example` / tablas GFM / diagramas en la sección | ≥ 1 por cada 200 palabras |

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` | El doc aplica a todos los perfiles; el nivel de escalado puede depender de `use_case_profile`. |
| F45 | `references/04-authoring/block-directives.md` §10.4 | `:::example` admite 1 snippet por admonition; F96 norma el contenido. |
| F46 | `references/04-authoring/inline-marks.md` | `{src:blk_xxxx}` para código del SDM; `:::derived` para setup del agente. |
| F51 | `references/04-authoring/depth-layers.md` | `## Setup` y `## Limpieza` L2; `## Acción` y `## Resultado` L2/L3. |
| F76 | `references/07-visual/density.md` + `scripts/validate/density_check.py` | R3 anclajes visuales; R7 plegado si > 100 líneas. |
| F78 | `references/05-note-types/concept.md` §3 | `## Confirmación` usa ejemplos F96. |
| F94 | `references/06-writing/intuition-first.md` §5.4 | Regla C1 de `## Confirmación` exige caso real; F96 norma el caso. |
| F95 | `references/06-writing/analogies.md` §7 | Plantilla cerrada con propiedades obligatorias (F96 reutiliza el estilo). |
| F97 | `references/06-writing/comparisons.md` | Comparaciones entre ejemplos → F97. |
| F98 | `references/06-writing/paraphrase.md` | Setup que viene del SDM es literal (INV-09); F98 norma el parafraseo. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/executable-examples.md`
aparece en §5.2 con la entrada _"Redactar ejemplo ejecutable con
setup/acción/resultado/limpieza"_, entre F95 y F65.

---

## §9 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** Setup + limpieza o declaración explícita | `evals/executable-examples-sample/run_eval.py` C6 verifica `## Limpieza` o `> No requiere limpieza` ≥ 1 por nota. C7 verifica que la nota `anti-missing-cleanup.md` falla a propósito (test negativo de la señal). |
| **C2** Concepto mayor tiene ejemplo mínimo y realista | C4-C5: 4 notas base (DB + redes + CLI + anti) con 4 secciones canónicas + cabecera `> **Entorno:**` ≥ 4 campos. |
| **C3** Sin estado no declarado | C10: regex contra `asumiendo / suponiendo / depende de` sin bloque `## Setup` o cabecera `> **Entorno:**`. D4-D7 lo verifican por señal. |

Criterios derivados cubiertos por el eval:

- **D1.** `wc -l executable-examples.md` ≤ 600.
- **D2.** Las 9 secciones canónicas §1-§9 presentes.
- **D3.** §4 tiene tabla de 3 niveles (mínimo/realista/límite) con umbrales numéricos.
- **D4.** §7 tiene ≥ 8 señales algorítmicas D1-D10 con método (regex/conteo) y PASS/FAIL.
- **D5.** Las 4 notas fixture pasan `density_check.py --strict` exit 0.
- **D6.** Wirings cerrados (C8).
