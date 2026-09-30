# `procedure` — `references/05-note-types/procedure.md`

> Documento normativo de la **Fase 80** del roadmap. Define el patrón de la nota
> de tipo `procedure`: 8 secciones obligatorias + 2 opcionales + 3 de cierre,
> pasos numerados con comando + salida esperada + verificación, declaración de
> impacto y reversibilidad, y contrato de activación por perfil.
>
> **Cuándo cargar:** tras decidir el tipo de nota (selector F93) cuando el
> `note-type` resuelto es `procedure`; antes de redactar el primer paso. Este
> archivo instancia el patrón común de `references/07-visual/note-templates.md`
> (F75) §6.3 y delega cabecera, apertura y cierre allí.
>
> **Wirings:**
> - `references/07-visual/note-templates.md` (F75) — cabecera canónica, apertura/cierre común, §6.3 patrón resumido.
> - `references/07-visual/density.md` (F76) — reglas R1-R8 ejecutables por `scripts/validate/density_check.py`.
> - `references/04-authoring/properties.md` (F47) — frontmatter canónico; `source-bearing` recomendado (§6.3).
> - `references/04-authoring/inline-marks.md` (F46) — marcas `{src:blk_xxxx}`, `[[term:nombre]]`, `[[note:id]]`.
> - `references/04-authoring/block-directives.md` (F45) — directivas `:::step`, `:::warning`, `:::danger`, `:::note`, `:::example`, `:::console`, `:::collapsible`.
> - `references/04-authoring/depth-layers.md` (F51) — capas L1/L2/L3; `## Procedimiento` siempre L2.
> - `references/05-note-types/concept.md` (F78) — paraguas común (perfil-activación, checklist).
> - `references/05-note-types/api-reference.md` (F79) —姊妹: `api-reference` documenta **qué** hace cada subprograma; `procedure` documenta **cómo** orquestarlos en un flujo.

---

## §1 · Propósito y alcance

Una nota `procedure` documenta **un flujo operativo reproducible**: el
procedimiento para hacer X de principio a fin, con verificación en cada paso.
El lector debe poder ejecutarlo sin volver al manual: cada paso lleva comando,
salida esperada y criterio de "cómo sé que funcionó".

`procedure` cubre operaciones de operaciones: despliegues, migraciones,
mantenimiento (VACUUM, log rotation), recuperación ante desastres,
configuración de un servicio nuevo, rotación de secretos,演练 de incidentes.
La diferencia con `api-reference` (F79) es de granularidad y objetivo:
`api-reference` describe **una** API; `procedure` orquesta **varias** APIs o
sub-comandos en un orden específico para lograr un objetivo compuesto.

**Fuera de alcance:**

- Documentación de una API individual → `api-reference` (F79).
- Comparación entre 3+ procedimientos → `comparison` (F87).
- Resolución de un error específico → `error-troubleshooting` (F82).
- Análisis arquitectónico de un sistema → `architecture` (F83).
- Tutorial puramente conceptual → `concept` (F78).

---

## §2 · Estructura de la nota

### §2.1 · Frontmatter (orden canónico, `source-bearing` recomendado)

```yaml
---
title: "<verbo en imperativo + objeto>: <contexto si aplica>"
note-type: procedure
status: draft | published
summary: "<≤ 200 chars, 1 línea>"
reading-time-minutes: <int ≥ 1>
tags: [type/procedure, domain/<uno o más>, product/<nombre>]
source: "<ruta al runbook o fuente>"
source-type: docs | runbook | wiki | article
source-anchor: "<page|section_path>"
source-url: "<opcional>"
retrieved: <YYYY-MM-DD>
vendor: "<proveedor, si aplica>"
product: "<nombre del producto>"
product-version: "<versión>"
related: "[[note:...]], [[note:...]]"
---
```

`source-bearing` es **recomendado** (F75 §6.3). Las 5 universales son
obligatorias en `status: published` (INV-P5). `vendor`/`product` cuando aplica.

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

