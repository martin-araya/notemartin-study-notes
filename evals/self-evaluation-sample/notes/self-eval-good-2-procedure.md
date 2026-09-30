---
title: "Backup lógico con pg_dump -Fc"
note-type: procedure
status: published
summary: "Procedimiento para respaldar y restaurar una base de datos PostgreSQL con formato custom (-Fc) y pg_restore."
reading-time-minutes: 3
language: es
tags: [type/procedure, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [aplicacion, prediccion]
---


# Backup lógico con pg_dump -Fc

## TL;DR

`pg_dump -Fc` produce un archivo binario comprimido que `pg_restore`
puede aplicar selectivamente. {src:blk_b11f8e02c1d3}

## Procedimiento

### 1. Crear el backup

:::step
Ejecutar `pg_dump -Fc -d <dbname> -f <ruta.backup>`.

El flag `-Fc` selecciona el formato custom (comprimido). El archivo
resultante es binario, no legible por `cat`, y permite restauración
selectiva por tabla o esquema. {src:blk_b11f8e02c1d3}
:::

### 2. Verificar integridad

:::step
Ejecutar `pg_restore -l <ruta.backup>` para listar el contenido sin
restaurar. Confirma que las tablas esperadas están presentes. La salida
es texto plano con cabecera y líneas tipo `<id> <tipo> <nombre>`. {src:blk_b11f8e02c1d3}
:::

### 3. Restaurar

:::step
Ejecutar `pg_restore -d <dbname> <ruta.backup>` desde un objetivo
donde la base de datos destino ya existe. Para una restauración limpia
añade `-c` (drop before create) o `--clean`. {src:blk_b11f8e02c1d3}
:::

## Errores frecuentes

:::warning
`pg_restore` no crea la base de datos destino. Debes crearla primero
con `createdb` o `CREATE DATABASE`.
:::
{src:blk_b11f8e02c1d3}

## Autoevaluación

Tipos asignados a `procedure`: aplicación, predicción.

### Aplicación

:::collapsible{default_open=false}
Dados una base `app_prod` y un archivo `backup_20250929.backup`, ¿qué comando usarías para restaurar solo la tabla `orders`?
`pg_restore -d app_prod --table=orders backup_20250929.backup`.
> Fundamento: {src:blk_b11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con un backup de 50 GB en formato custom, ¿qué flag añadirías para paralelizar la restauración?
`pg_restore -j 8 ...` (donde `8` es el número de workers concurrentes; ajustar a CPUs disponibles).
> Fundamento: [[note:pg-restore-parallelism#workers]]
:::

:::collapsible{default_open=false}
Para verificar que el backup es íntegro antes de borrarlo, ¿qué comando usarías?
`pg_restore -l backup.backup` lista el contenido sin aplicar; complementa con `pg_restore --stats` para estadísticas.
> Fundamento: [[note:pg-restore-verify#listing]]
:::

### Predicción

:::collapsible{default_open=false}
¿Qué ocurre si ejecutas `pg_restore` sobre una base de datos destino que no existe?
Falla con error `FATAL: database "<name>" does not exist`; debes crearla primero.
> Fundamento: {src:blk_b11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué log esperas si el archivo de backup está corrupto en su cabecera?
`pg_restore` emite `pg_restore: error: header is not valid` y termina con exit code 1.
> Fundamento: [[note:pg-restore-errors#corrupt-header]]
:::

:::collapsible{default_open=false}
Si la base destino tiene una tabla `orders` con más filas que el backup, ¿qué sucede al restaurar con `-c` (clean)?
`pg_restore -c` borra (`DROP`) los objetos antes de crearlos; las filas extra de la tabla destino se pierden.
> Fundamento: [[note:pg-restore-flags#clean]]
:::
