# `api-reference` — `references/05-note-types/api-reference.md`

> Documento normativo de la **Fase 79** del roadmap. Define el patrón de la nota
> de tipo `api-reference`: 9 secciones obligatorias + 1 opcional + 3 de cierre,
> tabla canónica de parámetros con 5 columnas (Parámetro, Tipo, Obligatorio,
> Default, Descripción), cobertura exhaustiva sobre paquetes con ≥ 15
> subprogramas, y contrato de activación por perfil (sección `## Notas` y
> ejemplos ejecutables opcionales).
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `api-reference`; antes de redactar la primera
> sección específica del tipo. Este archivo instancia el patrón común de
> `references/07-visual/note-templates.md` (F75) §6.2 y delega cabecera,
> apertura y cierre allí.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) — cabecera canónica, apertura/cierre común, §6.2 patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8 ejecutables por `scripts/validate/density_check.py`.
> - `references/04-authoring/properties.md` (F47) — frontmatter canónico de 20 propiedades; `source-bearing` obligatorio (§6.2 F75).
> - `references/04-authoring/inline-marks.md` (F46) — marcas `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::example`, `:::warning`, `:::danger`, `:::note`, `:::param-table`, `:::collapsible`.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3; L1 ≤ 60 palabras.
> - `references/05-note-types/concept.md` (F78) — paraguas común (perfil-activación, checklist); F79 hereda el patrón y lo especializa para APIs.
> - `references/05-note-types/README.md` — los 15 tipos cerrados (F78-F92). `api-reference` ocupa el lugar §6.2.

---

## §1 · Propósito y alcance

Una nota `api-reference` documenta **una API o un paquete de subprogramas**
para que un desarrollador pueda usarla sin abrir el manual: firma, parámetros,
retornos, errores, privilegios, precondiciones, ejemplos ejecutables y
gotchas. Cubre funciones, endpoints REST, comandos CLI y schemas declarativos;
el denominador común es que existe una **firma** y un **conjunto cerrado de
parámetros** tabularizables.

**Fuera de alcance:** tutorial → `procedure`; comparativa 3+ APIs → `comparison`;
arquitectura → `architecture`; flag único → `glossary-term`; cambios entre
versiones → `version-delta`.

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` obligatorio)

```yaml
---
title: "<canónico, con versión si aplica>"
note-type: api-reference
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/api-reference, domain/<uno o más>, product/<nombre>]
source: "<ruta al SDM original>"
source-type: docs | api | article | book
source-anchor: "<page|section_path|endpoint>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<proveedor, si aplica>"
product: "<nombre del producto>"
product-version: "<versión>"
related: "[[note:...]], [[note:...]]"
---
```

`source-bearing` es **obligatorio** (F75 §6.2). Las 5 universales son
obligatorias en `status: published` (INV-P5). `vendor`, `product` y
`product-version` se recomiendan en APIs comerciales.

### §2.2 · Apertura común (heredada de F75 §3)

```markdown
# {title}

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | ... |
| **Procedencia** | source (source-type) §source-anchor · recuperado YYYY-MM-DD |
| **Versión** | product product-version |
| **Estado** | Publicado (published) / Borrador (draft) |
| **Tiempo de lectura** | N min |

## TL;DR
{primer párrafo del L1 — ≤ 8 líneas / ≤ 60 palabras}

{layer:l2}

