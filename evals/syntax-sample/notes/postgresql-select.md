---
title: "SQL SELECT — sintaxis BNF (PostgreSQL 16)"
note-type: syntax
status: draft
summary: "Sintaxis BNF completa del statement SELECT de PostgreSQL 16 con todas las cláusulas (incluyendo opcionales raras como DISTINCT ON, GROUP BY (), WINDOW, FETCH, FOR UPDATE/SHARE)."
tags: [type/syntax, domain/databases, product/postgresql]
source: "PostgreSQL 16 — SELECT reference"
source-type: docs
source-anchor: "sql-select"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:api-reference-postgres-select]], [[note:postgres-connection-errors]]"
---

# SQL SELECT — sintaxis BNF (PostgreSQL 16)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Sintaxis BNF completa del statement SELECT de PostgreSQL 16 con todas las cláusulas (incluyendo opcionales raras como DISTINCT ON, GROUP BY (), WINDOW, FETCH, FOR UPDATE/SHARE). |
| **Procedencia** | PostgreSQL 16 — SELECT reference (docs) §sql-select · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
SELECT recupera filas con cláusulas opcionales (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET, WINDOW) y modificadores (WITH, UNION, FOR UPDATE). La BNF cubre > 30 cláusulas; las opcionales raras (`DISTINCT ON`, `GROUP BY ()`, `USING operator`) se documentan aquí. {src:blk_f00000000001}

{layer:l2}

## Convención de metasímbolos
| Símbolo | Significado |
|---|---|
| `::=` | se define como |
| `\|` | alternativa |
| `[...]` | opcional (0 o 1 ocurrencia) |
| `{...}` | 0 o más repeticiones |
| `(...)` | agrupación |
| `<...>` | no-terminal (referencia a otra regla) |

## Sintaxis
```bnf
[WITH [RECURSIVE] cte_name [(column_list)] AS (select_stmt) [, ...]]
SELECT [ALL | DISTINCT [ON (expr [, ...])]] {src:blk_eeeeff000001}
    select_list
    [FROM from_list]
    [WHERE condition]
    [GROUP BY expr [, ...] [HAVING condition]]
    [WINDOW window_definition [, ...]]
    [{ UNION | INTERSECT | EXCEPT } [ALL | DISTINCT] select_stmt]
    [ORDER BY expr [ASC | DESC | USING operator] [, ...]]
    [LIMIT {count | ALL}]
    [OFFSET start]
    [FETCH {FIRST | NEXT} [count] {ROW | ROWS} ONLY]
    [FOR {UPDATE | NO KEY UPDATE | SHARE | KEY SHARE} [OF table [, ...]] [NOWAIT | SKIP LOCKED]]
# {src:blk_ccddeebf0001}
```

## Cláusula por cláusula

### `WITH [RECURSIVE] cte` {src:blk_aabbccddee01}
Common Table Expressions: define subqueries con nombre que pueden referenciarse en el FROM. `RECURSIVE` permite queries recursivos (ej: árboles). {src:blk_f00000000002}

### `SELECT [ALL | DISTINCT [ON (expr)]]` {src:blk_aabbccddee02}
ALL (default) o DISTINCT eliminan duplicados. `DISTINCT ON (expr)` aplica DISTINCT solo sobre las primeras columnas (PostgreSQL extension). {src:blk_f00000000003}

### `select_list` {src:blk_aabbccddee03}
Lista de expresiones separadas por comas: `*`, `table.*`, `expr [AS alias]`. Puede incluir window functions (`row_number() OVER (...)`). {src:blk_f00000000004}

### `FROM from_list` {src:blk_aabbccddee04}
Tablas, vistas, subqueries (entre paréntesis), `VALUES (...)`, o funciones de tabla (`generate_series`). JOINs: `[INNER|LEFT|RIGHT|FULL [OUTER]] JOIN`, `CROSS JOIN`, `LATERAL`. {src:blk_f00000000005}

### `WHERE condition` {src:blk_aabbccddee05}
Filtra filas antes de agregación. Operadores: `=`, `<>`, `<`, `>`, `BETWEEN`, `IN`, `IS NULL`, `LIKE`, `ILIKE`, `~` (regex). {src:blk_f00000000006}

### `GROUP BY expr [, ...] [HAVING condition]` {src:blk_aabbccddee06}
Agrupa filas con el mismo valor. `GROUP BY ()` agrupa todas las filas en un solo grupo (opcional raro). HAVING filtra grupos. {src:blk_f00000000007}

