---
title: "MVCC"
note-type: concept
status: published
summary: "Control de concurrencia multiversión en PostgreSQL: cada fila lleva marcas de versión y los lectores ven un snapshot estable sin locks."
reading-time-minutes: 6
tags: [type/concept, domain/databases, f78/concept, f94/intuition-first]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
source-url: ""
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:pg_dump]], [[note:transactions]]"
---

# MVCC

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. El contenido principal sigue el patrón de 5 etapas
> definido por `references/06-writing/intuition-first.md` (F94).

## TL;DR

MVCC da a cada transacción un snapshot en su `BEGIN`; cada fila lleva
`xmin` y `xmax`, y la fila solo es visible si su versión cae dentro del
snapshot del lector. No hay locks de lectura.

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

## Trampas

:::warning
**Falsa suposición de visibilidad inmediata.** Un escritor que ejecuta
`UPDATE` y `COMMIT` puede no ser visible para un lector que abrió
transacción antes del commit. Causa: el snapshot del lector se fija en su
`BEGIN`. Evitación: usa `READ COMMITTED` y reintenta la lectura, o acepta
la latencia del snapshot.
:::

## Resumen

- MVCC sustituye locks de lectura por marcas de versión por fila. {src:blk_a3f1}
- Cada transacción ve un snapshot estable en su `BEGIN`. {src:blk_a3f1}
- `VACUUM` libera versiones viejas. {src:blk_a3f1}

## Cuándo NO usarlo

- Si la carga es 99% escritura con cardinalidad reducida (las versiones
  se acumulan rápido y `VACUUM` se vuelve costoso). Alternativa: lock
  pesimista explícito. {external}

## Límites y alternativas

| Concepto | [[note:vacuum]] | Lock pesimista explícito (`SELECT FOR UPDATE`) |
|---|---|---|
| Visibilidad de versiones | sí (con `VACUUM`) | n/a |
| Latencia de lectura | estable | variable (locks) |

## Relacionados

- [[note:transactions]] — prerrequisito (qué es una transacción).
- [[note:vacuum]] — derivado (recolector de versiones).
- [[note:pg_dump]] — caso de uso (no bloquea lecturas por MVCC).

## Backlinks

- [[note:transactions]]
- [[note:vacuum]]

## Queries

```dataview
LIST FROM [[note:mvcc]] AND -"templates"
```