## Sintaxis
```

### §2.3 · Las 9 secciones específicas + 1 opcional + 3 de cierre

Orden obligatorio; cada sección es H2 salvo indicación.

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | Heredada de F75. ≤ 60 palabras / 8 líneas (R1). |
| 2 | `## Sintaxis` | obligatoria | Firma completa. Si hay overloads, enumerar 2-3 firmas explícitamente (anti-patrón §6.2). |
| 3 | `## Parámetros` | obligatoria | Tabla 5-col canónica; ≥ 1 fila por parámetro documentado por el SDM (criterio #1). |
| 4 | `## Retornos` | obligatoria | Tipo exacto + ejemplo serializado (JSON/XML/YAML); `void`/`n/a` si aplica. |
| 5 | `## Excepciones` | obligatoria | Tabla o `:::danger` por código (criterio §6.2 anti-patrón: nunca prosa). |
| 6 | `## Privilegios` | obligatoria | Capacidad requerida (root, IAM role, GRANT, capability); `n/a` si no requiere. |
| 7 | `## Precondiciones` | obligatoria | Estado externo asumido (servicio arriba, namespace existe, archivo presente). |
| 8 | `## Ejemplos` | obligatoria | ≥ 1 ejemplo ejecutable (criterio #3); preferir "mínimo + realista". |
| 9 | `## Gotchas` | obligatoria | `:::warning` por gotcha con causa + manifestación + workaround. |
| 10 | `## Notas` | **opcional-condicional** | `:::note` per aclaración (deprecación, versionado, portabilidad). Ver §5. |
| 11 | `## Backlinks` | obligatoria si hay aristas | Cierre común. |
| 12 | `## Queries` | obligatoria si queries activas | Cierre común. |
| 13 | `## Ver también` | opcional si `related:` | Cierre común. |

Para paquetes con ≥ 15 subprogramas, `## Sintaxis`, `## Parámetros`, `## Retornos`,
`## Excepciones` y `## Ejemplos` se **sub-dividen** en `### Subprograma: <nombre>`
para mantener legibilidad. El subprograma raíz (la firma principal del paquete)
se mantiene en el H2; cada sub-complemento va en H3.

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. ≤ 60 palabras / 8 líneas. |
| L2 | `{layer:l2}` | Secciones 2-10 (sintaxis → notas). 70-90% del total. |
| L3 | `{layer:l3}` | Solo si la nota es muy extensa; `:::collapsible` con `default_open: true` cuando > 100 líneas en `## Parámetros` (R7). |

`api-reference` rara vez es "extensa" (≥ 50 líneas por sección típica); si
supera 100 líneas en `## Parámetros`, se pliega. La L1 siempre va en plano.

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `api-reference` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | ✅ |
| Aplicación | ✅ |
| Diagnóstico | — |
| Decisión | — |
| Predicción | — |

Notas: por defecto solo recuerdo + aplicación. Diagnóstico y decisión se
añaden solo si la nota documenta errores o trade-offs de uso (sub-tipo
`api-reference-with-errors`); ver `self-evaluation.md` §4. La nota puede
declarar `self-evaluation-types` como superset del default.

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `## TL;DR` | ≤ 60 palabras / 8 líneas | F76 R1 |
| `## Sintaxis` | Bloque `code` con caption; ≥ 1 firma | esta fase |
| `## Parámetros` | Tabla 5-col (`Parámetro`, `Tipo`, `Obligatorio`, `Default`, `Descripción`) | esta fase + §6.2 F75 |
| Tabla 5-col sin celdas vacías | 0 vacías en Tipo/Obligatorio/Default/Descripción | criterio #2 |
| `## Retornos` | 1 bloque con tipo + ejemplo | esta fase |
| `## Excepciones` | Tabla código/causa/remediación o `:::danger` por error | §6.2 |
| `## Privilegios` | 1 línea por capacidad; `n/a` si ninguna | esta fase |
| `## Precondiciones` | 1 lista con bullets por estado externo | esta fase |
| `## Ejemplos` | ≥ 1 bloque `:::example` o `code` con caption | criterio #3 |
| `## Gotchas` | ≥ 1 `:::warning` por gotcha (recomendado 3-5) | esta fase |
| `## Notas` | Opcional por perfil | §5 |
| Marcas `{src:blk_xxxx}` | ≥ 1 cada 200 palabras en tablas fácticas | F46 + F76 R8 |
| Anclaje visual | ≥ 1 cada 200 palabras (tablas cuentan) | F76 R3 |
| Cierre | `## Backlinks` + `## Queries` | F75 §4 |

### §3.1 · Tabla canónica de parámetros (5 columnas)

```
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `--rm` | flag | no | `false` | elimina el contenedor al salir |
| `-p` / `--port` | int:int | no | (aleatorio) | mapeo host:container; sin valor = aleatorio |
| `--name` | string | no | (generado) | nombre del contenedor |
| `image` | string | **sí** | n/a | imagen base (registry/path:tag) |
```

Reglas:

- Las 5 columnas son obligatorias y en este orden.
- Cero celdas vacías: si no hay default, se escribe `n/a` y se explica en la columna Descripción.
- "Obligatorio" acepta 3 valores: `sí`, `no`, `condicional` (con la condición entre paréntesis, p.ej. `sí (con --privileged)`).
- Si un parámetro tiene alias (`-p` / `--port`), el alias va antes del canónico.
- Cada fila lleva `{src:blk_xxxx}` cuando el parámetro viene del SDM.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas.
- **R2** Cada párrafo del L2 ≤ 200 palabras. Las tablas NO cuentan como párrafo.
- **R3** ≥ 1 anclaje visual cada 200 palabras. Las tablas y los code fences con caption cuentan.
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama, ecuación o code.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: true` (el lector de API espera ver los parámetros sin desplegar nada; el plegable es solo para aligerar scroll).
- **R8** Densidad de marcas `{src:}` ≥ 0.80 sobre bloques fácticos (las filas de tabla cuentan como bloques fácticos si declaran un campo del SDM).

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). En `## Parámetros`, cada fila lleva `{src:}` si el parámetro viene del SDM. En `## Ejemplos`, el bloque `code` lleva `{src:}` que apunta al bloque del SDM de donde se extrajo el ejemplo.
- **`[[term:nombre]]`** — primera aparición del término (INV-I2). Usar para: nombres de flags no triviales (`--privileged`), nombres de campos técnicos (`xmin`), nombres de protocolos (`TCP`).
- **`[[note:id]]`** — enlaces a notas `concept`, `procedure`, `comparison` o `error-troubleshooting` relacionadas. En `## Gotchas`, cada gotcha enlaza a su nota de error (`[[note:docker-oomkilled]]`).

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Sintaxis` | Bloque `code` con caption (sin directiva; fence ``` con título en línea 0) | F45 §10 ejemplos de código. |
| `## Parámetros` | Tabla GFM 5-col (no `:::param-table`, que tiene 4 col) | F75 §5.1 + esta fase. |
| `## Excepciones` | Tabla GFM o `:::danger` por código | F75 §6.2 anti-patrón "nunca prosa". |
| `## Ejemplos` | `:::example` con bloque `code` | F45 §10.5 + F45 §6 fila 10. |
| `## Gotchas` | `:::warning` por gotcha | F45 §6 fila 1. |
| `## Notas` | `:::note` por aclaración | F45 §6 fila 12. |
| `## Privilegios` | Lista con bullets o tabla corta | F75 §5.1. |
| `## Precondiciones` | Lista con bullets (con o sin checklist `[ ]`) | F75 §5.1. |

### §4.4 · Diferencias operativas

| Concepto | Definición | Ejemplo |
|---|---|---|
| **Excepción** | Respuesta oficial de la API ante un fallo. El SDM la documenta. | HTTP 404, `Errno 13`. |
| **Gotcha** | Comportamiento sorpresivo **no** marcado como error oficial. | "El flag `--rm` se ignora con volume `:cached`" (Docker 24.x bug). |
| **Privilegio** | Capacidad de seguridad que la API requiere del llamante. **Estática**. | `CAP_NET_ADMIN` para `iptables`. |
| **Precondición** | Estado externo que la API asume verdadero. **Estado del mundo**. | `kubelet` corriendo en el nodo. |

### §4.5 · Anti-patrones

1. **"Errores en prosa"** — `## Excepciones` con párrafos largos. Solución: tabla `| Código | Causa | Remediación |` o callouts `:::danger` discretos.
2. **"Op-args con 'puede ser X o Y'"** — firmas ambiguas. Solución: enumerar 2-3 firmas en `## Sintaxis`.
3. **"Tabla sin columna Default"** — flag sin default marcado. Solución: 5 columnas siempre; `n/a` explícito.
4. **"Ejemplo decorativo"** — `:::example` con placeholders `{{image}}`. Solución: imagen real + comando completo + salida esperada.
5. **"Privilegios en Precondiciones"** — root listado como precondición. Solución: 2 secciones separadas.
6. **"Gotchas como errores"** — bugs listados como códigos oficiales. Solución: distinguir por fuente.
7. **"Sección `## Parámetros` con bullets"** — flags en bullets. Solución: tabla 5-col siempre.
8. **"Sin `## Ejemplos` si hay 0 ejemplos"** — omitir la sección. Solución: marcar con `:::warning` "Sin ejemplos en el SDM".
9. **"Default = 'automático'"** — no documentar. Solución: explicar en Descripción cómo se calcula.
10. **"Sin `## Cabecera` porque 'ya está en la tabla'"** — anti-patrón F75. La cabecera siempre va.

---

## §5 · Activación por perfil

La sección `## Notas` (opcional) y la profundidad de `## Ejemplos` (mínimo vs
mínimo + realista) están **desactivadas parcialmente por default**. Se activan
vía perfil (`assets/profile.template.yaml`, F11):

```yaml
notes:
  types:
    api-reference:
      include_notes: true                 # default: true
      include_examples_realistic: true    # default: true
      include_gotchas: true               # default: true
      include_error_table: true           # default: true
      min_examples: 1                     # default: 1; mínimo duro (criterio #3)
      min_table_columns: 5                # default: 5; mínimo duro (criterio #2)
      executable_examples_only: false     # default: false; si true, rechaza ejemplos con placeholders
```

| Campo | Default | Significado |
|---|---|---|
| `include_notes` | `true` | `## Notas` se incluye si el SDM tiene material; si no, se omite con `:::note` "Sin notas del SDM". |
| `include_examples_realistic` | `true` | Incluye 1 ejemplo realista además del mínimo. |
| `include_gotchas` | `true` | Incluye `## Gotchas`; con `false`, se omite (rompe cobertura de errores no documentados). |
| `include_error_table` | `true` | Errores como tabla GFM; con `false`, `:::danger` por código. |
| `min_examples` | `1` | Mínimo de bloques ejecutables (criterio #3). |
| `min_table_columns` | `5` | Mínimo de columnas en `## Parámetros` (criterio #2). |
| `executable_examples_only` | `false` | `true` rechaza placeholders `{{...}}` o `TODO`. |

Precedencia F11 §7.4: **prompt > perfil > defaults**.

---

## §6 · Checklist de cierre

Antes de publicar:

- [ ] Cabecera con 5 campos en orden (F75 §2.1).
- [ ] `source-bearing`: `source`, `source-type`, `source-anchor`, `retrieved` presentes.
- [ ] `vendor`, `product`, `product-version` cuando aplica.
- [ ] `## TL;DR` ≤ 60 palabras / 8 líneas (R1).
- [ ] Las 9 secciones obligatorias (Sintaxis → Gotchas) presentes y en orden.
- [ ] `## Parámetros` con tabla 5-col: `Parámetro`, `Tipo`, `Obligatorio`, `Default`, `Descripción`.
- [ ] Cero celdas vacías en Tipo/Obligatorio/Default/Descripción (criterio #2).
- [ ] SDM lista N parámetros → tabla tiene N filas (criterio #1).
- [ ] Si ≥ 15 subprogramas, cada uno tiene `### Subprograma: <nombre>` con firma + tabla.
- [ ] `## Ejemplos` con ≥ `min_examples` bloques `:::example` o `code` con caption (criterio #3).
- [ ] `## Excepciones` con tabla o `:::danger` (nunca prosa).
- [ ] `## Privilegios` ≠ `## Precondiciones` (sin duplicar).
- [ ] `## Gotchas` con ≥ 1 `:::warning` (recomendado 3-5).
- [ ] `## Notas` solo si hay material del SDM y `include_notes: true`.
- [ ] Si `## Parámetros` > 100 líneas, `:::collapsible` con `default_open: true` (R7).
- [ ] Cierre: `## Backlinks` + `## Queries`.
- [ ] Densidad `{src:}` ≥ 0.80 sobre bloques fácticos (R8).
- [ ] `density_check.py --note <path>` exit 0.
- [ ] `validate_ir.py --ir <path>` exit 0.

---

## §7 · Nota mínima viable (subprograma individual)

Ejemplo canónico de ~30 líneas para una API individual. Pasa
`density_check.py --strict` exit 0.

```markdown
---
title: "docker run"
note-type: api-reference
status: draft
tags: [type/api-reference, domain/cli, product/docker]
source: "Docker Engine 25 — docker run reference"
source-type: docs
source-anchor: "cli/run"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
---

# docker run

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Crea y arranca un contenedor a partir de una imagen, con flags de runtime, redes y volúmenes. |
| **Procedencia** | Docker Engine 25 — docker run reference (docs) §cli/run · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 2 min |

## TL;DR
`docker run IMAGE [COMMAND] [ARG...]` crea y arranca un contenedor desde `IMAGE`; flags como `--rm`, `-p`, `-d` modifican el ciclo de vida, las redes y el modo de ejecución. {src:blk_001122334455}

{layer:l2}

## Sintaxis
```bash
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

## Parámetros
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `-d` / `--detach` | flag | no | `false` | segundo plano; imprime solo ID |
| `-p` / `--publish` | int:int | no | (aleatorio) | publica puerto host:container |
| `IMAGE` | string | **sí** | n/a | imagen base (registry/path:tag) |

## Retornos
ID del contenedor creado (string). Con `-d` se imprime por stdout; sin `-d` se adjunta a la TTY.

## Excepciones
| Código | Causa | Remediación |
|---|---|---|
| 125 | flags CLI inválidos | `docker run --help` |
| 127 | binario no existe en la imagen | usar imagen con el binario |

## Privilegios
n/a por defecto. Con `--privileged` se requiere `CAP_SYS_ADMIN` en el host. {src:blk_667788990011}

## Precondiciones
- Docker daemon corriendo (`docker info` exit 0).
- Imagen disponible localmente o en un registry alcanzable.

## Ejemplos
:::example
**Mínimo:** contenedor efímero que imprime `hola`.

```bash
docker run --rm alpine echo hola
```
:::

:::example
**Realista:** nginx en el puerto 8080 del host, en segundo plano.

```bash
docker run -d --name web -p 8080:80 nginx:1.27
```
:::

## Gotchas
:::warning
**`--rm` no funciona con `--restart=always`.** Docker rechaza con exit 125. Solución: usar `--restart=on-failure:5` o eliminar manualmente.
:::

## Notas
:::note
`docker run` es un wrapper sobre `docker create` + `docker start`. Para crear sin arrancar, usa `docker create`.
:::

## Backlinks
- [[note:docker-cli-bundle]] — la nota bundle de Docker CLI.
```

Esta nota mínima (~50 líneas de cuerpo) cumple R1-R8 de F76 y los 3
criterios ROADMAP. Sirve de referencia de **forma**; el contenido se
sustituye por el del SDM en producción.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5.
- **F12** `references/04-authoring/notemark.md` — directivas `:::example`, `:::warning`, `:::danger`, `:::note` y `code` con caption.
- **F44** `references/03-knowledge/note-plan.md` — el selector asigna `api-reference` cuando la unidad es una firma o paquete.
- **F45** `references/04-authoring/block-directives.md` — directivas de `## Ejemplos`, `## Gotchas`, `## Notas`, `## Excepciones`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` en filas de tabla; `[[term:nombre]]` en flags no triviales.
- **F47** `references/04-authoring/properties.md` — frontmatter de 20 propiedades; `source-bearing` obligatorio.
- **F51** `references/04-authoring/depth-layers.md` — `## Parámetros` puede ir en L3 plegable si > 100 líneas.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.2 patrón resumido.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable por `scripts/validate/density_check.py`.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; F79 hereda §5 y §6.
- **F80** `references/05-note-types/procedure.md` — se complementa con procedure (no en la misma nota).
- **F82** `references/05-note-types/error-troubleshooting.md` — cada `:::danger` puede enlazar a su nota de troubleshooting.
- **F84** `references/05-note-types/syntax.md` — para sintaxis BNF/EBNF; `api-reference` documenta la **API**, no el **lenguaje**.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/api-reference.md` ≤ 400 líneas.
- §2 con 4 subsecciones (frontmatter, apertura, secciones, capas).
- §3 con tabla de componentes mínimos con ≥ 13 filas + §3.1 tabla 5-col.
- §4 con 5 subsecciones (densidad, marcas, directivas, diferencias operativas, anti-patrones).
- §5 con la tabla de campos del perfil y sus defaults.
- §6 con el checklist de cierre de ≥ 13 items.
- §7 con la nota mínima viable (≥ 25 líneas, pasa `density_check.py`).
- §8 con al menos 14 wirings documentados.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F79:**

1. _Sobre un paquete de 15+ subprogramas, ningún parámetro queda fuera._ → `evals/api-reference-sample/notes/docker-cli-bundle.md` cubre ≥ 15 subcomandos extraídos del corpus `07-docker-cli-ref`; battery C1 verifica nº de subcomandos + nº de filas por subcomando vs SDM.
2. _Toda entrada tiene tipo, obligatoriedad y default o `n/a` explícito._ → batería C2 itera filas de los 3 fixtures y exige las 5 celdas rellenas.
3. _Hay al menos un ejemplo ejecutable._ → batería C3 cuenta bloques `:::example` o `code` con caption; mínimo 1 por fixture; preferiblemente 2 (mínimo + realista).