### `WINDOW window_definition` {src:blk_aabbccddee07}
Define ventanas para window functions: `window_name AS ([PARTITION BY expr] [ORDER BY expr] [frame_clause])`. {src:blk_f00000000008}

### `UNION | INTERSECT | EXCEPT [ALL] [select_stmt]` {src:blk_aabbccddee08}
Combina resultados. `ALL` mantiene duplicados. Sin paréntesis, la evaluación es de izquierda a derecha. {src:blk_f00000000009}

### `ORDER BY expr [ASC | DESC | USING operator]` {src:blk_aabbccddee09}
Ordena por 1+ expresiones. `USING operator` usa un operador (`<`, `>`). NULLs: `NULLS FIRST|LAST` (opcional raro). {src:blk_f00000000010}

### `LIMIT / OFFSET / FETCH` {src:blk_aabbccddee0a}
Limita y desplaza el resultado. `LIMIT n OFFSET m` ≈ `FETCH FIRST n ROWS ONLY OFFSET m ROWS`. {src:blk_f00000000011}

### `FOR UPDATE | NO KEY UPDATE | SHARE | KEY SHARE` {src:blk_aabbccddee0b}
Locking pesimista: bloquea filas seleccionadas hasta `COMMIT`. `NOWAIT` falla inmediatamente si la fila está lockeada. `SKIP LOCKED` omite filas lockeadas. {src:blk_f00000000012}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[WITH? RECURSIVE? cte AS select] --> B[SELECT] {src:blk_eeeeff000002}
    B --> C[ALL/DISTINCT ON?] {src:blk_eeeeff000003}
    C --> D[select_list] {src:blk_eeeeff000004}
    D --> E[FROM?]
    E --> F[WHERE?]
    F --> G[GROUP BY? HAVING?] {src:blk_eeeeff000005}
    G --> H[WINDOW?] {src:blk_eeeeff000006}
    H --> I[UNION/INTERSECT/EXCEPT?] {src:blk_eeeeff000007}
    I --> J[ORDER BY?] {src:blk_eeeeff000008}
    J --> K[LIMIT? OFFSET? FETCH?] {src:blk_eeeeff000009}
    K --> L[FOR UPDATE? NOWAIT/SKIP LOCKED?] {src:blk_eeeeff00000a}
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee000c}

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** SELECT básico sin FROM.

```sql
SELECT 1 + 1;
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee000d}

:::example
**Ejemplo 2 — + FROM + WHERE:** Filtrado.

```sql
SELECT id, name FROM users WHERE active = true AND created_at > '2026-01-01'; {src:blk_eeeeff00000b}
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee000e}

:::example
**Ejemplo 3 — + GROUP BY + HAVING + ORDER BY + LIMIT:** Agregación completa.

```sql
SELECT country, count(*) AS n {src:blk_eeeeff00000c}
FROM users
WHERE active = true {src:blk_eeeeff00000d}
GROUP BY country {src:blk_eeeeff00000e}
HAVING count(*) > 100 {src:blk_eeeeff00000f}
ORDER BY n DESC
LIMIT 10;
# {src:blk_ccddeebf0005}
```
::: {src:blk_bbccddee000f}

## Contraejemplos

:::warning
**Input:** `SELECT FROM users;` (sin columnas).
**Error literal:** `ERROR:  syntax error at or near "FROM"`
**Línea 1: SELECT FROM users;`
**Causa:** el parser espera `select_list` antes de `FROM`.
**Solución:** especificar columnas o `SELECT * FROM users;`.
::: {src:blk_bbccddee0010}

:::warning
**Input:** `SELECT * FROM users ORDER BY x;` cuando `x` no existe.
**Error literal:** `ERROR:  column "x" does not exist`
**Causa:** el parser no detecta el error de sintaxis (es sintácticamente válido); la validación semántica falla al resolver la columna.
**Solución:** verificar el nombre de la columna con `\d users` antes.
::: {src:blk_bbccddee0011}

## Backlinks
La sintaxis de SELECT se complementa con el API programático (psql, pgx) y los errores típicos del parser; los enlaces muestran ambos aspectos. {src:blk_f00000000070}

- [[note:api-reference-postgres-select]] — el API programático equivalente.
- [[note:postgres-connection-errors]] — errores típicos del parser.