## Objetivo
```

### §2.3 · Las 8 secciones específicas + 2 opcionales + 3 de cierre

Orden obligatorio; cada sección es H2 salvo indicación.

| # | Sección | Estado | Notas |
|---|---|---|---|
| 1 | `## TL;DR` | obligatoria | Heredada F75. ≤ 60 palabras / 8 líneas (R1). |
| 2 | `## Objetivo` | obligatoria | 1-2 frases: qué se logra y por qué. |
| 3 | `## Aplicabilidad` | obligatoria | En qué contextos SÍ aplica y en cuáles NO (≥ 1 bullet cada uno). |
| 4 | `## Precondiciones verificadas` | obligatoria | Lista de estado externo que debe cumplirse **antes** del primer paso, cada uno con criterio de verificación. |
| 5 | `## Impacto y reversibilidad` | obligatoria | Tabla con: ventana de indisponibilidad, datos afectados, **rollback** documentado **o** declaración explícita de irreversibilidad (criterio #2). |
| 6 | `## Procedimiento` | obligatoria | Lista numerada de pasos, cada uno con `### Paso N: <título>` + comando + salida esperada + verificación (criterio #1). |
| 7 | `## Verificación final` | obligatoria | ≥ 1 criterio global que confirma el éxito del procedimiento completo. |
| 8 | `## Errores frecuentes` | obligatoria | ≥ 1 `:::danger` o `:::warning` por error con causa típica + diagnóstico + resolución. Pasos destructivos usan `:::danger` (criterio #3). |
| 9 | `## Troubleshooting` | opcional | `:::warning` con casos menos frecuentes (heredado §6.3). |
| 10 | `## Notas` | opcional | `:::note` con aclaraciones laterales (heredado §6.3). |
| 11 | `## Backlinks` | obligatoria si hay aristas | Cierre común. |
| 12 | `## Queries` | obligatoria si queries activas | Cierre común. |
| 13 | `## Ver también` | opcional si `related:` | Cierre común. |

Para procedimientos extensos (> 10 pasos), `## Procedimiento` se **sub-divide**
en `## Procedimiento: <sub>` (anti-patrón §6.3 — no más de 10 pasos por bloque).

### §2.4 · Capas (heredado de F51)

| Capa | Marcador | Contenido |
|---|---|---|
| L1 | `{layer:l1}` | Solo `## TL;DR`. ≤ 60 palabras / 8 líneas. |
| L2 | `{layer:l2}` | Secciones 2-10 (objetivo → notas). 70-90% del total. |
| L3 | `{layer:l3}` | Variantes, casos edge o apéndices. `:::collapsible` con `default_open: false` si > 100 líneas (R7). |

Si la nota tiene `len(body_lines) < 50`, las 3 capas son **optativas** y basta L2.

### §2.5 · Autoevaluación (F102)

Tipos de pregunta asignados a `procedure` (ver
`references/09-study/self-evaluation.md` §3):

| Tipo de pregunta | Asignado |
|---|---|
| Recuerdo | — |
| Aplicación | ✅ |
| Diagnóstico | — |
| Decisión | — |
| Predicción | ✅ |

Notas: por defecto aplicación + predicción (el lector transfiere a un caso
y anticipa el efecto del comando). Recuerdo se añade solo si la nota
enumera comandos (sub-tipo recordatorio). La nota puede declarar
`self-evaluation-types` como superset del default.

---

## §3 · Componentes mínimos

| Componente | Mínimo | Fuente |
|---|---|---|
| Cabecera (F75 §2) | 5 campos en orden | F75 §2.1 |
| `## TL;DR` | ≤ 60 palabras / 8 líneas | F76 R1 |
| `## Objetivo` | 1-2 frases; el L1 es esta misma frase | esta fase |
| `## Aplicabilidad` | ≥ 1 bullet SÍ + ≥ 1 bullet NO | esta fase |
| `## Precondiciones verificadas` | ≥ 2 precondiciones, cada una con criterio de verificación | esta fase |
| `## Impacto y reversibilidad` | Tabla con ventana + datos afectados + rollback **o** declaración de irreversibilidad | criterio #2 |
| `## Procedimiento` | Pasos numerados; cada paso tiene comando + salida esperada + verificación | criterio #1 |
| Verificación por paso | Cada paso tiene 1 línea `**Verificación:** <cómo sé que funcionó>` | criterio #1 |
| Pasos destructivos | Cualquier paso que borre datos, modifique estado persistente o sea irreversible usa `:::danger` | criterio #3 |
| `## Verificación final` | ≥ 1 criterio global post-procedimiento | esta fase |
| `## Errores frecuentes` | ≥ 1 bloque `:::danger` o `:::warning` con causa + resolución | esta fase |
| `## Backlinks` | obligatorio si hay aristas | F75 §4 |
| Anclaje visual | ≥ 1 cada 200 palabras de prosa (R3); tablas, callouts y code con caption cuentan | F76 R3 |
| Marcas `{src:blk_xxxx}` | ≥ 1 cada 200 palabras en bloques fácticos cuando hay SDM | F46 + F76 R8 |
| Máximo de pasos en `## Procedimiento` | ≤ 10; si > 10, dividir en `## Procedimiento: <sub>` | F75 §6.3 anti-patrón |

### §3.1 · Patrón canónico de un paso

Cada paso sigue esta estructura:

```markdown
### Paso N: <verbo en imperativo> <objeto>

<contexto del paso en ≤ 3 frases>

```bash
comando --flag valor
```

**Salida esperada:**
```
línea esperada 1
línea esperada 2
```

**Verificación:** <cómo sé que funcionó: exit code, output específico, estado observable>
```

Reglas:

- El comando va en bloque `code` con lenguaje explícito (`bash`, `sql`, `kubectl`, etc.).
- La salida esperada es opcional pero **obligatoria** cuando el SDM la da o cuando el éxito es ambiguo.
- La verificación es **obligatoria** (criterio #1). Formato: 1 línea `**Verificación:** ...`.
- Si el paso es destructivo, abre con `:::danger` antes del comando y referencia el rollback de `## Impacto y reversibilidad`.

---

## §4 · Reglas de contenido

### §4.1 · Densidad y estructura (R1-R8 de F76)

- **R1** `## TL;DR` ≤ 60 palabras / 8 líneas.
- **R2** Cada párrafo del L2 ≤ 200 palabras.
- **R3** ≥ 1 anclaje visual cada 200 palabras. **Cada bloque `:::danger`/`:::warning`/`:::example` cuenta como anclaje y resetea el contador**.
- **R4** ≤ 3 callouts consecutivos sin prosa intermedia. Para pasos consecutivos que requieren todos `:::danger`, añadir 1 párrafo de transición entre ellos.
- **R5** ≤ 5 viñetas consecutivas.
- **R6** Cada H2/H3 tiene ≥ 1 párrafo, tabla, callout, figura, diagrama, ecuación o code.
- **R7** Cualquier sección > 100 líneas → `:::collapsible` con `default_open: false`. En `procedure` el plegable es **menos común** que en `concept` o `api-reference` porque el lector sigue los pasos en orden; si es necesario, dividir en sub-procedimientos.
- **R8** Densidad `{src:}` ≥ 0.80 sobre bloques fácticos.

### §4.2 · Marcas inline (F46)

- **`{src:blk_xxxx}`** — 12 caracteres hexadecimales (INV-I5). Cada paso lleva `{src:}` si la operación viene del SDM/runbook.
- **`[[term:nombre]]`** — primera aparición del término (INV-I2). Usar para: nombres de servicios, flags, rutas del sistema de archivos.
- **`[[note:id]]`** — enlaces a notas `concept`, `error-troubleshooting` o `api-reference` relacionadas. Cada paso puede enlazar a su nota `concept` (qué hace el comando) o `error-troubleshooting` (qué hacer si falla).

### §4.3 · Directivas de bloque (F45)

| Sección | Directiva preferida | Justificación |
|---|---|---|
| `## Procedimiento` paso destructivo | `:::danger` | F45 §6 fila 2 + criterio #3. |
| `## Procedimiento` paso reversible pero cuidadoso | `:::warning` | F45 §6 fila 1. |
| `## Procedimiento` paso con output específico | `:::example` + `:::console` | F45 §10.21 (console) para transcripción literal. |
| `## Precondiciones verificadas` | Lista con bullets + `:::tip` para verificar | F75 §5.1. |
| `## Impacto y reversibilidad` | Tabla GFM | F75 §5.1. |
| `## Errores frecuentes` | `:::danger` por error destructivo, `:::warning` por error reversible | F45 §6. |
| `## Notas` | `:::note` | F45 §6 fila 12. |
| Comando inline | Bloque `code` con lenguaje explícito | F45 §10 ejemplos. |

### §4.4 · Diferencias operativas

| Concepto | Definición operativa |
|---|---|
| **Precondición** | Estado externo que DEBE cumplirse antes del primer paso. Es **requisito**, no opcional. |
| **Verificación por paso** | Estado observable que confirma que ese paso **se completó correctamente**. |
| **Verificación final** | Estado observable que confirma que **todo el procedimiento** se completó correctamente (objetivo logrado). |
| **Rollback** | Pasos para revertir los efectos del procedimiento si algo sale mal **después** de iniciar. |
| **Irreversibilidad** | Declaración explícita de que el procedimiento **no se puede deshacer** (criterio #2: la nota debe declararlo, no callarlo). |

Una nota `procedure` sin verificación por paso falla el criterio #1.
Una nota sin rollback **ni** declaración de irreversibilidad falla el criterio #2.
Una nota con pasos destructivos sin `:::danger` falla el criterio #3.

### §4.5 · Anti-patrones

1. **"Paso sin verificación"** — falta la línea `**Verificación:** ...`. Solución: añadir siempre.
2. **"Procedimiento irreversible sin declaración"** — el SDM dice "no se puede deshacer" pero la nota lo calla. Solución: declarar en `## Impacto y reversibilidad` con la razón.
3. **"Paso destructivo sin `:::danger`"** — un `DROP TABLE` o `rm -rf` envuelto en prosa. Solución: anteponer `:::danger` con el resumen del riesgo.
4. **"Más de 10 pasos en `## Procedimiento`"** — anti-patrón §6.3. Solución: dividir en `## Procedimiento: <sub>`.
5. **"Comando sin bloque `code` con lenguaje"** — `docker ps` en línea de párrafo. Solución: bloque `code` con `bash`.
6. **"Salida esperada inventada"** — outputs que no vienen del SDM ni del comportamiento conocido. Solución: marcar como `aprox.` o eliminarla.
7. **"Procedimiento sin rollback cuando aplica"** — un `DELETE FROM ...` sin plan de recuperación. Solución: añadir paso de rollback en `## Impacto y reversibilidad`.
8. **"Sección solo de viñetas"** (R6) — `## Aplicabilidad` con 1 lista sin contexto. Solución: añadir 1 párrafo introductorio.
9. **"Pasos sin comando, solo prosa"** — "configura el firewall" sin el `ufw`/`iptables` exacto. Solución: comando literal en bloque `code`.
10. **"Mezcla procedimiento y tutorial conceptual"** — explica qué es TCP en medio de los pasos. Solución: enlazar a `concept: tcp` y mantener el paso conciso.

---

## §5 · Activación por perfil

La profundidad de `## Errores frecuentes` y la inclusión de `## Troubleshooting`
y `## Notas` están controladas por perfil (`assets/profile.template.yaml`, F11):

```yaml
notes:
  types:
    procedure:
      include_troubleshooting: true        # default: true
      include_notes: true                  # default: true
      include_rollback_section: true       # default: true (criterio #2)
      destructive_steps_use_danger: true   # default: true (criterio #3)
      min_steps: 2                         # default: 2
      max_steps_per_block: 10              # default: 10 (anti-patrón §6.3)
      require_verification_per_step: true  # default: true (criterio #1)
```

| Campo | Default | Significado |
|---|---|---|
| `include_troubleshooting` | `true` | Incluye `## Troubleshooting`; con `false`, se omite. |
| `include_notes` | `true` | Incluye `## Notas`; con `false`, se omite. |
| `include_rollback_section` | `true` | Si el procedimiento es reversible, `## Impacto y reversibilidad` debe incluir la columna Rollback. |
| `destructive_steps_use_danger` | `true` | Si `false`, los pasos destructivos pueden ir sin `:::danger` (no recomendado; rompe criterio #3). |
| `min_steps` | `2` | Mínimo de pasos en `## Procedimiento` (procedimientos con 1 paso son `api-reference` o `cheatsheet`). |
| `max_steps_per_block` | `10` | Si > 10, dividir en sub-procedimientos. |
| `require_verification_per_step` | `true` | Si `false`, el validador no exige la línea `**Verificación:**` (no recomendado; rompe criterio #1). |

Precedencia F11 §7.4: **prompt > perfil > defaults**.

---

## §6 · Checklist de cierre

Esta sección resume el bloque del tipo. La fuente normativa es
`references/10-quality/checklists-by-type.md` §4.3. Esta copia se conserva
para que el agente que carga solo este archivo tenga la lista delante;
cualquier cambio debe aplicarse primero allí y después sincronizarse aquí.

### §6.1 · Bloqueantes [B]

- [ ] [B] Cabecera con 5 campos en orden (F75 §2.1).
- [ ] [B] `## TL;DR` ≤ 60 palabras / 8 líneas (R1).
- [ ] [B] Las 8 secciones obligatorias (Objetivo → Errores frecuentes) presentes y en orden.
- [ ] [B] `## Procedimiento` con pasos numerados (≥ 2 pasos por `min_steps`).
- [ ] [B] Cada paso tiene `**Verificación:**` explícita (criterio #1).
- [ ] [B] Pasos destructivos envueltos en `:::danger` con resumen del riesgo (criterio #3).
- [ ] [B] `## Impacto y reversibilidad` con tabla que incluye columna Rollback **o** declaración explícita de irreversibilidad (criterio #2).
- [ ] [B] `## Verificación final` con ≥ 1 criterio global post-procedimiento.
- [ ] [B] `## Errores frecuentes` con ≥ 1 `:::danger` o `:::warning`.
- [ ] [B] Densidad `{src:}` ≥ 0.80 sobre bloques fácticos (R8).
- [ ] [B] `density_check.py --note <path>` exit 0.
- [ ] [B] `validate_ir.py --ir <path>` exit 0.

### §6.2 · Recomendados [R]

- [ ] [R] ≤ 10 pasos por bloque en `## Procedimiento` (anti-patrón §6.3).
- [ ] [R] Cada paso con bloque `code` con lenguaje explícito.
- [ ] [R] Cierre: `## Backlinks` + `## Queries` si queries activas.

---

## §7 · Nota mínima viable

Ejemplo canónico de ~30-40 líneas para un procedimiento reversible simple.
Pasa `density_check.py --strict` exit 0.

```markdown
---
title: "Rotar logs de nginx sin reiniciar"
note-type: procedure
status: draft
tags: [type/procedure, domain/sysadmin, product/nginx]
source: "Nginx docs — log rotation"
source-type: docs
source-anchor: "logging"
retrieved: 2026-09-27
product: nginx
product-version: "1.27"
---

# Rotar logs de nginx sin reiniciar

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Rota los access/error logs de nginx enviando USR1 al master; no requiere reinicio y mantiene los file descriptors abiertos. |
| **Procedencia** | Nginx docs — log rotation (docs) §logging · recuperado 2026-09-27 |
| **Versión** | nginx 1.27 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 1 min |

## TL;DR
Rotar logs de nginx sin reiniciar requiere 2 comandos: `mv` al archivo nuevo y `kill -USR1` al master para que reabra los descriptores. La ventana de indisponibilidad es 0 (los file descriptors originales siguen aceptando escritura hasta que el master cierra los archivos rotados). {src:blk_p0000000a01b}

{layer:l2}

## Objetivo
Liberar espacio en disco rotando los logs de nginx sin perder requests ni reiniciar workers.

## Aplicabilidad
- **SÍ:** nginx 1.x en Linux con logs en `/var/log/nginx/`.
- **NO:** nginx en Windows (USR1 no soportado); servicios que aún no fueron configurados para logrotate (`/etc/logrotate.d/nginx` ausente).

## Precondiciones verificadas
- Nginx corriendo: `systemctl status nginx` muestra `active (running)`.
- Permiso de escritura en `/var/log/nginx/`: `test -w /var/log/nginx && echo OK`.

## Impacto y reversibilidad

| Aspecto | Detalle |
|---|---|
| Ventana de indisponibilidad | 0 segundos (master sigue aceptando) |
| Datos afectados | Solo los archivos de log; cero impacto en requests |
| Rollback | `kill -USR1 <master-pid>` reabre los logs originales desde el backup `access.log.1` |

## Procedimiento

### Paso 1: Mover el log actual a un archivo `.1`
```bash
sudo mv /var/log/nginx/access.log /var/log/nginx/access.log.1
```

**Verificación:** `ls -la /var/log/nginx/access.log*` muestra `access.log.1` con el tamaño anterior.

### Paso 2: Enviar USR1 al master para que reabra descriptores
```bash
sudo kill -USR1 $(cat /var/run/nginx.pid)
```

**Verificación:** `ls -la /var/log/nginx/access.log` muestra un archivo nuevo de 0 bytes propiedad del worker de nginx.

## Verificación final
`curl -s http://localhost/healthz > /dev/null && tail -1 /var/log/nginx/access.log` muestra el request recién hecho en la última línea del log nuevo.

## Errores frecuentes
:::warning
**`access.log.1` con permisos de root y nginx no puede escribir.** El nuevo archivo hereda los permisos del `mv`. Solución: `sudo chown www-data:adm /var/log/nginx/access.log` antes del USR1.
:::

## Backlinks
- [[note:nginx-logrotate-config]] — la configuración recomendada de `logrotate.d/nginx`.
```

Esta nota mínima (~50 líneas de cuerpo) cumple R1-R8 de F76 y los 3
criterios ROADMAP. Sirve de **referencia de forma**; el contenido se
sustituye por el del runbook en producción.

---

## §8 · Wirings y referencias cruzadas

- **F11** `assets/profile.template.yaml` — defaults de §5 (`min_steps`, `max_steps_per_block`, `require_verification_per_step`).
- **F12** `references/04-authoring/notemark.md` — directivas `:::step` (F45 §10.16), `:::warning`, `:::danger`, `:::note`, `:::example`, `:::console`.
- **F44** `references/03-knowledge/note-plan.md` — el selector asigna `procedure` cuando la unidad es un flujo operativo (no un parámetro).
- **F45** `references/04-authoring/block-directives.md` — directivas usadas en `## Procedimiento`, `## Errores frecuentes`, `## Notas`, `## Troubleshooting`.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` en pasos; `[[term:nombre]]` en servicios/flags; `[[note:id]]` a `concept`/`error-troubleshooting`/`api-reference`.
- **F47** `references/04-authoring/properties.md` — frontmatter de 20 propiedades; `source-bearing` recomendado.
- **F51** `references/04-authoring/depth-layers.md` — capas L1/L2/L3; `## Procedimiento` siempre L2.
- **F72** `references/07-visual/tokens.md` — colores semánticos de las directivas.
- **F75** `references/07-visual/note-templates.md` — cabecera, apertura/cierre común, §6.3 patrón resumido + anti-patrón de > 10 pasos.
- **F76** `references/07-visual/density.md` — tabla cerrada R1-R8 ejecutable por `scripts/validate/density_check.py`.
- **F77** `evals/visual/` — verificación visual multi-destino.
- **F78** `references/05-note-types/concept.md` — paraguas común; F80 hereda §5 y §6.
- **F79** `references/05-note-types/api-reference.md` — `procedure` orquesta comandos documentados por `api-reference` (enlazar por `[[note:docker-run]]` etc.).
- **F82** `references/05-note-types/error-troubleshooting.md` — cada error en `## Errores frecuentes` puede enlazar a su nota dedicada.
- **F83** `references/05-note-types/architecture.md` — los flujos diagramados en `architecture` se ejecutan siguiendo `procedure`.
- **F86** `references/05-note-types/chapter-digest.md` — los capítulos de un libro técnico resumen varios procedimientos; la nota `chapter-digest` los enlaza.

---

## §9 · Verificación al cierre de la fase

- `wc -l references/05-note-types/procedure.md` ≤ 500 líneas.
- §2 con 4 subsecciones (frontmatter, apertura, secciones, capas).
- §3 con tabla de componentes mínimos con ≥ 13 filas + §3.1 patrón canónico de paso.
- §4 con 5 subsecciones (densidad, marcas, directivas, diferencias operativas, anti-patrones).
- §5 con la tabla de campos del perfil y sus defaults.
- §6 con el checklist de cierre de ≥ 13 items.
- §7 con la nota mínima viable (≥ 25 líneas, pasa `density_check.py`).
- §8 con al menos 15 wirings documentados.
- §9 lista de verificación explícita.

**Criterios de aceptación del ROADMAP F80:**

1. _Todo paso tiene criterio de "cómo sé que funcionó"._ → battery C1 verifica que cada paso (`### Paso N:`) lleva `**Verificación:**` (regex).
2. _Existe rollback o declaración de irreversibilidad._ → battery C2 verifica que `## Impacto y reversibilidad` contiene la palabra `Rollback` o `irreversible`/`irreversibilidad`.
3. _Los pasos destructivos usan la intención `danger`._ → battery C3 verifica que cada `:::danger` en `## Procedimiento` envuelve un paso destructivo (palabras clave: `DROP`, `DELETE`, `rm -rf`, `TRUNCATE`, `kubectl delete`, `kubectl drain`, `kubectl cordon`, `terraform destroy`, `--force`, etc.).
